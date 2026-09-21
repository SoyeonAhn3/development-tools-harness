# Phase 2 — Planning `✅ Completed`

> Connect one AI tool and generate a plan the user can review against the project.

**Prerequisites**: [Phase 1](Phase1_Foundation.md) accepted. The user selected ChatGPT authentication through Codex CLI and authorized implementation on 2026-09-18. Planner capability enforcement has been verified with the installed CLI.

**Technology**: Python + pytest, SQLite; inherit the version fixed in Phase 1.

**Plan status**: Technical verification and user acceptance are complete as of 2026-09-21, including Task 2.6 planning-only harness dogfooding. P2-01 and CLI compatibility fixes passed all 156 tests. Supported CLI versions are 0.154.0 and 0.155.1. The later Task 2.7 skill/template integration passed 172 tests and a real example call. One real Planner call produced the Phase 3 draft, followed by a recorded manual revision. Requirements come from the user-selected specification; related code in the designated project may also be analyzed. Decision Desk is the first later real-use project, after harness dogfooding. Temporary test projects remain integration fixtures.

**Completed**: 2026-09-21.

**User acceptance (2026-09-21)**: The user explicitly stated “phase2 인수” after reviewing the implementation, verification results and remaining scope. Tasks 2.1–2.7, the P2-01 fix and CLI compatibility improvements are accepted, completing Phase 2. This records acceptance of the harness development Phase; generated-plan approvals remain separate. Phases 3–4 implementation has not started. Planning without a passing pytest baseline remains an additional scope candidate and is not included in this acceptance.

## Overview

Implement project registration/baseline checks and the real Planner Adapter, following specification §§2, 5 and 7.3. Verify actual execution permissions before granting the Adapter access. Use generated plans when reviewing the next harness Phase; this is planning-only self-use.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | One real Adapter and documented permission/authentication boundaries | ✅ Verified |
| 2 | Project registration, configuration and baseline checks | ✅ Verified |
| 3 | Overall/current Phase plans, requirements mapping and relevant-code summary | ✅ Verified |
| 4 | Plan review/approval connection and actual Planner-call records | ✅ Verified |
| 5 | Planning-only harness dogfooding and reviewed Phase 3 draft | ✅ Verified; Phase 2 accepted |
| 6 | Project phase-doc skill/template, pinned writing rules and bilingual Phase documents | ✅ Verified |

## Verification & Exit Criteria

| Task | Work / Acceptance criteria | Verification |
|---|---|---|
| 2.1 | Connect the installed Codex CLI using existing ChatGPT authentication; enforce and record a Planner permission boundary before project analysis. | Local capability/permission probes and a minimal real call; prohibited access must fail before effects. |
| 2.2 | Register a specification, explicit related-code inputs and validation commands; preserve user files and keep runtime state outside OneDrive. | Invalid paths, links, unavailable inputs, concurrent registration and configuration changes. |
| 2.3 | Run actual baseline validation before planning; stop on failed, missing, skipped, interrupted or zero tests. | Real subprocess fixtures and existing validation regressions. |
| 2.4 | Generate and validate overall/current Phase plans, requirement mapping, code evidence, uncertainties and English/Korean documents. | Structured-output validation, source-reference checks and manual comparison of a real generated plan. |
| 2.5 | Record attempts, interrupted calls and approval waiting; bind approval to the reviewed input/plan versions without starting implementation. | Resume, stale evidence, idempotent approval, malformed responses and provider failures. |
| 2.6 | Verify the integrated CLI and use the Planner on the harness's next Phase; record manual corrections and remaining boundaries. | Verified 2026-09-21: 156 baseline tests, one real Planner call, reviewed v2 and unchanged source inputs. User result acceptance remains separate. |
| 2.7 | Load the project phase-doc skill/template for new planning Runs, preserve its version and generate bilingual Phase documents. | 172 regression tests, skill validation, isolated wheel resources and one real planning call. Old Runs retain their original format. |

- A prepared small project passes actual baseline tests and yields the overall Phase plan plus current Tasks, acceptance criteria and verification methods. Missing tools/documents/commands, failed checks and zero tests stop with actionable information.
- Plan contents identify related code and conventions, distinguish explicit rules from inferred patterns, and map requirements to current/later work, reuse or justified exclusion. Blocking ambiguities are surfaced. Reuse has a Phase and verification method, not an assumed pass.
- User approval references the reviewed plan version. Changed scope requires updated approval; unchanged approval is retained. Planning does not authorize implementation.
- Verify allowed file access and denied edits to policy/approval storage, Git writes, installation and unsupported external transfer. Permit only the selected AI service communication needed for the authorized call. Unsupported risky operations stop before execution; prompt instructions alone are not evidence of isolation.
- Record actual Planner call attempts, stage times, interruptions and approval waiting separately. Project-wide planning calls are not duplicated across Phases; unavailable token/cost data is not invented.

**Evidence**: pytest integration fixtures for registration/approval; real Adapter permission probes and a saved plan manually compared with source requirements/code. Completion requires successful checks and user acceptance.

**Results (2026-09-18)**: All **123 tests passed** (63 existing, 60 new); `pip check` reported no broken requirements. A minimal authenticated live call and one real example planning call succeeded. The example's two baseline tests passed; one AI attempt produced a bilingual plan with five mapped requirements and two Tasks. Manual comparison confirmed the proposed negative-input validation matches the specification and existing positive/zero behavior. Test approval was idempotent, fake execution was blocked, and the source files stayed unchanged. This fixture approval is not user acceptance of Phase 2.

- Permission checks use the actual Codex executable against a loopback provider: eight synthetic requests, zero AI calls, and seven forced tool categories rejected. No marker file was written. Every real planning call repeats this check and pins the executable hash.
- Regression coverage includes stale specification/code/configuration, unexpected user files, hard links, artifact tampering, revision approval invalidation, blocking questions, malformed/duplicate JSON, baseline failures and interrupted publication. Actual inert subprocesses verify timeout/interrupt cleanup and unknown completion time; they do not consume AI calls.
- Local evidence lives under `%LOCALAPPDATA%/development-tools-harness/`: `phase2-tests.xml`, `phase2-probes/live-smoke-result.json`, and `phase2-demo/d98457898bca4153a09473f370ea0a47/`. The example run is `ebbf7cd2ca4e40a786da97b55614c685`; `approval-checks.json` records the CLI approval/blocked-execution checks.

### Issue P2-01 — Long Windows runtime path (fix and regression complete)

