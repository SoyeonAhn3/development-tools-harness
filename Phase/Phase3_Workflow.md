# Phase 3 — Workflow `🚧 In Progress`

> Complete one real example Phase and prepare a verified fixed runner for self-development.

**Prerequisites**: [Phase 2](Phase2_Planning.md) accepted on 2026-09-21; actual worker execution additionally requires verified permissions and a prepared example.

**Technology**: Python + pytest, SQLite and the selected single AI Adapter.

**Plan status**: P3-T1–T3 preparation, real roles, isolated validation, execution admission and durable records are implemented and verified. P3-T4 connects sequential execution, bounded corrections, explicit independent review assessments and final validation; its two-Task live example reached technical completion. P3-T5 implements explicit interruption recovery with preserved approvals, files and call history. P3-T6 implements minimum JSON reports, feedback routes, final reuse/manual evidence and explicit acceptance gates; current verification is recorded below. Validation uses standard-user AppContainer under the no-administrator constraint. The accepted external example and fixed runner A remain P3-T7–T8. Phase 2 is accepted; Phase 3 acceptance remains pending. The reviewed eight-Task, 18-requirement plan and its original AI/manual-review evidence are preserved.

## Overview

Connect actual implementation, validation, separate review, bounded corrections and minimum result acceptance. Verify the whole flow and interruption/resume in a separate example before touching the harness through itself. Covers specification §§6–10, with final report presentation completed in Phase 4.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Real sequential Developer/Validation Runner/Reviewer workflow | ✅ T4 implemented; current verification below |
| 2 | Call/timing/finding records, corrections and process-aware resume | ✅ T3–T5 implemented; current recovery verification below |
| 3 | Minimum success/failure report, feedback and result acceptance | ✅ T6 implemented; current verification below |
| 4 | Accepted external example and verified fixed runner A | 🔲 |

## Verification & Exit Criteria

The [reviewed plan](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan.md) contains completion criteria, proposed paths and verification methods. [Review evidence](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md) preserves the original AI output and manual corrections. P3-T1 and P3-T2 components are verified, including two actual AI calls on a disposable example. P3-T3 admission/records are implemented and verified; the full suite passed 378 tests. P3-T4 implementation and its four-call live example are recorded in [execution evidence](Evidence/Phase3_Execution.json). P3-T5 recovery is implemented; its separate [recovery evidence](Evidence/Phase3_Recovery.json) is preserved. P3-T6 results, feedback and acceptance gates are implemented; [results evidence](Evidence/Phase3_Results.json) and current verification are recorded below. P3-T7–T8 implementation has not started.

| Task | Planned work | Completion evidence |
|---|---|---|
| P3-T1 | Confirm prerequisites, investigate Windows worker isolation, define the execution contract and prepare the small CLI example. | Phase 2 acceptance record, permission mechanism investigation/probes, baseline example tests and bounded specification. |
| P3-T2 | Extend the single Adapter for Developer and read-only Reviewer sessions; enforce worker/test permissions. | Implemented and verified: distinct real sessions, controlled patches, isolated pytest and descendant/file/network denial tests. [Evidence](Evidence/Phase3_Workers.json). |
| P3-T3 | Connect version-bound execution admission and durable call/time/finding records. | Implemented and verified: separate execution authorization, atomic/idempotent records, lifecycle hooks and evidence-linked findings. Full suite: 378 tests passed. Evidence in [Phase3_Records.json](Evidence/Phase3_Records.json). |
| P3-T4 | Run Developer → validation → separate Reviewer sequentially with bounded corrections. | Implemented: real isolated validation, explicit finding assessments, shared correction limits, patch lineage and final-content checks. Four-call live example reached technical completion. [Evidence](Evidence/Phase3_Execution.json). |
| P3-T5 | Recover partial implementation and interrupted validation safely. | Implemented: explicit resume, saved-response proof/reuse, checked partial files, process-tree inspection, separate recovery facts and preserved approval/correction counts. [Evidence](Evidence/Phase3_Recovery.json); current verification below. |
| P3-T6 | Add minimum reports, feedback routing, final reuse checks and acceptance gates. | Implemented: read-only JSON results, preserved feedback/correction or replanning routes, final reuse/manual confirmations and version-bound acceptance gates. [Evidence](Evidence/Phase3_Results.json); current verification below. |
| P3-T7 | Complete the external CLI example through actual roles, interruption/resume and user acceptance. | Full regressions, actual outputs, distinct role sessions and recorded user result acceptance. |
| P3-T8 | Freeze runner A and prove isolation before Phase 4. | Independent installed origins, fixed artifacts, actual B/test write-denial evidence and installed workflow/resume checks. |

P3-T2 verifies the worker components on an explicitly scoped disposable example. P3-T3 prepares and authorizes a specific plan/code/policy version without dispatching work. P3-T4 starts that authorized work through `workflow-run`; P3-T5 adds explicit `workflow-resume`; P3-T6 supplies minimum reports and result acceptance conditions. The external example's actual user acceptance remains T7 work. The unelevated candidate failed network denial; elevated setup remains excluded under company policy. No administrator setup or unrestricted fallback is used.

Verify the following behavior with pytest integration/regression tests and actual example runs:

- An approved small Phase executes Tasks sequentially. The Reviewer uses a separate session and checks requirements, actual implementation and tests. Required findings must have follow-up review/validation evidence; Developer self-report is insufficient.
- Required validation runs after changes and on final Phase content. Failed, skipped, interrupted and zero-test outcomes do not pass. Corrections stop at the configured limit; environment/permission/specification problems stop without spending code-fix retries.
- Approval/evidence/result acceptance reference matching plan and code versions. Same-scope defect feedback reopens correction in the current Phase; changed requirements update the plan and approval. Store the original feedback and outcome.
- Interrupted implementation inspects partial files; interrupted validation checks remaining processes and reruns required checks. Unexpected user edits stop without overwrite, and another runner cannot acquire unsafe ownership. Metadata-only manual Git changes do not block an otherwise unchanged run.
- Actual role-call attempts, completed/incomplete times, approval waiting and findings have stable identities. Resume does not double-count calls or repeated findings. Confirmed fixes have evidence; deferred mandatory findings still block completion. Do not estimate unknown duration, tokens or money.
- Minimum reports exist for success and failure and show delivered files, validation/reuse evidence, unresolved items, manual checks and detailed-record locations. User acceptance is separate from technical completion and cannot override unmet mandatory criteria.
- A separate prepared example completes a small Phase, including stop/resume and user acceptance. Freeze A's code, dependencies and role/policy instructions; prove that B and its test processes cannot modify A or its runtime/approval storage before the next Phase.

**Results (2026-09-21)**: P3-T1 added a prepared CLI fixture, a synthetic `workflow-doctor` command and an execution contract. The full suite passed **187 tests**, with zero failures or skips; `pip check` passed. The separate example baseline passed two actual tests. Three roles and their child processes obeyed the candidate file-write boundaries, but all six direct loopback TCP connections succeeded despite network being disabled. Diagnosis returned `ready=false`, exit code 1 and `execution_enabled=false`. Existing project inputs and the planning Run were preserved; actual AI calls were zero. This completes preparation/investigation, not P3-T2 isolation or an actual Phase workflow. See [preparation evidence](Evidence/Phase3_Preparation.json).

## P3-T1 Execution Contract and Permission Investigation

The following is the contract for subsequent implementation. `workflow-doctor` implements only the synthetic investigation, not execution admission.

| Contract | Required behavior |
|---|---|
| Planning input | Reuse the approved Phase 2 `plan.json`, its version/artifact hashes and pinned writing profile. Execute only the current Phase's Tasks, dependencies, declared paths, requirements and acceptance criteria. Keep plan approval separate from an explicit execution request. |
| Execution policy | The controller owns registered validation commands, the initial content baseline and correction limit; proposed default is two corrections per Task. AI output cannot change the approval policy, checks or limit. |
| Developer | Receive the current Task, approved requirements, relevant code and prior failure/review evidence. Restrict target changes to approved paths; report changes and unresolved questions. A completion message is not verification evidence. |
| Validation | Run the registered commands on the actual resulting code. Permit dedicated temporary test files, protect project inputs/control records and inherit restrictions into descendants. Failed, skipped, missing, interrupted and zero-test outcomes do not pass. |
| Reviewer | Use a separate read-only session to compare requirements, changes and actual validation. Record finding identity, severity, required/optional status, location and evidence. A required finding closes only with follow-up review/validation evidence. |
| Records and resume | Bind attempts, findings, approval and evidence to plan/content versions. Record a process identity before dispatch, preserve incomplete durations and inspect partial files/remaining processes before resuming. Preserve unexpected user edits. |
| Results and acceptance | Validate the final Phase content, including reused requirements. Produce a basic result even on failure; unmet mandatory conditions block acceptance. Same-scope defects return to correction; changed requirements update the plan. |

**Prepared example**: [cli.py](../tests/fixtures/workflow_project/cli.py), [test_cli.py](../tests/fixtures/workflow_project/test_cli.py) and [spec.md](../tests/fixtures/workflow_project/spec.md) form the starting project. `python cli.py 3` prints `6`, and `python cli.py 0` prints `0`; both exit 0 with no stderr. `python -m pytest -q` discovers and passes two command-level baseline cases. Negative rejection is deliberately unimplemented: `python cli.py -1` currently prints `-2` and exits 0. The later live change must instead return nonzero, no numeric stdout and a clear stderr explanation while preserving existing behavior. Only `cli.py` and `test_cli.py` are implementation targets. [workflow-checks.json](../tests/fixtures/workflow-checks.json) defines the baseline command.

