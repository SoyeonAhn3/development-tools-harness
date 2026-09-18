# Phase 1 — Foundation `✅ Completed`

> Establish an execution foundation that preserves approvals, results and files across interruption.

**Prerequisites**: Review [the overall plan](Overview.md) and this Phase's scope before implementation.

**Technology**: Windows, Python 3.12.10, pytest 9.1.1, SQLite, psutil 7.2.2.

**Plan status**: Initial implementation authorized on 2026-09-15. On 2026-09-18 the user authorized recording and fixing three review findings. R1–R3 are implemented and technically verified with 63 passing tests; user result acceptance is complete.

**User acceptance (2026-09-18)**: The user stated “이해 했고 phase1 인수한다” after reviewing the implementation, review fixes and verification results. Tasks 1.1–1.7 and R1–R3 are accepted, completing Phase 1. Phases 2–4 remain not started.

## Overview

Implement the minimum CLI, state storage and sequential runner with a fake AI Adapter. Verify approval waiting, failures, interruption, resume and exclusive project ownership without an actual AI service. This covers the foundations of specification §§6–8 and §10.3; it does not establish real Adapter isolation.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Python package and working pytest setup | ✅ |
| 2 | SQLite execution state, approval records and file baseline | ✅ |
| 3 | Fake Adapter, runner and registered-command validation | ✅ |
| 4 | Ownership/resume handling and core regression tests | ✅ |

## Tasks & Verification

Tasks were implemented in the order below; Task 1.7 integrates the preceding Tasks. Source mapping: 1.1 → §2 environment prerequisites; 1.2 and 1.6 → §8 state/resume; 1.3 → §§7–8 approval/baseline; 1.4–1.5 → §6 execution/validation; 1.7 → §10.3 core regressions. No application code was available for reuse at the start. Task checkmarks mean technical verification, not user acceptance of the Phase.

| Task | Work | Acceptance Criteria | Verification | Status |
|---|---|---|---|---|
| 1.1 | Fix Python version; create package, CLI entry and test configuration | The documented environment launches the CLI and discovers/runs an actual behavior test; setup instructions identify dependencies | CLI subprocess smoke test and `python -m pytest` in the prepared environment | ✅ |
| 1.2 | Store Project/Run/Phase/Task IDs, stages, attempts, interruptions and evidence in SQLite | Reopening the DB preserves confirmed state; unfinished work remains unfinished; an interrupted update does not leave contradictory records | Temporary-DB reopen and transaction-failure tests | ✅ |
| 1.3 | Bind approval to plan/input versions and capture the content baseline | A fake Developer cannot run before approval or with an obsolete approval; pre-existing edits are part of the baseline; generated outputs and Git metadata are excluded under documented rules | Changed-plan and changed-input tests; content-change versus metadata-only tests | ✅ |
| 1.4 | Run fake Developer → validation → fake Reviewer sequentially; track bounded corrections | No out-of-order completion; unresolved mandatory review findings block completion; correction limit stops execution with a reason | Deterministic pass, fail, interruption and exhausted-correction scenarios | ✅ |
| 1.5 | Execute registered validation commands and store actual outcomes | Capture command, exit/outcome, start/end and code/plan identity; failed, missing, interrupted or zero-test checks never count as passed | Small subprocess test fixtures covering all outcomes, including a pytest project with no tests | ✅ |
| 1.6 | Enforce single-run ownership; inspect state/processes/files before resume | Of two competing processes only one owns a project; stop leaves useful records; active/orphaned workers prevent unsafe takeover; unexpected edits stop without overwrite | Two-process contention, termination/restart and user-file-edit tests using temporary folders | ✅ |
| 1.7 | Exercise the foundation end to end and preserve core regressions | A small fake-Adapter run waits for approval, executes, stops/resumes and reports its outcome; partial edits are inspected; interrupted checks rerun after process checks; final required checks use final content | Separate-process CLI integration tests plus the complete Phase 1 pytest suite; user inspects results | ✅ |

**Results (2026-09-15)**: 43 pytest tests passed in 12.98 seconds; `pip check` reported no broken requirements. Real subprocess tests covered CLI execution, test failure/correction, mandatory review correction, zero/skipped tests, missing commands, timeout, competing runners, force-killed parent/descendants, resume and final acceptance. Unit tests covered transaction rollback, approval invalidation, partial writes, file preservation and case aliases. These exercise the fake Adapter foundation, not live AI or a permission sandbox.