- **Observed**: On 2026-09-18, planning-only dogfooding on a separate harness snapshot passed all 123 baseline tests, then stopped while creating `<attempt-id>.schema.json`. The call directory was 217 characters and the complete schema path was 262 characters. This environment returned `[Errno 2] No such file or directory` at `codex_adapter.py`'s schema write; the path length is the identified cause to address.
- **Original impact**: The Planner process had not been dispatched (`dispatched=false`), so this dogfooding attempt made zero AI calls and produced no Phase 3 plan. The successful small example and prior test results did not cover this longer-path case. Task 2.6 remained incomplete at that point; the successful rerun is recorded below.
- **Evidence**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/2085ced4918341da99a99ed03df06676/plan.json`; run `729a78364bd746bbb2be2439996ae018`, attempt `97677feca038475aae33826fb18cb3b7`.
- **Fix (2026-09-21)**: Use `schema.json`, `events.jsonl` and `stderr.log` inside each existing unique call directory. For the reproduced directory length, the schema path is now 229 characters instead of 262. Attempt records retain their IDs and log paths and now also record the schema path. Calls remain separated by their unique directories.
- **Regression evidence**: `test_adapter_long_runtime_path_preserves_attempt_artifacts` reproduced the original `FileNotFoundError` before the fix and passed afterward. It uses two local Python worker processes in separate 217-character call directories to verify schema reads, stdin/response handling, recorded artifact paths and preservation of earlier artifacts. No AI call is used.
- **Checks at the time of the path fix**: 123 passed, 1 failed, 0 skipped out of 124 tests; `pip check` found no broken requirements. The installed-CLI test stopped because the installed version was `codex-cli 0.155.1`, while the single reviewed version was `0.154.0`. The compatibility work below subsequently resolved that separate failure. Original report: `%LOCALAPPDATA%/development-tools-harness/phase2-p2-01-tests.xml`.
- **Rerun outcome**: The 2026-09-21 harness planning run succeeded with a 217-character call directory and 229-character schema path, and its generated plan was reviewed. The filename change fixes the reproduced case; it does not add general support for arbitrary-length Windows paths.
- **User decision**: The user resumed P2-01 development on 2026-09-21 after the original record-only deferral, then authorized compatibility improvements and the next planning-verification step. The user subsequently accepted Phase 2 on 2026-09-21.

### Task 2.6 — Planning-only harness dogfooding (technical verification complete)

On 2026-09-21, a new separate snapshot containing the current source/tests and uncommitted compatibility fixes passed **156 tests, with zero failures or skips**. The snapshot CLI imported its own source. Using the original Phase 3 outline as the specification and 31 related context files, the real Codex CLI 0.155.1 Planner generated a plan in **one AI invocation**. Local permission/I/O probes passed separately and used zero AI calls.

- **Output**: Eight Phase 3 Tasks, 18 mapped requirements and 11 code-context summaries. Preserve [AI v1](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v1/Plan.md), [reviewed v2](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan.md), [manual review](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md) and [verification record](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Evidence.json). The [Phase 3 document](Phase3_Workflow.md) now summarizes the draft Tasks.
- **Manual corrections**: Clarified prerequisite investigation versus live worker admission; made Reviewer read-only and specified actual permission-denial probes; added finding severity/dispositions; restored Phase 4 external-example/MVP verification; corrected an unsupported code-summary implication. `plan-revise` created v2 without another AI call. Both languages were updated.
- **Integrity**: All 41 snapshot files and corresponding original inputs retained their hashes before documentation updates. Six published artifacts were copied into this repository and checked against their recorded hashes. No source/test code changed in this step. The snapshot preserves the pre-update documents for exact source quotations.
- **Recorded timing**: Baseline 32.69 seconds; Planner 328.68 seconds. Approval waiting is separate. The longer planning timeout was explicitly registered as 1,200 seconds for this input; no default timeout changed.
- **Evidence location**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/d8b4b48e8c9047d1a21ae17c93eee60f`; run `45e4c4397c42468e87d9dad81d7b9ce9`, Planner attempt `e07c878c099b46668e921f2cb02d1d9a`. `snapshot.json`, baseline XML/log, call input/schema/events, `revision.json` and `status.json` retain the details. Runtime DB/logs remain outside OneDrive.
- **Remaining boundary**: The recorded `plan-status` reports `awaiting_plan_approval`, no approval and no inspection error. Phase 2 was accepted on 2026-09-21; this does not approve the generated Phase 3 plan. The future Windows worker/test permission mechanism remains unresolved. Investigating that mechanism is Phase 3 development work. No Phase 3 implementation, actual Developer/Reviewer workflow or frozen runner A isolation has been completed.

## Planner & Project Entry

### Purpose / Implementation Files

Project configuration/plans stay in the project; runtime DB/logs stay outside OneDrive.

| File | Responsibility |
|---|---|
| `src/development_harness/project.py` | Register explicit UTF-8 specification/code inputs, check paths/links/secrets and size limits, hash project inputs, preserve versioned artifacts. |
| `src/development_harness/codex_adapter.py` | Select the executable, diagnose supported versions/options/login, apply the text-only capability profile, execute/stop the CLI and validate response events. |
| `src/development_harness/codex_probe.py` | Use a local synthetic provider to inspect the real tool manifest and force prohibited calls before any project analysis. |
| `src/development_harness/plan_schema.py` | Validate bilingual JSON, requirement/code source quotations, identifiers and Task dependencies; render English/Korean documents. |
| `src/development_harness/phase_docs.py` | Load and pin the executing harness's writing resources, validate template slots and render bilingual Phase documents from validated plan data. |
| `.agents/skills/phase-doc/` | Project skill 1.1 and template; source of document headings, layout and writing rules, also bundled in wheels. |
| `src/development_harness/planning.py` | Coordinate registration, baseline checks, planning, interrupted recovery, revisions and input/version-bound human approval. |
| `src/development_harness/cli.py` | Expose planning commands alongside the explicit Phase 1 fixture commands. |
| `model.py`, `store.py`, `runner.py` in the same package | Share validation rules/storage/ownership; prevent real planning records from entering fake execution. |
| `tests/unit/test_planning.py`, `tests/integration/test_planning_cli.py` | Planning regressions, real baseline subprocesses, cleanup and installed-CLI permission probes. |
| `tests/unit/test_codex_compatibility.py` | Multi-version admission, actionable diagnostics, executable precedence, binary changes and startup-notice regressions. |
| `tests/unit/test_phase_docs.py`, `tests/integration/test_phase_doc_package.py` | Template changes, pinned revisions/resume, artifact integrity, target-skill exclusion, legacy compatibility and installed-package resources. |

`harness-project.json` stores relative input paths, validation commands, model and timeout. Each reviewed version creates `Phase/Generated/<run-id>/vN/plan.json`, `Plan.md` and `Plan_ko.md`. New skill-backed Runs also create bilingual `PhaseN_EnglishName.md` files and `writing-profile.json` as described in Task 2.7. The runtime retains exact transmitted inputs, call logs, baseline evidence and approval hashes. A planning attempt counts one dispatched CLI invocation, not an estimated number of underlying HTTP requests. Interrupted calls retain unknown end/duration; approval waiting is accumulated separately. No cost estimate is invented.

### Design Decisions

- Use Codex CLI with ChatGPT login. Authentication stays managed by Codex; no token is copied into project configuration or the harness database. A failed permission probe blocks live project analysis without blocking implementation and regression work.
- Supported versions: **Codex CLI 0.154.0 and 0.155.1**, sharing the reviewed `text-only-v1` profile; configured model **gpt-6-astra**, reasoning effort `medium`. The model defaults to the local Codex model setting or explicit `--model`. Unknown versions receive diagnostics but cannot plan before compatibility review. No broad minimum-version rule, automatic CLI installation, or silent API-key/provider fallback is used.
- The Planner receives a bounded JSON packet through stdin: at most 128,000 bytes per selected file and 320,000 bytes total. All file/process/web/app/agent tools, plugins, hooks, user/project rules and host skill discovery are disabled; the CLI also runs with read-only writes and approval policy `never`. Its actual model tool manifest was empty. The host harness alone writes validated generated documents.
- A restrictive Windows read allowlist required the elevated Windows sandbox backend in this environment. No elevated setup was performed. The verified Phase 2 boundary is the removed model tool capabilities plus read-only write enforcement, **not a general OS read/network allowlist**. Baseline commands still run as trusted user-supplied commands. Isolation of Developer/test processes from runner A and approval storage remains a Phase 3 gate.
- Analyze only the designated specification and related project code. Treat project content as input data, not permission policy; do not include unrelated projects or credentials. Actual input files and versions must be inspectable.
- Introduce project/planning modules alongside the Phase 1 fake-runner contract; real plan approval must never launch fake implementation.
- Use temporary Python/pytest projects for integration checks, then planning-only harness dogfooding. Decision Desk follows self-development verification; its offline file/browser requirements need a later compatible validation setup.
- Load the project-owned `phase-doc` skill and template explicitly for new Runs. The user authorized this local 1.1 integration; the global 1.0 skill remains unchanged. Use template-driven bilingual Phase documents, detailed current Tasks and other Phases at outline level. Keep requirement validation and approval/storage rules in code.
- Keep policy and approval writes owned by the harness, separated from worker permissions. Do not rely on project-controlled instructions to grant permissions.
- Start with one prepared Python/pytest example as proposed in the overview. The user prepares dependencies; no template installer or environment repair engine is added.

### CLI Compatibility and Executable Selection (2026-09-21)

The user authorized four changes: retain multiple reviewed versions, verify actual capabilities, explain failures through `doctor`, and select a separately installed executable. These extend Task 2.1 and preserve existing project configurations and planning records.

