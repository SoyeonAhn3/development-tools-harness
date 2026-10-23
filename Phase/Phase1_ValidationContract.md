# Phase 1 — Validation Contract & Isolation `🔲 Not Started`

> Judge test and quality results the same way for any language; preserve AppContainer protection and detect record tampering in normal-permission execution.

**Prerequisites**: Met — [Phase 0](Phase0_Baseline.md) accepted on 2026-10-23 ([record](Evidence/Phase0_Acceptance.json)).

**Technology**: Harness unchanged (Windows, Python 3.12.10, pytest 9.1.1, SQLite). Example projects: Python with pytest, and Java. Proposed fixture: Maven and JUnit; Gradle is an alternative if the company environment requires it. Exact JDK/build-tool/test-tool versions and download sources are pending P1-T1 inventory and selection, before installation or execution commands are finalized.

**Plan status**: Detailed on 2026-10-23 following Phase 0 acceptance. All implementation Tasks are not started. Execution begins on the user's Phase 1 start instruction.

## Overview

Spec 12 steps 1–2. Replace the pytest-only validation with the language-independent check contract (spec 5), and implement isolation option C (spec 5.1). These are the riskiest items, so they come first: the Java package download on the company network and the isolation method are checked here.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Check registration: argv, working folder, timeout. The harness runs each check and records exit code and output | 🔲 |
| 2 | JUnit XML judgement: exit code 0, report exists, at least one test, zero failures and errors; comparison with the previous passing-test list; skip rules (baseline skips allowed, new skips flagged for the Reviewer) | 🔲 |
| 3 | Quality checks judged by exit code; the missing-report exception becomes a manual check only with user approval | 🔲 |
| 4 | Isolation option C: AppContainer kept for Python; other checks run with normal user permissions plus tamper detection; isolation level shown in results | 🔲 |
| 5 | Python and Java example projects, and the recorded result of the Java package download check | 🔲 |

## Tasks & Verification

Execute P1-T1–T8 in order; T9 is the separate user acceptance step. All entries below describe planned work.

| Task | Work | Acceptance Criteria | Verification | Status |
|---|---|---|---|---|
| P1-T1 | Inspect Java tools and company network; select and pin example dependencies | Record exact JDK, build/test tool versions and sources; run an actual dependency download without administrator rights. If blocked, record proxy/internal repository options and required action without claiming success | Capture version output, dependency command, exit code and logs in a short local directory outside OneDrive; review lock/configuration files | 🔲 |
| P1-T2 | Define the shared check registration and result contract | Register test/quality kind, argv, cwd, timeout, report locations and isolation mode; remove pytest-only registration assumptions in `model` and `project`; invalid paths/arguments fail explicitly | Unit tests for valid Python/Java/quality registrations and malformed configuration; assess compatibility with existing saved registrations | 🔲 |
| P1-T3 | Generalize JUnit judgement and test identity comparison | Tests pass only with exit 0, fresh valid report, at least one executed test and no failures/errors. Preserve identities across reports; detect removed tests and every new skip for mandatory review. Baseline skips remain allowed | Fixtures covering nested/multiple suites, malformed or ambiguous reports, failure/error, empty/all-skipped suites, unchanged skip, removed test and new skip; no language branch in judgement | 🔲 |
| P1-T4 | Execute the contract through both isolation modes | Keep Python AppContainer including project virtualenv dependencies; add normal-user execution for other runtimes and checks requiring local network. Record mode, argv, cwd, output, exit and timeout; never silently downgrade after AppContainer failure | Actual Python virtualenv and Java child processes; timeout/descendant cleanup and failed-isolation cases; inspect mode recorded for every check | 🔲 |
| P1-T5 | Detect record and installation tampering | Hold the latest legitimate record hashes in controller memory, compare after every command, check installation manifest, and read reports only from newly created controller result folders. Mismatch stops further execution | Disposable fixtures modify records, policy/approval data or installation files; reject stale/outside-folder results; legitimate controller writes do not trigger false positives | 🔲 |
| P1-T6 | Connect registration, workflow and acceptance to the contract | Update `workflow.prepare` and `workflow_acceptance.final_validation` so quality checks use exit codes and test checks use JUnit. Missing reports stay unverified; conversion to manual checking requires user approval plus recorded manual result. Preserve content/version and approval binding | Integration tests reach final validation through both backends; reject missing evidence, stale results and unapproved manual conversion; previously passing tests removed/new skips require Reviewer evidence | 🔲 |
| P1-T7 | Verify Python and Java examples using the same implementation | Both examples exercise pass, failure, zero tests, missing report, timeout, removed test and new skip. Record the actual Java download and Python virtualenv results; do not change harness code between languages | Save commands, JUnit, normalized outcomes, isolation level and code hashes for both example runs; trace each outcome to the contract | 🔲 |
| P1-T8 | Run final regression and prepare bilingual evidence | Full suite passes with JUnit; compare exact IDs with the accepted 691-test Phase 0 baseline. Explain every removed/changed/newly skipped test and record unresolved limits; no zero-test or interrupted run is a pass | Run Windows checks sequentially with short local runtime roots; verify report hashes and test-ID differences; document changes and results in this file | 🔲 |
| P1-T9 | User acceptance | User reviews T1–T8 evidence, intentional baseline changes and limitations, and explicitly accepts Phase 1 | Record acceptance separately and then mark Phase 1 complete in both languages and the Overview | 🔲 |

