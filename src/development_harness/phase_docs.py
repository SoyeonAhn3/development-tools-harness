"""Pinned project-owned writing rules and non-executable Markdown templates."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from .files import require_single_link, target
from .model import HarnessError, digest


RESOURCE_NAMES = ("SKILL.md", "references/phase-template.md")
SLOTS = {
    "overview": {"overview", "phases", "documents", "requirements", "questions",
                 "skill_version", "profile_hash"},
    "phase": {"number", "title", "goal", "prerequisites", "technology", "scope", "deliverables",
              "tasks", "requirements", "code_context", "questions", "date", "skill_version", "profile_hash"},
}
TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")


def skill_directory():
    # Resolve from the executing harness, never the target project's or user's skills.
    module = Path(__file__).resolve()
    if not (module.parent / "_phase_doc").is_dir() and module.parent.parent.name == "src":
        return module.parents[2] / ".agents" / "skills" / "phase-doc"
    return module.parent / "_phase_doc"


def templates(profile):
    text = profile["files"]["references/phase-template.md"]["text"]
    blocks = {}
    for kind, required in SLOTS.items():
        for language in ("en", "ko"):
            key = kind + ":" + language
            start, end = "<!-- harness:" + key + " -->", "<!-- /harness:" + key + " -->"
            if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
                raise HarnessError("phase-doc template needs exactly one ordered block: " + key)
            body = text.split(start, 1)[1].split(end, 1)[0].strip()
            if set(TOKEN.findall(body)) != required or "{{" in TOKEN.sub("", body) or "}}" in TOKEN.sub("", body):
                raise HarnessError("phase-doc template has missing/unknown slots: " + key)
            blocks[key] = body
    return blocks


def validate_profile(profile):
    try:
        if set(profile) != {"name", "version", "format", "sha256", "files"}:
            raise ValueError("unexpected profile fields")
        if profile["name"] != "phase-doc" or profile["format"] != 1 or not isinstance(profile["version"], str):
            raise ValueError("unsupported profile")
        if set(profile["files"]) != set(RESOURCE_NAMES):
            raise ValueError("missing writing resources")
        for item in profile["files"].values():
            if set(item) != {"text", "sha256"} or not isinstance(item["text"], str):
                raise ValueError("invalid writing resource")
            raw = item["text"].encode("utf-8")
            if not raw or len(raw) > 64_000 or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("writing resource digest mismatch")
        expected = digest({k: v for k, v in profile.items() if k != "sha256"})
        if expected != profile["sha256"]:
            raise ValueError("writing profile digest mismatch")
        templates(profile)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise HarnessError("Invalid recorded phase-doc writing rules: " + str(exc)) from exc
    return profile


def load_profile():
    root = skill_directory()
    files = {}
    try:
        if root.is_symlink() or root.is_junction():
            raise HarnessError("Linked phase-doc skill directory is not supported.")
        for name in RESOURCE_NAMES:
            path = target(root, name)
            before = path.stat()
            require_single_link(path, before)
            if not 0 < before.st_size <= 64_000:
                raise HarnessError("phase-doc resource is empty or too large: " + name)
            raw = path.read_bytes()
            after = path.stat()
            target(root, name)
            require_single_link(path, after)
            if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
                raise HarnessError("phase-doc changed while reading; retry registration.")
            files[name] = {"text": raw.decode("utf-8"), "sha256": hashlib.sha256(raw).hexdigest()}
        frontmatter = files["SKILL.md"]["text"].split("---", 2)[1]
        version = re.search(r'^\s+version:\s*["\x27]?([\w.-]+)', frontmatter, re.MULTILINE)
        if not re.search(r"^name: phase-doc\s*$", frontmatter, re.MULTILINE) or not version:
            raise HarnessError("phase-doc SKILL.md needs its name and metadata.version.")
    except (OSError, UnicodeError, IndexError) as exc:
        raise HarnessError("Cannot load the harness's phase-doc skill/template; restore its installation: " + str(exc)) from exc
    profile = {"name": "phase-doc", "version": version[1], "format": 1, "files": files}
    profile["sha256"] = digest(profile)
    return validate_profile(profile)


def profile_summary(profile):
    return {**{k: v for k, v in profile.items() if k != "files"},
            "files": {name: item["sha256"] for name, item in profile["files"].items()}}


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers, rows):
    return "\n".join("| " + " | ".join(cell(x) for x in row) + " |"
                     for row in [headers, ["---"] * len(headers), *rows])


def quote(text):
    # Source Markdown is evidence, not links relative to the generated document.
    fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", text)), default=3))
    return fence + "text\n" + text + "\n" + fence


def requirement_text(items, lang):
    return "\n\n".join(f"- **{r['id']}** {r['text'][lang]} — {r['disposition']} / {r['phase_id'] or '—'}\n\n"
                       + r["rationale"][lang] + "\n\n" + r["verification"][lang] + "\n\n" + quote(r["source_quote"])
                       for r in items) or ("None mapped." if lang == "en" else "대응된 항목 없음.")


def question_text(plan, lang):
    return "\n".join(f"- {q['id']} ({'blocking' if q['blocking'] else 'nonblocking'}): {q['text'][lang]}"
                     for q in plan["questions"]) or ("None reported." if lang == "en" else "보고된 질문 없음.")


def phase_names(plan):
    names = {}
    for index, phase in enumerate(plan["phases"], 1):
        digits = re.findall(r"\d+", phase["id"])
        number = int(digits[-1]) if digits else index
        title = re.sub(r"^Phase\s*\d+\s*[-—:]*\s*", "", phase["title"]["en"], flags=re.IGNORECASE)
        words = re.findall(r"[A-Za-z][A-Za-z0-9]*", title)
        name = "".join(w[:1].upper() + w[1:] for w in words)[:64]
        if number < 1 or not name:
            raise HarnessError("A Phase needs a positive number and an English document title: " + phase["id"])
        names[phase["id"]] = (number, f"Phase{number}_{name}.md")
    if len({v[1].casefold() for v in names.values()}) != len(names):
        raise HarnessError("Phase document names collide; revise the Phase identifiers/titles.")
    return names


def render_documents(plan, profile, registered_at):
    validate_profile(profile)
    blocks, names = templates(profile), phase_names(plan)
    result = {}
    shared = {"skill_version": profile["version"], "profile_hash": profile["sha256"],
              "date": datetime.fromtimestamp(registered_at, timezone.utc).date().isoformat()}
    def fill(key, values):
        return TOKEN.sub(lambda m: str(values[m[1]]), blocks[key]) + "\n"

    for index, phase in enumerate(plan["phases"]):
        number, name = names[phase["id"]]
        current = phase["id"] == plan["current_phase"]
        sections = []
        for lang in ("en", "ko"):
            en = lang == "en"
            outline = ("Outline only; detail Tasks using preceding Phase results."
                       if en else "개요만 작성. 선행 Phase 결과를 반영해 Task를 상세화한다.")
            tasks = table(["Task", "Work", "Acceptance", "Verification", "Dependencies", "Files"] if en else
                          ["Task", "작업", "완료 기준", "검증 방법", "선행 작업", "파일"],
                          [[t["id"], t["title"][lang], t["acceptance"][lang], t["verification"][lang],
                            ", ".join(t["depends_on"]) or "—", ", ".join(t["paths"])] for t in plan["tasks"]])
            prior = plan["phases"][index - 1] if index else None
            prerequisites = (("Preceding planned Phase: " if en else "계획 순서상 선행 Phase: ")
                             + prior["id"] + " — " + prior["title"][lang]) if prior else (
                                 "Verify project readiness and unresolved questions." if en else "프로젝트 준비 상태와 미해결 질문을 확인한다.")
            code = "\n\n".join(f"- `{c['path']}` ({c['kind']}): {c['summary'][lang]}\n\n" + quote(c["evidence"])
                               for c in plan["code_context"]) if current else outline
            values = {**shared, "number": number, "title": phase["title"][lang], "goal": phase["goal"][lang],
                      "prerequisites": prerequisites, "technology": plan["technology"][lang],
                      "scope": plan["overview"][lang] if current else outline,
                      "deliverables": phase["exit_criteria"][lang], "tasks": tasks if current else outline,
                      "requirements": requirement_text([r for r in plan["requirements"] if r["phase_id"] == phase["id"]], lang),
                      "code_context": code or ("No related code supplied." if en else "제공된 관련 코드 없음."),
                      "questions": question_text(plan, lang)}
            sections.append(fill("phase:" + lang, values))
        result[name] = sections[0] + "\n---\n\n" + sections[1]

    for lang, filename in (("en", "Plan.md"), ("ko", "Plan_ko.md")):
        values = {**shared, "overview": plan["overview"][lang],
                  "phases": "\n\n".join(f"### {p['id']} — {p['title'][lang]}\n\n{p['goal'][lang]}\n\n{p['exit_criteria'][lang]}"
                                         for p in plan["phases"]),
                  "documents": "\n".join(f"- [{p['id']} — {p['title'][lang]}]({names[p['id']][1]})" for p in plan["phases"]),
                  "requirements": requirement_text(plan["requirements"], lang), "questions": question_text(plan, lang)}
        result[filename] = fill("overview:" + lang, values)
    return result
