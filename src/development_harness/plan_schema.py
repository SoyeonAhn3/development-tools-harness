"""Strict plan structure, cross references and bilingual human review documents."""

import re

from .model import HarnessError, relative_path


def obj(**properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


TEXT = {"type": "string"}
WORDS = obj(en=TEXT, ko=TEXT)
SCHEMA = obj(
    overview=WORDS,
    current_phase=TEXT,
    phases=array(obj(id=TEXT, title=WORDS, goal=WORDS, exit_criteria=WORDS)),
    tasks=array(obj(id=TEXT, title=WORDS, requirements=array(TEXT), paths=array(TEXT),
                    acceptance=WORDS, verification=WORDS, depends_on=array(TEXT))),
    requirements=array(obj(id=TEXT, text=WORDS, source_quote=TEXT,
                           disposition={"type": "string", "enum": ["implement", "reuse", "defer", "exclude"]},
                           phase_id=TEXT, verification=WORDS, rationale=WORDS)),
    code_context=array(obj(path=TEXT, summary=WORDS, evidence=TEXT,
                           kind={"type": "string", "enum": ["explicit", "inferred"]})),
    questions=array(obj(id=TEXT, text=WORDS, blocking={"type": "boolean"})),
)


def check_shape(value, schema, where="plan"):
    kind = schema["type"]
    expected = {"object": dict, "array": list, "string": str, "boolean": bool}[kind]
    if type(value) is not expected:
        raise HarnessError(f"{where}: expected {kind}.")
    if kind == "object":
        if set(value) != set(schema["properties"]):
            raise HarnessError(f"{where}: missing or unknown fields.")
        for key, child in schema["properties"].items():
            check_shape(value[key], child, where + "." + key)
    elif kind == "array":
        if len(value) > 200:
            raise HarnessError(f"{where}: too many items.")
        for i, item in enumerate(value):
            check_shape(item, schema["items"], f"{where}[{i}]")
    elif kind == "string":
        if len(value) > 10_000 or (not value.strip() and not where.endswith(".phase_id")):
            raise HarnessError(f"{where}: empty or oversized text.")
        if "enum" in schema and value not in schema["enum"]:
            raise HarnessError(f"{where}: unsupported value.")


def unique(items, label):
    ids = [x["id"] for x in items]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", x) for x in ids):
        raise HarnessError("Invalid or duplicate " + label + " identifiers.")
    return set(ids)


def validate_plan(plan, files):
    check_shape(plan, SCHEMA)
    phases = unique(plan["phases"], "Phase")
    tasks = unique(plan["tasks"], "Task")
    requirements = unique(plan["requirements"], "requirement")
    unique(plan["questions"], "question")
    current = plan["current_phase"]
    if current not in phases or not tasks or not requirements:
        raise HarnessError("A valid current Phase, Tasks and requirements are required.")
    task_order = set()
    implemented = set()
    mapped = {item["id"]: item for item in plan["requirements"]}
    for task in plan["tasks"]:
        if not task["requirements"] or not set(task["requirements"]) <= requirements:
            raise HarnessError("Every Task must reference existing requirements.")
        if not set(task["depends_on"]) <= task_order:
            raise HarnessError("Task dependencies must precede the Task; cycles/forward references are invalid.")
        task_order.add(task["id"])
        for key in task["requirements"]:
            req = mapped[key]
            if req["phase_id"] != current or req["disposition"] not in {"implement", "reuse"}:
                raise HarnessError("Current Tasks cannot implement excluded or later-Phase requirements.")
            implemented.add(key)
        if not task["paths"]:
            raise HarnessError("Every Task needs related or proposed file paths.")
        for path in task["paths"]:
            relative_path(path)
            if any(p in {".codex", ".agents", "harness-project.json"} for p in path.split("/")):
                raise HarnessError("A plan cannot propose changing harness policies/configuration.")
    for req in plan["requirements"]:
        if req["source_quote"] not in files[0]["text"]:
            raise HarnessError("Requirement source_quote is not in the designated specification: " + req["id"])
        if req["disposition"] == "exclude":
            if req["phase_id"]:
                raise HarnessError("Excluded requirements must use an empty phase_id and explain the reason.")
        elif req["phase_id"] not in phases:
            raise HarnessError("Requirement refers to an unknown Phase.")
        if req["disposition"] == "defer" and req["phase_id"] == current:
            raise HarnessError("Deferred requirements must belong to another Phase.")
        if req["disposition"] == "implement" and req["phase_id"] == current and req["id"] not in implemented:
            raise HarnessError("Current implementation requirement has no Task: " + req["id"])
    sources = {item["path"]: item["text"] for item in files[1:]}
    seen = set()
    for item in plan["code_context"]:
        if item["path"] not in sources or item["evidence"] not in sources[item["path"]]:
            raise HarnessError("Code evidence is not in the selected source files: " + item["path"])
        seen.add(item["path"])
    if sources and not seen:
        raise HarnessError("Related-code summary is required when source files were supplied.")
    return plan


def render(plan, language):
    en = language == "en"
    lines = ["# " + ("Development plan" if en else "개발 계획"), "", plan["overview"][language], "",
             "## " + ("Overall Phases" if en else "전체 Phase"), ""]
    for phase in plan["phases"]:
        lines += [f"### {phase['id']} — {phase['title'][language]}", "", phase["goal"][language], "",
                  ("Exit criteria: " if en else "완료 기준: ") + phase["exit_criteria"][language], ""]
    lines += ["## " + ("Current Phase Tasks: " if en else "현재 Phase Task: ") + plan["current_phase"], ""]
    for task in plan["tasks"]:
        lines += [f"### {task['id']} — {task['title'][language]}", "",
                  ("Requirements: " if en else "요구사항: ") + ", ".join(task["requirements"]), "",
                  ("Files: " if en else "파일: ") + ", ".join(task["paths"]), "",
                  ("Depends on: " if en else "선행 Task: ") + (", ".join(task["depends_on"]) or "—"), "",
                  ("Acceptance: " if en else "완료 기준: ") + task["acceptance"][language], "",
                  ("Verification: " if en else "검증 방법: ") + task["verification"][language], ""]
    lines += ["## " + ("Requirements mapping" if en else "요구사항 대응표"), ""]
    for req in plan["requirements"]:
        lines += [f"- **{req['id']}** {req['text'][language]} — {req['disposition']} / {req['phase_id'] or '—'}",
                  "  " + req["rationale"][language], "  " + req["verification"][language], "",
                  ("  Source: " if en else "  원문 근거: ") + req["source_quote"].replace("\n", " "), ""]
    lines += ["## " + ("Related code" if en else "관련 코드"), ""]
    for item in plan["code_context"]:
        lines += [f"- `{item['path']}` ({item['kind']}): {item['summary'][language]}", "",
                  "  " + item["evidence"].replace("\n", " "), ""]
    lines += ["## " + ("Questions" if en else "확인할 사항"), ""]
    for item in plan["questions"]:
        lines += [f"- {item['id']} ({'blocking' if item['blocking'] else 'nonblocking'}): {item['text'][language]}", ""]
    if not plan["questions"]:
        lines += ["None reported." if en else "보고된 질문 없음.", ""]
    lines += ["Planning approval does not authorize implementation. Reuse is a proposal, not verified completion."
              if en else "계획 승인은 구현 실행을 승인하지 않습니다. 재사용은 계획이며 검증 완료 근거가 아닙니다.", ""]
    return "\n".join(lines)