- **Support and readiness are separate**: `SUPPORTED_VERSIONS` maps exact version strings to a reviewed profile; both supported versions currently use the same CLI settings. New support is added without replacing the older entry. Version, executable path/hash and applied profile are recorded. Unknown versions are `unverified`, not automatically declared incompatible; their read-only inventory is still collected, but no execution probe or AI call is granted.
- **Actual checks**: Inspect required `exec --help` options, available feature controls, ChatGPT login and configured model. For supported, prepared installations, the local provider verifies stdin and JSON-schema transmission, seven rejected tool categories and JSON event/response parsing. Each real planning call repeats the checks; executable changes during diagnosis or before dispatch invalidate the evidence. Local probes use zero AI calls and do not establish remote model availability or account quota.
- **Diagnostic output**: `doctor` returns JSON with `ready`, actual `version`/`executable`, `support_status`, `supported_versions`, individual `checks` and `next_steps`. Checks distinguish `passed`, `failed`, `unverified` and `not_run`. Exit code is 0 only when ready, otherwise 1 for a completed diagnostic. Login, missing model/options, executable selection and probe failures remain distinct. Existing top-level command/storage errors still use exit code 2.
- **Selection**: `doctor`, `plan` and `plan-resume` accept `--codex-path`. Precedence is explicit option, `DEVELOPMENT_HARNESS_CODEX_PATH`, then existing automatic discovery. An explicit selection must be an existing absolute `.exe` path; an invalid selection never falls back silently. The environment variable is a user/machine setting and is not added to the project-controlled specification/configuration or transmitted to the Planner. A command-line selection applies to that invocation; supply it again on resume or use the environment setting. The harness never installs or replaces Codex automatically.
- **Expected startup notice**: The reviewed text-only profile intentionally disables Code Mode host. The CLI can emit an exact startup `item.error` explaining that this capability is unavailable while still producing a successful text response. Only that exact notice before `turn.started` is accepted and retained in `notices`/`probe_notices`. Other errors, the same notice during a turn, missing completion and `turn.failed` still reject the response; tools remain disabled.
- **Live evidence**: The installed `0.155.1` passed the actual `doctor --codex-path` command and the local stdin/schema/response/permission probe. Two minimal authenticated AI attempts were made: the first exposed the startup-notice parsing issue; the second returned the expected `{"ok": true}` with the notice recorded after the fix. Evidence under `%LOCALAPPDATA%/development-tools-harness/compatibility/`: first attempt `19389930dfdd437095ed94f2b283c774`, successful attempt `31cfb0fa5bfa41bab7d40fc284844ecd`, CLI doctor report `1bf80e60521641499e1a2dcbfbf8e711/doctor.json`. `0.154.0` retains its 2026-09-18 live evidence and has version-contract regression coverage; its binary was not reinstalled/rerun in this session.

**Regression results**: All **156 tests passed**, with no failures or skips; `pip check` found no broken requirements. This includes the P2-01 regression, both supported-version contracts, older/newer/prerelease unknown versions, missing controls, login/model failures, executable selection and resume, changed binaries, and strict error handling. Report: `%LOCALAPPDATA%/development-tools-harness/phase2-compatibility-tests.xml`.