The initial test run found an interrupted implementation incorrectly receiving an exact duration on resume; this was fixed and regressed. A separate CLI demonstration completed prepare → approve → one-stage pause → resume → awaiting acceptance. Local evidence: `%LOCALAPPDATA%/development-tools-harness/phase1-tests.xml` and `phase1-demo.json`; command logs and SQLite evidence are in the runtime directory linked by `status`. User result acceptance was pending at the time of this initial demonstration.

## Review Follow-up — 2026-09-18

The review reran the original suite: 43 tests passed in 12.33 seconds and `pip check` passed. Three additional temporary-project experiments exposed gaps not covered by that suite. The original checkmarks above describe the initial verification; technical completion now also requires the following fixes and regressions.

| ID / Related Tasks | Reproduced Finding | Authorized Fix and Acceptance Criteria | Verification | Status |
|---|---|---|---|---|
| R1 / 1.3, 1.6 | A hard-linked project file changed an external file and still reached result acceptance waiting. | Reject hard-linked files during baseline inspection and before writing through the opened file handle; preserve external contents. | Real hard links present before prepare, introduced after approval and introduced between path inspection and opening. | ✅ |
| R2 / 1.2, 1.6 | Process termination between truncating and rewriting ownership metadata allowed another state directory to prepare a second active Run. | Preserve the previous DB reference throughout ownership updates; retain the stable OS lock and stop on malformed metadata. Preserve valid legacy ownership records. | Subprocess termination during metadata updates, alternate state-directory contention, malformed records and legacy-record compatibility. | ✅ |
| R3 / 1.4, 1.5 | Python without pytest returned exit code 1, triggering three Developer attempts and exhausting two corrections. | Treat unavailable pytest as an environment problem without consuming corrections; real test failures must still trigger bounded correction. | An isolated Python environment without pytest, followed by environment repair and resume; existing failure/correction integration tests. | ✅ |

**Implementation**: `files.require_single_link` checks the baseline's file metadata and `os.fstat` on the opened write handle. `processes.ProjectLock` retains the original `.lock` file and reads valid legacy inline records; new ownership metadata uses a separate `.json` file written to a flushed/fsynced temporary file and replaced under the same lock. Invalid metadata stops execution without overwriting the evidence. `validation.validate` requires both pytest exit code 1 and JUnit failure evidence before consuming a correction; missing pytest leaves the attempt `unverified`, with an environment/log diagnostic and unchanged correction count.

**Verification (2026-09-18)**: The six initial regression cases failed before the fixes and passed afterward. Added 20 cases in total, including forced subprocess exits before/after metadata replacement in both current and legacy formats, malformed metadata preservation and environment repair followed by CLI resume without another Developer attempt. The full suite passed **63 tests in 16.71 seconds**; `pip check` passed. Evidence: `%LOCALAPPDATA%/development-tools-harness/phase1-remediation-tests.xml`. Tests are in [file protection regressions](../tests/unit/test_inputs.py), [ownership regressions](../tests/unit/test_ownership.py), and [CLI/process integration tests](../tests/integration/test_cli.py).

This follow-up stays within the Phase 1 fake-Adapter foundation; it does not introduce the Phase 2 baseline admission gate or permission sandbox. The user accepted the foundation and review fixes on 2026-09-18. No separate dev-log skill is installed; this document's change log records the work.

## Runner Foundation

### Purpose

Provide predictable state transitions and evidence before adding live AI execution. A fake Adapter returns controlled responses; it is not a substitute for the real permission checks in Phase 2.

### Implementation Files

- [Package and test configuration](../pyproject.toml), [locked development dependencies](../requirements-dev.lock), and `.python-version`.
- [CLI](../src/development_harness/cli.py): `prepare`, `approve`, `run`, `resume`, `status`, `accept`, `cancel`.
- [Harness](../src/development_harness/runner.py) and [Store](../src/development_harness/store.py): transitions and transactional state/evidence.
- [Input contract](../src/development_harness/model.py), [file handling](../src/development_harness/files.py), [process ownership/containment](../src/development_harness/processes.py), [validation](../src/development_harness/validation.py) and its [internal launch gate](../src/development_harness/gate.py).
- [Unit tests](../tests/unit/), [CLI/process integration tests](../tests/integration/test_cli.py), and [example plan](../tests/fixtures/fake-plan.json).