**Implemented diagnostic**: [worker_probe.py](../src/development_harness/worker_probe.py) and its [payload](../src/development_harness/worker_probe_payload.py) create fresh synthetic files outside the target project. They use the installed `codex sandbox` command, an isolated configuration home and managed requirements, without authentication or an AI call. Developer writes are limited to a synthetic source directory and scratch directory; validation may write scratch only; Reviewer is read-only. Direct and child attempts target project files, Git metadata, plan/configuration files, mock runner/approval/install paths and an unrelated file. The host checks actual resulting files and a controller-owned TCP listener, with before/after positive controls. No external service, real approval DB, package installation or user file is targeted.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython -m development_harness --project . workflow-doctor --backend codex-unelevated
```

The `codex-unelevated` diagnostic saves `report.json`, role profiles and raw process evidence under the runtime directory's `worker-probes/<id>/`. It returns 1 on a failed/incomplete probe and keeps `execution_enabled=false`. This candidate's compatibility covers the tested CLI 0.155.1; older Planner support is unchanged. An unknown worker version is reported for review rather than silently admitted. This command neither approves a plan nor starts implementation. The default backend is now `appcontainer`, described below.

**Observed limitation**: The installed configuration uses `windows.sandbox="unelevated"`. File writes behaved as requested in all three roles and descendants; raw TCP traffic reached the owned loopback listener in all six cases. This demonstrates an insufficient network boundary, not an actual external-data transfer. OpenAI documents environment-level offline controls for unelevated mode and stronger user/firewall separation for elevated mode; elevated setup requires administrator support. The next candidate must be configured and tested before live worker admission. No Windows accounts, firewall policies or global Codex configuration were changed. Sources: [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox), [permission scope](https://learn.chatgpt.com/docs/permissions), [sandbox command](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

**Verification details**: The 15 added cases cover diagnosis evidence, child/network/file discrepancies, failed/incomplete probes, unknown versions, preserved evidence, CLI errors and the actual prepared example. Windows pytest temporary roots with OWNER RIGHTS ACLs prevented restricted-token reads; the real probe test uses a fresh normally inherited runtime directory, matching the CLI, without changing existing ACLs. Local evidence is under `%LOCALAPPDATA%/development-tools-harness/phase3/cb8b06882b6a417fbdef359ef883c540`; the example Run is `715dfc64eae6480a9b25d04378bd171a`. `preparation-evidence.json` records the two passing baseline tests, original hashes, unchanged Run and CLI outputs; the diagnostic contains three roles with two failed network checks each. The full-suite report is `%LOCALAPPDATA%/development-tools-harness/phase3-preparation-tests.xml`.

## Workflow & Minimum Results

### Administrator-free alternative — P3-T2 candidate investigation

**Constraint and decision (2026-09-21)**: The user stated “회사 정책상 관리자 설정 불가”. Elevated Codex setup, account creation and firewall changes are excluded. Read-only environment checks found no WSL distribution and no accessible Docker engine, so neither provides an immediately available execution environment. Windows AppContainer was then successfully created, used and removed by the current standard-user process on Windows 10 build 19045. This is a per-user application profile, not a new Windows login account. Microsoft documents [per-user profile creation](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile) and [capability-based process and network isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer).

**Implementation**: [appcontainer_probe.py](../src/development_harness/appcontainer_probe.py), [windows_appcontainer.py](../src/development_harness/windows_appcontainer.py) and the [trusted payload](../src/development_harness/appcontainer_probe_payload.py) investigate a zero-capability AppContainer. The harness copies its base Python runtime into a fresh disposable directory; ACL grants apply only to those copies and synthetic project paths. It starts the process suspended, assigns the existing kill-on-close Job, checks its token and then resumes it. Only explicit standard-I/O handles are inherited. Installed-runtime ACLs, machine accounts, firewall rules and Codex configuration are unchanged. Each temporary profile is removed; setup/cleanup failures reject readiness without unrestricted fallback.

```powershell
# Default: administrator-free investigation; no Codex login or AI call.
& $harnessPython -m development_harness --project . workflow-doctor
# Explicit equivalent:
& $harnessPython -m development_harness --project . workflow-doctor --backend appcontainer
```

**Observed results**: All three roles and their children retained AppContainer tokens with zero capabilities and no elevation. Twenty-four direct TCP/UDP IPv4/IPv6 attempts were blocked against controller-owned loopback listeners; eight host controls succeeded. Developer could write source/scratch, validation scratch only, and Reviewer neither. Synthetic Git/configuration/plan/runtime files resisted writes, while runner/approval/unrelated files also resisted reads. Runtime and probe-input hashes stayed unchanged. A separate deadline test stopped both the waiting process and its child. Diagnosis returned `ready=true` and exit code 0, with `execution_enabled=false` and zero AI calls. These are local synthetic results, not external-network tests or full workflow admission. [Evidence](Evidence/Phase3_AppContainer.json) records the final regression count and raw artifact hashes; the earlier unelevated failure evidence is preserved.

**Integration decision**: AI-service authentication/traffic stays with the existing text-only Codex adapter. The Developer returns structured changes for controller application; the Reviewer receives selected before/after files and actual validation evidence. Generated code and tests run in AppContainer. P3-T2 implements and verifies these components below; P3-T3 adds admission and records. T4 orchestration and T5 explicit recovery are connected below; acceptance and fixed-runner verification remain P3-T6–T8. The old trusted-command validator is not used for this generated code; existing Planner compatibility rules remain in force.

**Verification (2026-09-21)**: All 206 tests passed, with zero failures/errors/skips; `pip check` passed. The 19 new cases include actual standard-user isolation and descendant termination, false denial reports, missing evidence, setup failure and preservation of existing records. A separate CLI run preserved the prepared example's files, planning Run and events. No actual AI calls or new plan/result approvals were made.

### P3-T2 — Real Roles, Controlled Changes and Isolated Tests

The user's “그럼 T2 개발 해보자” request authorized these four components:

| Component | Implemented behavior |
|---|---|
| [CodexWorker](../src/development_harness/workers.py) | Reuses the reviewed text-only CLI adapter/capability probe. Developer and Reviewer each use a fresh, single-call session without filesystem, command or network tools. Saves selected input, response, session and attempt evidence. |
| [TaskScope / apply_proposal](../src/development_harness/worker_contract.py) | Checks bounded JSON, explicit paths and expected hashes before applying UTF-8 file changes. Rejects sensitive/control/generated/linked paths. Records each write and partial failures; preserves unexpected user edits without rollback. |
| [IsolatedValidator](../src/development_harness/isolated_validation.py) | Copies reviewed Python/pytest dependencies, verifies permissions, and tests content-identical read-only project copies with writable scratch. Checks original/copy/runtime hashes and saves stdout, stderr, JUnit and process evidence. |
| Independent Reviewer | Compares requirements, before/after files and actual validation for the same code version. Requires finding identifiers, severity, mandatory status and evidence. Rejects invalid references and a pass over failed/unverified validation. |

**Isolation**: Grants apply only inside the owned disposable tree. Ancestor directories there receive non-inheriting read/list access for Python metadata checks. The suspended process is recorded and checked for a zero-capability, non-elevated token before startup; completion/deadlines terminate descendants. Standard pytest `--capture=sys`, an explicit scratch log and the read-only [bootstrap](../src/development_harness/validation_entry.py)'s TEMP/TMP selection resolve Windows device/temp access failures. Package auto-loading is disabled. No administrator setup, installed-runtime ACL changes, dependency installation or unrestricted fallback occurs.

**Live example**: [verify_t2.py](../scripts/verify_t2.py) passed two baseline tests on a fresh fixture copy outside OneDrive. One actual Developer call changed only `cli.py` and `test_cli.py`, preserving positive/zero behavior and rejecting negative input. Eight resulting tests and five separate controller-authored command checks passed inside AppContainer. A distinct Reviewer session returned `pass` with no findings. Actual AI call attempts: **2**. The repository fixture was preserved; no plan/result approval was created. Raw evidence: `%LOCALAPPDATA%/development-tools-harness/t2-live/078cd86f7dca`.

```powershell
# Explicit component verification: two real AI calls on a new disposable fixture.
& $harnessPython scripts/verify_t2.py --live
```

**Verification (2026-09-21)**: All **265 tests passed**, with zero failures/errors/skips; `pip check` passed. The 59 new cases cover role/patch contracts and isolated validation. Actual pytest checks distinguish passing, failing, skipped/empty, collection-error and interrupted outcomes. Parent/child tests deny protected reads/writes and eight TCP/UDP IPv4/IPv6 attempts to owned loopback listeners; host controls succeed. Other checks cover stale versions, user edits, out-of-scope changes, descendant cleanup and persistence failure before execution. Actual CLI probes reject forced tools without AI calls. [Phase3_Workers.json](Evidence/Phase3_Workers.json) records source/artifact hashes; historical evidence is preserved.

**Limits / subsequent integration**: Supports the reviewed Python 3.12/pytest dependencies and UTF-8 creation/replacement. Deletion/rename and unreviewed dependencies are unsupported; test outputs must use scratch. Missing dependencies/incomplete checks cannot pass. This component script is not general Phase execution or the P3-T7 accepted example. P3-T3 connects admission/records and P3-T4 connects sequential execution/corrections below. Planning approval remains planning-only.

### P3-T3 — Execution Admission and Durable Records

**Implemented and verified (2026-09-22)**: [Workflow](../src/development_harness/workflow.py) creates a separate execution record from the latest approved planning Run. It checks the plan/version, initial files, generated artifacts, pinned writing profile, registered validation commands and current-Phase task scope. The registered specification and protected paths cannot become implementation targets. Execution authorization is bound to the admitted plan, code and controller policy; `plan-approve` retains its planning-only meaning.

```powershell
# Use the prepared project from the README planning example after plan approval.
& $harnessPython -m development_harness --project $planningProject workflow-prepare
& $harnessPython -m development_harness --project $planningProject workflow-status
# Authorize this exact plan/code/policy; this command makes no AI call.
& $harnessPython -m development_harness --project $planningProject workflow-approve
# Optional: release this workflow while preserving files and evidence.
& $harnessPython -m development_harness --project $planningProject workflow-cancel
```

`workflow-prepare --planning-run <run-id>` can name the latest approved planning Run explicitly. Preparation enters `awaiting_execution_approval`; approval enters `execution_ready`. Repeating either command preserves the same record/authorization. `plan-status` still reads the planning Run. `workflow-status` returns raw attempts/findings, measured summaries and inspection errors; an inspection error gives CLI exit code 1. Authorization does not start tasks. T3 recorded `workflow_execution_enabled=false` and `orchestration_available=false`; new T4 records advertise both capabilities as `true` and require `workflow-run` to start. Existing `run`/`resume` still belong to Phase 1 fixtures and reject real workflow records.

| Component | Implemented behavior |
|---|---|
| [Store.transition](../src/development_harness/store.py) | Writes state and its stable event identity in one SQLite transaction. Replaying the same transition does not append records or increment counts; conflicting replay data is rejected. |
| [WorkflowRecords](../src/development_harness/workflow_records.py) | Binds attempts, approval waits and findings to task/plan/code/policy identities. Stores observed time/usage; incomplete or unknown totals remain `null`. Separates dispatch attempts, confirmed responses and uncertain calls. |
| Worker lifecycle hooks | Persist `prepared`, `process_registered`, `dispatch_intent`, `responded` and `finished` observations. Process identity and dispatch intent are saved before prompt delivery. Missing confirmation remains uncertain and blocks automatic redispatch. |
| Controller single-call/check entries | `Workflow.invoke` and `validate_task` connect existing role/isolated-validation components to the journal. Reviewer inputs use controller-recorded files and passing evidence for every registered check. These internal entries do not schedule tasks or apply Developer changes. |
| Finding history | Controller identities distinguish review-local labels. Exact repeats retain identity; wording changes require explicit mapping. `open`, `resolved`, `false_positive` and `deferred` retain their evidence/history. Closure requires matching follow-up review, and resolution requires subsequent passing registered checks. Deferred mandatory findings remain blocking. |

**Verification scope**: Admission/CLI tests cover stale plan/code/policy/profile data, protected scope, repeated authorization, ownership and preserved planning behavior. Journal tests inject failures around dispatch and transaction persistence, replay events and findings, and check unknown values. Deterministic local subprocess tests exercise the Adapter-to-journal bridge without an AI service; actual AppContainer checks retain the validation boundary. T3 makes **zero live AI calls**. All **378 tests passed** in 272.93 seconds, with zero failures/errors/skips; `pip check` passed. T3 adds 113 cases to the T2 total of 265. [Phase3_Records.json](Evidence/Phase3_Records.json) records the evidence; the full report is `%LOCALAPPDATA%/development-tools-harness/t3-regression/27473119975a/pytest.xml`. The dated T1/T2 evidence remains unchanged.

**Preserved boundary**: An incomplete attempt or missing finding ingestion stops further dispatch for inspection. T3 records uncertainty; it does not automatically recover or retry it. T4 adds task order, controlled changes and bounded corrections below; T5 adds explicit recovery with evidence checks. Reports/feedback/acceptance, the accepted external example and frozen runner A remain P3-T6–T8.

### P3-T4 — Sequential Execution, Corrections and Final Validation

**Implemented (2026-09-22)**: [Execution](../src/development_harness/workflow_execution.py) connects approved Tasks in order through Developer → checked file application → AppContainer validation → a fresh read-only Reviewer. [Workflow](../src/development_harness/workflow.py) holds project ownership, pins the execution policy and supplies recorded evidence. A dependent Task starts only after its predecessors complete.

```powershell
# After planning approval, pin the additional correction allowance and authorize execution.
& $harnessPython -m development_harness --project $planningProject workflow-prepare --max-corrections 2
& $harnessPython -m development_harness --project $planningProject workflow-approve
& $harnessPython -m development_harness --project $planningProject workflow-run
& $harnessPython -m development_harness --project $planningProject workflow-status
# Alternative: run one complete stage, inspect, then continue with workflow-run.
# & $harnessPython -m development_harness --project $planningProject workflow-run --steps 1
```

| Rule | Implemented behavior |
|---|---|
| Initial approval and current code | Preserve the initial plan/code/policy approval. Every accepted content version must follow a complete chain of scoped Developer proposals and hashed patch records from that start. Unexpected user edits stop execution and are preserved. |
| Correction budget | Default: two additional Developer attempts per Task, shared by test failures and required review findings. The limit is fixed by `workflow-prepare --max-corrections` and cannot be changed by AI output. Exhaustion fails the Task and prevents later Tasks. |
| Validation and stopping | Use registered pytest checks in AppContainer. Structured JUnit failures distinguish code defects from environment/permission problems. Missing dependencies, permissions, unclear requirements, timeouts, skips, zero tests and incomplete evidence stop without requesting a code correction. Each correction reruns the checks. |
| Independent follow-up review | Supply original Task before-files, current after-files, the latest matching validation batch and unresolved controller finding IDs. Every prior ID receives exactly one explicit `open`, `resolved`, `false_positive` or `deferred` assessment with reason/evidence. Repeated findings keep identity; omission/self-report cannot close them. Resolution requires subsequent passing checks for that code. Mandatory deferred findings still block completion. |
| Final checks | After all Tasks pass, rerun every registered check against final content and check unresolved mandatory findings. Final failure stops for inspection without assigning it automatically to a Task or spending a Task correction. Success is `technically_complete`; user acceptance remains separate. |
| Durable boundaries | `--steps` pauses after completed stage records. A later `workflow-run` continues that clean boundary without reapproval. In-flight/uncertain calls, missing finding ingestion and partial patches prevent redispatch; explicit interrupted recovery uses T5 below. |

New workflow records report `workflow_execution_enabled=true` and `orchestration_available=true`; these are capability flags. Explicit execution authorization is still required. Earlier T3 policies must be replaced by a newly prepared/authorized workflow before sequential execution. `workflow-run` returns nonzero for stopped/failed execution. Unknown duration/usage remains `null`.

**Live example**: [verify_t4.py](../scripts/verify_t4.py) used a fresh fixture outside OneDrive with a controller-authored two-Task plan and two passing baseline tests. No Planner service call was made. Configured model `gpt-6-astra` performed **four actual, confirmed role calls in distinct sessions**, with zero uncertain calls. Task 1 changed `cli.py` and `test_cli.py`; Task 2 reported unchanged because those changes already covered its cases, and still received its own validation and independent review. Task 1, Task 2 and final AppContainer runs each passed **eight tests**; **six additional controller checks** passed against the same application copy. Both Tasks used zero corrections. The workflow reached `technically_complete`, preserved its initial approval and left the repository fixture unchanged. Raw report: `%LOCALAPPDATA%/development-tools-harness/t4-live/d912782f99cd/report.json`. This is T4 execution evidence, not T5 interruption recovery, P3-T7 acceptance or completed self-development.

```powershell
# Explicit live verification on a new disposable project; makes actual role calls.
& $harnessPython scripts/verify_t4.py --live
```

**Default storage regression**: The live script reused a separately prepared validator. A subsequent no-AI test of the default validation factory reproduced Windows `WinError 206` while copying Python into the longer workflow path. Validation runtime storage now uses `<state-home>/workflow-validation/<attempt-id>` and the journal retains its absolute evidence paths. The real default-factory AppContainer regression passed after that fix.

**Regression verification (2026-09-22)**: All **465 tests passed** in 348.78 seconds, with zero failures, errors or skips; `pip check` passed. T4 adds 87 cases to the historical T3 total of 378, including the real default-storage regression. The final report is `%LOCALAPPDATA%/development-tools-harness/t4-regression/bcda88eaee1f/pytest.xml`. [Phase3_Execution.json](Evidence/Phase3_Execution.json) records the final source/report hashes, four-call live example and default-path verification. T1–T3 historical evidence remains unchanged.

### P3-T5 — Explicit Interruption Recovery

**Implemented (2026-09-22)**: [workflow_recovery.py](../src/development_harness/workflow_recovery.py) inspects the recorded `active_step` cursor, approved task order, plan/policy, process ownership and actual files before resuming. [workflow_attempt_recovery.py](../src/development_harness/workflow_attempt_recovery.py) verifies saved role artifacts and records an explicit reconciliation decision through [WorkflowRecords](../src/development_harness/workflow_records.py). `workflow-status` exposes an advisory `recovery` assessment without applying files or updating attempt history. `workflow-resume` repeats those checks under the project lock before making changes.

```powershell
# Inspect recovery availability/reason, then explicitly resume the approved workflow.
& $harnessPython -m development_harness --project $planningProject workflow-status
& $harnessPython -m development_harness --project $planningProject workflow-resume
# Optional: complete only one recovered/execution boundary before returning.
# & $harnessPython -m development_harness --project $planningProject workflow-resume --steps 1
```

| Interrupted state | Recovery behavior |
|---|---|
| No durable dispatch intent, with no response evidence contradicting non-dispatch | Settle the original attempt as proven unsent and allow a fresh identity. This contributes zero AI calls. The transport must commit dispatch intent before sending request input. |
| Request may have been sent, but no complete verified saved response exists | Block redispatch and explain the missing evidence. An empty log or absent response does not prove that the service received nothing. |
| Complete saved Developer/Reviewer response | Check fixed controller artifact paths, input hash, original task/files, output schema, successful event stream, distinct session, response hash and known observations. Reuse the response without repeating that role call. Reviewer reuse also verifies original before-files, latest matching checks and prior findings/assessments. |
| Some approved files were applied | Compare every actual file with its recorded before/after hash. Retain matching applied content and write only proven unapplied changes. Unrecognized partial bytes, unrelated additions or user edits stop without rollback or overwrite. |
| Validation interrupted | Confirm the old process tree ended, preserve the incomplete outcome/timing and rerun registered checks. A saved completed failure retains its normal code/environment classification; resume cannot turn it into a pass or bypass correction limits. |
| Review saved or already ingested before the next boundary | Reuse the verified review and replay the original finding/assessment transaction once. Closed findings and completed task/correction transitions are not counted again. |

**Process and ownership checks**: [processes.py](../src/development_harness/processes.py) compares PID plus creation time and queries the recorded named Windows Job to detect surviving descendants. Recovery inspection is read-only and does not terminate an arbitrary process to acquire ownership. The AI transport starts an inert trusted gate and releases the command only after containment and durable dispatch registration; controller death before release closes the input without starting the AI CLI. AppContainer process creation attaches the Job atomically, closing the interval between creation and containment. Kill-on-close jobs contain descendants. Shared project ownership applies across `--state-dir` values; an active, missing or corrupt previous database blocks reassignment. Administrator setup and installed-runtime ACL changes remain excluded.

**Preserved records and authorization**: Reconciliation stores separate `recovery` facts and idempotent events; it never rewrites the original attempt's observed lifecycle. `effective_attempt` supplies validated recovered facts to scheduling, findings and aggregate call/usage totals, while `workflow-status.attempts` preserves raw history with its recovery record. A reused response counts once; an unsent attempt counts zero. Unknown timing remains `null`, and the recovery operation has its own timestamps. The same initial execution approval and per-Task correction counts survive. Cancelled, failed and technically complete runs are not restarted. An interrupted legacy T4 run without a durable `active_step` cursor remains blocked for inspection. Source-identical `.git` metadata changes do not invalidate the content snapshot.

**Verification coverage**: Local subprocess cases exercise actual termination before/after dispatch, saved-response reuse, partial writes, recovery interrupted again, review ingestion replay, user-edit preservation, unchanged approvals/counters and metadata-only changes. Real AppContainer cases interrupt validation and confirm process cleanup plus fresh final checks. Artifact tests reject altered input/output/schema/events/session/usage, invalid timing and repeated recovery with changed evidence; read-only assessment and transaction rollback are also checked.

**Regression verification (2026-09-22)**: The full run passed **535 tests** in 474.664 seconds, with zero failures, errors or skips; `pip check` passed. After that run had started, a final audit added the missing `final_interrupted` recovery classification and one new regression. The subsequent **nine recovery edge checks passed** in 17.66 seconds. Eight overlap the full run, so the combined evidence covers all **536 currently collected tests**, including **71 T5 additions** over T4's 465. The full JUnit report is `%LOCALAPPDATA%/development-tools-harness/t5-regression/c382926a7112/pytest.xml`. [Phase3_Recovery.json](Evidence/Phase3_Recovery.json) records the final source/report hashes and both runs separately. The focused attempt-record/review suite also passed 96 tests without live AI calls. T1–T4 evidence, including T4's four-call example, remains historical and unchanged.

**Live recovery example**: [verify_t5.py](../scripts/verify_t5.py) passed on a fresh one-Task fixture outside OneDrive using a controller-authored plan and two real passing baseline tests, with no Planner AI call. The controller exited with code 99 immediately after saving the actual Developer response. `workflow-resume` reused that response with **zero additional Developer calls**, then completed isolated validation and a separate Reviewer session. Configured model `gpt-6-astra` made **two confirmed distinct role calls**, with zero uncertain calls or corrections. The Task and final checks each passed **eight tests**, and **six independent controller checks** passed. Original approval and repository fixture were unchanged; repeating resume after completion performed no work. The state is `technically_complete`, with user acceptance false. Raw report: `%LOCALAPPDATA%/development-tools-harness/t5-live/0bd5406cb3a6/report.json`. The script reused a verified validator in a short external path; default per-attempt storage is tested separately. P3-T6–T8 and Phase 3 user acceptance remain pending.

```powershell
# Explicit disposable live recovery verification; at most two actual role calls.
& $harnessPython scripts/verify_t5.py --live
```

### P3-T6 — Minimum Results, Feedback and Acceptance

**Implemented (2026-09-22)**: [results.py](../src/development_harness/results.py) produces the minimum `workflow-report` JSON, [workflow_feedback.py](../src/development_harness/workflow_feedback.py) preserves and routes feedback, and [workflow_acceptance.py](../src/development_harness/workflow_acceptance.py) checks final evidence and records explicit user acceptance. These extend the existing Workflow APIs and CLI. A short formatted report and richer presentation remain Phase 4 work.

| Area | Implemented behavior |
|---|---|
| Read-only result | Show success, failure, interruption, permission failure, unverified evidence, replanning and superseded results. Reading a report/status does not change project files, existing database bytes, approvals, findings or calls. Inspection failures are reported alongside preserved history. |
| Delivered files and evidence | Compare original/current hashes and scoped patch history; show actual contributing Tasks, unexpected changes and interrupted patches. Include registered commands, Task acceptance/verification, current/final validation, reuse/manual status, unresolved findings/feedback and metrics. Evidence entries include an absolute path and whether the file exists. |
| Same-scope feedback | Preserve original text, stable identity and routing/outcome history. A defect targets an approved Task, retains the original approval and consumes its remaining shared correction allowance. Exhaustion blocks further automatic correction. Corrected earlier Tasks trigger fresh validation/review of the previously completed suffix and all final checks. |
| Changed requirements | Mark the old workflow `replanning_required`; preserve approval as history while blocking further use. Update the registered specification to reflect the request, then `workflow-replan` creates fresh planning from current files without an AI call. Exact feedback is preserved but does not rewrite the Planner's source specification. The later planning baseline runs previously generated code in AppContainer; a new plan and execution approval are required. No implicit scope expansion or reuse of the old authorization. |
| Reused requirements | Require a separate user explanation for every current `reuse` requirement, including those without Tasks, mapped to actual passing final-validation IDs. A passing generic test run alone does not establish which reused requirement it proves. |
| Manual checks | Pin all required definitions before execution approval. Each has `id`, current `requirement_ids`, `procedure` and `expected`; all declared checks are mandatory. Record the actual user-observed passed/failed result and evidence after technical completion. |
| Acceptance gate | Check matching plan/policy/content/completion, complete Task order/reviews, no pending work or mandatory findings/feedback, all current final tests and sealed artifacts. Missing, stale, modified or failed proof blocks acceptance. Technical success can remain true while reuse/manual evidence is pending; explicit user acceptance is still required. |

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-report
# Choose the applicable feedback route; substitute actual Task IDs and original feedback.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind defect --task '<task-id>' --text 'Observed defect within the approved scope.'
& $harnessPython -m development_harness --project $planningProject workflow-run
# Changed requirements instead require a fresh plan, then plan/execution approval.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind requirements --text 'Describe the changed requirement.'
# Update the registered specification with the requested change before replanning.
& $harnessPython -m development_harness --project $planningProject workflow-replan
& $harnessPython -m development_harness --project $planningProject plan
```

