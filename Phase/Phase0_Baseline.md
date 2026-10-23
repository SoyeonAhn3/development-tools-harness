# Phase 0 — Baseline `✅ Completed`

> Confirm that the current repository runs and passes all of its tests, and record the starting point for the new Phases.

**Prerequisites**: Met — [specification 1.10](../Draft/ai-development-harness-plan-v1.md) finalized on 2026-10-23. The user instructed Phase 0 to start and subsequently accepted its results and module map on the same date ("인수한다").

**Technology**: Windows 10 without administrator rights, Python 3.12.10 (`.python-version`), pytest 9.1.1, psutil 7.2.2 and setuptools 84.0.0 (`requirements-dev.lock`), SQLite from the standard library. No tool is added in this Phase.

**Form**: Check-only (spec 4.4). No installation, no code change and no AI development call.

## Overview

The new harness is built by changing this repository (spec 11, F1). Before any change, confirm that the environment and current behavior are intact and record a baseline of passing tests, so later Phases can tell which failures they caused. This applies the spec's check-only Phase 0 and its "block only new problems" rule (spec 6.5) to the harness itself. The work is done manually with existing coding tools, because the harness is not used to develop itself.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Environment check record: versions, lock-file comparison, `pip check` | ✅ |
| 2 | Full regression result with a JUnit XML report and actual counts | ✅ |
| 3 | Baseline record: passing test IDs, skipped tests with reasons, duration, report hash | ✅ |
| 4 | Confirmed module map (reuse, extend, redesign, preserved) | ✅ Accepted 2026-10-23 |
| 5 | User acceptance of Phase 0 | ✅ |

## Tasks & Verification

| Task | Work | Acceptance Criteria | Verification | Status |
|---|---|---|---|---|
| P0-T1 | Check the harness environment | Python is 3.12.10; installed packages match `requirements-dev.lock`; `pip check` reports no broken requirements; the CLI prints its version. The Codex CLI version is recorded for later Phases without making an AI call | `python --version`, `pip freeze` compared with the lock file, `pip check`, `python -m development_harness --version`, `codex --version` | ✅ |
| P0-T2 | Run the full regression once, sequentially | Exit code 0, JUnit report exists, at least one test executed, zero failures and errors (spec 5). The total is compared with the last recorded 691 (2026-09-30, runner A08) and any difference is explained | `python -m pytest --junitxml=<local folder outside OneDrive>\junit.xml` | ✅ |
| P0-T3 | Record the baseline | Passing test IDs, skipped tests with reasons, total duration and the report hash are stored in `Phase/Evidence/Phase0_Baseline.json`, with the JUnit report copied beside it. A failing test is not accepted as baseline: report the cause, then fix it with user approval or let the user fix it, and rerun T2 | The record matches the JUnit file and its hash | ✅ |
| P0-T4 | Confirm the module map | Each of the 41 modules has a classification and reason (reviewed table below). Unclear items stay marked "needs confirmation" with the Phase that decides them | Compare each module's code with spec 11; the user reviews the map | ✅ Accepted 2026-10-23 |
| P0-T5 | User acceptance | The user reviews T1–T4 results and accepts Phase 0 | Acceptance recorded in this document and the Overview | ✅ |

**Results**: Technical verification finished on 2026-10-23. **691 passed, 0 failed, 0 errors, 0 skipped**; exit code 0. JUnit duration: 1322.867 seconds; process duration: 22 min 3.6 s. The exact test-ID set matches the hash-verified 2026-09-30 record: no added, removed or newly skipped tests. The user accepted these results and the 41-module map on 2026-10-23. Phase 0 is complete; Phase 1 has a detailed plan but has not started.

### Verification Evidence

- [User acceptance](Evidence/Phase0_Acceptance.json): the exact user statement and hashes bind acceptance to the verified baseline and module map. All nine referenced artifacts and 108 input files were checked again when recording acceptance. Baseline and module-map JSON retain their historical, pre-acceptance status; this separate record establishes the current acceptance. Tests were not rerun for this documentation-only update.

- [Baseline and 691 passing test IDs](Evidence/Phase0_Baseline.json), [JUnit XML](Evidence/Phase0_JUnit.xml), [exact command and run result](Evidence/Phase0_Run.json).
- [Environment and locked-package comparison](Evidence/Phase0_Environment.json): Python 3.12.10, pytest 9.1.1, psutil 7.2.2, setuptools 84.0.0; all eight locked packages match. `pip check` passed; harness CLI reports 0.1.0. Pip 25.0.1 and the editable harness package are additional installed distributions, not lock mismatches.
- [Input file hashes](Evidence/Phase0_Inputs.json): 108 source, test, script, skill-resource and configuration files unchanged before/after the run. No implementation or test was changed in Phase 0. Runtime logs and databases remain outside OneDrive.
- [41-module review](Evidence/Phase0_ModuleMap.json): source hashes, inspected symbols, classification and follow-up Phase. Shared pytest/AppContainer assumptions require changes beyond the original draft map; details are below and in Phase 1/3 notes.

### Codex Selection and Limits