The CLI contracts were checked against local help and the official [non-interactive output documentation](https://learn.chatgpt.com/docs/non-interactive-mode) and [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference). Those references do not replace the installed-binary checks.

### Project phase-doc integration — Task 2.7 (2026-09-21)

The user authorized bringing the skill into this repository and connecting document generation to it. The previous renderer had fixed headings and did not read the skill at runtime; the earlier wording that it used the skill's structure was insufficiently precise.

- **Resources**: [Project SKILL.md](../.agents/skills/phase-doc/SKILL.md) and [template](../.agents/skills/phase-doc/references/phase-template.md) are a local 1.1 adaptation of the global 1.0 skill. The template retains the direct-authoring example and adds four `harness:*` blocks for overview/Phase × English/Korean. Changing titles/layout changes newly registered plans without changing Python. Required data slots are validated; no template code is executed.
- **Actual use**: `register` loads only the executing harness's resources and records their exact contents, version and hashes. The Planner receives these rules and returns validated JSON including the selected/proposed technology. The host renders the template from that JSON. Target-project/global skill discovery stays disabled; the skill does not grant tool or filesystem permissions.
- **Outputs**: New versions retain `plan.json` and `Plan.md`/`Plan_ko.md` overview indexes, and add one `PhaseN_EnglishName.md` per planned Phase, English above Korean, plus `writing-profile.json`. Current Tasks, acceptance and verification are populated from the same validated data; other Phases remain outlines. Source quotations are code evidence, avoiding broken relative links inside quotations. Existing project Phase files are not overwritten.
- **History**: The profile hash is attached to call attempts, plan versions and approvals. Resume and manual revisions use the registration snapshot; edits to the installed skill/template apply only to new Runs. Older records without a profile keep their legacy schema/renderer/artifacts and remain reviewable. No active Run is silently migrated.
- **Packaging**: The wheel includes the same project skill/template. An isolated interpreter loaded identical resources from the built wheel, including an installation directory named `src`, without relying on the checkout or global skill directory.
- **Verification**: All **172 tests passed**, no failures/skips; dependencies are valid. Sixteen additional cases cover actual prompt payloads, template-change behavior, corrupted/missing rules, publication recovery, document/profile tampering, legacy approval/revisions, outline/detail separation and packaging. The skill-creator validator passed using PyYAML in a temporary validation directory; PyYAML was not added to product dependencies. Report: `%LOCALAPPDATA%/development-tools-harness/phase2-skill-tests.xml`.
- **Live result**: A fresh copy of the small planning fixture passed two baseline tests. Codex CLI 0.155.1 made one actual Planner call (75.92 seconds), producing one Phase, two Tasks and five requirements. The generated [bilingual Phase document](Generated/78fb56ab088648e49111258ff74112ad/v1/Phase1_InputValidation.md) was compared with its specification and code: negative-input validation, unchanged zero/positive behavior, existing Python/pytest and no new dependencies were retained. All three original input files stayed unchanged. [Evidence](Generated/78fb56ab088648e49111258ff74112ad/Evidence.json) records exact artifact hashes and the profile. Runtime: `%LOCALAPPDATA%/development-tools-harness/phase2-skill/02527e2443044eb0b0c4ba1d63002adb`; run `78fb56ab088648e49111258ff74112ad`, attempt `5009053163fb4492bcff030d43c82601`. Status remains `awaiting_plan_approval`, with no inspection error or user approval.

**Scope**: This is skill-based planning documentation, not automatic README/dev-log maintenance or implementation-result documentation. Code still owns structured fields, table data, file naming, validation and approval. Customizing the required data contract needs a code change; prose headings/layout live in the template. Semantic plan coverage still needs review. The pytest baseline prerequisite remains; Phase 2 user acceptance was completed on 2026-09-21. Decision Desk was not registered or modified.

### Usage Example

From the repository root, after the README setup and `codex login` (skip login if already authenticated):

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningExample = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningExample -Recurse
& $harnessPython -m development_harness --project $planningExample doctor
& $harnessPython -m development_harness --project $planningExample register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json
& $harnessPython -m development_harness --project $planningExample plan
& $harnessPython -m development_harness --project $planningExample plan-status
```

To use a separately installed CLI, replace the example path with the actual `.exe` location:

```powershell
$selectedCodex = 'C:\Tools\Codex\codex.exe'
& $harnessPython -m development_harness --project $planningExample doctor --codex-path $selectedCodex
& $harnessPython -m development_harness --project $planningExample plan --codex-path $selectedCodex
# Alternatively, set the selection for subsequent commands in this PowerShell session.
$env:DEVELOPMENT_HARNESS_CODEX_PATH = $selectedCodex
& $harnessPython -m development_harness --project $planningExample doctor
```

Review the versioned `Plan.md`/`Plan_ko.md` and mapping before `plan-approve`. This command approves planning only. `baseline` runs tests without AI; `plan-resume` retries interrupted work explicitly. To revise, copy `plan.json` to a separate file outside the input baseline, edit it, and use `plan-revise --from <file>`; changed content creates a new version requiring approval. Resolve blocking questions there. `plan-cancel` preserves files/evidence and releases the run for a new registration. If source/configuration changes, inspect, cancel the unfinished run if necessary, then register again; stale approval is never reused.

## Prerequisites & Development Notes

Phase 1 storage, validation, approval and ownership regressions passed. Source quotations and mapping structure are checked automatically, but full semantic requirement coverage still needs human review. Live Developer/Reviewer orchestration and complete result acceptance are Phase 3 work. Decision Desk has not been registered or executed. Its eventual browser/application stack needs suitable baseline commands; current admission requires an actual pytest check. A project-local Git skill is a user development aid, not a Git capability granted to the harness agents.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the real-connection and planning outline; provider choice and later Task details left explicit. |
| 2026-09-18 | User authorized Phase 2 after selecting ChatGPT/Codex, specification plus related project code, harness dogfooding before Decision Desk, and the proposed implementation scope. Recorded Tasks 2.1–2.6 before implementation. No separate dev-log skill is available. |
| 2026-09-18 | Implemented real planning, bounded inputs, capability probes, baseline admission, bilingual evidence and versioned approval/recovery. Verified 123 tests and the actual example. Added the project-local `harness-github-push` skill without committing/pushing. Separate dev-log omitted because the skill is unavailable. Phase acceptance remains pending. |
| 2026-09-18 | Recorded P2-01 after harness planning dogfooding stopped before AI dispatch on a 262-character schema path. At the user's request, deferred the filename change, regression and rerun; Task 2.6 remains incomplete. |
| 2026-09-21 | Resumed P2-01 at the user's request; shortened call artifact filenames and recorded the schema path. Reproduced the original error and passed the new subprocess regression. Full suite: 123 passed, 1 installed-CLI version failure; dependencies valid. Dogfooding and Phase acceptance remain pending. Updated both language sections; separate dev-log omitted because the skill is unavailable. |
| 2026-09-21 | Implemented the user's four CLI compatibility improvements: cumulative version support, capability/I/O checks, detailed doctor diagnostics and explicit/environment executable selection. Retained 0.154.0 and verified installed 0.155.1; handled the exact disabled-Code-Mode startup notice without accepting other errors. All 156 tests passed, dependencies valid, CLI doctor and minimal live response verified. Updated both language sections; separate dev-log omitted because the skill is unavailable. Task 2.6 remains pending. |
| 2026-09-21 | Completed Task 2.6 technical verification: snapshot baseline 156/156, one real Planner call, successful long path, original/reviewed versioned plans and input/artifact integrity. Recorded manual corrections and detailed the Phase 3 draft in both languages. Phase 2 user acceptance remains pending; separate dev-log omitted because the skill is unavailable. |
| 2026-09-21 | Implemented authorized Task 2.7: project phase-doc 1.1, real rule/template loading, pinned provenance, bilingual per-Phase documents and wheel resources. Preserved legacy Runs. Verified 172 tests, skill validation and one real example call; updated both language sections and README usage. Separate dev-log omitted because no dev-log skill is available; user acceptance remains pending. |
| 2026-09-21 | Recorded the user's explicit “phase2 인수”: accepted Tasks 2.1–2.7, P2-01 and compatibility improvements based on the existing 172 passing tests and live planning evidence. Marked Phase 2 completed and synchronized both languages, the overview, README status and Phase 3 prerequisite. Generated-plan approvals remain separate; Phases 3–4 implementation is not started. Separate dev-log omitted because the skill is unavailable. |

---

# Phase 2 — 실제 연결과 계획 `✅ 완료`

> AI 도구 한 개를 연결하고 사용자가 프로젝트와 대조해 검토할 수 있는 계획을 생성한다.

**선행 조건**: [Phase 1](Phase1_Foundation.md) 인수 완료. 사용자는 ChatGPT 인증을 사용하는 Codex CLI를 선정하고 2026-09-18 구현을 승인했다. 설치된 CLI에서 Planner 도구 권한 집행을 검증했다.

**기술 구성**: Python + pytest, SQLite. Phase 1에서 고정한 버전을 따른다.

**계획 상태**: 2026-09-21 Task 2.6 하네스 계획 기능 dogfooding을 포함한 기술 검증과 사용자 인수를 완료했다. P2-01·CLI 호환성 수정은 전체 156개 검사를 통과했고 지원 버전은 0.154.0과 0.155.1이다. 이후 Task 2.7 스킬·템플릿 연결도 검사 172개와 실제 예제 호출로 검증했다. 실제 Planner 호출 1회로 Phase 3 초안을 생성하고 수동 보완을 기록했다. 요구사항은 사용자가 지정한 기획문서를 기준으로 하며 지정 프로젝트의 관련 코드도 분석할 수 있다. 하네스 dogfooding 이후 Decision Desk를 첫 실사용 프로젝트로 진행한다. 임시 테스트 프로젝트는 통합 검사용으로 유지한다.

**완료일**: 2026-09-21.

**사용자 인수(2026-09-21)**: 구현 내용·검증 결과·남은 범위를 확인한 사용자가 “phase2 인수”라고 명시했다. Task 2.1–2.7, P2-01 수정과 CLI 호환성 개선을 인수해 Phase 2를 완료한다. 이는 하네스 개발 Phase의 결과 인수이며 생성한 계획의 승인은 별도다. Phase 3–4 구현은 미시작 상태다. 통과하는 pytest 기본 검사 없이 계획을 생성하는 기능은 추가 범위 후보로 남으며 이번 인수에 포함하지 않는다.

## 개요

기획서 2·5·7.3장에 따라 프로젝트 등록·기본 검사와 실제 Planner Adapter를 구현한다. Adapter에 접근 권한을 주기 전에 실제 실행 권한을 검증한다. 생성한 계획을 다음 하네스 Phase 검토에 활용하며, 이 단계는 계획 기능만 자체 사용하는 것이다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Adapter 한 개와 권한·인증 경계 기록 | ✅ 검증 |
| 2 | 프로젝트 등록·설정·기본 검사 | ✅ 검증 |
| 3 | 전체·현재 Phase 계획, 요구사항 대응표, 관련 코드 요약 | ✅ 검증 |
| 4 | 계획 검토·승인 연결과 실제 Planner 호출 기록 | ✅ 검증 |
| 5 | 하네스 계획 기능 dogfooding과 검토한 Phase 3 초안 | ✅ 검증, Phase 2 인수 완료 |
| 6 | 프로젝트 phase-doc 스킬·템플릿, 고정한 작성 규칙과 영문·국문 통합 Phase 문서 | ✅ 검증 |

## 검증 및 종료 조건

| Task | 작업 내용 / 완료 기준 | 검증 방법 |
|---|---|---|
| 2.1 | 설치된 Codex CLI의 ChatGPT 인증을 연결하고 프로젝트 분석 전에 Planner 권한 경계를 집행·기록한다. | 로컬 기능·권한 시험과 최소 실제 호출. 금지한 접근은 영향 발생 전에 실패해야 한다. |
| 2.2 | 기획문서·명시적인 관련 코드 입력·검증 명령을 등록한다. 사용자 파일을 보존하고 실행 상태는 OneDrive 밖에 둔다. | 잘못된 경로·링크·입력 누락·등록 경쟁·설정 변경 검사. |
| 2.3 | 계획 생성 전 실제 기본 검사를 수행한다. 실패·도구 누락·생략·중단·테스트 0개는 중단한다. | 실제 하위 프로세스 예제와 기존 검증 회귀 검사. |
| 2.4 | 전체·현재 Phase 계획, 요구사항 대응표, 코드 근거, 불확실성과 영문·국문 문서를 생성·검사한다. | 구조화된 응답·원문 참조 검사와 실제 생성 계획의 수동 대조. |
| 2.5 | 호출 시도·중단·승인 대기를 기록하고 검토한 입력·계획 버전에 승인을 연결한다. 승인으로 구현을 시작하지 않는다. | 재개·오래된 근거·동일 승인 유지·잘못된 응답·제공자 실패 검사. |
| 2.6 | 통합 CLI를 검증하고 하네스 다음 Phase 계획에 Planner를 사용한다. 수동 보완과 남은 경계를 기록한다. | 2026-09-21 검증: 기본 검사 156개, 실제 Planner 호출 1회, 검토한 v2, 원본 입력 보존. 사용자 결과 인수는 별도다. |
| 2.7 | 새 계획 Run에 프로젝트 phase-doc 스킬·템플릿을 읽고 버전을 보존하며 영문·국문 통합 Phase 문서를 생성한다. | 회귀 검사 172개, 스킬 검사, 독립 wheel 리소스와 실제 계획 호출 1회. 이전 Run은 기존 형식을 유지한다. |

- 준비된 작은 프로젝트에서 실제 기본 테스트가 통과하고 전체 Phase와 현재 Task·완료 기준·검증 방법을 생성한다. 도구·문서·명령 누락, 검사 실패·테스트 0개는 준비할 내용을 안내하고 중단한다.
- 계획에 관련 코드·규칙을 기록하고 명시 규칙과 추정 패턴을 구분한다. 요구사항을 현재·후속 작업, 재사용 또는 근거 있는 제외에 연결하고 구현을 막는 불확실성을 표시한다. 재사용은 Phase·검증 방법에 연결하며 통과로 추정하지 않는다.
- 사용자 승인은 검토한 계획 버전에 연결한다. 범위가 바뀌면 갱신된 승인이 필요하며 동일한 승인은 유지한다. 계획 생성 자체가 구현을 승인하지 않는다.
- 허용 파일 접근, 정책·승인 저장소 변경 차단, Git 쓰기·설치·지원하지 않는 외부 전송 차단을 확인한다. 승인된 호출에 필요한 선택 AI 서비스 통신만 허용한다. 지원하지 않는 위험 작업은 실행 전에 중단하며 프롬프트 지침만으로 분리를 입증하지 않는다.
- 실제 Planner 호출 시도·단계 시간·중단·승인 대기를 구분해 기록한다. 전체 계획 호출을 여러 Phase에 중복 합산하지 않으며 제공되지 않은 토큰·비용을 만들지 않는다.

**검증 근거**: 등록·승인의 pytest 통합 예제, 실제 Adapter 권한 시험, 생성 계획과 원문 요구사항·코드의 수동 대조. 검사 통과와 사용자 인수가 완료 조건이다.

**결과(2026-09-18)**: 전체 **123개 검사 통과**(기존 63개, 신규 60개), `pip check` 의존성 이상 없음. 인증을 사용하는 최소 실제 호출과 실제 예제 계획 생성이 성공했다. 예제 기본 테스트 2개가 통과한 후 AI 호출 시도 1회로 요구사항 5개·Task 2개의 영문·국문 계획을 생성했다. 원문·코드 수동 대조에서 음수 입력 검증과 기존 양수·0 동작 유지가 일치했다. 검사 목적의 계획 승인·재승인은 동일하게 유지됐고 가짜 실행은 차단됐으며 소스 파일은 변경되지 않았다. 이 예제 승인은 Phase 2 사용자 인수가 아니다.

- 권한 검사는 실제 Codex 실행 파일과 루프백 제공자를 사용한다. 합성 요청 8회, AI 호출 0회이며 강제로 요청한 도구 7종이 거부됐다. 금지 쓰기 표식 파일은 생성되지 않았다. 실제 계획 호출마다 검사를 반복하고 실행 파일 해시를 고정한다.
- 기획서·코드·설정 변경, 예상 밖 사용자 파일, 하드링크, 산출물 변조, 수정본 재승인, 차단 질문, 잘못된·중복 JSON, 기본 검사 실패, 문서 기록 중단을 회귀 검사했다. 실제 무해한 하위 프로세스로 시간 초과·중단 정리와 미확정 시간 기록을 확인했으며 AI 호출은 사용하지 않는다.
- 로컬 근거는 `%LOCALAPPDATA%/development-tools-harness/`의 `phase2-tests.xml`, `phase2-probes/live-smoke-result.json`, `phase2-demo/d98457898bca4153a09473f370ea0a47/`에 있다. 예제 Run은 `ebbf7cd2ca4e40a786da97b55614c685`이며 `approval-checks.json`에 CLI 승인·실행 차단 검사를 기록했다.

### P2-01 — Windows 실행 경로 길이 문제(수정·회귀 검증 완료)

- **재현 내용**: 2026-09-18 하네스 별도 복사본의 계획 기능 dogfooding에서 기본 테스트 123개가 통과한 뒤 `<attempt-id>.schema.json` 생성 중 중단됐다. 호출 폴더 경로는 217자, 전체 스키마 경로는 262자였다. 이 환경의 `codex_adapter.py` 스키마 쓰기에서 `[Errno 2] No such file or directory`가 발생했으며 경로 길이를 보완할 원인으로 확인했다.
- **최초 영향**: Planner 프로세스 실행 전(`dispatched=false`)이므로 해당 dogfooding 시도의 실제 AI 호출은 0회이고 Phase 3 계획은 생성되지 않았다. 작은 실제 예제와 당시 검사 결과는 이 긴 경로 조건을 검증하지 못했다. 당시 Task 2.6은 미완료였으며 아래에 재실행 성공을 기록했다.
- **근거**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/2085ced4918341da99a99ed03df06676/plan.json`, Run `729a78364bd746bbb2be2439996ae018`, 시도 `97677feca038475aae33826fb18cb3b7`.
- **수정(2026-09-21)**: 기존 호출별 고유 폴더 안에서 `schema.json`, `events.jsonl`, `stderr.log`를 사용한다. 재현된 폴더 길이에서 스키마 경로는 262자에서 229자로 줄었다. 호출 기록은 기존 ID·로그 경로를 유지하며 스키마 경로도 저장한다. 호출 간 파일은 고유 폴더로 구분한다.
- **회귀 근거**: `test_adapter_long_runtime_path_preserves_attempt_artifacts`에서 수정 전 동일한 `FileNotFoundError`를 재현하고 수정 후 통과를 확인했다. 별도의 217자 호출 폴더 두 곳에서 로컬 Python 프로세스를 실행해 스키마 읽기, 표준 입력·응답 처리, 기록된 파일 경로와 이전 호출 파일 보존을 검증한다. AI 호출은 사용하지 않는다.
- **경로 수정 당시 검사**: 총 124개 중 123개 통과, 1개 실패, 생략 0개이며 `pip check` 의존성 이상 없음. 설치 버전은 `codex-cli 0.155.1`, 당시 단일 검증 버전은 `0.154.0`이어서 CLI 검사가 중단됐다. 이후 아래의 호환성 작업으로 이 별도 실패를 해결했다. 당시 보고서: `%LOCALAPPDATA%/development-tools-harness/phase2-p2-01-tests.xml`.
- **재실행 결과**: 2026-09-21 하네스 계획 실행이 호출 폴더 217자·스키마 경로 229자 조건에서 성공했고 생성 계획도 검토했다. 이번 파일명 수정은 재현된 조건을 해결하며 임의 길이의 Windows 경로 지원을 추가한 것은 아니다.
- **사용자 결정**: 최초 기록만 남기는 보류 이후 2026-09-21 사용자가 P2-01 개발을 재개하고 호환성 개선과 다음 계획 검증 단계를 승인했다. 이후 2026-09-21 Phase 2를 인수했다.

### Task 2.6 — 하네스 계획 기능 dogfooding(기술 검증 완료)

2026-09-21 현재 소스·테스트와 미커밋 호환성 수정을 포함한 새 복사본에서 **검사 156개 통과, 실패·생략 0개**를 확인했다. CLI는 복사본 자체 소스를 사용했다. 갱신 전 Phase 3 개요를 기획 기준으로, 관련 파일 31개를 문맥으로 제공해 실제 Codex CLI 0.155.1 Planner가 **AI 호출 1회**로 계획을 생성했다. 별도 로컬 권한·입출력 시험도 통과했으며 이 시험의 AI 호출은 0회다.

- **산출물**: Phase 3 Task 8개·대응 요구사항 18개·코드 문맥 요약 11개. [AI v1](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v1/Plan_ko.md), [검토한 v2](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan_ko.md), [수동 검토 기록](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md), [검증 기록](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Evidence.json)을 보존했다. [Phase 3 문서](Phase3_Workflow.md)에는 초안 Task를 요약했다.
- **수동 보완**: 선행 조건 조사와 실제 작업 실행 조건을 구분하고, Reviewer 읽기 전용·실제 권한 차단 시험·지적 중요도와 처리 상태를 명시했다. Phase 4 외부 예제·MVP 검증 범위를 복원하고 근거가 부족한 코드 요약 표현을 고쳤다. 추가 AI 호출 없이 `plan-revise`로 v2를 생성했으며 영문·국문을 함께 갱신했다.
- **무결성**: 문서 갱신 전 복사본 파일 41개와 원본의 대응 입력이 시작 해시를 유지했다. 버전별 산출물 6개를 저장소로 복사해 기록된 해시와 대조했다. 이 단계에서 소스·테스트 코드는 변경하지 않았다. 복사본에는 갱신 전 문서가 남아 정확한 원문 인용을 보존한다.
- **기록된 시간**: 기본 검사 32.69초, Planner 328.68초이며 승인 대기는 별도다. 이번 입력의 계획 시간 제한은 등록 시 1,200초로 지정했다. 기본 시간 제한은 변경하지 않았다.
- **근거 위치**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/d8b4b48e8c9047d1a21ae17c93eee60f`, Run `45e4c4397c42468e87d9dad81d7b9ce9`, Planner 시도 `e07c878c099b46668e921f2cb02d1d9a`. `snapshot.json`, 기본 검사 XML·로그, 호출 입력·스키마·이벤트, `revision.json`, `status.json`에 상세 근거를 보존했다. 실행 DB·로그는 OneDrive 밖에 유지했다.
- **남은 경계**: 기록된 `plan-status`는 `awaiting_plan_approval`이며 승인 기록·검사 오류가 없다. 2026-09-21 Phase 2를 인수했으며 생성한 Phase 3 계획의 승인은 별도다. 이후 Windows 작업·테스트 권한 수단은 미해결 항목으로 남았다. 권한 수단 조사는 Phase 3 개발에서 다룬다. Phase 3 구현·실제 Developer/Reviewer 흐름·고정 실행용 A 분리는 아직 완료하지 않았다.

## Planner와 프로젝트 진입

### 목적 / 구현 파일

프로젝트 설정·계획은 프로젝트에, 실행 DB·로그는 OneDrive 밖에 둔다.

| 파일 | 역할 |
|---|---|
| `src/development_harness/project.py` | UTF-8 기획서·코드 입력 등록, 경로·링크·비밀정보·크기 검사, 프로젝트 입력 해시와 버전별 산출물 보존. |
| `src/development_harness/codex_adapter.py` | 실행 파일 선택, 지원 버전·옵션·로그인 진단, 텍스트 전용 도구 정책 적용, CLI 실행·중단과 응답 이벤트 검사. |
| `src/development_harness/codex_probe.py` | 로컬 합성 제공자로 실제 도구 목록과 금지 도구 호출을 프로젝트 분석 전에 시험. |
| `src/development_harness/plan_schema.py` | 영문·국문 JSON, 요구사항·코드 원문 근거, 식별자·Task 의존 관계 검사 및 문서 생성. |
| `src/development_harness/phase_docs.py` | 실행 하네스의 작성 리소스 읽기·고정, 템플릿 슬롯 검사, 검증된 계획 데이터로 영문·국문 통합 Phase 문서 생성. |
| `.agents/skills/phase-doc/` | 프로젝트 스킬 1.1과 템플릿. 문서 제목·배치·작성 규칙의 원본이며 wheel에도 포함. |
| `src/development_harness/planning.py` | 등록·기본 검사·계획 생성·중단 복구·수정·입력과 버전에 연결된 사용자 승인. |
| `src/development_harness/cli.py` | 계획 명령과 명시적인 Phase 1 예제 명령 제공. |
| 같은 패키지의 `model.py`, `store.py`, `runner.py` | 검증 규칙·저장·소유권 재사용, 실제 계획 기록의 가짜 구현 실행 차단. |
| `tests/unit/test_planning.py`, `tests/integration/test_planning_cli.py` | 계획 회귀 검사, 실제 기본 검사 프로세스, 중단 정리와 설치된 CLI 권한 시험. |
| `tests/unit/test_codex_compatibility.py` | 다중 버전 진입, 해결 방법을 포함한 진단, 실행 파일 우선순위, 바이너리 변경과 시작 알림 회귀 검사. |
| `tests/unit/test_phase_docs.py`, `tests/integration/test_phase_doc_package.py` | 템플릿 변경, 규칙을 고정한 수정·재개, 산출물 무결성, 대상 스킬 제외, 이전 형식 호환과 설치 리소스. |

`harness-project.json`에는 상대 입력 경로·검증 명령·모델·시간 제한을 저장한다. 검토 버전마다 `Phase/Generated/<run-id>/vN/plan.json`, `Plan.md`, `Plan_ko.md`를 만든다. 새 스킬 기반 Run에는 Task 2.7의 영문·국문 통합 `PhaseN_EnglishName.md`와 `writing-profile.json`도 추가한다. 실행 저장소에는 실제 전송 입력·호출 로그·기본 검사 근거·승인 해시를 보존한다. 호출 시도는 실행한 CLI 1회를 세며 내부 HTTP 요청 횟수를 추정하지 않는다. 중단 호출의 종료·소요 시간은 미확정으로 두고 승인 대기는 별도로 누적한다. 비용은 추정하지 않는다.

### 설계 결정 사항

- Codex CLI와 ChatGPT 로그인을 사용한다. 인증은 Codex가 관리하고 프로젝트 설정·하네스 DB에 토큰을 복사하지 않는다. 권한 시험 실패 시 실제 프로젝트 분석을 막되 구현·회귀 검사는 계속한다.
- 지원 버전은 **Codex CLI 0.154.0과 0.155.1**이며 검토된 `text-only-v1` 설정을 공유한다. 설정 모델은 **gpt-6-astra**, 추론 수준은 `medium`이다. 모델은 로컬 Codex 설정 또는 명시적 `--model`을 따른다. 미검증 버전은 진단 결과를 제공하되 호환성 검토 전에는 계획을 실행하지 않는다. 최소 버전 이상 일괄 허용, CLI 자동 설치, API 키·다른 제공자 자동 전환은 사용하지 않는다.
- Planner에는 선택한 파일당 최대 128,000바이트·총 320,000바이트의 JSON 입력을 표준 입력으로 전달한다. 파일·프로세스·웹·앱·에이전트 도구, 플러그인·훅·사용자 및 프로젝트 지침·호스트 스킬 탐색을 비활성화하고 읽기 전용 쓰기 제한과 승인 정책 `never`를 적용한다. 실제 모델의 도구 목록은 비어 있었다. 검증한 생성 문서는 호스트 하네스만 기록한다.
- Windows의 제한된 읽기 허용 목록은 이 환경에서 elevated sandbox backend를 요구해 권한 상승 설정은 수행하지 않았다. Phase 2에서 검증한 경계는 모델 도구 제거와 읽기 전용 쓰기 집행이며 **일반 OS 읽기·네트워크 허용 목록이 아니다**. 기본 검사는 여전히 신뢰하는 사용자 등록 명령으로 실행한다. Developer·테스트 프로세스와 실행본 A·승인 저장소의 분리는 Phase 3 통과 조건이다.
- 지정한 기획문서와 프로젝트 관련 코드만 분석한다. 프로젝트 내용은 입력 자료이며 권한 정책이 아니다. 무관한 프로젝트·인증정보를 포함하지 않고 실제 입력 파일·버전을 확인할 수 있게 한다.
- Phase 1 가짜 실행 계약과 함께 프로젝트·계획 모듈을 추가한다. 실제 계획 승인이 가짜 구현을 실행해서는 안 된다.
- 임시 Python/pytest 프로젝트로 통합 검사한 뒤 하네스 계획 기능을 dogfooding한다. Decision Desk는 자체 개발 검증 이후 진행하며 오프라인 파일·브라우저 요구에 맞는 검증 환경은 이후 연결한다.
- 새 Run에서 프로젝트 phase-doc 스킬·템플릿을 명시적으로 읽는다. 사용자가 로컬 1.1 연결을 승인했으며 전역 1.0 스킬은 유지한다. 템플릿 기반 영문·국문 통합 Phase 문서를 만들고 현재 Task는 상세화하며 다른 Phase는 개요로 둔다. 요구사항 검사·승인·저장 규칙은 코드가 담당한다.
- 정책·승인 기록 쓰기는 하네스가 담당하고 작업 에이전트의 권한과 분리한다. 프로젝트에서 바꿀 수 있는 지침에 권한 부여를 의존하지 않는다.
- 전체 개요에서 제안한 준비된 Python/pytest 예제 한 개로 시작한다. 의존성은 사용자가 준비하며 템플릿 설치기·환경 복구 엔진은 추가하지 않는다.

### CLI 호환성과 실행 파일 선택(2026-09-21)

사용자는 검증 버전 누적 관리, 실제 기능 검사, `doctor` 오류 설명, 별도 설치 실행 파일 선택의 네 가지 개선을 승인했다. Task 2.1을 확장하며 기존 프로젝트 설정과 계획 기록을 유지한다.

- **지원 여부와 준비 상태 구분**: `SUPPORTED_VERSIONS`는 정확한 버전 문자열을 검토된 실행 설정에 연결한다. 현재 지원하는 두 버전은 같은 CLI 설정을 사용한다. 새 버전을 추가해도 기존 항목은 유지하며 실제 버전·실행 파일 경로와 해시·적용 설정을 기록한다. 목록에 없는 버전은 곧바로 비호환으로 단정하지 않고 `unverified`로 표시한다. 읽기 전용 정보 수집은 계속하지만 실행 시험과 AI 호출은 허용하지 않는다.
- **실제 검사**: 필수 `exec --help` 옵션, 기능 제어 항목, ChatGPT 로그인과 모델 설정을 확인한다. 지원되고 준비된 설치본에서는 로컬 제공자로 표준 입력·JSON 스키마 전달, 금지 도구 7종 거부, JSON 이벤트·응답 해석을 검증한다. 실제 계획 호출마다 반복하며 진단 중 또는 호출 전에 실행 파일이 바뀌면 검증 근거를 무효화한다. 로컬 시험의 AI 호출은 0회이고 원격 모델 이용 가능 여부나 계정 사용량 한도까지 확인하는 것은 아니다.
- **진단 출력**: `doctor`는 `ready`, 실제 `version`·`executable`, `support_status`, `supported_versions`, 개별 `checks`, `next_steps`를 JSON으로 반환한다. 검사 상태는 `passed`, `failed`, `unverified`, `not_run`을 구분한다. 준비 완료일 때 종료 코드 0, 진단을 마쳤으나 준비되지 않았으면 1이다. 로그인·모델 및 옵션 누락·실행 파일 선택·권한 시험 실패를 구분하고 기존 명령·저장소 오류의 종료 코드 2는 유지한다.
- **실행 파일 선택**: `doctor`, `plan`, `plan-resume`에서 `--codex-path`를 받는다. 명시 옵션, `DEVELOPMENT_HARNESS_CODEX_PATH`, 기존 자동 탐색 순으로 적용한다. 지정 값은 존재하는 `.exe`의 절대 경로여야 하며 잘못 지정하면 다른 실행 파일로 자동 전환하지 않는다. 환경변수는 사용자·장치 설정으로 사용하고 프로젝트 기획서·설정이나 Planner 전송 자료에 추가하지 않는다. 명령 옵션은 해당 실행에만 적용하므로 재개할 때도 지정하거나 환경변수를 사용한다. 하네스가 Codex를 자동 설치·교체하지 않는다.
- **예상된 시작 알림**: 검토된 텍스트 전용 설정은 Code Mode host를 의도적으로 끈다. CLI는 정상적인 텍스트 응답을 생성하면서도 이 기능을 사용할 수 없다는 특정 시작 알림을 `item.error`로 출력할 수 있다. `turn.started` 전의 정확히 일치하는 알림만 허용하고 `notices`·`probe_notices`에 보존한다. 다른 오류, 실행 중 같은 알림, 완료 누락과 `turn.failed`는 계속 응답을 거부하며 도구 비활성화도 유지한다.
- **실제 근거**: 설치된 `0.155.1`에서 실제 `doctor --codex-path` 명령과 로컬 입력·스키마·응답·권한 검사가 통과했다. 인증을 사용하는 최소 AI 호출은 2회 수행했다. 첫 호출에서 시작 알림 해석 문제를 발견했고, 수정 후 두 번째 호출은 알림을 기록하면서 기대한 `{"ok": true}` 응답을 반환했다. `%LOCALAPPDATA%/development-tools-harness/compatibility/` 아래 첫 시도 `19389930dfdd437095ed94f2b283c774`, 성공 시도 `31cfb0fa5bfa41bab7d40fc284844ecd`, CLI doctor 보고서 `1bf80e60521641499e1a2dcbfbf8e711/doctor.json`에 근거를 저장했다. `0.154.0`은 2026-09-18 실제 검증 근거를 유지하고 버전 계약 회귀 검사를 추가했으며 이번 세션에서 구버전 바이너리를 재설치·재실행하지 않았다.

**회귀 결과**: 전체 **156개 검사 통과**, 실패·생략 0개이며 `pip check` 의존성 이상 없음. P2-01, 지원하는 두 버전 계약, 더 오래되거나 새로운 버전·사전 배포판의 미검증 처리, 필수 제어 누락, 로그인·모델 실패, 실행 파일 선택·재개, 바이너리 변경과 엄격한 오류 처리를 포함한다. 보고서: `%LOCALAPPDATA%/development-tools-harness/phase2-compatibility-tests.xml`.

CLI 계약은 로컬 도움말과 공식 [비대화형 출력 문서](https://learn.chatgpt.com/docs/non-interactive-mode), [설정 참조](https://learn.chatgpt.com/docs/config-file/config-reference)를 대조했다. 문서 확인이 설치된 실행 파일 검사를 대체하지는 않는다.

### 프로젝트 phase-doc 연결 — Task 2.7(2026-09-21)

사용자가 스킬을 저장소로 가져와 문서 생성에 연결하도록 승인했다. 이전 생성기는 제목·구조가 코드에 고정됐고 실행 시 스킬을 읽지 않았으므로, 기존의 스킬 구조를 사용한다는 표현은 충분히 정확하지 않았다.

- **리소스**: [프로젝트 SKILL.md](../.agents/skills/phase-doc/SKILL.md)와 [템플릿](../.agents/skills/phase-doc/references/phase-template.md)은 전역 1.0을 가져와 로컬 1.1로 연결했다. 템플릿에는 직접 작성용 예시와 개요·Phase × 영문·국문의 `harness:*` 블록 4개를 둔다. Python 수정 없이 제목·배치를 바꾸면 새 등록 계획에 반영된다. 필수 데이터 슬롯을 검사하며 템플릿 코드를 실행하지 않는다.
- **실제 사용**: `register`에서 실행 하네스 자체의 리소스만 읽어 원문·버전·해시를 기록한다. Planner에 규칙을 전달하고 선정·제안 기술 구성을 포함한 JSON을 검사한 뒤 호스트가 템플릿으로 출력한다. 대상 프로젝트·전역 스킬 자동 탐색은 계속 비활성화하며 스킬이 도구·파일 권한을 부여하지 않는다.
- **산출물**: 새 버전은 `plan.json`, `Plan.md`·`Plan_ko.md` 개요와 링크를 유지하고, 계획한 Phase별 `PhaseN_EnglishName.md` 및 `writing-profile.json`을 추가한다. Phase 문서는 상단 영어·하단 한국어이며 현재 Task·완료 기준·검증 방법은 검사한 동일 데이터에서 채운다. 다른 Phase는 개요만 작성한다. 원문 인용은 코드 근거로 표시해 인용 안의 상대 링크가 깨지는 문제를 피한다. 기존 프로젝트 Phase 문서는 덮어쓰지 않는다.
- **이력**: 호출·계획 버전·승인에 작성 규칙 해시를 연결한다. 재개·수동 수정은 등록 당시 원문을 사용하고 설치된 스킬·템플릿 변경은 새 Run부터 반영한다. 작성 규칙 기록이 없는 이전 Run은 기존 JSON·문서·산출물 형식을 유지하며 계속 검토할 수 있다. 진행 중인 Run을 자동 변환하지 않는다.
- **설치**: wheel에 같은 프로젝트 스킬·템플릿을 포함했다. 설치 폴더 이름이 `src`인 경우를 포함해 독립 인터프리터가 체크아웃·전역 스킬에 의존하지 않고 wheel의 동일 리소스를 읽었다.
- **검증**: 전체 **172개 검사 통과**, 실패·생략 0개이며 의존성 이상 없음. 추가 16개는 실제 전달 내용, 템플릿 변경 반영, 잘못된·누락된 규칙, 산출물 기록 복구, 문서·규칙 변조, 이전 승인·수정 호환, 상세·개요 구분과 패키징을 확인한다. skill-creator 검사기도 임시 검사 폴더의 PyYAML을 사용해 통과했으며 제품 의존성에는 추가하지 않았다. 보고서: `%LOCALAPPDATA%/development-tools-harness/phase2-skill-tests.xml`.
- **실제 결과**: 작은 계획 예제의 새 복사본에서 기본 검사 2개가 통과했다. Codex CLI 0.155.1의 실제 Planner 호출 1회(75.92초)로 Phase 1개·Task 2개·요구사항 5개를 생성했다. [영문·국문 통합 Phase 문서](Generated/78fb56ab088648e49111258ff74112ad/v1/Phase1_InputValidation.md)를 기획서·코드와 대조해 음수 검증, 기존 0·양수 동작, Python·pytest와 새 의존성 제외가 반영됐음을 확인했다. 원본 입력 3개는 그대로 유지됐다. [근거](Generated/78fb56ab088648e49111258ff74112ad/Evidence.json)에 산출물 해시·작성 규칙을 기록했다. 실행 위치: `%LOCALAPPDATA%/development-tools-harness/phase2-skill/02527e2443044eb0b0c4ba1d63002adb`, Run `78fb56ab088648e49111258ff74112ad`, 시도 `5009053163fb4492bcff030d43c82601`. 상태는 `awaiting_plan_approval`이고 검사 오류·사용자 승인은 없다.

**범위**: 스킬 기반 계획 문서 생성이며 README·dev-log 자동 관리나 구현 결과 문서화는 포함하지 않는다. 구조화된 항목·표 데이터·파일명·검사·승인은 코드가 담당한다. 필수 데이터 항목 변경에는 코드 수정이 필요하고 문서 제목·배치는 템플릿에서 바꾼다. 의미상 요구사항 전체 반영은 계속 검토해야 한다. pytest 기본 검사 조건은 유지하며 2026-09-21 Phase 2 사용자 인수를 완료했다. Decision Desk는 등록·수정하지 않았다.

### 사용 예시

README 설치와 `codex login` 후 저장소 루트에서 실행한다. 이미 로그인되어 있으면 다시 인증할 필요가 없다.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningExample = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningExample -Recurse
& $harnessPython -m development_harness --project $planningExample doctor
& $harnessPython -m development_harness --project $planningExample register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json
& $harnessPython -m development_harness --project $planningExample plan
& $harnessPython -m development_harness --project $planningExample plan-status
```

별도 설치한 CLI를 사용하려면 예시 경로를 실제 `.exe` 위치로 바꾼다.

```powershell
$selectedCodex = 'C:\Tools\Codex\codex.exe'
& $harnessPython -m development_harness --project $planningExample doctor --codex-path $selectedCodex
& $harnessPython -m development_harness --project $planningExample plan --codex-path $selectedCodex
# 또는 이후 PowerShell 명령에 적용할 실행 파일을 환경변수로 지정한다.
$env:DEVELOPMENT_HARNESS_CODEX_PATH = $selectedCodex
& $harnessPython -m development_harness --project $planningExample doctor
```

버전별 `Plan.md`·`Plan_ko.md`와 대응표를 검토한 뒤 `plan-approve`한다. 이 명령은 계획만 승인한다. `baseline`은 AI 없이 검사하고 `plan-resume`은 중단한 작업을 명시적으로 재개한다. 수정은 `plan.json`을 입력 기준선 밖의 별도 파일로 복사·편집한 후 `plan-revise --from <파일>`로 반영한다. 변경본은 새 버전이므로 재승인하며 차단 질문도 수정본에서 해결한다. `plan-cancel`은 파일·근거를 보존하고 새 등록을 허용한다. 소스·설정이 바뀌면 확인 후 필요 시 미완료 Run을 취소하고 다시 등록한다. 오래된 승인을 재사용하지 않는다.

## 선행 조건 및 개발 시 주의사항

Phase 1의 저장·검증·승인·소유권 회귀 검사가 통과했다. 원문 인용·대응 구조는 자동 검사하지만 의미상 전체 요구사항 반영 여부는 사람이 검토해야 한다. 실제 Developer·Reviewer 실행 연결과 전체 결과 인수는 Phase 3 범위다. Decision Desk는 등록·실행하지 않았다. 향후 브라우저·앱 기술 구성에 맞는 기본 검증 명령을 연결해야 하며 현재 진입에는 실제 pytest 검사가 필요하다. 프로젝트 전용 Git 스킬은 사용자 개발 보조 기능이며 하네스 에이전트에 Git 권한을 부여하지 않는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 실제 연결·계획 개요 최초 작성. 제공자 선정과 후속 Task 상세화는 미결정으로 명시. |
| 2026-09-18 | 사용자가 ChatGPT/Codex, 기획문서와 프로젝트 관련 코드 분석, 하네스 dogfooding 후 Decision Desk 적용, 제시한 구현 범위를 확인하고 Phase 2를 승인했다. 구현 전에 Task 2.1–2.6을 기록했다. 별도 dev-log 스킬은 없다. |
| 2026-09-18 | 실제 계획, 입력 범위 제한, 도구 권한 시험, 기본 검사 진입, 영문·국문 근거, 버전별 승인·복구를 구현했다. 검사 123개와 실제 예제를 검증했다. 프로젝트 전용 `harness-github-push` 스킬을 추가했으며 커밋·푸시는 수행하지 않았다. dev-log 스킬이 없어 별도 기록은 생략했다. Phase 사용자 인수는 대기 중이다. |
| 2026-09-18 | 하네스 계획 dogfooding이 AI 실행 전 262자 스키마 경로에서 중단된 P2-01을 기록했다. 사용자 요청으로 파일명 수정·회귀 검사·재실행은 보류하며 Task 2.6은 미완료로 유지한다. |
| 2026-09-21 | 사용자 요청으로 P2-01 개발을 재개해 호출 파일명을 줄이고 스키마 경로를 기록했다. 원래 오류를 재현한 뒤 신규 하위 프로세스 회귀 검사를 통과했다. 전체 검사 123개 통과·설치 CLI 버전 실패 1개, 의존성 이상 없음. dogfooding과 Phase 인수는 대기 중이다. 영문·국문을 함께 갱신했으며 dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-21 | 사용자가 승인한 CLI 호환성 개선 4건인 검증 버전 누적 관리, 기능·입출력 검사, 상세 doctor 진단, 옵션·환경변수 실행 파일 선택을 구현했다. 0.154.0 지원을 유지하고 설치된 0.155.1을 검증했으며 특정 Code Mode 비활성화 시작 알림만 구분하고 다른 오류는 계속 거부한다. 전체 156개 검사·의존성 검사·실제 CLI doctor·최소 AI 응답을 검증했다. 영문·국문을 갱신하고 dev-log 스킬이 없어 별도 기록은 생략했다. Task 2.6은 대기 중이다. |
| 2026-09-21 | Task 2.6 기술 검증 완료: 복사본 기본 검사 156/156, 실제 Planner 호출 1회, 긴 경로 성공, 원본·검토 버전 계획과 입력·산출물 무결성을 확인했다. 수동 보완과 Phase 3 상세 초안을 영문·국문으로 기록했다. Phase 2 사용자 인수는 대기 중이며 dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-21 | 승인된 Task 2.7로 프로젝트 phase-doc 1.1, 실제 규칙·템플릿 읽기, 작성 근거 고정, Phase별 영문·국문 문서와 wheel 리소스를 구현했다. 이전 Run 형식을 유지하며 검사 172개·스킬 검사·실제 예제 호출 1회를 검증했다. 영문·국문 기록과 README 사용법을 갱신했다. dev-log 스킬이 없어 별도 기록은 생략했으며 사용자 인수는 대기 중이다. |
| 2026-09-21 | 사용자 “phase2 인수”를 기록했다. 기존 검사 172개 통과와 실제 계획 검증 근거를 바탕으로 Task 2.1–2.7, P2-01·호환성 개선을 인수해 Phase 2를 완료 처리했다. 영문·국문, 전체 개요, README 상태와 Phase 3 선행 조건을 동기화했다. 생성한 계획의 승인은 별도이며 Phase 3–4 구현은 미시작이다. dev-log 스킬이 없어 별도 기록은 생략했다. |