**Manual policy and confirmations**: `workflow-prepare --manual-checks <json-file>` reads an array such as `[{"id":"M1","requirement_ids":["R1"],"procedure":"Inspect the negative-input CLI result.","expected":"A nonzero exit and explanatory stderr."}]`; replace the example with the current Phase's real requirements. This file is read and its definitions become part of the approved execution policy. After final validation, use `workflow-reuse --requirement <id> --validation-ids <actual-final-id> --outcome passed --evidence <explanation>` and `workflow-manual --check <id> --outcome passed --evidence <observation>`. Failed observations must use `--outcome failed`. UTF-8 feedback/evidence files are supported by `--from` and `--evidence-file`. [README usage](../README.md#phase-3-results-feedback-and-acceptance) provides complete examples.

**Version and artifact checks**: Final validation records seal the record, JUnit, stdout and stderr artifacts with SHA-256 hashes. Reuse/manual confirmations bind to the approved plan/policy, current content and final completion identity; a correction or new completion invalidates prior confirmations. `workflow-accept` cannot override missing criteria. The gate requires an approved `result_version=1` policy and sealed final evidence. Legacy T4/T5 live runs remain historical technical results and report as unverified for this acceptance gate; a new approved workflow is required. Reporting never adds seals, changes their policy or manufactures acceptance. After acceptance, confirmation replacement or feedback reopening is blocked.

**Verification coverage**: [test_workflow_results.py](../tests/integration/test_workflow_results.py) covers actual isolated success/failure, correction exhaustion, interrupted/permission outcomes, delivered-file attribution, missing/stale artifacts, preserved feedback, manual/reuse evidence and read-only database/project checks. Acceptance/feedback regressions separately check reused requirements with no Task, failed/stale/missing confirmations, early acceptance, final edits, shared correction exhaustion, downstream validation/review, changed-requirements planning and preserved authorization history. Reading the historical T5 live result makes **zero new AI calls**; its **two recorded role calls belong to T5**. It is not a new T6 live example or a user acceptance.

**Historical live-result inspection (2026-09-22)**: The final production `workflow-report` check on the saved T5 example passed its expected assertions: exit code 1, `outcome=unverified`, the original stage still `technically_complete`, and acceptance false. Its old policy, unsealed evidence and missing reuse confirmation for R1 block acceptance. The existing database bytes and project files were unchanged, with zero new AI calls. The final report and verification record are `%LOCALAPPDATA%/development-tools-harness/t6-results/df2c8127f247/report.json` and `verification.json`. These inspect the two historical T5 calls; no new live execution or user acceptance is claimed.

**Regression verification (2026-09-22)**: All **632 tests passed** in **1801.44 seconds** as recorded by JUnit, with zero failures, errors or skips; `pip check` passed. T6 adds **96 cases** to T5's 536: 14 report integrations, 22 acceptance integrations, six feedback-flow integrations, 34 feedback unit cases and 20 replanning unit cases. All 70 source/test files match the manifest captured before this full run. The JUnit report is `%LOCALAPPDATA%/development-tools-harness/t6-regression/43c96f65d234/pytest.xml`, SHA-256 `f84d5bd39f393a72c230c56676ee5ce8ef0db86e4efe2266e51d5237bfe338c3`. [Phase3_Results.json](Evidence/Phase3_Results.json) records the final verification and historical live-result inspection separately. T6 adds zero actual AI calls. Historical T1–T5 evidence and the approved generated plan remain unchanged. P3-T7–T8 and Phase 3 user acceptance remain pending.

### Purpose / Implementation Files

