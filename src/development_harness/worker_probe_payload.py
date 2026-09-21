"""Trusted synthetic payload; invoked only against worker_probe-created paths."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def observe(specification, generation):
    label = specification["role"] + ":" + generation
    result = {"pid": os.getpid(), "writes": {}}
    for name, raw_path in specification["paths"].items():
        try:
            Path(raw_path).write_text(label + "\n", encoding="utf-8")
            result["writes"][name] = {"outcome": "written"}
        except PermissionError as exc:
            result["writes"][name] = {"outcome": "denied", "errno": exc.errno,
                                      "winerror": getattr(exc, "winerror", None)}
        except OSError as exc:
            result["writes"][name] = {"outcome": "error", "error": str(exc)}
    try:
        with socket.create_connection(("127.0.0.1", specification["port"]), timeout=3) as connection:
            connection.sendall(label.encode("ascii"))
            response = connection.recv(16)
        result["network"] = {"outcome": "connected" if response == b"ack" else "error"}
    except OSError as exc:
        result["network"] = {"outcome": "denied", "error": str(exc),
                             "errno": exc.errno, "winerror": getattr(exc, "winerror", None)}
    return result


def main():
    specification = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "--child" in sys.argv[2:]:
        print(json.dumps(observe(specification, "child")))
        return
    parent = observe(specification, "parent")
    child = subprocess.run([sys.executable, "-I", "-B", __file__, sys.argv[1], "--child"],
                           capture_output=True, text=True, encoding="utf-8", timeout=10,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        child_result = json.loads(child.stdout)
    except ValueError:
        child_result = {"error": "Child did not return observations", "stderr": child.stderr}
    print(json.dumps({"parent": parent, "child": child_result, "child_exit_code": child.returncode}))


if __name__ == "__main__":
    main()