The normal-user backend provides detection after execution, not AppContainer-equivalent prevention. Its recorded isolation level must make this distinction visible. Local-network routing is verified with a local fixture; Oracle and other server DB support remain unverified. Phase 2 planning/setup and Phase 3 CLI/report redesign remain in their scheduled Phases.

## Verification & Exit Criteria

- The same contract judges the Python and Java examples. The judgement code has no language-specific branch.
- In both languages, pass, failure, zero tests, missing report, timeout, removed test and new skip each produce the correct outcome.
- The Java dependency download result on the company network is recorded. If it is blocked, the proxy or internal repository steps are written down; if that also fails, the cause and the needed action are reported.
- The AppContainer path works for a Python project that uses its own virtual environment (spec 5.1).
- Tamper detection: the harness keeps the latest record hash in memory, compares it after each command, checks its own installation manifest and reads results only from folders it created. A changed record stops the run.
- The full regression is compared with the Phase 0 baseline; changed tests are listed with reasons.
- User acceptance.

**Results**: Not started.

## Development Notes

- The Java runtime and build tool must be installed in user scope without administrator rights (for example portable distributions). P1-T1 records available versions and official distribution sources before selecting and pinning them.
- Existing `validation.py` already distinguishes empty pytest suites; this logic becomes part of the general contract. Whether `test_collection.py` (pytest observer) is replaced by JUnit judgement is decided in this Phase.
- Phase 0 code review found additional integration points: `model.validate_checks` requires pytest, `project.validate_config` calls that shared contract, `workflow.prepare` pins pytest/AppContainer, and `workflow_acceptance.final_validation` requires an AppContainer token and positive test count for every check. Adapt these with the new contract so quality commands and the normal-permission backend can reach acceptance. Keep the current Python backend and its diagnostics.
- TypeScript is not required here; npm downloads are already known to work. It is verified in Phases 2 and 4.

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created the outline from spec 12 steps 1–2. Not started. |
| 2026-10-23 | Recorded Phase 0 findings about shared registration, workflow and acceptance dependencies. Outline only; Phase 1 has not started. |
| 2026-10-23 | After Phase 0 acceptance, detailed P1-T1–T9 with work, acceptance criteria and verification. Java versions/sources remain pending the first environment task. No installation, implementation or test execution; Phase 1 not started. Separate dev-log omitted: skill unavailable. |

---

# Phase 1 — 검사 계약과 격리 `🔲 미시작`

> 어떤 언어든 테스트와 품질 검사 결과를 같은 방식으로 판정한다. AppContainer 보호를 유지하고 일반 권한 실행에서는 기록 변조를 탐지한다.

**선행 조건**: 충족 — 2026-10-23 [Phase 0](Phase0_Baseline.md) 인수([기록](Evidence/Phase0_Acceptance.json)).

**기술 구성**: 하네스는 그대로(Windows, Python 3.12.10, pytest 9.1.1, SQLite). 예제 프로젝트는 pytest를 쓰는 Python, Java. 예제는 Maven과 JUnit을 제안하며 회사 환경에 필요하면 Gradle이 대안이다. JDK·빌드 도구·테스트 도구의 정확한 버전과 배포처는 미정이며, 설치·실행 명령 확정 전에 P1-T1에서 환경 확인 후 선택한다.

**계획 상태**: Phase 0 인수 후 2026-10-23 상세화했다. 모든 구현 Task는 미시작이며 사용자 Phase 1 시작 지시에 따라 실행한다.

## 개요