Extend the Phase 1 runner/storage and Phase 2 Adapter. P3-T1 preparation, P3-T2 components, P3-T3 `workflow.py`/`workflow_records.py` admission/journaling, P3-T4 `workflow_execution.py` scheduling and P3-T5 `workflow_recovery.py`/`workflow_attempt_recovery.py` reconciliation now exist. P3-T6 adds `results.py`, `workflow_feedback.py`, `workflow_acceptance.py` and their CLI/planning integration. Full existing/proposed paths are listed in the reviewed plan.

### Design Decisions

- Keep one sequential workflow and the implemented two-correction default; no Fast/Standard/Strict routing or parallel Tasks.
- Implement all event collection now. Provide minimum evidence access now; reserve a small remaining report summary for Phase 4 self-development.
- Recheck reused requirements at final acceptance even without an implementation Task. No broad code-analysis or coverage engine is added.
- Freeze A as a separately installed/copied runtime, not an editable installation referencing B. Place runtime records outside OneDrive; B tests use temporary records and limited permissions. Record actual isolation probes.

### Usage Example

The proposed Python CLI doubles an integer, with baseline tests for positive and zero input. The bounded change rejects negative input with a clear error and nonzero exit while preserving normal output. Use a separate temporary copy, review the generated Phase, approve execution, interrupt once, resume, inspect review/validation evidence and obtain user acceptance. P3-T1 records the exact commands and expected outputs before the live example.

## Prerequisites & Development Notes

Reuse earlier components with regression evidence. Core protections must work with actual worker processes, not only the fake Adapter. A permissions or resume defect blocks promotion to runner A. Existing coding tools may fix such defects; record that manual intervention. This external example is preparation for full dogfooding, not the self-development milestone itself.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the full-flow outline, external example gate and fixed-runner requirements. |
| 2026-09-21 | Used the successful Phase 2 planning dogfood run to draft eight Tasks and 18 requirements. Preserved AI v1, reviewed v2 and evidence; clarified role permissions, findings, Phase 4 scope and technical gates. Implementation and user acceptance remain pending. |
| 2026-09-21 | Recorded Phase 2 user acceptance as a satisfied prerequisite. Phase 3 plan approval, implementation and worker permission verification remain outstanding. |
| 2026-09-21 | User authorized Phase 3 development after reviewing its order and logic. Started P3-T1 execution-contract/example preparation and disposable permission investigation. No actual target-modifying AI worker has been admitted. |
| 2026-09-21 | Completed P3-T1 preparation/investigation: execution contract, two-test CLI baseline and synthetic workflow-doctor. All 187 tests passed. File-write restrictions held, but six parent/child raw TCP connections exposed the unelevated network limitation; P3-T2 remains gated on stronger verified isolation. Preserved project inputs/Run and recorded zero AI calls. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-21 | Applied the company prohibition on administrator setup. Added the default AppContainer diagnostic and actual standard-user role/network/descendant/deadline probes; retained the previous Codex candidate via an explicit backend option. Recorded the proposed text-only AI plus isolated-test integration and kept live execution disabled. See AppContainer evidence for regressions. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-21 | Implemented P3-T2 real roles, controlled patches and isolated pytest. All 265 regressions and a two-call live example passed. P3-T3–T8 and Phase acceptance remain pending. Updated both languages; dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Implemented P3-T3 execution admission, atomic/idempotent call/time/finding records and controller lifecycle integration. Added no-dispatch CLI usage and verified local subprocess/AppContainer integration. All 378 tests and pip check passed. No live AI calls. P3-T4–T8 and Phase acceptance remain pending. Updated both languages and README status; separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Implemented P3-T4 sequential execution, shared correction budgets, checked patch lineage, explicit follow-up review and final validation. A two-Task live example passed with four real role calls; a default-storage AppContainer regression verified the Windows path-length fix. Current full regressions are recorded above. T5–T8 and Phase 3 acceptance remain pending. Updated both languages and README; separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Implemented P3-T5 explicit workflow-resume, artifact-proven response reuse, checked partial-file repair, process-tree/ownership guards and separate idempotent recovery facts. Preserved original approval, correction counts and historical T1–T4 evidence. Current verification is recorded above. Updated both languages and README; T6–T8 and Phase acceptance remain pending. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Implemented P3-T6 read-only minimum JSON reports, preserved same-scope/changed-requirements feedback, final reuse/manual evidence and explicit acceptance gates. Preserved T1–T5 evidence and the generated plan; zero new actual AI calls. Updated both languages and README; T7–T8 and Phase acceptance remain pending. Separate dev-log omitted because the skill is unavailable. |

---

# Phase 3 — 전체 실행 흐름 `🚧 진행 중`

> 실제 예제 Phase 하나를 완료하고 자체 개발에 사용할 검증된 고정 실행본을 준비한다.

**선행 조건**: 2026-09-21 [Phase 2](Phase2_Planning.md) 인수 완료. 실제 작업 프로세스 실행 전에는 권한 검증과 준비된 예제도 필요하다.

**기술 구성**: Python + pytest, SQLite, 선정한 단일 AI Adapter.

**계획 상태**: P3-T1–T3 준비·실제 역할·격리된 검증·실행 승인·영속 기록의 구현·검증을 완료했다. P3-T4는 순차 실행·제한된 수정·독립 리뷰의 명시적 지적 평가·최종 검사를 연결했고 실제 Task 2개 예제가 기술적 완료에 도달했다. P3-T5는 승인·파일·호출 이력을 유지하는 명시적 중단 복구를 구현했다. P3-T6는 최소 JSON 보고서·피드백 처리·최종 재사용 및 수동 근거·명시적 인수 조건을 구현했으며 현재 검증 결과는 아래 기록한다. 회사 정책상 관리자 설정 없이 일반 사용자 AppContainer를 사용한다. 외부 예제 인수·고정 실행용 A는 P3-T7–T8에 남아 있다. Phase 2는 인수했으며 Phase 3 전체 인수는 대기 중이다. Task 8개·요구사항 18개의 검토 계획과 AI 원본·수동 검토 근거는 보존했다.

## 개요

실제 구현·검증·별도 리뷰·제한된 수정·최소 결과 인수를 연결한다. 하네스로 자신을 수정하기 전에 별도 예제로 전체 흐름과 중단·재개를 확인한다. 기획서 6–10장을 다루며 최종 보고서 표현은 Phase 4에서 완성한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Developer·Validation Runner·Reviewer 순차 Workflow | ✅ T4 구현, 현재 검증 결과는 아래 기록 |
| 2 | 호출·시간·지적 기록, 수정·프로세스 확인을 포함한 재개 | ✅ T3–T5 구현, 현재 복구 검증 결과는 아래 기록 |
| 3 | 최소 성공·실패 보고서, 피드백·결과 인수 | ✅ T6 구현, 현재 검증 결과는 아래 기록 |
| 4 | 인수한 외부 예제와 검증된 고정 실행용 A | 🔲 |

## 검증 및 종료 조건

[검토한 계획](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan_ko.md)에 완료 기준·제안 경로·검증 방법을 기록했다. [검토 근거](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md)에 AI 원본과 수동 보완을 보존했다. P3-T1·T2 구성요소를 검증했으며 임시 예제에서 실제 AI 호출 2회를 확인했다. P3-T3 실행 승인·기록을 구현·검증했으며 전체 검사 378개를 통과했다. P3-T4 구현과 실제 호출 4회의 예제는 [실행 근거](Evidence/Phase3_Execution.json)에 기록했다. P3-T5 복구를 구현했으며 별도 [복구 근거](Evidence/Phase3_Recovery.json)를 보존한다. P3-T6 결과·피드백·인수 조건을 구현했으며 [결과 근거](Evidence/Phase3_Results.json)와 현재 검증 결과는 아래에 기록한다. P3-T7–T8 구현은 미시작이다.

| Task | 개발 내용 | 완료 근거 |
|---|---|---|
| P3-T1 | 선행 조건 확인, Windows 작업 권한 분리 검토, 실행 계약과 작은 CLI 예제 준비. | Phase 2 인수 기록, 권한 수단 조사·시험, 예제 기본 검사와 한정된 변경 기획. |
| P3-T2 | 단일 Adapter에 Developer·읽기 전용 Reviewer 연결, 작업·테스트 권한 집행. | 구현·검증 완료: 실제 별도 세션·파일 변경 검사·격리된 pytest와 자식·파일·통신 차단. [검증 근거](Evidence/Phase3_Workers.json). |
| P3-T3 | 버전별 실행 진입과 호출·시간·지적의 영속 기록 연결. | 별도 실행 승인, 원자적·중복 없는 기록, 호출 단계 연결과 근거 기반 지적 기록 구현·검증 완료. 전체 검사 378개 통과. [검증 근거](Evidence/Phase3_Records.json). |
| P3-T4 | Developer → 검증 → 별도 Reviewer 순차 실행과 제한된 수정. | 구현: 실제 격리 검사·명시적 지적 평가·공통 수정 한도·변경 이력·최종 코드 검사. 실제 호출 4회의 예제가 기술적 완료에 도달했다. [근거](Evidence/Phase3_Execution.json). |
| P3-T5 | 부분 구현과 중단된 검사의 안전한 재개. | 구현: 명시적 재개·저장 응답 검증 및 재사용·부분 파일 확인·프로세스와 자식 검사·별도 복구 사실·승인 및 수정 횟수 유지. [근거](Evidence/Phase3_Recovery.json), 현재 검증 결과는 아래 기록. |
| P3-T6 | 최소 보고서·피드백 처리·최종 재사용 확인·인수 조건 추가. | 구현: 읽기 전용 JSON 결과, 피드백 보존·수정 및 재계획 경로, 최종 재사용·수동 확인과 버전에 연결된 인수 조건. [근거](Evidence/Phase3_Results.json), 현재 검증 결과는 아래 기록. |
| P3-T7 | 외부 CLI 예제의 실제 역할 실행·중단·재개·사용자 인수. | 전체 회귀 검사, 실제 출력·별도 역할 세션과 사용자 결과 인수 기록. |
| P3-T8 | 실행용 A 고정과 Phase 4 이전 분리 입증. | 독립 설치 위치·고정 산출물, 실제 B·테스트 쓰기 차단, 설치본의 흐름·재개 검사. |

P3-T2에서 범위가 명확한 임시 예제로 실제 작업 구성요소를 검증했다. P3-T3는 특정 계획·코드·정책 버전을 준비·승인하며 작업 호출은 시작하지 않는다. P3-T4는 `workflow-run`으로 승인한 작업을 시작하고 P3-T5는 명시적 `workflow-resume`, P3-T6는 최소 보고서·결과 인수 조건을 추가한다. 외부 예제의 실제 사용자 인수는 T7에 남아 있다. unelevated 후보는 통신 차단에 실패했으며 elevated 설정은 회사 정책상 제외한다. 관리자 설정이나 제한 없는 실행으로 대체하지 않는다.

pytest 통합·회귀 검사와 실제 예제 실행으로 다음 동작을 확인한다.

- 승인된 작은 Phase의 Task를 순차 실행한다. Reviewer는 별도 세션에서 요구사항·실제 구현·테스트를 대조한다. 필수 지적에는 후속 리뷰·검증 근거가 필요하며 Developer 자기 보고만으로 해결하지 않는다.
- 변경 후 필요한 검사를 다시 수행하고 Phase 최종 내용에서도 검증한다. 실패·생략·중단·테스트 0개는 통과하지 않는다. 수정은 설정한 한도에서 멈추며 환경·권한·기획 문제는 코드 수정 재시도를 소모하지 않고 중단한다.
- 승인·검증 근거·결과 인수는 일치하는 계획·코드 버전에 연결한다. 같은 범위의 결함 피드백은 현재 Phase 수정으로, 요구사항 변경은 계획 갱신·승인으로 처리한다. 피드백 원문과 처리 결과를 저장한다.
- 구현 중단 시 부분 파일을 확인한다. 검사 중단 시 잔여 프로세스를 확인하고 필요한 검사를 다시 실행한다. 예상 밖 사용자 변경은 덮어쓰지 않고 중단하며 다른 Runner의 안전하지 않은 소유권 획득을 막는다. Git 메타데이터만 수동 변경된 경우 나머지 입력이 같으면 재개를 막지 않는다.
- 실제 역할별 호출 시도·확정된 시간과 미완료 구간·승인 대기·리뷰 지적에 안정적인 식별자를 부여한다. 재개 시 호출과 동일 지적을 중복 집계하지 않는다. 수정 확인에는 근거가 필요하고 보류한 필수 지적도 완료를 막는다. 알 수 없는 시간·토큰·금액을 추정하지 않는다.
- 성공·실패 모두 최소 보고서를 제공하고 산출물, 검사·재사용 근거, 미해결 항목, 수동 확인, 상세 기록 위치를 표시한다. 사용자 인수와 기술적 완료를 구분하며 인수로 미충족 필수 조건을 무시하지 않는다.
- 별도 준비된 예제에서 중단·재개와 사용자 인수를 포함해 작은 Phase를 완료한다. A의 코드·의존성·역할 지침·정책을 고정하고, 다음 Phase 전에 B와 테스트 프로세스가 A 및 실행·승인 저장소를 변경하지 못함을 입증한다.

