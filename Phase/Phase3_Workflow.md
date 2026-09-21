# Phase 3 — Workflow `🚧 In Progress`

> Complete one real example Phase and prepare a verified fixed runner for self-development.

**Prerequisites**: [Phase 2](Phase2_Planning.md) accepted on 2026-09-21; actual worker execution additionally requires verified permissions and a prepared example.

**Technology**: Python + pytest, SQLite and the selected single AI Adapter.

**Plan status**: The user authorized Phase 3 on 2026-09-21 and explicitly requested P3-T2 implementation. P3-T1 preparation and P3-T2 Developer, controlled file application, isolated validation and separate Reviewer components are implemented and verified. Validation uses standard-user AppContainer under the no-administrator constraint. General workflow execution remains disabled pending P3-T3–T8. Phase 2 is accepted; Phase 3 acceptance remains pending. The reviewed eight-Task, 18-requirement plan and its original AI/manual-review evidence are preserved.

## Overview

Connect actual implementation, validation, separate review, bounded corrections and minimum result acceptance. Verify the whole flow and interruption/resume in a separate example before touching the harness through itself. Covers specification §§6–10, with final report presentation completed in Phase 4.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Real sequential Developer/Validation Runner/Reviewer workflow | 🚧 Components verified; orchestration pending |
| 2 | Call/timing/finding records, corrections and process-aware resume | 🔲 |
| 3 | Minimum success/failure report, feedback and result acceptance | 🔲 |
| 4 | Accepted external example and verified fixed runner A | 🔲 |

## Verification & Exit Criteria

The [reviewed plan](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan.md) contains completion criteria, proposed paths and verification methods. [Review evidence](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md) preserves the original AI output and manual corrections. P3-T1 and P3-T2 components are verified, including two actual AI calls on a disposable example. P3-T3–T8 implementation has not started.

| Task | Planned work | Completion evidence |
|---|---|---|
| P3-T1 | Confirm prerequisites, investigate Windows worker isolation, define the execution contract and prepare the small CLI example. | Phase 2 acceptance record, permission mechanism investigation/probes, baseline example tests and bounded specification. |
| P3-T2 | Extend the single Adapter for Developer and read-only Reviewer sessions; enforce worker/test permissions. | Implemented and verified: distinct real sessions, controlled patches, isolated pytest and descendant/file/network denial tests. [Evidence](Evidence/Phase3_Workers.json). |
| P3-T3 | Connect version-bound execution admission and durable call/time/finding records. | Crash/replay checks, no duplicate calls/findings, severity/disposition evidence and unchanged planning-only approval. |
| P3-T4 | Run Developer → validation → separate Reviewer sequentially with bounded corrections. | Actual validation classifications, evidence-based finding resolution, correction limits and final-content verification. |
| P3-T5 | Recover partial implementation and interrupted validation safely. | Actual process interruption, descendant cleanup, preserved user edits, ownership races and metadata-only resume. |
| P3-T6 | Add minimum reports, feedback routing, final reuse checks and acceptance gates. | Success/failure reports, preserved feedback, version checks and rejection of unmet mandatory conditions. |
| P3-T7 | Complete the external CLI example through actual roles, interruption/resume and user acceptance. | Full regressions, actual outputs, distinct role sessions and recorded user result acceptance. |
| P3-T8 | Freeze runner A and prove isolation before Phase 4. | Independent installed origins, fixed artifacts, actual B/test write-denial evidence and installed workflow/resume checks. |

P3-T2 verifies the worker components on an explicitly scoped disposable example. General project execution still requires P3-T3 admission and P3-T4 orchestration. The unelevated candidate failed network denial; elevated setup remains excluded under company policy. No administrator setup or unrestricted fallback is used.

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

**Integration decision**: AI-service authentication/traffic stays with the existing text-only Codex adapter. The Developer returns structured changes for controller application; the Reviewer receives selected before/after files and actual validation evidence. Generated code and tests run in AppContainer. P3-T2 implements and verifies these components below. General admission, orchestration, resume, acceptance and fixed-runner verification remain P3-T3–T8. The old trusted-command validator is not used for this generated code; existing Planner compatibility rules remain in force.

**Verification**: All 206 tests passed, with zero failures/errors/skips; `pip check` passed. The 19 new cases include actual standard-user isolation and descendant termination, false denial reports, missing evidence, setup failure and preservation of existing records. A separate CLI run preserved the prepared example's files, planning Run and events. No actual AI calls or new plan/result approvals were made.

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