기획서 12장 1–2단계다. pytest 전용 검사를 언어와 무관한 검사 계약(기획서 5장)으로 바꾸고, 격리 방식 C(기획서 5.1)를 구현한다. 위험이 가장 큰 항목이라 먼저 한다. 회사 네트워크에서 Java 패키지 다운로드가 되는지와 격리 방식을 여기서 확인한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 검사 등록: argv, 작업 폴더, 제한 시간. 하네스가 검사를 실행하고 종료 코드와 출력을 기록한다 | 🔲 |
| 2 | JUnit XML 판정: 종료 코드 0, 보고서 존재, 테스트 1개 이상, 실패·오류 0개. 이전 통과 테스트 목록과 비교. skip 규칙(기준선 skip 허용, 새 skip은 Reviewer 확인 대상으로 표시) | 🔲 |
| 3 | 품질 검사는 종료 코드로 판정. 보고서를 낼 수 없는 예외는 사용자 승인이 있을 때만 수동 확인 항목으로 전환 | 🔲 |
| 4 | 격리 방식 C: Python은 AppContainer 유지, 그 밖은 일반 사용자 권한 실행과 변조 탐지, 결과에 격리 수준 표시 | 🔲 |
| 5 | Python과 Java 예제 프로젝트, Java 패키지 다운로드 확인 결과 기록 | 🔲 |

## Task와 검증

P1-T1–T8 순서로 실행하며 T9는 별도 사용자 인수 단계다. 아래는 모두 예정 작업이다.

| Task | 작업 | 완료 기준 | 검증 방법 | 상태 |
|---|---|---|---|---|
| P1-T1 | Java 도구·회사 네트워크 확인, 예제 의존성 선택·고정 | JDK·빌드/테스트 도구의 정확한 버전과 배포처를 기록하고 관리자 권한 없이 실제 의존성을 다운로드한다. 막히면 프록시·사내 저장소 대안과 필요한 조치를 기록하며 성공으로 표시하지 않는다 | OneDrive 밖 짧은 로컬 경로에 버전 출력·다운로드 명령·종료 코드·로그 저장, 잠금/설정 파일 확인 | 🔲 |
| P1-T2 | 공통 검사 등록·결과 계약 정의 | 테스트/품질 구분, argv, cwd, 제한 시간, 보고서 위치, 격리 방식을 등록한다. `model`·`project`의 pytest 필수 가정을 제거하고 잘못된 경로·인자는 명시적으로 거부한다 | Python·Java·품질 검사 등록과 잘못된 설정의 단위 검사, 기존 저장된 등록 정보와 호환성 검토 | 🔲 |
| P1-T3 | JUnit 판정·테스트 ID 비교 일반화 | 종료 코드 0, 유효한 새 보고서, 실제 실행 테스트 1개 이상, 실패·오류 0일 때만 통과한다. 보고서 간 ID를 유지하며 삭제된 테스트·모든 새 skip을 필수 리뷰 대상으로 표시한다. 기준선 skip은 허용한다 | 중첩/복수 suite, 잘못되거나 모호한 보고서, 실패/오류, 0개/전부 skip, 기존 skip 유지, 테스트 삭제·새 skip fixture 검사. 판정에 언어별 분기 없음 확인 | 🔲 |
| P1-T4 | 두 격리 방식으로 계약 실행 | 프로젝트 가상환경 의존성을 포함한 Python AppContainer를 유지한다. 다른 런타임·로컬 네트워크 필요 검사는 일반 권한 실행을 추가한다. 방식·argv·cwd·출력·종료·시간 초과를 기록하고 AppContainer 실패 시 조용히 격리를 낮추지 않는다 | 실제 Python 가상환경·Java 자식 프로세스 실행, 시간 초과·자손 정리·격리 실패 검사, 검사별 격리 수준 기록 확인 | 🔲 |
| P1-T5 | 기록·설치본 변조 탐지 | 정당한 최신 기록 해시를 컨트롤러 메모리에 보관해 명령마다 대조한다. 설치본 매니페스트를 확인하고 새로 만든 결과 폴더에서만 보고서를 읽는다. 불일치면 후속 실행을 중단한다 | 일회용 fixture로 기록·정책/승인 데이터·설치 파일 변조, 오래된/폴더 밖 결과 거부, 정당한 컨트롤러 기록의 오탐 없음 확인 | 🔲 |
| P1-T6 | 등록·워크플로·인수를 공통 계약에 연결 | `workflow.prepare`·`workflow_acceptance.final_validation`을 수정해 품질 검사는 종료 코드, 테스트는 JUnit으로 판정한다. 보고서 누락은 미확인이고 수동 전환은 사용자 승인과 실제 확인 결과가 필요하다. 내용/버전·승인 연결을 보존한다 | 두 백엔드로 최종 검사까지 통합 검증, 근거 누락·오래된 결과·미승인 수동 전환 거부, 기존 통과 테스트 삭제·새 skip의 Reviewer 확인 근거 요구 | 🔲 |
| P1-T7 | 같은 구현으로 Python·Java 예제 검증 | 두 예제에서 통과·실패·테스트 0개·보고서 없음·시간 초과·테스트 삭제·새 skip을 확인한다. Java 실제 다운로드와 Python 가상환경 결과를 기록하고 언어를 바꿀 때 하네스 코드를 수정하지 않는다 | 예제별 명령·JUnit·공통 판정 결과·격리 수준·코드 해시 저장, 결과와 계약 조건 대조 | 🔲 |
| P1-T8 | 최종 전체 회귀·영문/국문 근거 작성 | 전체 검사가 통과하고 JUnit을 남긴다. 인수한 Phase 0의 691개 테스트와 정확한 ID를 비교한다. 삭제/변경/새 skip 이유와 남은 한계를 기록한다. 테스트 0개·중단을 통과로 표시하지 않는다 | Windows 검사는 짧은 로컬 실행 경로에서 순차 수행, 보고서 해시·테스트 ID 차이 검증, 이 문서에 변경 내용·실제 결과 기록 | 🔲 |
| P1-T9 | 사용자 인수 | 사용자가 T1–T8 근거·의도적인 기준선 변경·한계를 검토하고 Phase 1을 명시적으로 인수한다 | 별도 인수 기록 후 양쪽 언어와 Overview의 Phase 1을 완료 처리 | 🔲 |