**결과(2026-09-21)**: P3-T1의 준비된 CLI 예제, 합성 `workflow-doctor` 명령과 실행 계약을 추가했다. 전체 **187개 검사 통과**, 실패·생략 0개이며 `pip check`도 통과했다. 별도 예제 기본 검사 2개가 실제로 통과했다. 세 역할과 자식 프로세스의 파일 쓰기 제한은 동작했지만, 네트워크 비활성화 설정에도 직접 루프백 TCP 연결 6개가 모두 성공했다. 진단은 `ready=false`, 종료 코드 1, `execution_enabled=false`를 반환했다. 프로젝트 입력·기존 계획 Run을 보존했고 실제 AI 호출은 0회다. 준비·조사 완료이며 P3-T2 권한 분리나 실제 Phase Workflow 완료가 아니다. [준비 검증 근거](Evidence/Phase3_Preparation.json)를 보존했다.

## P3-T1 실행 계약과 권한 조사

아래는 후속 구현에서 지킬 실행 계약이다. `workflow-doctor`는 합성 시험만 구현하며 실행 승인을 처리하지 않는다.

| 계약 | 필수 동작 |
|---|---|
| 계획 입력 | Phase 2에서 승인한 `plan.json`과 버전·산출물 해시·고정된 작성 규칙을 재사용한다. 현재 Phase의 Task·선행 관계·명시 경로·요구사항·완료 기준만 실행 대상으로 삼는다. 계획 승인과 명시적인 실행 지시는 구분한다. |
| 실행 정책 | 제어 프로그램이 등록된 검증 명령·시작 파일 상태·수정 한도를 관리한다. 제안 기본값은 Task당 수정 2회다. AI 응답으로 승인 정책·검사·한도를 바꿀 수 없다. |
| Developer | 현재 Task, 승인 요구사항, 관련 코드와 이전 실패·리뷰 근거를 제공한다. 승인 경로로 수정을 제한하고 변경 내용·미해결 질문을 받는다. 완료 응답만으로 검증을 통과시키지 않는다. |
| 검증 | 실제 변경된 코드에서 등록 명령을 실행한다. 전용 임시 테스트 파일만 허용하고 프로젝트 입력·제어 기록을 보호하며 제한을 자식 프로세스에 상속한다. 실패·생략·미실행·중단·테스트 0개는 통과하지 않는다. |
| Reviewer | 별도 읽기 전용 세션에서 요구사항·변경·실제 검사 결과를 대조한다. 지적 ID·중요도·필수 여부·위치·근거를 기록하고 필수 지적은 후속 리뷰·검증 근거로만 해결한다. |
| 기록·재개 | 시도·지적·승인·검사 근거를 계획·코드 버전에 연결한다. 실행 전 프로세스 식별자를 기록하고 미완료 시간은 미확정으로 유지한다. 재개 전에 부분 파일과 잔여 프로세스를 확인하고 예상 밖 사용자 변경은 보존한다. |
| 결과·인수 | 재사용 요구사항을 포함해 최종 Phase 코드를 검증한다. 실패해도 기본 결과를 제공하고 필수 조건 미충족이면 인수를 막는다. 같은 범위 결함은 수정으로, 요구사항 변경은 계획 갱신으로 처리한다. |

**준비된 예제**: [cli.py](../tests/fixtures/workflow_project/cli.py), [test_cli.py](../tests/fixtures/workflow_project/test_cli.py), [spec.md](../tests/fixtures/workflow_project/spec.md)를 시작 프로젝트로 준비했다. `python cli.py 3`은 `6`, `python cli.py 0`은 `0`을 출력하며 둘 다 종료 코드 0·stderr 없음이다. `python -m pytest -q`는 실제 명령 실행을 검사하는 기본 사례 2개를 찾아 통과한다. 음수 거부는 의도적으로 미구현이며 `python cli.py -1`은 현재 `-2`와 종료 코드 0을 반환한다. 후속 실제 개발에서 기존 동작을 유지하면서 음수에 0이 아닌 종료 코드·숫자 stdout 없음·명확한 stderr 설명을 반환해야 한다. 구현 대상은 `cli.py`와 `test_cli.py`뿐이다. [workflow-checks.json](../tests/fixtures/workflow-checks.json)에 기본 검사 명령을 정의했다.