**Verification**: All **265 tests passed**, with zero failures/errors/skips; `pip check` passed. The 59 new cases cover role/patch contracts and isolated validation. Actual pytest checks distinguish passing, failing, skipped/empty, collection-error and interrupted outcomes. Parent/child tests deny protected reads/writes and eight TCP/UDP IPv4/IPv6 attempts to owned loopback listeners; host controls succeed. Other checks cover stale versions, user edits, out-of-scope changes, descendant cleanup and persistence failure before execution. Actual CLI probes reject forced tools without AI calls. [Phase3_Workers.json](Evidence/Phase3_Workers.json) records source/artifact hashes; historical evidence is preserved.

**Limits / next step**: Supports the reviewed Python 3.12/pytest dependencies and UTF-8 creation/replacement. Deletion/rename and unreviewed dependencies are unsupported; test outputs must use scratch. Missing dependencies/incomplete checks cannot pass. This component script is not general Phase execution or the P3-T7 accepted example. P3-T3 connects approved plan/code versions and durable call/time/finding records; P3-T4 adds sequential execution/corrections. Planning approval remains planning-only.

### Purpose / Implementation Files

Extend the Phase 1 runner/storage and Phase 2 Adapter. P3-T1 preparation and the P3-T2 modules above now exist. `src/development_harness/results.py` and the remaining workflow admission/record/orchestration/resume/results integration are still planned. Full existing/proposed paths are listed in the reviewed plan.

### Design Decisions

- Keep one sequential workflow and the proposed two-correction default; no Fast/Standard/Strict routing or parallel Tasks.
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

---

# Phase 3 — 전체 실행 흐름 `🚧 진행 중`

> 실제 예제 Phase 하나를 완료하고 자체 개발에 사용할 검증된 고정 실행본을 준비한다.

**선행 조건**: 2026-09-21 [Phase 2](Phase2_Planning.md) 인수 완료. 실제 작업 프로세스 실행 전에는 권한 검증과 준비된 예제도 필요하다.

**기술 구성**: Python + pytest, SQLite, 선정한 단일 AI Adapter.

**계획 상태**: 사용자가 2026-09-21 Phase 3 착수 후 P3-T2 구현을 명시적으로 요청했다. P3-T1 준비와 P3-T2 Developer·파일 변경 검사·격리된 검증·별도 Reviewer 구성요소의 구현·검증을 완료했다. 회사 정책상 관리자 설정 없이 일반 사용자 AppContainer를 사용한다. 일반 프로젝트의 전체 실행은 P3-T3–T8 연결 전까지 비활성화 상태다. Phase 2는 인수했으며 Phase 3 전체 인수는 대기 중이다. Task 8개·요구사항 18개의 검토 계획과 AI 원본·수동 검토 근거는 보존했다.

## 개요

실제 구현·검증·별도 리뷰·제한된 수정·최소 결과 인수를 연결한다. 하네스로 자신을 수정하기 전에 별도 예제로 전체 흐름과 중단·재개를 확인한다. 기획서 6–10장을 다루며 최종 보고서 표현은 Phase 4에서 완성한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Developer·Validation Runner·Reviewer 순차 Workflow | 🚧 구성요소 검증 완료·실행 흐름 연결 대기 |
| 2 | 호출·시간·지적 기록, 수정·프로세스 확인을 포함한 재개 | 🔲 |
| 3 | 최소 성공·실패 보고서, 피드백·결과 인수 | 🔲 |
| 4 | 인수한 외부 예제와 검증된 고정 실행용 A | 🔲 |

## 검증 및 종료 조건

[검토한 계획](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan_ko.md)에 완료 기준·제안 경로·검증 방법을 기록했다. [검토 근거](Generated/45e4c4397c42468e87d9dad81d7b9ce9/Review.md)에 AI 원본과 수동 보완을 보존했다. P3-T1·T2 구성요소를 검증했으며 임시 예제에서 실제 AI 호출 2회를 확인했다. P3-T3–T8 구현은 미시작이다.