### Core Structure & Design Decisions

- Keep runner decisions, storage, validation and Adapter calls separate enough to substitute fake responses. Do not introduce a general workflow framework.
- Initial flow: plan approval → implementation → validation → review → final Phase validation → result acceptance. Waiting, failure and interruption must remain explicit; detailed internal state names are decided during implementation.
- Model approval and evidence versions from the beginning. The work Adapter cannot approve itself through its response; real OS/tool protection is verified later.
- Use SQLite transactions for consistent records and atomic ownership acquisition. Persist enough process identity to inspect outstanding work; do not assume a stale timestamp means a process is dead.
- Put runtime DB/logs outside OneDrive. Tests use separate temporary DBs/folders. Define file snapshot inclusions/exclusions and include user edits in the starting baseline; never automatically restore or merge files.
- Preserve core tests as the comparison baseline for later self-development. Fake calls are marked synthetic and do not count as real AI usage. Prepare attempt IDs and timestamps for later actual-call records.
- Start with a proposed correction limit of two; approval waiting does not consume attempts. Environment failures are not code-fix retries.

Implementation details: use explicit JSON input for the fake Adapter, with sequential Tasks and per-attempt file contents/review outcomes. Windows file handles deny competing writes/deletes during checked writes. A project-wide OS lock covers alternate state-directory choices, while SQLite transactions protect state/event consistency. Validation workers wait for containment and persisted PID/creation-time identity before starting commands; a Windows Job terminates their descendants on harness exit. This manages process lifetime, not execution permissions. Interrupted spans without a confirmed end retain an unknown duration.

The baseline excludes `.git` (directory or worktree pointer), `.venv`, `__pycache__`, `.pytest_cache` and `.harness-output`; other files are content-hashed. Linked paths are unsupported. Unrecognized partial content stops for inspection; `cancel` preserves it and permits a new run. All Developer/Reviewer attempts are synthetic; actual AI calls remain zero.

### Usage Examples