**구현한 진단**: [worker_probe.py](../src/development_harness/worker_probe.py)와 [시험 스크립트](../src/development_harness/worker_probe_payload.py)가 대상 프로젝트 밖에 새 합성 파일을 만든다. 설치된 `codex sandbox` 명령, 분리된 설정 폴더와 관리형 요구사항을 사용하며 인증·AI 호출은 하지 않는다. Developer는 합성 소스·임시 폴더, 검증 역할은 임시 폴더에만 쓸 수 있고 Reviewer는 읽기 전용이다. 부모·자식 프로세스가 프로젝트 파일, Git 메타데이터, 계획·설정, 가짜 실행본·승인·설치 경로, 무관한 파일의 쓰기를 시도한다. 호스트가 실제 파일 결과와 자체 TCP 수신 서버를 확인하고 전후 정상 연결도 검사한다. 외부 서비스·실제 승인 DB·패키지 설치·사용자 파일은 시험 대상으로 삼지 않는다.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython -m development_harness --project . workflow-doctor --backend codex-unelevated
```

`codex-unelevated` 진단은 실행 저장소의 `worker-probes/<id>/`에 `report.json`, 역할별 정책과 원시 프로세스 근거를 저장한다. 실패·미완료 시험은 종료 코드 1이며 `execution_enabled=false`를 유지한다. 이 후보의 호환성은 실제 확인한 CLI 0.155.1을 대상으로 하며 이전 Planner 지원은 유지한다. 미검토 작업 버전은 실행 허용 없이 검토 필요로 안내한다. 이 명령은 계획 승인이나 구현을 시작하지 않는다. 현재 기본 방식은 아래 설명하는 `appcontainer`다.

**확인한 한계**: 설치된 설정은 `windows.sandbox="unelevated"`다. 세 역할·자식 프로세스 모두 파일 쓰기는 설정대로 제한됐지만 직접 TCP 통신 6개가 자체 루프백 수신 서버에 도달했다. 네트워크 경계가 충분하지 않다는 근거이며 실제 외부 데이터 전송을 수행한 것은 아니다. OpenAI 공식 문서는 unelevated의 환경 변수 수준 오프라인 제어와 elevated의 별도 사용자·방화벽 분리를 설명하며, elevated 설정에는 관리자 지원이 필요하다. 다음 후보는 설정과 시험을 마쳐야 실제 작업에 사용할 수 있다. Windows 계정·방화벽 정책·전역 Codex 설정은 변경하지 않았다. 출처: [Windows 샌드박스](https://learn.chatgpt.com/docs/windows/windows-sandbox), [권한 적용 범위](https://learn.chatgpt.com/docs/permissions), [sandbox 명령](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

**검증 상세**: 추가 검사 15개는 진단 근거, 자식·통신·파일 결과 불일치, 실패·미완료 시험, 미검토 버전, 기존 근거 보존, CLI 오류와 준비된 실제 예제를 다룬다. Windows pytest 임시 루트의 OWNER RIGHTS ACL 때문에 제한 토큰의 읽기가 거부되는 조건을 확인했다. 실제 시험은 기존 ACL을 바꾸지 않고 CLI와 동일하게 일반 권한을 상속한 새 실행 저장소 폴더를 사용한다. 로컬 근거는 `%LOCALAPPDATA%/development-tools-harness/phase3/cb8b06882b6a417fbdef359ef883c540`, 예제 Run은 `715dfc64eae6480a9b25d04378bd171a`다. `preparation-evidence.json`에 기본 검사 2개·원본 해시·Run 유지·CLI 출력을 기록했고, 진단에 세 역할별 네트워크 검사 2개씩의 실패를 보존했다. 전체 검사 보고서는 `%LOCALAPPDATA%/development-tools-harness/phase3-preparation-tests.xml`이다.

## Workflow와 최소 결과 안내

### 관리자 설정 없는 대안 — P3-T2 후보 조사

**제약과 결정(2026-09-21)**: 사용자가 “회사 정책상 관리자 설정 불가”라고 명시했다. Codex elevated 설정·계정 생성·방화벽 변경은 제외한다. 읽기 전용 환경 확인에서 WSL 배포판과 연결 가능한 Docker 엔진이 없어 즉시 사용할 실행 환경으로 삼지 않았다. 이후 Windows 10 빌드 19045의 현재 일반 사용자 프로세스에서 AppContainer 생성·실행·삭제에 성공했다. 이는 사용자별 앱 프로필이며 Windows 로그인 계정을 새로 만드는 작업이 아니다. Microsoft 공식 문서에 [사용자별 프로필 생성](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile)과 [기능 권한에 따른 프로세스·통신 격리](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)가 설명돼 있다.

**구현**: [appcontainer_probe.py](../src/development_harness/appcontainer_probe.py), [windows_appcontainer.py](../src/development_harness/windows_appcontainer.py), [신뢰하는 시험 코드](../src/development_harness/appcontainer_probe_payload.py)로 기능 권한이 없는 AppContainer를 시험한다. 기본 Python 실행 환경을 새 임시 폴더에 복사하고 이 복사본과 합성 프로젝트 경로에만 파일 권한을 부여한다. 프로세스를 정지 상태로 만든 뒤 기존 Job에 연결하고 토큰을 확인한 후 시작하며, 지정한 표준 입출력 핸들만 상속한다. 설치된 Python의 권한·Windows 계정·방화벽 규칙·Codex 설정은 변경하지 않는다. 임시 앱 프로필은 삭제하고 설정·정리 실패 시 준비 불가로 판정하며 제한 없는 실행으로 대체하지 않는다.

```powershell
# 기본값: 관리자 설정 없는 시험. Codex 로그인·AI 호출 없음.
& $harnessPython -m development_harness --project . workflow-doctor
# 동일한 명시적 명령:
& $harnessPython -m development_harness --project . workflow-doctor --backend appcontainer
```

**실제 결과**: 세 역할과 자식 프로세스 모두 관리자 권한·추가 기능 권한이 없는 AppContainer 토큰을 유지했다. 자체 루프백 수신 서버를 향한 TCP·UDP, IPv4·IPv6 직접 연결 24건이 차단됐고 호스트 정상 연결 8건은 성공했다. Developer는 소스·임시 폴더, 검증 역할은 임시 폴더만 수정했고 Reviewer는 두 곳 모두 수정하지 못했다. 합성 Git·설정·계획·Python 파일의 쓰기가 차단됐고 실행본·승인·무관한 파일은 읽기도 차단됐다. Python 복사본·시험 입력의 해시가 유지됐으며 별도 시간 초과 시험에서 대기 중인 프로세스와 자식이 모두 종료됐다. 진단은 종료 코드 0과 `ready=true`를 반환했지만 `execution_enabled=false`, AI 호출 0회를 유지했다. 이는 로컬 합성 시험이며 외부 네트워크 시험이나 전체 Workflow 실행 허용을 뜻하지 않는다. [검증 근거](Evidence/Phase3_AppContainer.json)에 최종 회귀 검사 수와 원시 파일 해시를 기록하고 기존 unelevated 실패 근거도 보존한다.

**연결 결정**: AI 서비스 인증·통신은 기존 Codex 텍스트 전용 Adapter가 담당한다. Developer는 구조화한 변경안을 반환하고 하네스가 적용한다. Reviewer는 선택한 변경 전후 파일과 실제 검증 근거를 전달받는다. 생성 코드·테스트는 AppContainer에서 실행한다. 아래 P3-T2에서 이 구성요소를 구현·검증했으며 P3-T3에서 실행 승인·기록을 추가했다. T4 순차 실행과 T5 명시적 복구는 아래에 연결했으며 인수·고정 실행본 검증은 P3-T6–T8에 남아 있다. 이번 생성 코드를 기존 신뢰 명령용 검증기에서 실행하지 않으며 Planner 호환성 규칙은 유지한다.

**검증(2026-09-21)**: 전체 검사 206개가 통과했고 실패·오류·생략은 0개이며 `pip check`도 통과했다. 추가 검사 19개는 실제 일반 사용자 격리·자식 종료, 거짓 차단 보고, 근거 누락, 설정 실패와 기존 자료 보존을 다룬다. 별도 CLI 실행에서 준비된 예제의 파일·계획 Run·이벤트도 유지했다. 실제 AI 호출과 새 계획·결과 승인은 수행하지 않았다.

### P3-T2 — 실제 역할·파일 변경 검사·격리된 테스트

사용자의 “그럼 T2 개발 해보자” 요청에 따라 다음 네 구성요소를 구현했다.

| 구성요소 | 구현한 동작 |
|---|---|
| [CodexWorker](../src/development_harness/workers.py) | 검토된 텍스트 전용 CLI Adapter·기능 시험을 재사용한다. Developer·Reviewer는 각각 새 세션에서 한 번 호출하며 파일·명령·네트워크 도구를 받지 않는다. 선택한 입력·응답·세션·호출 시도 근거를 저장한다. |
| [TaskScope / apply_proposal](../src/development_harness/worker_contract.py) | 크기가 제한된 JSON·명시 경로·예상 해시를 검사한 뒤 UTF-8 파일 변경을 적용한다. 민감·제어·생성·연결 경로는 거부한다. 파일별 쓰기와 부분 실패를 기록하며 예상 밖 사용자 변경을 되돌리거나 덮어쓰지 않는다. |
| [IsolatedValidator](../src/development_harness/isolated_validation.py) | 검토한 Python·pytest 의존성을 복사하고 권한을 확인한다. 내용이 같은 읽기 전용 프로젝트 복사본과 쓰기 가능한 scratch에서 테스트한다. 원본·복사본·실행 환경 해시를 대조하고 출력·오류·JUnit·프로세스 근거를 저장한다. |
| 독립 Reviewer | 동일 코드 버전의 요구사항·변경 전후 파일·실제 검증을 대조한다. 지적에는 식별자·중요도·필수 여부·근거가 필요하다. 잘못된 참조나 실패·미검증을 통과로 판단한 응답은 거부한다. |

**권한**: 소유한 임시 트리 안에만 권한을 부여한다. Python의 폴더 정보 확인을 위해 해당 트리 내부 상위 폴더에만 하위 파일로 상속되지 않는 읽기·목록 권한을 준다. 정지 상태 프로세스를 기록하고 기능 권한·관리자 권한 없는 토큰을 확인한 후 시작하며 완료·시간 초과 시 자식까지 종료한다. Windows 장치·임시 경로 문제는 표준 pytest `--capture=sys`, scratch 로그와 읽기 전용 [실행 진입부](../src/development_harness/validation_entry.py)의 TEMP/TMP 설정으로 해결했다. 패키지 자동 로딩은 끈다. 관리자 설정·설치 Python의 ACL 변경·의존성 설치·제한 없는 실행 대체는 하지 않았다.

**실제 예제**: [verify_t2.py](../scripts/verify_t2.py)가 OneDrive 밖에 새 예제 복사본을 만들고 기본 검사 2개를 통과했다. 실제 Developer 호출 1회로 `cli.py`·`test_cli.py`만 수정해 양수·0 동작을 유지하고 음수를 거부했다. 변경 후 검사 8개와 별도 하네스 작성 명령 검사 5개가 AppContainer에서 통과했다. 다른 세션의 Reviewer는 지적 없이 `pass`를 반환했다. 실제 AI 호출 시도는 총 **2회**다. 저장소 예제 원본을 유지했고 계획·결과 승인은 만들지 않았다. 원시 근거: `%LOCALAPPDATA%/development-tools-harness/t2-live/078cd86f7dca`.

```powershell
# 새 임시 예제로 실제 AI 2회를 호출하는 명시적 구성요소 검사.
& $harnessPython scripts/verify_t2.py --live
```

**검증(2026-09-21)**: 전체 **265개 검사 통과**, 실패·오류·생략 0개이며 `pip check`도 통과했다. 추가 59개 검사는 역할·변경 계약과 격리된 검증을 다룬다. 실제 pytest에서 통과·실패·생략 및 빈 테스트·수집 오류·중단을 구분한다. 부모·자식의 보호 파일 읽기·쓰기가 차단됐고 자체 루프백 수신 서버 대상 TCP·UDP·IPv4·IPv6 연결 8건도 모두 차단됐다. 호스트 정상 연결은 성공했다. 지난 버전·사용자 변경·범위 밖 변경·자식 정리·실행 전 기록 실패도 확인했다. 실제 CLI 시험은 AI 호출 없이 강제 도구 요청을 거부한다. [Phase3_Workers.json](Evidence/Phase3_Workers.json)에 소스·산출물 해시를 기록하고 이전 근거는 유지한다.

**한계 / 후속 연결**: 검토한 Python 3.12·pytest 의존성과 UTF-8 생성·교체를 지원한다. 삭제·이름 변경·미검토 의존성은 지원하지 않으며 테스트 출력은 scratch를 사용해야 한다. 의존성 누락·미완료 검사는 통과하지 않는다. 이 스크립트는 일반 Phase 실행이나 P3-T7 사용자 인수 예제가 아니다. P3-T3에서 실행 승인·기록을 연결했고 P3-T4에서 아래 순차 실행·수정을 연결했다. 계획 승인은 계속 계획 전용이다.

### P3-T3 — 실행 승인과 영속 기록

**구현·검증 내용(2026-09-22)**: [Workflow](../src/development_harness/workflow.py)는 가장 최근에 승인한 계획 Run으로부터 별도 실행 기록을 만든다. 계획·버전, 시작 파일, 생성 산출물, 고정한 작성 규칙, 등록 검사 명령과 현재 Phase의 Task 범위를 확인한다. 등록 기획서·보호 경로는 구현 대상이 될 수 없다. 실행 승인은 검토한 계획·코드·제어 정책에 연결하며 `plan-approve`는 계속 계획만 승인한다.

```powershell
# README 계획 예제에서 준비한 프로젝트의 계획을 승인한 뒤 사용한다.
& $harnessPython -m development_harness --project $planningProject workflow-prepare
& $harnessPython -m development_harness --project $planningProject workflow-status
# 이 계획·코드·정책의 실행을 승인한다. 이 명령으로 AI를 호출하지 않는다.
& $harnessPython -m development_harness --project $planningProject workflow-approve
# 선택 사항: 파일·근거를 보존하고 Workflow를 취소한다.
& $harnessPython -m development_harness --project $planningProject workflow-cancel
```

`workflow-prepare --planning-run <run-id>`로 최근 승인한 계획 Run을 명시할 수도 있다. 준비 후 `awaiting_execution_approval`, 실행 승인 후 `execution_ready` 상태가 된다. 명령을 반복해도 같은 기록·승인을 유지한다. `plan-status`는 계속 계획 Run을 조회한다. `workflow-status`는 시도·지적 원본과 측정 집계·검사 오류를 보여주며 검사 오류가 있으면 CLI 종료 코드 1을 반환한다. 승인만으로 Task를 시작하지 않는다. T3 당시에는 `workflow_execution_enabled=false`·`orchestration_available=false`였으며 새 T4 기록은 두 기능을 `true`로 표시하고 `workflow-run`으로 시작한다. 기존 `run`·`resume`은 Phase 1 예제용이며 실제 Workflow 기록은 거부한다.

| 구성요소 | 구현한 동작 |
|---|---|
| [Store.transition](../src/development_harness/store.py) | 상태와 고정 이벤트 식별자를 SQLite 트랜잭션 하나로 저장한다. 같은 전이를 재처리해도 기록·집계를 늘리지 않으며 같은 ID의 다른 데이터는 거부한다. |
| [WorkflowRecords](../src/development_harness/workflow_records.py) | 호출 시도·승인 대기·지적을 Task·계획·코드·정책 식별자에 연결한다. 관측한 시간·사용량만 저장하고 미완료·미확정 합계는 `null`로 유지한다. 전송 시도·확인된 응답·확인하지 못한 호출을 구분한다. |
| 호출 단계 연결 | `prepared`, `process_registered`, `dispatch_intent`, `responded`, `finished`를 기록한다. 프롬프트 전달 전에 프로세스 식별자·전송 의도를 저장한다. 응답 확인이 없으면 미확정으로 남기며 자동 재호출을 막는다. |
| 제어 프로그램의 단일 호출·검사 진입점 | `Workflow.invoke`·`validate_task`가 실제 역할·격리된 검증 구성요소를 기록 계층에 연결한다. Reviewer에는 제어 프로그램이 기록한 파일과 모든 등록 검사의 통과 근거를 제공한다. 내부 진입점은 Task 순서를 실행하거나 Developer 변경을 적용하지 않는다. |
| 지적 이력 | 리뷰 안에서 쓰는 번호와 별개로 제어 프로그램의 지적 ID를 유지한다. 같은 지적은 ID를 재사용하며 표현이 달라지면 명시적으로 대응시킨다. `open`·`resolved`·`false_positive`·`deferred`의 근거·이력을 보존한다. 종료에는 맞는 후속 리뷰, 해결에는 이후 등록 검사 통과가 필요하다. 보류한 필수 지적도 완료를 막는 항목으로 유지한다. |

**검증 범위**: 실행 승인·CLI 검사는 지난 계획·코드·정책·작성 규칙, 보호 경로, 반복 승인, 소유권과 계획 기능 보존을 다룬다. 기록 검사는 전송 전후·트랜잭션 저장 중 실패, 이벤트·지적 재처리와 미확정 값을 확인한다. 응답이 정해진 로컬 자식 프로세스로 AI 서비스 호출 없이 Adapter와 기록 계층의 연결을 확인하고 실제 AppContainer 검사로 검증 경계를 유지한다. T3의 **실제 AI 호출은 0회**다. 전체 **검사 378개가 272.93초에 통과**했으며 실패·오류·생략은 0개이고 `pip check`도 통과했다. T2의 265개에 T3 검사 113개를 추가했다. [Phase3_Records.json](Evidence/Phase3_Records.json)에 근거를 기록하며 전체 보고서는 `%LOCALAPPDATA%/development-tools-harness/t3-regression/27473119975a/pytest.xml`이다. 날짜가 명시된 T1·T2 근거는 변경하지 않는다.

**유지하는 경계**: 미완료 시도나 누락된 지적 반영이 있으면 확인을 위해 추가 호출을 멈춘다. T3는 불확실성을 기록하며 자동 복구·재시도하지 않는다. T4는 아래 Task 순서·파일 변경·제한된 수정을 연결하며 T5는 근거 확인을 거치는 명시적 복구를 추가한다. 보고서·피드백·인수, 인수한 외부 예제와 고정 실행용 A는 P3-T6–T8에 남아 있다.

### P3-T4 — 순차 실행·제한된 수정과 최종 검사

**구현 내용(2026-09-22)**: [Execution](../src/development_harness/workflow_execution.py)은 승인한 Task를 Developer → 파일 변경 검사·적용 → AppContainer 검증 → 새 세션의 읽기 전용 Reviewer 순서로 연결한다. [Workflow](../src/development_harness/workflow.py)는 프로젝트 소유권을 유지하고 실행 정책을 고정하며 기록된 근거를 제공한다. 선행 Task가 완료돼야 다음 의존 Task를 시작한다.

```powershell
# 계획 승인 후 추가 수정 한도를 고정하고 실행을 승인한다.
& $harnessPython -m development_harness --project $planningProject workflow-prepare --max-corrections 2
& $harnessPython -m development_harness --project $planningProject workflow-approve
& $harnessPython -m development_harness --project $planningProject workflow-run
& $harnessPython -m development_harness --project $planningProject workflow-status
# 다른 사용법: 단계 하나를 완료한 뒤 확인하고 workflow-run으로 계속한다.
# & $harnessPython -m development_harness --project $planningProject workflow-run --steps 1
```

| 규칙 | 구현한 동작 |
|---|---|
| 최초 승인과 현재 코드 | 최초 계획·코드·정책 승인을 보존한다. 현재 코드는 시작 시점에서 승인 범위의 Developer 변경안과 해시가 기록된 변경 근거로 이어져야 한다. 예상 밖 사용자 변경은 보존하고 실행을 멈춘다. |
| 수정 한도 | Task마다 최초 구현 뒤 추가 Developer 시도 2회가 기본이다. 테스트 실패와 필수 리뷰 지적이 같은 한도를 사용한다. `workflow-prepare --max-corrections`로 고정하며 AI가 변경할 수 없다. 한도를 소진하면 Task를 실패 처리하고 다음 Task를 시작하지 않는다. |
| 검사와 중단 | AppContainer에서 등록한 pytest 검사를 실행한다. 구조화된 JUnit 실패로 코드 결함과 환경·권한 문제를 구분한다. 의존성 누락·권한·요구사항 불명확·시간 초과·생략·테스트 0개·근거 미완료는 코드 수정을 요청하지 않고 멈춘다. 수정할 때마다 검사를 다시 실행한다. |
| 독립 후속 리뷰 | Task 시작 파일·현재 파일·최신 동일 코드 검사 묶음·미해결 지적 ID를 제공한다. 이전 ID마다 `open`·`resolved`·`false_positive`·`deferred` 중 하나를 이유·근거와 함께 정확히 한 번 명시한다. 반복 지적은 ID를 유지하며 누락·자기 보고로 종료하지 않는다. 해결에는 해당 코드에서 이후 수행한 검사 통과가 필요하다. 보류한 필수 지적도 완료를 막는다. |
| 최종 검사 | 모든 Task 통과 후 최종 코드에서 등록 검사 전체를 다시 실행하고 미해결 필수 지적을 확인한다. 최종 실패는 특정 Task의 결함으로 자동 판단하거나 수정 횟수를 사용하지 않고 확인을 위해 멈춘다. 성공 상태는 `technically_complete`이며 사용자 인수와 별개다. |
| 저장된 단계에서 계속 | `--steps`는 단계 완료 기록을 저장한 뒤 멈춘다. 다음 `workflow-run`은 재승인 없이 그 정상 지점부터 계속한다. 진행 중·미확정 호출, 지적 반영 누락, 부분 파일 변경은 추가 호출을 막는다. 명시적 중단 복구는 아래 T5에서 처리한다. |

새 Workflow는 `workflow_execution_enabled=true`·`orchestration_available=true`로 기능 제공을 표시하며 명시적 실행 승인은 계속 필요하다. 이전 T3 정책은 새 Workflow 준비·승인을 거쳐야 순차 실행할 수 있다. `workflow-run`은 중단·실패 시 0이 아닌 종료 코드를 반환한다. 미확정 시간·사용량은 `null`로 유지한다.

**실제 예제**: [verify_t4.py](../scripts/verify_t4.py)는 OneDrive 밖의 새 복사본에 제어 프로그램이 작성한 Task 2개 계획을 사용하고 기본 검사 2개를 통과했다. Planner 서비스 호출은 하지 않았다. 설정 모델 `gpt-6-astra`가 **서로 다른 세션에서 실제 역할 호출 4회를 수행하고 모두 응답을 확인**했으며 미확정 호출은 0회다. Task 1은 `cli.py`·`test_cli.py`를 변경했다. Task 2는 앞선 변경이 자신의 검사 항목도 충족해 변경 없음으로 응답했지만 별도 검사와 독립 리뷰는 수행했다. Task 1·Task 2·최종 AppContainer 검사가 각각 **8개씩 통과**했고 같은 응용프로그램 복사본의 **추가 제어 프로그램 검사 6개**도 통과했다. 두 Task의 수정 횟수는 모두 0회다. `technically_complete`에 도달했으며 최초 승인·저장소 예제 원본은 유지했다. 원시 보고서: `%LOCALAPPDATA%/development-tools-harness/t4-live/d912782f99cd/report.json`. T4 실행 근거이며 T5 중단 복구·P3-T7 인수·자체 개발 완료 실적은 아니다.

```powershell
# 새 임시 프로젝트에서 실제 역할을 호출하는 명시적 검증.
& $harnessPython scripts/verify_t4.py --live
```

**기본 저장 경로 회귀 검사**: 실제 AI 예제는 별도로 준비한 검증기를 재사용했다. 이후 AI 없는 기본 검증기 시험에서 긴 Workflow 경로에 Python을 복사할 때 Windows `WinError 206`이 재현됐다. 검증 실행 환경을 `<state-home>/workflow-validation/<attempt-id>`에 저장하도록 줄였고 절대 근거 경로는 호출 기록에 유지한다. 수정 후 실제 기본 검증기의 AppContainer 회귀 검사가 통과했다.

**회귀 검증(2026-09-22)**: 전체 **검사 465개가 348.78초에 통과**했으며 실패·오류·생략은 0개이고 `pip check`도 통과했다. T3의 378개에 실제 기본 저장 경로 회귀 검사를 포함한 T4 검사 87개를 추가했다. 최종 보고서는 `%LOCALAPPDATA%/development-tools-harness/t4-regression/bcda88eaee1f/pytest.xml`이다. [Phase3_Execution.json](Evidence/Phase3_Execution.json)에 최종 소스·보고서 해시, 실제 호출 4회의 예제와 기본 경로 검증 근거를 기록한다. T1–T3의 과거 근거는 변경하지 않는다.

### P3-T5 — 명시적 중단 복구

**구현 내용(2026-09-22)**: [workflow_recovery.py](../src/development_harness/workflow_recovery.py)는 재개 전에 저장된 `active_step` 위치, 승인한 Task 순서·계획·정책, 프로세스 소유권과 실제 파일을 검사한다. [workflow_attempt_recovery.py](../src/development_harness/workflow_attempt_recovery.py)는 역할별 저장 근거를 검증하고 [WorkflowRecords](../src/development_harness/workflow_records.py)에 명시적 복구 판단을 기록한다. `workflow-status`는 파일 적용·호출 이력 변경 없이 참고용 `recovery` 판정을 보여준다. `workflow-resume`은 프로젝트 소유권을 확보한 상태에서 같은 조건을 다시 검사한 뒤 변경한다.

```powershell
# 복구 가능 여부와 이유를 확인한 뒤 승인된 Workflow를 명시적으로 재개한다.
& $harnessPython -m development_harness --project $planningProject workflow-status
& $harnessPython -m development_harness --project $planningProject workflow-resume
# 선택 사항: 복구 또는 실행 단계 하나만 완료하고 반환한다.
# & $harnessPython -m development_harness --project $planningProject workflow-resume --steps 1
```

| 중단 상태 | 복구 동작 |
|---|---|
| 영속 전송 시작 기록이 없고, 그 사실과 모순되는 응답 근거도 없음 | 원래 시도를 미전송으로 확정하고 새 식별자로 요청할 수 있다. 이 시도의 실제 AI 호출은 0회다. 요청 입력을 보내기 전에 전송 시작 기록 저장이 반드시 완료돼야 한다. |
| 요청을 보냈을 수 있지만 완전한 검증 응답이 없음 | 추가 호출을 막고 부족한 근거를 표시한다. 빈 로그·응답 누락만으로 서비스에 아무것도 전달되지 않았다고 판단하지 않는다. |
| 완전하게 저장된 Developer·Reviewer 응답 | 고정된 제어 프로그램 저장 경로, 입력 해시, 원래 Task·파일, 응답 스키마, 성공한 이벤트 기록, 독립 세션, 응답 해시와 기존 관측을 확인한다. 같은 역할 호출 없이 응답을 재사용한다. Reviewer는 원래 변경 전 파일, 최신 일치 검사, 이전 지적·평가도 검증한다. |
| 승인한 파일 일부 적용 | 실제 모든 파일을 기록된 변경 전·후 해시와 비교한다. 적용된 내용은 유지하고 미적용이 증명된 변경만 쓴다. 알 수 없는 중간 바이트·무관한 추가 파일·사용자 편집은 되돌리거나 덮어쓰지 않고 멈춘다. |
| 검증 중단 | 기존 프로세스와 자식이 끝났는지 확인하고 미완료 결과·시간을 보존한 뒤 등록 검사를 다시 실행한다. 이미 기록된 실패는 기존 코드·환경 분류를 유지하며 재개로 통과 처리하거나 수정 한도를 우회하지 않는다. |
| 리뷰 저장·반영 후 다음 단계 전에 중단 | 검증된 리뷰를 재사용하고 원래 지적·평가 트랜잭션을 한 번만 반영한다. 해결한 지적과 완료한 Task·수정 횟수를 중복 집계하지 않는다. |

**프로세스·소유권 검사**: [processes.py](../src/development_harness/processes.py)는 PID와 생성 시간을 함께 대조하고 기록된 이름 있는 Windows Job을 조회해 남은 자식을 확인한다. 복구 검사는 읽기 전용이며 소유권을 얻으려고 임의의 프로세스를 종료하지 않는다. AI 전송은 대기만 하는 신뢰 진입부로 시작하고 프로세스 격리·영속 전송 기록이 끝나야 명령을 실행한다. 그 전에 제어 프로그램이 종료되면 입력이 닫혀 AI CLI를 시작하지 않는다. AppContainer는 프로세스 생성과 동시에 Job에 연결해 생성 후 격리 전의 틈을 없앤다. Job의 마지막 핸들이 닫히면 자식까지 종료한다. `--state-dir`이 달라도 프로젝트 소유권을 공유하며 이전 DB가 활성·누락·손상 상태면 전환을 막는다. 관리자 설정·설치 실행 환경의 ACL 변경은 계속 제외한다.

**기록·승인 유지**: 원래 호출 시도의 관측 이력을 덮어쓰지 않고 별도 `recovery` 사실과 중복 없는 이벤트를 저장한다. `effective_attempt`는 검증된 복구 사실을 실행·지적·호출 및 사용량 집계에 제공하며 `workflow-status.attempts`는 원본 이력과 복구 기록을 함께 보존한다. 재사용 응답은 1회, 미전송 시도는 0회로 집계한다. 미확정 시간은 `null`로 유지하고 복구 작업 자체 시간은 별도 기록한다. 최초 실행 승인과 Task별 수정 횟수는 유지한다. 취소·실패·기술적 완료 상태를 다시 시작하지 않는다. 영속 `active_step` 위치가 없는 이전 T4 중단 기록은 별도 확인을 위해 막는다. 소스 내용이 같고 `.git` 관리 정보만 바뀌었다면 파일 기준선이 무효화되지 않는다.

**검증 범위**: 로컬 자식 프로세스로 실제 전송 전후 종료, 저장 응답 재사용, 부분 파일 적용, 복구 중 재중단, 리뷰 반영 재처리, 사용자 변경 보존, 승인·수정 횟수 유지와 Git 관리 정보만 변경한 상황을 검사한다. 실제 AppContainer 검사에서는 검증을 중단하고 프로세스 정리·새 최종 검사를 확인한다. 저장 근거 검사는 입력·응답·스키마·이벤트·세션·사용량 변조, 잘못된 시간과 복구 후 근거 변경을 거부하며 읽기 전용 판정·트랜잭션 원복도 확인한다.

**회귀 검증(2026-09-22)**: 전체 실행에서 **검사 535개가 474.664초에 통과**했고 실패·오류·생략은 0개이며 `pip check`도 통과했다. 그 실행을 시작한 뒤 최종 검토에서 누락된 `final_interrupted` 복구 분류와 회귀 검사 1개를 추가했다. 이후 **복구 경계 검사 9개가 17.66초에 통과**했다. 이 중 8개는 전체 실행과 겹치므로 두 근거를 합치면 **현재 수집되는 검사 536개 전체**를 확인했으며 T4의 465개보다 **T5 검사 71개**가 늘었다. 전체 JUnit 보고서는 `%LOCALAPPDATA%/development-tools-harness/t5-regression/c382926a7112/pytest.xml`이다. [Phase3_Recovery.json](Evidence/Phase3_Recovery.json)에 최종 소스·보고서 해시와 두 실행을 별도로 기록한다. 호출·기록·리뷰 집중 검사 96개도 실제 AI 호출 없이 통과했다. T4의 실제 호출 4회 예제를 포함한 T1–T4 근거는 과거 기록으로 유지한다.

**실제 복구 예제**: [verify_t5.py](../scripts/verify_t5.py)가 OneDrive 밖의 새 Task 1개 예제에서 통과했다. 제어 프로그램이 작성한 계획과 실제 기본 검사 2개 통과를 사용했으며 Planner AI 호출은 없었다. 실제 Developer 응답을 저장한 직후 제어 프로그램을 종료 코드 99로 강제 종료했다. `workflow-resume`은 **추가 Developer 호출 0회**로 그 응답을 재사용하고 격리 검사·별도 Reviewer 세션을 완료했다. 설정 모델 `gpt-6-astra`의 **서로 다른 실제 역할 호출 2회**를 확인했으며 미확정 호출·수정 횟수는 0회다. Task·최종 검사에서 각각 **8개**, **추가 독립 검사 6개**가 통과했다. 최초 승인과 저장소 예제 원본을 유지했고 완료 후 재개를 반복해도 새 작업은 없었다. 상태는 `technically_complete`이며 사용자 인수는 false다. 원시 보고서: `%LOCALAPPDATA%/development-tools-harness/t5-live/0bd5406cb3a6/report.json`. 이 스크립트는 짧은 외부 경로의 검증된 검증기를 재사용하며 기본 시도별 저장 경로는 별도 검사한다. P3-T6–T8과 Phase 3 사용자 인수는 대기 중이다.

```powershell
# 임시 예제의 명시적 실제 복구 검증. 실제 역할 호출은 최대 2회다.
& $harnessPython scripts/verify_t5.py --live
```

### P3-T6 — 최소 결과·피드백·인수

**구현 내용(2026-09-22)**: [results.py](../src/development_harness/results.py)는 최소 `workflow-report` JSON, [workflow_feedback.py](../src/development_harness/workflow_feedback.py)는 피드백 원문 보존·처리, [workflow_acceptance.py](../src/development_harness/workflow_acceptance.py)는 최종 근거 확인과 명시적 사용자 인수를 담당한다. 기존 Workflow API와 CLI를 확장했다. 짧게 정리한 보고서와 표현 개선은 Phase 4에 남긴다.

| 영역 | 구현한 동작 |
|---|---|
| 읽기 전용 결과 | 성공·실패·중단·권한 문제·근거 미검증·재계획·대체된 결과를 표시한다. 보고서·상태 조회는 프로젝트 파일·기존 DB 바이트·승인·지적·호출을 바꾸지 않는다. 내용 검사 실패도 보존된 이력과 함께 표시한다. |
| 변경 파일과 근거 | 최초·현재 해시와 승인 범위의 변경 이력을 대조하고 실제 기여 Task, 예상 밖 변경·중단된 적용을 보여준다. 등록 명령·Task 인수 및 검증 조건·현재 및 최종 검사·재사용 및 수동 상태·미해결 지적 및 피드백·측정값을 포함한다. 근거에는 절대 경로와 실제 존재 여부를 표시한다. |
| 같은 범위 피드백 | 원문·고정 ID·처리 경로 및 결과 이력을 보존한다. 결함은 승인 Task를 지정하고 최초 승인·남은 공통 수정 한도를 유지한다. 횟수 소진 시 추가 자동 수정을 막는다. 앞선 Task를 고치면 이미 완료한 후속 Task도 검사·리뷰하고 최종 검사 전체를 다시 수행한다. |
| 요구사항 변경 | 기존 Workflow를 `replanning_required`로 바꾸고 승인은 이력으로 보존하되 사용을 막는다. 등록된 기획서에 요청을 반영한 뒤 `workflow-replan`으로 AI 호출 없이 현재 파일에서 새 계획 Run을 만든다. 피드백 원문은 보존하지만 Planner의 근거인 기획서를 자동 수정하지 않는다. 이후 계획의 기본 검사는 이미 생성된 코드를 AppContainer에서 실행하며 새 계획·실행 승인이 필요하다. 범위를 자동 확장하거나 이전 승인을 재사용하지 않는다. |
| 재사용 요구사항 | Task가 없는 항목을 포함한 현재 `reuse` 요구사항마다 실제 최종 통과 검사 ID와 연결한 별도 사용자 설명을 요구한다. 일반 검사 통과만으로 어떤 재사용 요구사항을 입증했는지 자동 판단하지 않는다. |
| 수동 확인 | 실행 승인 전에 모든 필수 정의를 고정한다. 각 항목은 `id`, 현재 `requirement_ids`, `procedure`, `expected`를 포함하며 선언한 항목은 모두 필수다. 기술적 완료 후 사용자가 관찰한 실제 통과·실패와 근거를 기록한다. |
| 인수 조건 | 계획·정책·코드·최종 완료 일치, 전체 Task 순서·리뷰 완료, 미처리 작업·필수 지적·피드백 없음, 현재 최종 검사·봉인한 근거를 확인한다. 누락·이전 버전·변조·실패 근거는 인수를 막는다. 재사용·수동 확인 대기 중에도 기술적 성공일 수 있으며 사용자 인수는 별도로 필요하다. |

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-report
# 상황에 맞는 피드백 경로를 선택하고 실제 Task ID·피드백 원문으로 바꾼다.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind defect --task '<task-id>' --text '승인 범위에서 관찰한 결함을 설명한다.'
& $harnessPython -m development_harness --project $planningProject workflow-run
# 요구사항 변경은 새 계획 작성·계획 승인·실행 승인이 필요하다.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind requirements --text '변경할 요구사항을 설명한다.'
# 재계획 전에 등록된 기획서 파일에 요청한 요구사항 변경을 반영한다.
& $harnessPython -m development_harness --project $planningProject workflow-replan
& $harnessPython -m development_harness --project $planningProject plan
```