| Task | 개발 내용 | 완료 근거 |
|---|---|---|
| P3-T1 | 선행 조건 확인, Windows 작업 권한 분리 검토, 실행 계약과 작은 CLI 예제 준비. | Phase 2 인수 기록, 권한 수단 조사·시험, 예제 기본 검사와 한정된 변경 기획. |
| P3-T2 | 단일 Adapter에 Developer·읽기 전용 Reviewer 연결, 작업·테스트 권한 집행. | 구현·검증 완료: 실제 별도 세션·파일 변경 검사·격리된 pytest와 자식·파일·통신 차단. [검증 근거](Evidence/Phase3_Workers.json). |
| P3-T3 | 버전별 실행 진입과 호출·시간·지적의 영속 기록 연결. | 중단·재처리 검사, 호출·지적 중복 방지, 중요도·처리 근거, 계획 전용 승인 유지. |
| P3-T4 | Developer → 검증 → 별도 Reviewer 순차 실행과 제한된 수정. | 실제 검사 결과 분류, 근거 있는 지적 해결, 수정 한도와 최종 내용 검증. |
| P3-T5 | 부분 구현과 중단된 검사의 안전한 재개. | 실제 프로세스 중단·자손 정리, 사용자 변경 보존, 소유권 경쟁·메타데이터 전용 변경 재개. |
| P3-T6 | 최소 보고서·피드백 처리·최종 재사용 확인·인수 조건 추가. | 성공·실패 보고서, 피드백 보존, 버전 확인과 필수 조건 미충족 인수 차단. |
| P3-T7 | 외부 CLI 예제의 실제 역할 실행·중단·재개·사용자 인수. | 전체 회귀 검사, 실제 출력·별도 역할 세션과 사용자 결과 인수 기록. |
| P3-T8 | 실행용 A 고정과 Phase 4 이전 분리 입증. | 독립 설치 위치·고정 산출물, 실제 B·테스트 쓰기 차단, 설치본의 흐름·재개 검사. |

P3-T2에서 범위가 명확한 임시 예제로 실제 작업 구성요소를 검증했다. 일반 프로젝트 실행에는 P3-T3 승인 연결과 P3-T4 실행 흐름이 필요하다. unelevated 후보는 통신 차단에 실패했으며 elevated 설정은 회사 정책상 제외한다. 관리자 설정이나 제한 없는 실행으로 대체하지 않는다.

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

**연결 결정**: AI 서비스 인증·통신은 기존 Codex 텍스트 전용 Adapter가 담당한다. Developer는 구조화한 변경안을 반환하고 하네스가 적용한다. Reviewer는 선택한 변경 전후 파일과 실제 검증 근거를 전달받는다. 생성 코드·테스트는 AppContainer에서 실행한다. 아래 P3-T2에서 이 구성요소를 구현·검증했다. 일반 실행 승인·순차 실행·재개·인수·고정 실행본 검증은 P3-T3–T8에 남아 있다. 이번 생성 코드를 기존 신뢰 명령용 검증기에서 실행하지 않으며 Planner 호환성 규칙은 유지한다.

**검증**: 전체 검사 206개가 통과했고 실패·오류·생략은 0개이며 `pip check`도 통과했다. 추가 검사 19개는 실제 일반 사용자 격리·자식 종료, 거짓 차단 보고, 근거 누락, 설정 실패와 기존 자료 보존을 다룬다. 별도 CLI 실행에서 준비된 예제의 파일·계획 Run·이벤트도 유지했다. 실제 AI 호출과 새 계획·결과 승인은 수행하지 않았다.

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

**검증**: 전체 **265개 검사 통과**, 실패·오류·생략 0개이며 `pip check`도 통과했다. 추가 59개 검사는 역할·변경 계약과 격리된 검증을 다룬다. 실제 pytest에서 통과·실패·생략 및 빈 테스트·수집 오류·중단을 구분한다. 부모·자식의 보호 파일 읽기·쓰기가 차단됐고 자체 루프백 수신 서버 대상 TCP·UDP·IPv4·IPv6 연결 8건도 모두 차단됐다. 호스트 정상 연결은 성공했다. 지난 버전·사용자 변경·범위 밖 변경·자식 정리·실행 전 기록 실패도 확인했다. 실제 CLI 시험은 AI 호출 없이 강제 도구 요청을 거부한다. [Phase3_Workers.json](Evidence/Phase3_Workers.json)에 소스·산출물 해시를 기록하고 이전 근거는 유지한다.

**한계 / 다음 단계**: 검토한 Python 3.12·pytest 의존성과 UTF-8 생성·교체를 지원한다. 삭제·이름 변경·미검토 의존성은 지원하지 않으며 테스트 출력은 scratch를 사용해야 한다. 의존성 누락·미완료 검사는 통과하지 않는다. 이 스크립트는 일반 Phase 실행이나 P3-T7 사용자 인수 예제가 아니다. 다음 P3-T3에서 승인 계획·코드 버전과 호출·시간·지적의 영속 기록을 연결하고 P3-T4에서 순차 실행·수정을 연결한다. 계획 승인은 계속 계획 전용이다.

### 목적 / 구현 파일

Phase 1 Runner·저장 계층과 Phase 2 Adapter를 확장한다. P3-T1 준비와 위 P3-T2 모듈은 구현했다. `src/development_harness/results.py`와 나머지 실행 승인·기록·순차 실행·재개·결과 연결은 계획 상태다. 기존·신규 경로 전체는 검토 계획에 기록했다.

### 설계 결정 사항

- 단일 순차 Workflow와 기본 수정 2회 제안을 유지한다. Fast·Standard·Strict 분기와 병렬 Task는 추가하지 않는다.
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