The machine default is **Codex CLI 0.163.0**, which is not in the current adapter's reviewed versions. The regression process alone selected the preserved **0.155.1** executable from runner A08 through `DEVELOPMENT_HARNESS_CODEX_PATH`, after verifying the full runner manifest. Python imported the **current checkout**, not A08's harness code. No global configuration, tool version or dependency was changed. This run establishes a baseline for 0.155.1; it does not establish compatibility with 0.163.0. Local capability probes made no live AI service requests. Formatter/linter/type-checker adoption remains a Phase 3 decision.

### Environment Retry (Failure Preserved)

The first full run produced **685 passed and 6 failed**. All six failures were `WinError 206` while creating workflow-worker folders under the long pytest temporary root. The code, tests and dependencies were unchanged. Shortening the local root to `%LOCALAPPDATA%/h0-1023` made all 10 journal-bridge tests pass, followed by the full passing regression above. The baseline uses only the successful full run; results from separate runs are not combined. This is an operating limitation: keep runtime/temp paths short; long-path support has not been established.

Evidence: [initial failed run](Evidence/Phase0_InitialRun.json), [initial JUnit](Evidence/Phase0_InitialJUnit.xml), [short-path check](Evidence/Phase0_PathCheckRun.json), [10-test JUnit](Evidence/Phase0_PathCheck.xml).

### Changes to the Draft Module Map

- `model.validate_checks` is shared by real project registration and requires pytest: generalize it in Phase 1. Only its legacy fake-plan portion is a later CLI decision.
- `workflow.prepare` and `workflow_acceptance.final_validation` pin pytest/AppContainer; the latter also demands tests for every check. Adapt both when introducing mixed isolation and quality commands.
- `files`, `worker_contract` and recovery need coordinated deletion/rename handling in Phase 3. Existing hash and user-change protection remains the foundation.
- `workflow_attempt_recovery` directly parses Codex events. Include recovery in the common AI adapter boundary required by specification 1.10 (I1).
- Python diagnostics and self-test helpers are imported by active code. Preserve those shared dependencies even though self-development is outside the product scope.

## Module Map (Reviewed and Accepted)

All 41 modules were checked against specification 1.10. The table records the treatment and the Phase responsible; it does not imply that those later changes are implemented. Shared code is kept even when the old fake-Adapter or self-development feature is outside the first version.

