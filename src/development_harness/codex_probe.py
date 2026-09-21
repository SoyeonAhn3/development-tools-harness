"""Verify the real CLI's tool manifest and reject forced unsafe tool calls locally.

The loopback provider receives synthetic probes only, never project data or tokens.
It is not an AI invocation and is not counted as one.
"""

import http.server
import json
from pathlib import Path
import subprocess
import threading

from .codex_adapter import DISABLED_CODE_MODE_NOTICE, environment, parse_events
from .model import HarnessError
from .processes import Job


ALLOWED_TOOLS = {"request_user_input"}  # No file/process/network capability.
DENIED_TOOLS = ("exec_command", "shell", "apply_patch", "view_image", "web.run",
                "mcp__probe__send", "spawn_agent")
PROBE_PROMPT = "Synthetic permission probe; no project data."
PROBE_SCHEMA = {"type": "object", "properties": {"probe": {"type": "string", "enum": ["ok"]}},
                "required": ["probe"], "additionalProperties": False}


def verify_capabilities(adapter):
    manifests, replies, failures = [], [], []
    marker = adapter.directory / "forbidden-tool-write.txt"
    if marker.exists():
        raise HarnessError("Permission probe marker already exists; preserve and inspect it.")
    schema_path = adapter.directory / "probe-schema.json"
    schema_path.write_text(json.dumps(PROBE_SCHEMA), encoding="utf-8")

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                if self.headers.get("Authorization"):
                    raise ValueError("Unexpected authentication on the local probe.")
                size = int(self.headers.get("Content-Length", 0))
                if not 0 < size < 2_000_000:
                    raise ValueError("Unexpected probe request size.")
                request = json.loads(self.rfile.read(size))
                output_format = request.get("text", {}).get("format", {})
                if output_format.get("type") != "json_schema" or output_format.get("schema") != PROBE_SCHEMA:
                    raise ValueError("CLI did not transmit the required output schema.")
                if not manifests and not any(
                        item.get("role") == "user" and any(
                            part.get("type") == "input_text" and part.get("text") == PROBE_PROMPT
                            for part in item.get("content", [])) for item in request.get("input", [])):
                    raise ValueError("CLI did not transmit the synthetic stdin prompt.")
                names = {tool.get("name", tool.get("type")) for tool in request.get("tools", [])}
                manifests.append(sorted(names))
                if not names <= ALLOWED_TOOLS:
                    raise ValueError("Unsafe tool manifest: " + ", ".join(sorted(names - ALLOWED_TOOLS)))
                for item in request.get("input", []):
                    if item.get("type") in {"function_call_output", "custom_tool_call_output"}:
                        replies.append(item)
                number = len(manifests) - 1
                if number < len(DENIED_TOOLS):
                    tool = DENIED_TOOLS[number]
                    item = {"type": "function_call", "id": "fc_" + str(number),
                            "call_id": "probe_" + str(number), "name": tool,
                            "arguments": json.dumps({"cmd": "Set-Content -LiteralPath '" + str(marker) + "' -Value forbidden",
                                                     "command": "echo forbidden", "path": str(marker)})}
                    if tool == "apply_patch":
                        item = {"type": "custom_tool_call", "id": "fc_" + str(number),
                                "call_id": "probe_" + str(number), "name": "apply_patch",
                                "input": "*** Begin Patch\n*** Add File: " + marker.as_posix() +
                                         "\n+forbidden\n*** End Patch"}
                else:
                    item = {"type": "message", "id": "msg_probe", "role": "assistant",
                            "content": [{"type": "output_text", "text": '{"probe":"ok"}', "annotations": []}]}
                response = {"id": "resp_" + str(number), "object": "response", "status": "completed",
                            "output": [item], "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
                events = [{"type": "response.created", "response": dict(response, status="in_progress", output=[])},
                          {"type": "response.output_item.added", "output_index": 0, "item": item},
                          {"type": "response.output_item.done", "output_index": 0, "item": item},
                          {"type": "response.completed", "response": response}]
                body = "".join("event: " + e["type"] + "\ndata: " + json.dumps(e) + "\n\n" for e in events).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                failures.append(str(exc))
                self.send_error(400)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    worker = None
    job = Job()
    try:
        args = adapter.arguments(schema_path, probe_url=f"http://127.0.0.1:{server.server_port}/v1")
        worker = subprocess.Popen(args, cwd=adapter.directory, env=environment(), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        job.assign(worker.pid)
        try:
            output, error = worker.communicate(PROBE_PROMPT.encode("utf-8"), timeout=45)
        except subprocess.TimeoutExpired as exc:
            raise HarnessError("Codex capability probe timed out; live calls are disabled.") from exc
        (adapter.directory / "permission-probe.jsonl").write_bytes(output)
        (adapter.directory / "permission-probe.stderr.log").write_bytes(error)
        if worker.returncode or failures or marker.exists():
            raise HarnessError("Codex capability probe failed; inspect permission-probe logs. " + "; ".join(failures))
        blocked = set()
        for reply in replies:
            result = str(reply.get("output", "")).lower()
            if result == "aborted" or any(word in result for word in (
                    "unrecognized", "unknown tool", "unsupported", "not found", "denied",
                    "patch rejected: writing is blocked by read-only sandbox")):
                blocked.add(reply.get("call_id"))
        expected = {"probe_" + str(i) for i in range(len(DENIED_TOOLS))}
        (adapter.directory / "permission-probe-results.json").write_text(
            json.dumps({"manifests": manifests, "replies": replies, "failures": failures}, indent=2), encoding="utf-8")
        if not manifests or not expected <= blocked:
            raise HarnessError("Codex did not prove rejection of every forced tool call; live calls are disabled.")
        notices = []
        response, _ = parse_events(output.decode("utf-8"), allowed_notices=(DISABLED_CODE_MODE_NOTICE,), notices=notices)
        if response != {"probe": "ok"}:
            raise HarnessError("Codex did not return the expected synthetic JSON response.")
        return {"tool_manifest": manifests[0], "rejected_tools": list(DENIED_TOOLS),
                "probe_requests": len(manifests), "probe_actual_ai_calls": 0,
                "stdin_verified": True, "output_schema_verified": True, "json_response_verified": True,
                "probe_notices": notices}
    finally:
        job.close()
        if worker:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=10)
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