**수동 정책과 확인 기록**: `workflow-prepare --manual-checks <json-file>`은 `[{"id":"M1","requirement_ids":["R1"],"procedure":"음수 입력의 CLI 결과를 확인한다.","expected":"0이 아닌 종료 코드와 stderr 설명을 반환한다."}]` 같은 배열을 읽는다. 예시는 현재 Phase의 실제 요구사항으로 바꾸며 정의는 승인할 실행 정책에 포함된다. 최종 검사 후 `workflow-reuse --requirement <id> --validation-ids <actual-final-id> --outcome passed --evidence <explanation>`과 `workflow-manual --check <id> --outcome passed --evidence <observation>`으로 기록한다. 실패 관찰은 `--outcome failed`를 사용해야 한다. UTF-8 피드백·근거 파일은 `--from`·`--evidence-file`로 제공할 수 있다. 전체 예시는 [README 사용법](../README_ko.md#phase-3-결과피드백인수)에 기록했다.

**버전·근거 검사**: 최종 검사 기록에 record·JUnit·stdout·stderr 파일의 SHA-256 해시를 봉인한다. 재사용·수동 확인은 승인 계획·정책, 현재 내용·최종 완료 ID에 연결하므로 수정이나 새 완료 후에는 이전 확인이 유효하지 않다. `workflow-accept`로 누락된 조건을 무시할 수 없다. 승인한 `result_version=1` 정책과 봉인된 최종 근거를 요구하며 이전 T4·T5 실제 Run은 과거 기술적 결과로 보존하고 이번 인수 조건에서는 미검증으로 표시한다. 인수하려면 새 승인 Workflow가 필요하다. 보고서 조회는 해시 봉인·정책 변경·인수를 만들어내지 않는다. 인수 후 확인 기록 교체나 피드백을 통한 재시작도 막는다.

**검증 범위**: [test_workflow_results.py](../tests/integration/test_workflow_results.py)는 실제 격리 성공·실패, 수정 횟수 소진, 중단·권한 결과, 변경 파일의 실제 기여 Task, 근거 누락·이전 버전, 피드백 보존, 수동·재사용 근거와 DB·프로젝트 읽기 전용 조회를 다룬다. 별도 인수·피드백 회귀 검사는 Task 없는 재사용 요구사항, 실패·이전 버전·누락 확인, 조기 인수, 최종 파일 편집, 공통 수정 한도 소진, 후속 검사·리뷰, 요구사항 변경 후 새 계획과 승인 이력 보존을 확인한다. 과거 T5 실제 결과를 읽는 작업의 **새 AI 호출은 0회**이며 **기록된 역할 호출 2회는 T5 이력**이다. 새로운 T6 실제 예제나 사용자 인수가 아니다.

**과거 실제 결과 조회(2026-09-22)**: 최종 실제 `workflow-report` 명령으로 저장된 T5 예제를 조회해 예상 조건을 통과했다. 종료 코드 1, `outcome=unverified`, 원래 단계 `technically_complete` 유지, 사용자 인수 false를 확인했다. 이전 정책·봉인되지 않은 근거·R1 재사용 확인 누락으로 인수를 막는다. 기존 DB 바이트·프로젝트 파일을 유지했고 새 AI 호출은 0회다. 최종 보고서·검증 기록은 `%LOCALAPPDATA%/development-tools-harness/t6-results/df2c8127f247/report.json`과 `verification.json`이다. T5의 과거 호출 2회를 조회한 근거이며 새로운 실제 실행이나 사용자 인수로 기록하지 않는다.

**회귀 검증(2026-09-22)**: JUnit 기록 기준 **전체 검사 632개가 1801.44초에 통과**했고 실패·오류·생략은 0개이며 `pip check`도 통과했다. T5의 536개보다 **T6 검사 96개**가 늘었다. 보고서 통합 14개, 인수 통합 22개, 피드백 흐름 통합 6개, 피드백 단위 34개와 재계획 단위 20개다. 소스·테스트 70개 파일 모두 전체 실행 시작 시 저장한 목록의 해시와 일치한다. JUnit 보고서는 `%LOCALAPPDATA%/development-tools-harness/t6-regression/43c96f65d234/pytest.xml`이며 SHA-256은 `f84d5bd39f393a72c230c56676ee5ce8ef0db86e4efe2266e51d5237bfe338c3`이다. [Phase3_Results.json](Evidence/Phase3_Results.json)에 최종 검증과 과거 실제 결과 조회를 구분해 기록했다. T6의 새 실제 AI 호출은 0회다. T1–T5 과거 근거와 승인한 생성 계획은 변경하지 않는다. P3-T7–T8과 Phase 3 사용자 인수는 대기 중이다.

### 목적 / 구현 파일

Phase 1 Runner·저장 계층과 Phase 2 Adapter를 확장한다. P3-T1 준비, P3-T2 구성요소, P3-T3 `workflow.py`·`workflow_records.py` 실행 승인·기록, P3-T4 `workflow_execution.py` 순차 실행과 P3-T5 `workflow_recovery.py`·`workflow_attempt_recovery.py` 복구를 구현했다. P3-T6에서 `results.py`·`workflow_feedback.py`·`workflow_acceptance.py`와 CLI·계획 연결을 추가했다. 기존·신규 경로 전체는 검토 계획에 기록했다.

### 설계 결정 사항

- 단일 순차 Workflow와 구현된 기본 수정 2회를 유지한다. Fast·Standard·Strict 분기와 병렬 Task는 추가하지 않는다.
- 이벤트 수집은 이 단계에서 모두 구현한다. 최소 검증 근거 조회도 준비하며 보고서의 작은 미완료 집계 항목은 Phase 4 자체 개발 대상으로 남긴다.
- 구현 Task가 없는 재사용 요구사항도 최종 인수에서 다시 확인한다. 범용 코드 분석·커버리지 엔진은 추가하지 않는다.
- A는 별도 설치·복사본으로 고정하며 B를 참조하는 editable 설치를 사용하지 않는다. 실행 기록은 OneDrive 밖에, B 테스트 기록은 임시 공간에 두고 권한을 제한한다. 실제 분리 시험 결과를 기록한다.

### 사용 예시

제안 Python CLI는 정수를 두 배로 출력하며 기본 검사는 양수·0을 다룬다. 정상 출력을 유지하면서 음수에 명확한 오류와 0이 아닌 종료 코드를 반환하는 변경 하나를 요청한다. 별도 임시 복사본에서 생성 Phase 검토·실행 승인 후 한 차례 중단·재개하고 리뷰·검증 근거 확인과 사용자 인수까지 진행한다. P3-T1에서 실제 예제 실행 전에 정확한 명령·기대 출력을 기록한다.

## 선행 조건 및 개발 시 주의사항

이전 구성요소는 회귀 근거와 함께 재사용한다. 핵심 보호 동작은 가짜 Adapter뿐 아니라 실제 작업 프로세스에서도 동작해야 한다. 권한·재개 결함이 있으면 실행용 A로 확정하지 않는다. 기존 코딩 도구로 결함을 고칠 수 있으며 수동 개입을 기록한다. 이 외부 예제는 전체 dogfooding 준비이며 자체 개발 실적 자체는 아니다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 전체 흐름 개요, 외부 예제 통과 조건과 고정 실행본 요구사항 최초 작성. |
| 2026-09-21 | Phase 2 계획 dogfooding 성공 결과로 Task 8개·요구사항 18개를 상세화했다. AI v1·검토한 v2·근거를 보존하고 역할 권한·지적·Phase 4 범위·기술 검증 조건을 보완했다. 구현과 사용자 인수는 대기 중이다. |
| 2026-09-21 | 선행 조건인 Phase 2 사용자 인수 완료를 반영했다. Phase 3 계획 승인·구현·작업 권한 검증은 미완료 상태로 유지한다. |
| 2026-09-21 | 사용자가 개발 순서와 실행 로직을 확인하고 Phase 3 착수를 승인했다. P3-T1 실행 계약·예제 준비와 임시 대상 권한 조사를 시작했다. 실제 대상 내용을 수정하는 AI 작업 프로세스는 아직 허용하지 않았다. |
| 2026-09-21 | P3-T1 준비·조사 완료: 실행 계약, 기본 검사 2개인 CLI 예제, 합성 workflow-doctor를 추가하고 전체 검사 187개를 통과했다. 파일 쓰기 제한은 동작했으나 부모·자식 직접 TCP 연결 6개로 unelevated 네트워크 한계를 확인해 P3-T2에는 더 강한 검증된 권한 수단이 필요하다. 프로젝트 입력·Run을 보존했고 AI 호출은 0회다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-21 | 회사 정책의 관리자 설정 금지를 반영했다. AppContainer를 기본 진단으로 추가하고 일반 사용자 권한의 역할별 파일·통신·자식·시간 초과 시험을 확인했다. 기존 Codex 후보는 명시적 옵션으로 유지한다. 텍스트 전용 AI와 격리된 검증의 연결 방향을 기록하고 실제 실행은 비활성화 상태로 유지했다. 회귀 결과는 AppContainer 근거에 기록하며 dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-09-21 | P3-T2 실제 역할·변경 검사·격리된 pytest를 구현했다. 회귀 검사 265개와 실제 호출 2회의 예제를 통과했다. P3-T3–T8·Phase 인수는 대기 중이다. 영문·국문을 갱신했으며 dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-09-22 | P3-T3 실행 승인, 원자적·중복 없는 호출·시간·지적 기록과 제어 프로그램의 호출 단계 연결을 구현했다. 자동 호출 없는 CLI 사용법과 로컬 자식 프로세스·AppContainer 연결을 검증했다. 전체 검사 378개와 pip check를 통과했다. 실제 AI 호출은 0회다. P3-T4–T8·Phase 인수는 대기 중이다. 영문·국문과 README 상태를 갱신했으며 dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-09-22 | P3-T4 순차 실행·공통 수정 한도·변경 이력 검사·명시적 후속 리뷰·최종 검사를 구현했다. Task 2개·실제 호출 4회의 예제가 통과했고 기본 저장 경로 AppContainer 회귀 검사로 Windows 경로 길이 수정을 확인했다. 현재 전체 회귀 결과는 위에 기록한다. T5–T8·Phase 3 인수는 대기 중이다. 영문·국문과 README를 갱신했으며 dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-09-22 | P3-T5 명시적 workflow-resume, 근거를 확인한 응답 재사용, 부분 파일 검사·복구, 프로세스와 자식·소유권 검사 및 중복 없는 별도 복구 사실을 구현했다. 원래 승인·수정 횟수와 T1–T4 과거 근거를 유지했다. 현재 검증 결과는 위에 기록한다. 영문·국문과 README를 갱신했으며 T6–T8·Phase 인수는 대기 중이다. dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-09-22 | P3-T6 읽기 전용 최소 JSON 보고서, 같은 범위·요구사항 변경 피드백 보존, 최종 재사용·수동 근거와 명시적 인수 조건을 구현했다. T1–T5 근거·생성 계획을 보존했고 새 실제 AI 호출은 0회다. 영문·국문과 README를 갱신했으며 T7–T8·Phase 인수는 대기 중이다. dev-log 스킬이 없어 별도 로그는 생략했다. |