| Module | Treatment | Follow-up Phase | Code evidence and reason |
|---|---|---|---|
| [`__init__`](../src/development_harness/__init__.py) | Reuse | all | `__version__`: Package version; retain the entry contract. |
| [`__main__`](../src/development_harness/__main__.py) | Reuse | all | `main`: Delegates to CLI; no project-language logic. |
| [`appcontainer_probe`](../src/development_harness/appcontainer_probe.py) | Retain diagnostics | 1 | `diagnose_appcontainer`: Active Python boundary verification and runtime copy helper, not merely an optional script. |
| [`appcontainer_probe_payload`](../src/development_harness/appcontainer_probe_payload.py) | Retain diagnostics | 1 | `observe`: Retain synthetic token/file/network observations for Python containment proofs. |
| [`appcontainer_temp`](../src/development_harness/appcontainer_temp.py) | Retain Python backend | 1 | `install`: Private temporary-path compatibility is specific to copied Python; retain that backend behavior. |
| [`cli`](../src/development_harness/cli.py) | Redesign | 2,3 | `parser`: Separate legacy, planning and workflow commands; replace the user flow with the specified seven commands. |
| [`codex_adapter`](../src/development_harness/codex_adapter.py) | Extend / adapt | 3 | `CodexPlanner`: Keep verified Codex transport; extract the tool-independent boundary and assess Claude Code fit (I1). |
| [`codex_probe`](../src/development_harness/codex_probe.py) | Retain diagnostics | 3 | `verify_capabilities`: An active adapter admission gate; preserve forced-tool rejection and extend for the new permissions (I1). |
| [`files`](../src/development_harness/files.py) | Extend / adapt | 3 | `apply_write`: Retain hashes and checked writes; add equivalent guards for deletion and renaming. |
| [`fixed_runner`](../src/development_harness/fixed_runner.py) | Preserve | 1 | `build_runner`: Keep frozen installation/history and regressions outside product dogfooding; reassess manifest reuse in Phase 1. |
| [`fixed_runner_verify`](../src/development_harness/fixed_runner_verify.py) | Preserve | all | `main`: Retain historical installation/permission proofs, including the existing archive-path adjustment. |
| [`frozen_entry`](../src/development_harness/frozen_entry.py) | Preserve | 1 | `inspect_runner`: Keep frozen runner verification; its manifest hashing can inform new installation tamper checks. |
| [`gate`](../src/development_harness/gate.py) | Reuse | 1 | `main`: Already launches arbitrary argv only after containment and journaling; reuse with new monitoring. |
| [`isolated_validation`](../src/development_harness/isolated_validation.py) | Redesign | 1 | `IsolatedValidator`: Keep the copied Python backend; generalize command/evidence selection and add normal-permission tamper detection. |
| [`model`](../src/development_harness/model.py) | Redesign | 1,3 | `validate_checks`: Shared validation requires a pytest check; generalize in Phase 1. Retain shared errors/hashes/paths; decide only legacy fake-plan handling in Phase 3. |
| [`phase_docs`](../src/development_harness/phase_docs.py) | Extend / adapt | 2,3 | `render_documents`: Keep pinned bilingual templates; generate into Phase/ and update only allowed completion fields. |
| [`plan_schema`](../src/development_harness/plan_schema.py) | Extend / adapt | 2 | `validate_plan`: Current schema has Phases and current Tasks but lacks structured setup/check/version decisions. |
| [`planning`](../src/development_harness/planning.py) | Extend / adapt | 2,3 | `Planning`: Add Phase 0, technology/version choices, setup contracts and later the common Planner adapter. |
| [`processes`](../src/development_harness/processes.py) | Reuse | 1 | `ProjectLock`: Reuse Windows project locks, PID identity and Job containment for arbitrary commands. |
| [`project`](../src/development_harness/project.py) | Extend / adapt | 1,2,3 | `validate_config`: Explicit context and Phase/Generated policy depend on the pytest contract; adapt registration then safe whole-project reads. |
| [`results`](../src/development_harness/results.py) | Extend / adapt | 3 | `report`: Keep evidence-linked JSON; add bilingual Markdown including failure, quality, configuration and version changes. |
| [`reviewed_test_entry`](../src/development_harness/reviewed_test_entry.py) | Preserve | all | `main`: Preserve the reviewed host-regression bootstrap and evidence observer. |
| [`runner`](../src/development_harness/runner.py) | Decision pending | 3 | `Harness`: Legacy fake-Adapter command engine only; retain regressions and decide retirement during CLI simplification. |
| [`self_test_verify`](../src/development_harness/self_test_verify.py) | Preserve | all | `reviewed_host`: Keep isolated/host evidence tooling and tests; no harness-driven self-development is planned. |
| [`store`](../src/development_harness/store.py) | Reuse | 1 | `Store`: Reuse transactional SQLite journal; integrate the new tamper monitor around it. |
| [`test_collection`](../src/development_harness/test_collection.py) | Extend / adapt | 1 | `CollectionEvidence`: Keep pytest hooks as Python evidence; introduce language-independent inventory/skip comparisons above this layer. |
| [`validation`](../src/development_harness/validation.py) | Redesign | 1 | `pytest_result`: Launch is argv-based, but JUnit path, pytest exit rules and skip rejection are hard-coded. |
| [`validation_entry`](../src/development_harness/validation_entry.py) | Retain Python backend | 1 | `main`: Bootstrap imports pinned pytest and collection observer; keep it confined to the Python backend. |
| [`validation_profiles`](../src/development_harness/validation_profiles.py) | Preserve | 1 | `prepare_profile`: Self-test profile is outside product scope, but active modules import its filtering/helpers; do not remove it wholesale. |
| [`windows_appcontainer`](../src/development_harness/windows_appcontainer.py) | Retain Python backend | 1 | `AppContainer`: Zero-capability Windows primitive is reusable; retain it for Python rather than implement other runtimes here. |
| [`worker_contract`](../src/development_harness/worker_contract.py) | Redesign | 3 | `TaskScope`: Explicit file lists and content replacements only; support safe search, folder scope, delete/rename and bounded check requests. |
| [`worker_probe`](../src/development_harness/worker_probe.py) | Retain diagnostics | 3 | `diagnose_workers`: Retain reviewed Windows command-boundary diagnostics; reassess for the new read/search model. |
| [`worker_probe_payload`](../src/development_harness/worker_probe_payload.py) | Retain diagnostics | 3 | `observe`: Retain synthetic parent/child permission checks used by the worker probe. |
| [`workers`](../src/development_harness/workers.py) | Extend / adapt | 3 | `CodexWorker`: Codex-only text workers prohibit tools and deletion; extend the role protocol and Reviewer checklist via the common adapter. |
| [`workflow`](../src/development_harness/workflow.py) | Extend / adapt | 1,2,3 | `Workflow`: Preparation pins pytest/AppContainer/Codex; integrate general contracts and later combine plan approval with start. |
| [`workflow_acceptance`](../src/development_harness/workflow_acceptance.py) | Extend / adapt | 1,3 | `final_validation`: Requires AppContainer tokens and positive test counts for every check; generalize for mixed isolation and quality commands, then add document completion. |
| [`workflow_attempt_recovery`](../src/development_harness/workflow_attempt_recovery.py) | Extend / adapt | 1,3 | `reconcile_attempt`: Directly parses Codex events and isolated-validation evidence; move those dependencies behind common contracts (I1). |
| [`workflow_execution`](../src/development_harness/workflow_execution.py) | Extend / adapt | 1,3 | `Execution`: Retain sequential correction/final-check flow; adapt evidence and add quality devices, check requests and new file operations. |
| [`workflow_feedback`](../src/development_harness/workflow_feedback.py) | Reuse | 3 | `submit_feedback`: Keep same-scope defect versus requirements-change routing; connect the new planning entry point. |
| [`workflow_records`](../src/development_harness/workflow_records.py) | Extend / adapt | 3 | `WorkflowRecords`: Keep replay-safe journaling; findings currently constrain explicit paths and mandatory severity, so adapt to new scope/checklist. |
| [`workflow_recovery`](../src/development_harness/workflow_recovery.py) | Extend / adapt | 1,3 | `_patch`: Recovery currently reconstructs content writes; generalize validation evidence and recover deletion/rename operations. |

## Design Decisions