Follow the [README setup and example](../README.md#phase-1-setup-and-example). Verification is `python -m pytest`; the CLI is `python -m development_harness` or `dev-harness`. `run --steps 1` pauses at a stage boundary and `resume` continues. `status` prints JSON evidence and log locations. `accept` is a separate user action after final validation. Copy the fixture to a fresh local project before running it.

## Prerequisites & Dependencies

The harness environment was prepared with existing coding tools at `%LOCALAPPDATA%/development-tools-harness/venv`. This is development setup, not the product's excluded automatic project bootstrap feature. Python 3.12.10 and dependencies are recorded; no real AI provider is needed for this Phase.

## Development Notes

Out of scope: live planning/implementation, proof of real worker permission isolation, polished reports, external project acceptance and product dogfooding. These belong to later Phases. No Git writes or deployment. A passing fake workflow does not establish MVP completion.

Current supported execution environment is Windows/Python 3.12. Registered validation commands execute with the user's permissions and must be trusted; Phase 2 must establish the actual permission boundary. Phase 1 captures the starting files but does not implement Phase 2's baseline-test admission gate. The sample/fake plans are explicit test inputs, not AI-generated plans.

Exit requires all above Tasks and final Phase checks to pass with evidence, followed by user acceptance. Preserve failures in the result notes rather than marking incomplete work complete.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the initial detailed foundation plan with Python + pytest, seven Tasks and explicit verification criteria. |
| 2026-09-15 | User authorized Phase 1; implemented Tasks 1.1–1.7 and verified 43 tests plus a separate CLI demonstration. Technical work complete; user acceptance pending. |
| 2026-09-18 | Recorded review findings R1–R3 and user-authorized remediation criteria before starting the fixes. Technical completion reopened; user acceptance remains pending. |
| 2026-09-18 | Fixed R1–R3, added 20 regression cases and passed all 63 tests plus `pip check`. Recorded implementation and evidence; user acceptance remains pending. |
| 2026-09-18 | Recorded explicit user acceptance: “이해 했고 phase1 인수한다”. Marked Phase 1 completed, including Tasks 1.1–1.7 and review fixes R1–R3; Phases 2–4 remain not started. |

---

# Phase 1 — 실행 기반 `✅ 완료`

> 중단 후에도 승인·검사 결과·파일을 보존하는 실행 기반을 만든다.

**선행 조건**: 구현 전에 [전체 계획](Overview.md)과 현재 Phase 범위를 검토한다.

**기술 구성**: Windows, Python 3.12.10, pytest 9.1.1, SQLite, psutil 7.2.2.

**계획 상태**: 2026-09-15 최초 구현 승인. 2026-09-18 사용자가 리뷰 결함 3건의 기록과 수정을 승인했다. R1–R3 보완 구현과 검사 63개를 통한 기술 검증 및 사용자 결과 인수를 완료했다.

**사용자 인수(2026-09-18)**: 사용자가 구현 내용·리뷰 보완·검증 결과를 확인한 뒤 “이해 했고 phase1 인수한다”라고 명시했다. Task 1.1–1.7과 R1–R3을 인수해 Phase 1을 완료한다. Phase 2–4는 미시작 상태를 유지한다.

## 개요

가짜 AI Adapter로 최소 CLI·상태 저장·순차 Runner를 구현한다. 실제 AI 서비스 없이 승인 대기·실패·중단·재개·프로젝트 실행 소유권을 검증한다. 기획서 6–8장과 10.3의 기반을 다루며 실제 Adapter의 권한 분리가 검증되는 단계는 아니다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | Python 패키지와 실제 실행 가능한 pytest 환경 | ✅ |
| 2 | SQLite 실행 상태·승인 기록·파일 기준선 | ✅ |
| 3 | 가짜 Adapter·Runner·등록된 명령 검증 | ✅ |
| 4 | 실행 소유권·재개 처리·핵심 회귀 검사 | ✅ |

## Task 및 검증

아래 순서대로 구현했으며 Task 1.7은 앞선 Task를 통합 검증한다. 기획서 연결: 1.1 → 2장 환경 조건, 1.2·1.6 → 8장 상태·재개, 1.3 → 7–8장 승인·기준선, 1.4–1.5 → 6장 실행·검증, 1.7 → 10.3 핵심 회귀 검사. 시작 당시 재사용할 애플리케이션 코드는 없었다. Task 체크는 기술 검증을 뜻하며 Phase 사용자 인수와 구분한다.

| Task | 작업 내용 | 완료 기준 | 검증 방법 | 상태 |
|---|---|---|---|---|
| 1.1 | Python 버전 확정, 패키지·CLI 진입점·테스트 설정 | 문서화한 환경에서 CLI 실행 및 실제 동작 테스트 발견·실행 가능, 준비 안내에 의존성 명시 | CLI 하위 프로세스 기본 동작 검사와 준비한 환경의 `python -m pytest` | ✅ |
| 1.2 | Project·Run·Phase·Task 식별자, 단계·시도·중단·근거를 SQLite에 저장 | DB 재연결 후 확정된 상태 유지, 미완료는 미완료로 유지, 갱신 중단 시 모순된 기록이 남지 않음 | 임시 DB 재연결 및 트랜잭션 실패 테스트 | ✅ |
| 1.3 | 계획·입력 버전에 승인 연결, 내용 기반 기준선 기록 | 미승인·오래된 승인으로 가짜 Developer 실행 불가, 기존 사용자 변경은 기준선에 포함, 생성물·Git 메타데이터 제외 규칙 명시 | 계획·입력 변경, 파일 내용 변경과 메타데이터만 변경된 경우 테스트 | ✅ |
| 1.4 | 가짜 Developer → 검증 → 가짜 Reviewer 순차 실행, 수정 횟수 관리 | 단계 순서를 건너뛰어 완료 불가, 미해결 필수 리뷰 지적은 완료 차단, 수정 한도 초과 시 사유와 함께 중단 | 통과·실패·중단·수정 한도 초과를 정해진 응답으로 테스트 | ✅ |
| 1.5 | 등록된 검증 명령 실행과 실제 결과 기록 | 명령·종료 결과·시작과 종료·코드와 계획 식별 기록, 실패·미실행·중단·테스트 0개는 통과 불가 | 테스트 없는 pytest 프로젝트를 포함해 각 결과를 만드는 작은 하위 프로세스 예제 검사 | ✅ |
| 1.6 | 단일 실행 소유권 확보, 재개 전 상태·프로세스·파일 확인 | 두 프로세스 중 하나만 프로젝트 소유, 중단 기록 보존, 실행 중이거나 남은 작업 프로세스가 있으면 안전하지 않은 소유권 인계 차단, 예상 밖 변경은 보존하고 중단 | 임시 폴더에서 두 프로세스 경쟁·강제 종료와 재시작·사용자 파일 변경 테스트 | ✅ |
| 1.7 | 기반 전체 흐름 확인과 핵심 회귀 검사 보존 | 작은 가짜 Adapter Run에서 승인 대기·실행·중단·재개·결과 확인 연결, 부분 작성 파일 확인, 잔여 프로세스 확인 후 중단 검사 재실행, 최종 내용에서 필수 검사 수행 | 별도 프로세스의 CLI 통합 테스트와 Phase 1 전체 pytest, 사용자 결과 확인 | ✅ |

**결과(2026-09-15)**: pytest 43개가 12.98초에 통과했고 `pip check`에서 의존성 문제가 없었다. 실제 하위 프로세스 검사로 CLI 실행, 테스트 실패·수정, 필수 리뷰 수정, 테스트 0개·생략, 명령 누락, 시간 초과, 실행 경쟁, 부모·자손 프로세스 강제 종료, 재개·최종 인수를 확인했다. 단위 검사로 트랜잭션 롤백, 승인 무효화, 부분 파일 작성, 파일 보존과 대소문자 별칭을 확인했다. 가짜 Adapter 기반 검증이며 실제 AI·권한 샌드박스 검증은 아니다.

첫 검사에서 중단된 구현을 재개할 때 정확한 실행 시간이 있는 것으로 기록하는 결함을 발견해 수정하고 회귀 검사했다. 별도 CLI 시연에서 준비 → 승인 → 한 단계 후 일시 중단 → 재개 → 인수 대기까지 확인했다. 로컬 근거는 `%LOCALAPPDATA%/development-tools-harness/phase1-tests.xml`과 `phase1-demo.json`이며, 명령 로그·SQLite 기록은 `status`에 표시되는 실행 폴더에 있다. 이 최초 시연 당시 사용자 결과 인수는 대기 중이었다.

## 리뷰 후속 보완 — 2026-09-18

리뷰에서 기존 검사를 다시 실행해 43개가 12.33초에 통과했고 `pip check`도 통과했다. 별도 임시 프로젝트 실험 3건에서는 기존 검사가 다루지 않은 결함을 재현했다. 위 기존 체크는 최초 검증 결과이며, 기술적 완료를 위해 아래 보완과 회귀 검증이 추가로 필요하다.

| ID / 관련 Task | 재현한 결함 | 승인된 보완 내용과 완료 기준 | 검증 방법 | 상태 |
|---|---|---|---|---|
| R1 / 1.3, 1.6 | 프로젝트의 하드링크 파일 수정으로 외부 파일도 변경됐는데 결과 인수 대기에 도달했다. | 기준선 검사와 열린 파일 핸들을 통한 쓰기 전에 하드링크를 거부하고 외부 파일 내용을 보존한다. | 준비 전 존재한 링크, 승인 후 추가된 링크, 경로 검사와 파일 열기 사이에 추가된 실제 하드링크 검사. | ✅ |
| R2 / 1.2, 1.6 | 소유권 정보를 지우고 다시 쓰는 사이에 종료되면 다른 상태 폴더에서 두 번째 활성 Run을 준비할 수 있었다. | 소유권 갱신 중 이전 DB 연결 정보를 보존하고 고정된 OS 잠금을 유지한다. 손상된 기록에서는 중단하며 정상적인 기존 형식도 보존한다. | 정보 갱신 중 하위 프로세스 종료, 다른 상태 폴더 경쟁, 손상된 기록과 기존 형식 호환성 검사. | ✅ |
| R3 / 1.4, 1.5 | pytest 없는 Python의 종료 코드 1을 코드 실패로 판단해 Developer 3회 실행·수정 2회 소진으로 끝났다. | pytest 실행 불가를 수정 횟수를 소모하지 않는 환경 문제로 처리하고 실제 테스트 실패의 제한된 수정은 유지한다. | pytest 없는 독립 Python 환경에서 중단 후 환경 보완·재개, 기존 실패·수정 통합 검사. | ✅ |

**구현 내용**: `files.require_single_link`로 기준선의 파일 메타데이터와 열린 쓰기 핸들의 `os.fstat`을 검사한다. `processes.ProjectLock`은 기존 `.lock` 파일을 유지하고 정상적인 기존 내부 기록을 읽는다. 새 소유권 정보는 별도 `.json` 파일을 사용하며 동일한 잠금 안에서 임시 파일 쓰기·flush·fsync 후 교체한다. 손상된 기록은 덮어쓰지 않고 중단한다. `validation.validate`는 pytest 종료 코드 1과 JUnit 실패 근거가 모두 있을 때만 수정 횟수를 소모한다. pytest 미설치는 `unverified`로 남기고 환경·로그 확인 사유를 표시하며 수정 횟수를 유지한다.

**검증 결과(2026-09-18)**: 최초 회귀 사례 6개는 수정 전 실패하고 수정 후 통과했다. 총 20개를 추가했으며 기존·새 형식에서 소유권 정보 교체 직전·직후 프로세스 강제 종료, 손상된 기록 보존, 환경 보완 후 Developer 추가 실행 없이 CLI 재개를 포함한다. 전체 **63개 검사가 16.71초에 통과**했고 `pip check`도 통과했다. 근거: `%LOCALAPPDATA%/development-tools-harness/phase1-remediation-tests.xml`. 검사는 [파일 보호 회귀 검사](../tests/unit/test_inputs.py), [소유권 회귀 검사](../tests/unit/test_ownership.py), [CLI·프로세스 통합 검사](../tests/integration/test_cli.py)에 있다.

범위는 Phase 1 가짜 Adapter 기반을 유지하며 Phase 2의 기본 검사 진입 조건이나 권한 샌드박스를 추가하지 않는다. 사용자는 2026-09-18 실행 기반과 리뷰 보완을 인수했다. 별도 dev-log 스킬은 설치되지 않아 이 문서의 변경 이력에 기록했다.

## 실행 기반

### 목적

실제 AI 연결 전에 예측 가능한 상태 전이와 검증 근거를 준비한다. 가짜 Adapter는 정해진 응답을 반환하는 시험용이며 Phase 2의 실제 권한 검사를 대체하지 않는다.

### 구현 파일

- [패키지·테스트 설정](../pyproject.toml), [고정 개발 의존성](../requirements-dev.lock), `.python-version`.
- [CLI](../src/development_harness/cli.py): `prepare`, `approve`, `run`, `resume`, `status`, `accept`, `cancel`.
- [Harness](../src/development_harness/runner.py)와 [Store](../src/development_harness/store.py): 상태 전이와 트랜잭션 기반 상태·근거 저장.
- [입력 규약](../src/development_harness/model.py), [파일 처리](../src/development_harness/files.py), [프로세스 소유권·수명 관리](../src/development_harness/processes.py), [검증 실행](../src/development_harness/validation.py)과 [내부 실행 게이트](../src/development_harness/gate.py).
- [단위 검사](../tests/unit/), [CLI·프로세스 통합 검사](../tests/integration/test_cli.py), [예제 계획](../tests/fixtures/fake-plan.json).

### 핵심 구조와 설계 결정 사항

- Runner 판단·저장·검증·Adapter 호출을 구분해 가짜 응답을 연결한다. 범용 Workflow 프레임워크는 만들지 않는다.
- 기본 흐름은 계획 승인 → 구현 → 검증 → 리뷰 → Phase 최종 검증 → 결과 인수다. 대기·실패·중단은 명확히 구분하며 내부 상태 이름은 구현 중 결정한다.
- 처음부터 승인과 근거의 버전을 모델링한다. 작업 Adapter의 응답으로 스스로 승인할 수 없게 하며 실제 OS·도구 차원의 보호는 후속 단계에서 검증한다.
- SQLite 트랜잭션으로 기록 일관성과 원자적 소유권 획득을 처리한다. 잔여 작업 확인에 필요한 프로세스 식별 정보를 저장하며 오래된 시간 기록만으로 프로세스 종료를 추정하지 않는다.
- 실행 DB·로그는 OneDrive 밖에 둔다. 테스트는 별도 임시 DB·폴더를 쓴다. 파일 스냅샷 포함·제외 기준을 정하고 기존 사용자 변경을 기준선에 포함하며 자동 복원·병합하지 않는다.
- 핵심 검사를 이후 자체 개발의 비교 기준으로 보존한다. 가짜 호출은 시험용으로 표시해 실제 AI 사용량에 포함하지 않는다. 이후 실제 호출을 기록할 시도 식별자와 시간 항목을 준비한다.
- 수정 한도는 기본 2회를 제안하며 승인 대기는 횟수에서 제외한다. 환경 실패는 코드 수정 재시도로 처리하지 않는다.

구현 상세: 가짜 Adapter는 Task 순서와 시도별 파일 내용·리뷰 결과가 명시된 JSON 입력을 사용한다. Windows 파일 핸들로 내용 확인·쓰기 동안 다른 쓰기·삭제 접근을 막는다. 프로젝트 단위 OS 잠금은 다른 상태 폴더를 선택한 실행에도 적용하고, SQLite 트랜잭션은 상태·이벤트의 일관성을 보장한다. 검증 작업 프로세스는 수명 관리 설정과 PID·생성 시각 저장 이후에만 명령을 시작하며 Windows Job으로 하네스 종료 시 자손 프로세스를 종료한다. 이는 프로세스 수명 관리이며 실행 권한 제한이 아니다. 종료를 확인하지 못한 중단 구간의 시간은 미확정으로 유지한다.

기준선은 `.git`(디렉터리·worktree 포인터), `.venv`, `__pycache__`, `.pytest_cache`, `.harness-output`을 제외하고 나머지 파일 내용을 해시한다. 링크 경로는 지원하지 않는다. 알 수 없는 부분 파일 내용은 보존하고 확인을 위해 중단하며, `cancel`로 파일을 보존한 채 새 Run을 준비할 수 있다. Developer·Reviewer 시도는 모두 가짜이며 실제 AI 호출 수는 0이다.

### 사용 예시

[README 설치·예제 안내](../README_ko.md#phase-1-설치와-예제)를 따른다. 검증은 `python -m pytest`, CLI는 `python -m development_harness` 또는 `dev-harness`다. `run --steps 1`은 단계 경계에서 멈추고 `resume`은 이어서 실행한다. `status`는 JSON 근거와 로그 위치를 출력한다. `accept`는 최종 검증 후 사용자가 별도로 실행한다. 예제는 새 로컬 프로젝트에 복사한 뒤 실행한다.

## 선행 조건 및 의존성

기존 코딩 도구로 `%LOCALAPPDATA%/development-tools-harness/venv`에 하네스 개발 환경을 준비했다. 개발 준비 작업이며 제품 범위에서 제외한 자동 프로젝트 부트스트랩 기능이 아니다. Python 3.12.10과 의존성을 기록했으며 이 Phase에는 실제 AI 제공자가 필요하지 않다.

## 개발 시 주의사항

실제 계획·구현 호출, 실제 작업 프로세스의 권한 분리 입증, 완성된 보고서, 외부 프로젝트 인수와 제품 dogfooding은 후속 Phase 범위다. Git 쓰기·배포는 하지 않는다. 가짜 Workflow 통과를 MVP 완료로 취급하지 않는다.

현재 실행 지원 환경은 Windows/Python 3.12다. 등록된 검증 명령은 사용자 권한으로 실행하므로 신뢰하는 명령이어야 하며, 실제 권한 경계는 Phase 2에서 검증해야 한다. Phase 1은 시작 파일을 기록하지만 Phase 2의 기본 테스트 통과 후 진입 기능은 아직 구현하지 않았다. 예제·가짜 계획은 명시적인 테스트 입력이며 AI 생성 계획이 아니다.

위 Task와 Phase 최종 검사에 통과한 근거를 남기고 사용자 인수를 받아야 종료한다. 실패는 결과에 남기며 미완료 작업을 완료 처리하지 않는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | Python + pytest, Task 7개와 명시적인 검증 기준을 포함한 실행 기반 상세 계획 최초 작성. |
| 2026-09-15 | 사용자 Phase 1 착수 승인. Task 1.1–1.7 구현, 43개 검사와 별도 CLI 시연 검증. 기술 작업 완료, 사용자 인수 대기. |
| 2026-09-18 | 수정 착수 전에 리뷰 결함 R1–R3과 사용자가 승인한 보완 기준을 기록했다. 기술적 완료를 재검토하며 사용자 인수 대기는 유지한다. |
| 2026-09-18 | R1–R3 수정, 회귀 사례 20개 추가, 전체 63개 검사와 `pip check` 통과. 구현과 근거를 기록했으며 사용자 인수 대기는 유지한다. |
| 2026-09-18 | 사용자 “이해 했고 phase1 인수한다”를 인수 근거로 기록했다. Task 1.1–1.7과 리뷰 보완 R1–R3을 포함해 Phase 1을 완료 처리했으며 Phase 2–4는 미시작 상태를 유지한다. |