일반 권한 백엔드는 실행 후 탐지이며 AppContainer와 같은 사전 차단이 아니다. 기록된 격리 수준에서 이를 구분해야 한다. 로컬 네트워크 경로는 로컬 fixture로 검증하며 Oracle 등 서버 DB 지원은 미검증으로 남긴다. Phase 2 계획/세팅과 Phase 3 CLI/보고서 재설계는 해당 Phase 범위를 유지한다.

## 검증 및 종료 조건

- 같은 검사 계약으로 Python과 Java 예제를 판정한다. 판정 코드에 언어별 분기가 없다.
- 두 언어 모두에서 통과, 실패, 테스트 0개, 보고서 없음, 시간 초과, 테스트 삭제, 새 skip이 각각 올바른 결과로 나온다.
- 회사 네트워크에서 Java 의존성 다운로드 결과를 기록한다. 막혀 있으면 프록시나 사내 저장소 설정 절차를 적고, 그래도 안 되면 원인과 필요한 조치를 보고한다.
- 프로젝트 자체 가상환경을 쓰는 Python 프로젝트에서도 AppContainer 경로가 동작한다(기획서 5.1).
- 변조 탐지: 하네스는 실행 기록의 최신 해시를 메모리에 두고 명령마다 대조하며, 자기 설치본 매니페스트를 확인하고, 자기가 만든 폴더에서만 결과를 읽는다. 기록이 바뀌면 중단한다.
- 전체 회귀 검사를 Phase 0 기준선과 비교하고, 바뀐 테스트는 이유와 함께 적는다.
- 사용자 인수.

**결과**: 미시작.

## 개발 시 주의사항

- Java 런타임과 빌드 도구는 관리자 권한 없이 사용자 범위에 설치해야 한다(예: 포터블 배포판). P1-T1에서 사용 가능한 버전과 공식 배포처를 확인한 뒤 선택·고정한다.
- 기존 `validation.py`는 테스트가 없는 pytest 실행을 이미 구분한다. 이 판정은 일반 검사 계약의 일부가 된다. `test_collection.py`(pytest 관찰기)를 JUnit 판정으로 대체할지는 이 Phase에서 정한다.
- Phase 0 코드 대조에서 추가 연결 지점을 확인했다. `model.validate_checks`는 pytest를 필수로 요구하고 `project.validate_config`가 이 계약을 사용한다. `workflow.prepare`는 pytest·AppContainer에 고정되고 `workflow_acceptance.final_validation`은 모든 검사에 AppContainer 토큰·양수 테스트 수를 요구한다. 품질 명령과 일반 권한 백엔드도 인수까지 연결되도록 새 계약과 함께 수정한다. 기존 Python 백엔드와 진단은 유지한다.
- TypeScript는 이 Phase에서 필요하지 않다. npm 다운로드는 동작이 확인돼 있으며, Phase 2와 4에서 검증한다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | 기획서 12장 1–2단계로 개요를 작성했다. 미시작. |
| 2026-10-23 | Phase 0에서 확인한 공용 등록·워크플로·인수 의존성을 기록했다. 개요만 보완했으며 Phase 1은 미시작이다. |
| 2026-10-23 | Phase 0 인수 후 P1-T1–T9의 작업·완료 기준·검증 방법을 상세화했다. Java 버전·배포처는 첫 환경 확인 Task에서 선택할 미정 사항이다. 설치·구현·검사 실행 없이 Phase 1 미시작을 유지한다. dev-log 스킬이 없어 별도 로그는 생략했다. |