- **Check-only scope**: Phase 0 changes no code. The repository has no formatter, linter or type checker configured; adding one would change code and is left out of this Phase. **Proposed**: decide whether the harness repository gets its own quality checks when the quality devices are built in Phase 3.
- **No failing baseline**: as in spec 6.5, a failing test is fixed before the baseline is recorded. Skipped tests are allowed only when recorded with a reason.
- **Evidence location**: the JUnit report is first written outside OneDrive and then copied to `Phase/Evidence/` with its hash. Runtime databases and logs stay outside OneDrive.
- **Sequential run**: the full regression includes AppContainer and process tests. Run it alone; concurrent Windows verifications caused an ACL-grant timeout in the previous Phase 3.

## Usage Example

Run in PowerShell from the repository root, using the existing environment described in the archived [README](archive/lean-mvp-0.4/README_v0.4.md).

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython --version
& $harnessPython -m pip check
& $harnessPython -m pip freeze --all
& $harnessPython -m development_harness --version
$phase0RunDir = Join-Path $env:LOCALAPPDATA ("h0-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $phase0RunDir
$previousCodexPath = $env:DEVELOPMENT_HARNESS_CODEX_PATH
try {
    $env:DEVELOPMENT_HARNESS_CODEX_PATH = "$env:LOCALAPPDATA\development-tools-harness\runners\A-20260930-08\tools\codex.exe"
    & $env:DEVELOPMENT_HARNESS_CODEX_PATH --version
    & $harnessPython -m pytest --junitxml="$phase0RunDir\junit.xml" --basetemp="$phase0RunDir\tmp" -o "cache_dir=$phase0RunDir\pytest-cache"
} finally {
    $env:DEVELOPMENT_HARNESS_CODEX_PATH = $previousCodexPath
}
```

## Prerequisites & Development Notes

- On 2026-10-23 the old Phase documents were moved to `Phase/archive/lean-mvp-0.4`, and the acceptance-file path in `src/development_harness/fixed_runner_verify.py` was updated. A search found no test that reads the moved documents, and P0-T2 has now verified the current checkout with all 691 tests passing.
- If P0-T2 shows an environment problem (missing package, different version), fix the environment, not the code, and record what was done.

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created Phase 0 as a check-only Phase with Tasks P0-T1–T5 and a draft module map from spec 11. Not started; no test run or acceptance. Separate dev-log omitted because the skill is unavailable. |
| 2026-10-23 | Started on user instruction; verified the environment and 691 regressions, sealed the baseline, reviewed all 41 modules and synchronized specification 1.10/I1 references. No source/test changes. Module-map user review and Phase acceptance pending; separate dev-log omitted because the skill is unavailable. |
| 2026-10-23 | User explicitly accepted the verified results and module map ("인수한다"). Completed P0-T4/T5 and Phase 0; preserved evidence snapshots and added a hash-bound acceptance record. Detailed the Phase 1 plan without starting implementation. Separate dev-log omitted: skill unavailable. |

---

# Phase 0 — 기준선 확인 `✅ 완료`

> 현재 저장소가 실행되고 모든 테스트를 통과하는지 확인하고, 새 Phase의 출발점을 기록한다.

**선행 조건**: 충족 — 2026-10-23 [기획서 1.10](../Draft/ai-development-harness-plan-v1.md) 확정. 같은 날 사용자가 Phase 0 시작을 지시했고, 검증 결과와 모듈 대응표를 확인한 뒤 "인수한다"고 명시해 인수했다.

**기술 구성**: 관리자 권한 없는 Windows 10, Python 3.12.10(`.python-version`), pytest 9.1.1, psutil 7.2.2, setuptools 84.0.0(`requirements-dev.lock`), 표준 라이브러리의 SQLite. 이 Phase에서 추가하는 도구는 없다.

**형태**: 확인만(기획서 4.4). 설치, 코드 변경, AI 개발 호출이 없다.

## 개요

새 하네스는 이 저장소를 고쳐서 만든다(기획서 11장, F1). 고치기 전에 환경과 현재 동작이 정상인지 확인하고, 통과하는 테스트의 기준선을 기록한다. 그래야 다음 Phase에서 생긴 실패가 무엇 때문인지 가려낼 수 있다. 기획서의 "확인만" Phase 0과 "새로 생긴 문제만 막는다"(6.5) 규칙을 하네스 자신에게 적용한 것이다. 하네스로 하네스를 개발하지 않으므로, 기존 코딩 도구로 직접 수행한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 환경 확인 기록: 버전, 잠금 파일 대조, `pip check` | ✅ |
| 2 | JUnit XML 보고서와 실제 개수를 포함한 전체 회귀 검사 결과 | ✅ |
| 3 | 기준선 기록: 통과 테스트 ID, skip 테스트와 사유, 소요 시간, 보고서 해시 | ✅ |
| 4 | 확정한 모듈 대응표(재사용, 확장, 재설계, 보존) | ✅ 2026-10-23 인수 |
| 5 | Phase 0 사용자 인수 | ✅ |

## Task 및 검증

| Task | 작업 내용 | 완료 기준 | 검증 방법 | 상태 |
|---|---|---|---|---|
| P0-T1 | 하네스 실행 환경 확인 | Python이 3.12.10이다. 설치된 패키지가 `requirements-dev.lock`과 같다. `pip check`에 깨진 의존성이 없다. CLI가 버전을 출력한다. 다음 Phase를 위해 Codex CLI 버전을 기록하되 AI 호출은 하지 않는다 | `python --version`, 잠금 파일과 `pip freeze` 대조, `pip check`, `python -m development_harness --version`, `codex --version` | ✅ |
| P0-T2 | 전체 회귀 검사를 한 번, 순서대로 실행 | 종료 코드 0, JUnit 보고서 존재, 실행된 테스트 1개 이상, 실패·오류 0개(기획서 5장). 마지막 기록인 691개(2026-09-30, 실행본 A08)와 총수를 비교하고 차이가 있으면 이유를 밝힌다 | `python -m pytest --junitxml=<OneDrive 밖 로컬 폴더>\junit.xml` | ✅ |
| P0-T3 | 기준선 기록 | 통과 테스트 ID, skip 테스트와 사유, 총 소요 시간, 보고서 해시를 `Phase/Evidence/Phase0_Baseline.json`에 저장하고 JUnit 보고서를 옆에 복사한다. 실패 테스트는 기준선으로 인정하지 않는다. 원인을 보고하고, 사용자 승인을 받아 고치거나 사용자가 직접 고친 뒤 T2를 다시 실행한다 | 기록이 JUnit 파일과 그 해시에 일치하는지 확인 | ✅ |
| P0-T4 | 모듈 대응표 확정 | 41개 모듈마다 분류와 이유가 있다(아래 코드 대조표). 불분명한 항목은 "확인 필요"로 두고 결정할 Phase를 적는다 | 각 모듈 코드를 기획서 11장과 대조, 사용자가 대응표 검토 | ✅ 2026-10-23 인수 |
| P0-T5 | 사용자 인수 | 사용자가 T1–T4 결과를 확인하고 Phase 0을 인수한다 | 이 문서와 Overview에 인수 기록 | ✅ |

**결과**: 2026-10-23 기술 검증을 마쳤다. **691개 통과, 실패 0, 오류 0, skip 0**, 종료 코드 0이다. JUnit 소요 시간은 1322.867초, 전체 프로세스는 22분 3.6초다. 해시를 검증한 2026-09-30 기록과 테스트 ID 집합이 정확히 같으며 추가·삭제·새 skip은 없다. 2026-10-23 사용자가 이 결과와 41개 모듈 대응표를 인수했다. Phase 0은 완료했고 Phase 1은 상세 계획을 작성했으며 아직 시작하지 않았다.

### 검증 근거

- [사용자 인수 기록](Evidence/Phase0_Acceptance.json): 사용자 발언 원문과 기준선·모듈 대응표 해시로 인수 대상을 고정했다. 인수 기록 시 참조 근거 9개와 입력 파일 108개의 해시를 다시 확인했다. 기준선·대응표 JSON의 인수 대기 상태는 당시 스냅샷으로 보존하며, 현재 인수 여부는 이 별도 기록에 따른다. 문서만 갱신했으므로 테스트는 재실행하지 않았다.
- [기준선과 통과 테스트 ID 691개](Evidence/Phase0_Baseline.json), [JUnit XML](Evidence/Phase0_JUnit.xml), [실제 명령과 실행 결과](Evidence/Phase0_Run.json).
- [환경과 잠금 패키지 대조](Evidence/Phase0_Environment.json): Python 3.12.10, pytest 9.1.1, psutil 7.2.2, setuptools 84.0.0이며 잠금 파일의 8개 패키지가 모두 일치한다. `pip check` 통과, 하네스 CLI는 0.1.0이다. 추가 설치된 pip 25.0.1과 편집 가능 하네스 패키지는 잠금 파일 불일치가 아니다.
- [입력 파일 해시](Evidence/Phase0_Inputs.json): 소스·테스트·스크립트·스킬 리소스·설정 108개가 실행 전후 동일하다. Phase 0에서 구현 코드·테스트를 수정하지 않았다. 실행 로그와 DB는 OneDrive 밖에 있다.
- [41개 모듈 대조 기록](Evidence/Phase0_ModuleMap.json): 소스 해시, 확인한 심볼, 분류, 후속 Phase를 기록했다. 초안 외에도 공용 코드의 pytest·AppContainer 전용 가정을 수정해야 한다. 아래 대응표와 Phase 1·3 주의사항에 반영했다.

### Codex 선택과 검증 한계

PC 기본 버전은 **Codex CLI 0.163.0**이며 현재 Adapter의 검증된 버전 목록에 없다. A08 실행본 전체 매니페스트를 확인한 뒤 보관된 **0.155.1** 실행 파일을 `DEVELOPMENT_HARNESS_CODEX_PATH`로 이번 회귀 검사 프로세스에만 지정했다. Python이 불러온 하네스 코드는 A08이 아닌 **현재 체크아웃**이다. 전역 설정·도구 버전·의존성은 변경하지 않았다. 이번 기준선은 0.155.1 기준이며 0.163.0 호환성을 검증한 것이 아니다. 로컬 권한 진단은 외부 AI 서비스 요청을 하지 않았다. 포맷·린트·타입 검사 도입 여부는 Phase 3에서 결정한다.

### 환경 경로 변경 후 재검사 (실패 근거 보존)

첫 전체 검사 결과는 **685개 통과·6개 실패**였다. 여섯 건 모두 긴 pytest 임시 경로 아래 작업자 폴더를 만들 때 발생한 `WinError 206`이었다. 코드·테스트·의존성은 그대로 두고 로컬 루트만 `%LOCALAPPDATA%/h0-1023`으로 줄이자 기록 연결 검사 10개가 모두 통과했고, 이후 위의 전체 회귀 검사도 통과했다. 기준선은 성공한 전체 실행 하나를 기준으로 하며 여러 실행 결과를 합쳐 통과로 처리하지 않았다. 실행·임시 경로를 짧게 유지해야 한다는 운영상 한계가 있으며 긴 경로 지원을 검증한 것은 아니다.

근거: [첫 실패 실행](Evidence/Phase0_InitialRun.json), [첫 JUnit](Evidence/Phase0_InitialJUnit.xml), [짧은 경로 확인](Evidence/Phase0_PathCheckRun.json), [10개 검사 JUnit](Evidence/Phase0_PathCheck.xml).

### 모듈 대응표 초안에서 보완한 점

- `model.validate_checks`는 실제 프로젝트 등록에서도 쓰며 pytest를 필수로 요구하므로 Phase 1에서 일반화한다. 기존 가짜 계획 처리 부분만 후속 CLI 단계의 결정 대상이다.
- `workflow.prepare`와 `workflow_acceptance.final_validation`은 pytest·AppContainer에 고정돼 있다. 후자는 모든 검사에 테스트 수도 요구한다. 혼합 격리·품질 명령 도입과 함께 수정한다.
- `files`·`worker_contract`·복구 모듈은 Phase 3에서 삭제·이름 변경을 함께 다뤄야 한다. 기존 해시·사용자 변경 보호는 기반으로 유지한다.
- `workflow_attempt_recovery`가 Codex 이벤트를 직접 해석하므로 기획서 1.10의 공통 AI 연결 경계(I1)에 복구도 포함한다.
- Python 진단·자체 검사 도우미를 현재 코드가 사용한다. 자기 개발이 제품 범위 밖이어도 공용 의존성은 보존한다.

## 모듈 대응표 (검토·인수 완료)

41개 모듈을 기획서 1.10과 대조했다. 표는 처리 방향과 담당 Phase를 기록하며, 후속 변경을 이미 구현했다는 뜻은 아니다. 이전 가짜 Adapter나 자기 개발 기능이 첫 버전 범위 밖이어도 공용 코드는 유지한다.

| 모듈 | 처리 | 후속 Phase | 코드 근거와 이유 |
|---|---|---|---|
| [`__init__`](../src/development_harness/__init__.py) | 재사용 | all | `__version__`: 패키지 버전과 진입 계약을 유지한다. |
| [`__main__`](../src/development_harness/__main__.py) | 재사용 | all | `main`: CLI로 위임하며 대상 언어 지식이 없다. |
| [`appcontainer_probe`](../src/development_harness/appcontainer_probe.py) | 진단 유지 | 1 | `diagnose_appcontainer`: 실제 Python 경계 검증·런타임 복사에 사용되므로 선택적 스크립트로만 취급하지 않는다. |
| [`appcontainer_probe_payload`](../src/development_harness/appcontainer_probe_payload.py) | 진단 유지 | 1 | `observe`: Python 격리 입증을 위한 토큰·파일·네트워크 모의 관찰을 유지한다. |
| [`appcontainer_temp`](../src/development_harness/appcontainer_temp.py) | Python 경로 유지 | 1 | `install`: 복사된 Python의 임시 경로 호환 계층이므로 해당 백엔드 동작을 보존한다. |
| [`cli`](../src/development_harness/cli.py) | 재설계 | 2,3 | `parser`: 기존·계획·실행 명령으로 나뉜 사용자 흐름을 기획서의 일곱 명령으로 바꾼다. |
| [`codex_adapter`](../src/development_harness/codex_adapter.py) | 확장·수정 | 3 | `CodexPlanner`: 검증된 Codex 연결은 유지하고 도구 공통 경계를 분리하며 Claude Code 적합성을 확인한다(I1). |
| [`codex_probe`](../src/development_harness/codex_probe.py) | 진단 유지 | 3 | `verify_capabilities`: 실제 연결 허용 조건이므로 강제 도구 거부 검사를 보존하고 새 권한에 맞춰 확장한다(I1). |
| [`files`](../src/development_harness/files.py) | 확장·수정 | 3 | `apply_write`: 해시와 쓰기 검사를 유지하고 삭제·이름 변경에도 같은 보호를 추가한다. |
| [`fixed_runner`](../src/development_harness/fixed_runner.py) | 보존 | 1 | `build_runner`: 고정 실행본·이력·회귀 검사를 보존하되 자기 개발은 범위 밖이다. Phase 1에서 매니페스트 재사용을 검토한다. |
| [`fixed_runner_verify`](../src/development_harness/fixed_runner_verify.py) | 보존 | all | `main`: 기존 보관 경로 수정을 포함해 설치·권한 검증 도구를 보존한다. |
| [`frozen_entry`](../src/development_harness/frozen_entry.py) | 보존 | 1 | `inspect_runner`: 고정 실행본 검증을 보존한다. 매니페스트 해시는 새 설치본 변조 검사에 재사용 검토한다. |
| [`gate`](../src/development_harness/gate.py) | 재사용 | 1 | `main`: 격리·기록 후에만 임의 argv를 실행하는 게이트를 새 감시와 함께 재사용한다. |
| [`isolated_validation`](../src/development_harness/isolated_validation.py) | 재설계 | 1 | `IsolatedValidator`: 복사된 Python 백엔드를 유지하고 명령·근거 선택을 일반화하며 일반 권한 변조 탐지를 추가한다. |
| [`model`](../src/development_harness/model.py) | 재설계 | 1,3 | `validate_checks`: 공용 검사 검증이 pytest를 필수로 요구해 Phase 1에서 일반화해야 한다. 오류·해시·경로는 유지하고 가짜 계획 처리만 Phase 3에서 결정한다. |
| [`phase_docs`](../src/development_harness/phase_docs.py) | 확장·수정 | 2,3 | `render_documents`: 고정된 영문·국문 템플릿을 유지하고 Phase/ 생성 및 허용된 완료 필드 갱신을 추가한다. |
| [`plan_schema`](../src/development_harness/plan_schema.py) | 확장·수정 | 2 | `validate_plan`: Phase·현재 Task는 있으나 구조화한 세팅·검사·버전 결정 항목이 없다. |
| [`planning`](../src/development_harness/planning.py) | 확장·수정 | 2,3 | `Planning`: Phase 0·기술/버전 선택·세팅 계약과 공통 Planner 연결을 추가한다. |
| [`processes`](../src/development_harness/processes.py) | 재사용 | 1 | `ProjectLock`: 임의 명령에도 적용할 Windows 잠금·PID 식별·Job 관리를 재사용한다. |
| [`project`](../src/development_harness/project.py) | 확장·수정 | 1,2,3 | `validate_config`: 명시적 입력·Phase/Generated 정책과 pytest 계약 의존을 새 등록 규약·안전한 전체 읽기로 확장한다. |
| [`results`](../src/development_harness/results.py) | 확장·수정 | 3 | `report`: 근거 연결 JSON을 유지하고 실패·품질·설정·버전 변경을 포함한 영문·국문 Markdown을 추가한다. |
| [`reviewed_test_entry`](../src/development_harness/reviewed_test_entry.py) | 보존 | all | `main`: 검토된 호스트 회귀 검사 부트스트랩·근거 관찰자를 보존한다. |
| [`runner`](../src/development_harness/runner.py) | 존치 결정 대기 | 3 | `Harness`: 기존 가짜 Adapter 명령 실행기다. 회귀 검사를 유지하고 CLI 단순화 때 존치 여부를 결정한다. |
| [`self_test_verify`](../src/development_harness/self_test_verify.py) | 보존 | all | `reviewed_host`: 격리·호스트 근거 도구와 테스트는 보존하고 하네스 자기 개발은 진행하지 않는다. |
| [`store`](../src/development_harness/store.py) | 재사용 | 1 | `Store`: SQLite 트랜잭션 기록을 재사용하고 외부에 새 변조 감시를 연결한다. |
| [`test_collection`](../src/development_harness/test_collection.py) | 확장·수정 | 1 | `CollectionEvidence`: pytest 훅은 Python 근거로 유지하고 상위에 언어 공통 목록·skip 비교를 추가한다. |
| [`validation`](../src/development_harness/validation.py) | 재설계 | 1 | `pytest_result`: 실행은 argv 기반이지만 JUnit 경로·pytest 종료 판정·skip 거부가 고정돼 있다. |
| [`validation_entry`](../src/development_harness/validation_entry.py) | Python 경로 유지 | 1 | `main`: 고정 pytest·수집 관찰자를 불러오는 부트스트랩은 Python 백엔드에 한정해 유지한다. |
| [`validation_profiles`](../src/development_harness/validation_profiles.py) | 보존 | 1 | `prepare_profile`: 자체 검사 프로필은 제품 범위 밖이나 실행 모듈이 필터·도우미를 사용하므로 통째로 제거하지 않는다. |
| [`windows_appcontainer`](../src/development_harness/windows_appcontainer.py) | Python 경로 유지 | 1 | `AppContainer`: 권한 없는 Windows 실행 기반을 Python 경로에 유지한다. 다른 런타임 구현을 이곳에 추가하지 않는다. |
| [`worker_contract`](../src/development_harness/worker_contract.py) | 재설계 | 3 | `TaskScope`: 명시적 파일 목록·내용 교체만 허용한다. 안전한 탐색·폴더 범위·삭제/이름 변경·제한된 검사 요청을 설계한다. |
| [`worker_probe`](../src/development_harness/worker_probe.py) | 진단 유지 | 3 | `diagnose_workers`: Windows 명령 경계 진단을 유지하고 새 읽기·검색 권한 모델에 맞춰 재검토한다. |
| [`worker_probe_payload`](../src/development_harness/worker_probe_payload.py) | 진단 유지 | 3 | `observe`: 작업자 진단에 쓰이는 부모·자식 권한 모의 검사를 유지한다. |
| [`workers`](../src/development_harness/workers.py) | 확장·수정 | 3 | `CodexWorker`: Codex 전용 텍스트 작업자의 도구·삭제 금지를 새 역할 규약·리뷰 기준·공통 연결로 확장한다. |
| [`workflow`](../src/development_harness/workflow.py) | 확장·수정 | 1,2,3 | `Workflow`: 준비 단계가 pytest·AppContainer·Codex에 고정돼 있다. 공통 계약을 연결하고 계획 승인·시작을 통합한다. |
| [`workflow_acceptance`](../src/development_harness/workflow_acceptance.py) | 확장·수정 | 1,3 | `final_validation`: 모든 검사에 AppContainer 토큰·양수 테스트 수를 요구한다. 혼합 격리·품질 명령에 맞추고 문서 완료를 연결한다. |
| [`workflow_attempt_recovery`](../src/development_harness/workflow_attempt_recovery.py) | 확장·수정 | 1,3 | `reconcile_attempt`: Codex 이벤트·격리 검사 근거에 직접 의존하므로 공통 계약으로 분리한다(I1). |
| [`workflow_execution`](../src/development_harness/workflow_execution.py) | 확장·수정 | 1,3 | `Execution`: 순차 수정·최종 검사 흐름을 유지하고 근거 형식·품질 장치·검사 요청·새 파일 작업을 연결한다. |
| [`workflow_feedback`](../src/development_harness/workflow_feedback.py) | 재사용 | 3 | `submit_feedback`: 동일 범위 결함과 요구사항 변경의 분기를 유지하고 새 계획 진입점에 연결한다. |
| [`workflow_records`](../src/development_harness/workflow_records.py) | 확장·수정 | 3 | `WorkflowRecords`: 재실행에 안전한 기록은 유지하되 명시적 경로·필수 중요도 조건을 새 범위·리뷰 기준에 맞춘다. |
| [`workflow_recovery`](../src/development_harness/workflow_recovery.py) | 확장·수정 | 1,3 | `_patch`: 현재 내용 쓰기 중심 복구를 일반 검사 근거와 삭제·이름 변경까지 확장한다. |

## 설계 결정 사항

- **확인만 범위**: Phase 0에서는 코드를 바꾸지 않는다. 이 저장소에는 포맷·린트·타입 검사 도구가 설정돼 있지 않다. 도입하면 코드가 바뀌므로 이 Phase에서 제외한다. **제안**: 하네스 저장소 자체의 품질 검사 도입 여부는 Phase 3에서 품질 장치를 만들 때 정한다.
- **실패 기준선 불허**: 기획서 6.5와 같이 실패 테스트는 기준선 기록 전에 고친다. skip 테스트는 사유를 기록한 경우에만 허용한다.
- **근거 위치**: JUnit 보고서는 먼저 OneDrive 밖에 쓰고, 해시와 함께 `Phase/Evidence/`로 복사한다. 실행 DB와 로그는 OneDrive 밖에 둔다.
- **순서대로 실행**: 전체 회귀 검사에는 AppContainer와 프로세스 검사가 포함된다. 다른 검증과 동시에 돌리지 않는다. 이전 Phase 3에서 동시 실행으로 권한 설정 시간 초과가 발생했다.

## 사용 예시

저장소 루트의 PowerShell에서, 보관한 [README](archive/lean-mvp-0.4/README_ko_v0.4.md)에 적힌 기존 환경으로 실행한다.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython --version
& $harnessPython -m pip check
& $harnessPython -m pip freeze --all
& $harnessPython -m development_harness --version
$phase0RunDir = Join-Path $env:LOCALAPPDATA ("h0-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $phase0RunDir
$previousCodexPath = $env:DEVELOPMENT_HARNESS_CODEX_PATH
try {
    $env:DEVELOPMENT_HARNESS_CODEX_PATH = "$env:LOCALAPPDATA\development-tools-harness\runners\A-20260930-08\tools\codex.exe"
    & $env:DEVELOPMENT_HARNESS_CODEX_PATH --version
    & $harnessPython -m pytest --junitxml="$phase0RunDir\junit.xml" --basetemp="$phase0RunDir\tmp" -o "cache_dir=$phase0RunDir\pytest-cache"
} finally {
    $env:DEVELOPMENT_HARNESS_CODEX_PATH = $previousCodexPath
}
```

## 선행 조건 및 개발 시 주의사항

- 2026-10-23 기존 Phase 문서를 `Phase/archive/lean-mvp-0.4`로 옮기고 `src/development_harness/fixed_runner_verify.py`의 인수 파일 경로를 고쳤다. 검색으로는 옮긴 문서를 읽는 테스트가 없었지만, P0-T2에서 현재 체크아웃의 691개 테스트가 모두 통과함을 확인했다.
- P0-T2에서 환경 문제(패키지 누락, 버전 차이)가 나오면 코드가 아니라 환경을 고치고, 한 조치를 기록한다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | "확인만" 형태의 Phase 0을 Task P0-T1–T5와 기획서 11장 기반 모듈 대응표 초안으로 작성했다. 미시작이며 검사 실행·인수는 없다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-10-23 | 사용자 시작 지시에 따라 환경·전체 회귀 691개를 검증하고 기준선 근거를 저장했다. 41개 모듈을 코드와 대조하고 기획서 1.10/I1 참조를 동기화했다. 소스·테스트 변경은 없다. 대응표 사용자 검토·Phase 인수 대기. dev-log 스킬이 없어 별도 로그는 생략했다. |
| 2026-10-23 | 사용자가 검증 결과와 모듈 대응표를 "인수한다"고 명시했다. P0-T4/T5와 Phase 0을 완료 처리하고 기존 근거는 보존한 채 해시로 연결한 인수 기록을 추가했다. Phase 1 계획을 상세화했으며 구현은 시작하지 않았다. dev-log 스킬이 없어 별도 로그는 생략했다. |
