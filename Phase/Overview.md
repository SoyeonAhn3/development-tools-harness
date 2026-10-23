# Development Phases — Language-Independent Harness

**Revision**: 1.2 · **Date**: 2026-10-23 · **Status**: Specification 1.10 finalized. Phase 0 completed and accepted on 2026-10-23: environment verified, 691 regressions passed with identical test IDs and no skips, baseline and 41-module map accepted. Phase 1 is detailed into Tasks and has not started.

## Goal & Decisions

Build the first version described in the [specification 1.10](../Draft/ai-development-harness-plan-v1.md): a harness that reads a completed development specification, splits it into Phases starting with Phase 0 (environment), sets up the stated language and tools when the user says start, develops and tests, presents the deliverables, and marks the Phase complete when the user accepts. Its purpose is to reduce duplicate, wrong and low-quality code. The harness holds no language knowledge and judges only through common protocols: exit codes, JUnit XML reports and file hashes.

- **Decided**: continue in this repository and reuse the existing code (spec 11, F1). The harness itself is developed with existing AI coding tools (Claude Code, Codex), not with the harness (spec 11, Q4).
- **Decided**: the Phases follow the seven development steps of spec 12 and are numbered from 0 (spec 14.1, G1).
- **Decided**: harness environment is Windows without administrator rights, Python 3.12.10, pytest 9.1.1, psutil 7.2.2 and SQLite. Versions are recorded in `.python-version` and `requirements-dev.lock`. Codex CLI is the only AI tool in the first version.
- **Decided**: verification languages are Python, TypeScript and Java. Only SQLite is verified; server DBs remain an "unverified" limitation (spec 10.3).
- **Decided**: every Phase document has complete English and Korean sections. Only the current Phase is detailed into Tasks; the next Phase is detailed after the previous one is accepted.

## Phase Plan

| Phase | Goal & Main Deliverables | Prerequisite | Exit Condition |
|---|---|---|---|
| [0 — Baseline](Phase0_Baseline.md) ✅ | Check the current repository's environment and full regression, record a passing-test baseline and confirm the module reuse map. Check-only form: no installation, code change or AI call | Specification 1.10 finalized | Baseline recorded with zero failing tests, module map confirmed, user acceptance |
| [1 — Validation Contract & Isolation](Phase1_ValidationContract.md) 🔲 | Spec 12 steps 1–2: language-independent check contract (argv, JUnit judgement, test-list comparison, skip rules) and isolation option C (AppContainer for Python, normal permissions plus tamper detection otherwise, isolation level in results). Includes the Java package download check | Phase 0 accepted | Python and Java examples judged by the same contract without language-specific harness code; Java download result recorded; tamper detection stops on mismatch; user acceptance |
| [2 — Planning & Environment Setup](Phase2_PlanningAndSetup.md) 🔲 | Spec 12 steps 3–4: plans that include Phase 0, technology and version proposals, version pinning, bilingual `Phase/` documents, and Phase 0 execution with approved commands, manual administrator steps and the three Phase 0 forms | Phase 1 accepted | From a specification alone, Phase documents including Phase 0 are generated; a new project is set up and passes the contract; a ready project finishes check-only with a baseline; user acceptance |
| [3 — Workflow & Quality](Phase3_WorkflowAndQuality.md) 🔲 | Spec 12 steps 5–6: AI permissions (spec 7.1), quality devices (spec 6), results report (spec 8.1), acceptance that marks Phase documents complete, and the simplified CLI | Phase 2 accepted | Every spec 6 device leaves evidence in review and report; weakening is blocked; a report is produced even on failure; acceptance marks the Phase document complete; user acceptance |
| [4 — Real-World Validation](Phase4_RealWorldValidation.md) 🔲 | Spec 12 step 7: Decision Desk Phase 1 (new project, TypeScript and SQLite), one existing Python project and one mock Java project (spec 13.1) | Phase 3 accepted | Every spec 13 criterion has evidence; the three examples are accepted without changing harness code; user acceptance of the first version |

No development dates or effort estimates are committed.

## Requirements Mapping

| Specification | Planned Coverage | Verification Evidence |
|---|---|---|
| 2, 2.1, 2.2: basic flow, user decision points, commands | Phase 2 (plan, start of Phase 0), Phase 3 (start of development Phases, accept, simplified CLI) | Separate start and acceptance of Phase 0 and development Phases; no execution before start |
| 3: specification input, Phase rules, Phase documents | Phase 2; completion marking in Phase 3 | Generated bilingual documents; technology proposal with alternatives; "complete" only after acceptance |
| 4: Phase 0, version selection, pinning, three forms | Phase 2; lock-file review in Phase 3 | Approved-command execution, manual-step resume, check-only run, lock files registered |
| 5: check contract | Phase 1 | Pass, failure, zero-test, missing-report and removed-test cases in Python and Java |
| 5.1: isolation option C | Phase 1 | AppContainer path kept for Python; tamper detection stops on a changed record; isolation level shown |
| 6.1–6.5: quality devices, baseline comparison | Phase 3; test and quality-violation baselines in Phase 2, duplicate and suppression-comment baselines with their detectors in Phase 3 | Exact-copy duplicate report, quality checks, Reviewer table, config-change classification, suppression-comment report, new-problems-only blocking |
| 7, 7.1–7.3: execution and AI permissions | Phase 3 (reusing sequential execution, bounded correction and final validation) | Whole-project read with secret exclusion, file scope stops, check-request limit, final checks on final code |
| 8: results report and acceptance | Phase 3 | Bilingual report including failures; blocked acceptance when mandatory evidence is missing |
| 9: state, records, resume | Reused; regression in every Phase | Existing regression tests from the Phase 0 baseline |
| 10.3: Windows without administrator rights, Codex CLI, SQLite | All Phases | No administrator operation; runtime records outside OneDrive |
| 10.3, I1: tool-independent AI boundary, Codex module and Claude Code fit assessment | Phase 3 | Request/response, enforceable permissions and structured output assessed; company-login or documentation-only limits recorded; full Claude Code module deferred until first-version acceptance |
| 11: relation to current implementation | Phase 0 (module map), applied in Phases 1–3 | Confirmed map; changes recorded per Phase |
| 13, 13.1: completion criteria and examples | Phase 4 | Criterion-to-evidence table and three accepted examples |

## Shared Completion Rules

1. The harness is developed with existing AI coding tools in this repository. Phase documents record what was actually done and verified.
2. In every Phase, run the full regression on the final code and record actual counts with a JUnit XML report. Failed, interrupted, missing or zero-test outcomes never count as passed.
3. Compare with the Phase 0 baseline. A previously passing test that disappears, fails or becomes skipped must be explained. Tests that change because behavior intentionally changes (for example CLI simplification) are listed with the reason and approved by the user.
4. Technical completion and user acceptance are separate. A Phase is marked ✅ only after the user's explicit acceptance is recorded.
5. Keep runtime databases and logs outside OneDrive. Do not perform administrator operations. Git writes and deployment are manual; nothing is committed unless the user asks.
6. Run large Windows verifications sequentially; concurrent runs caused an ACL-grant timeout in the previous Phase 3.
7. Update the English and Korean sections together.

## Previous Phase Set

The earlier Phase set built on lean MVP 0.4 is archived in [archive/lean-mvp-0.4](archive/lean-mvp-0.4/Overview.md). Its Phases 1–3 were accepted on 2026-09-18, 2026-09-21 and 2026-10-07, and that code is the starting point here. Its Phase 4 (self-development) was cancelled on 2026-10-23 because the product direction changed. Evidence and generated files in the archive are unchanged so that their recorded hashes still match. The 0.4 specification is in [Draft/archive](../Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md).

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created the new Phase set (Phase 0–4) from specification 1.9 after archiving the lean MVP 0.4 Phases. Phase 0 detailed; Phases 1–4 at goal and exit-criteria level. No implementation, test run or acceptance. Separate dev-log omitted because the skill is unavailable. |
| 2026-10-23 | Phase 0 technical verification: 691 passed, no failures/errors/skips; exact historical test-ID set retained. Baseline and 41-module review recorded with Codex 0.155.1 selected only for regression (default 0.163.0 unverified). Synchronized I1 and Phase 1/3 integration notes. User review/acceptance pending; no source/test changes or Phase 1 start. |
| 2026-10-23 | User accepted Phase 0 results and the module map; see the [acceptance record](Evidence/Phase0_Acceptance.json). Phase 0 marked complete; Phase 1 detailed into P1-T1–T9 and remains not started. Evidence unchanged; no new test run. Separate dev-log omitted: skill unavailable. |

---

# 개발 Phase — 언어에 묶이지 않는 하네스

**문서 버전**: 1.2 · **작성일**: 2026-10-23 · **상태**: 기획서 1.10 확정. 2026-10-23 Phase 0 완료·인수: 환경 확인, 동일 테스트 ID의 전체 회귀 691개 통과·skip 0, 기준선·41개 모듈 대응표 인수. Phase 1은 Task를 상세화했으며 미시작이다.

## 목표와 결정 사항

[기획서 1.10](../Draft/ai-development-harness-plan-v1.md)의 첫 버전을 만든다. 완성된 개발 기획서를 읽어 Phase 0(환경 준비)부터 Phase를 나누고, 사용자가 시작을 지시하면 기획서에 적힌 언어·도구로 환경을 세팅하고 개발·테스트를 진행한다. 끝나면 산출물을 안내하고, 사용자가 인수하면 Phase를 완료 처리한다. 목적은 중복 코드, 잘못된 코드, 낮은 품질의 코드를 줄이는 것이다. 하네스는 언어 지식을 갖지 않고 공통 규약(종료 코드, JUnit XML 보고서, 파일 해시)으로만 판단한다.

- **확정**: 지금 저장소에서 기존 코드를 재사용해 이어서 수정한다(기획서 11장, F1). 하네스 자체는 하네스가 아니라 기존 AI 코딩 도구(Claude Code, Codex)로 개발한다(기획서 11장, Q4).
- **확정**: Phase는 기획서 12장의 개발 7단계를 따르고 0번부터 번호를 매긴다(기획서 14.1, G1).
- **확정**: 하네스 실행 환경은 관리자 권한 없는 Windows, Python 3.12.10, pytest 9.1.1, psutil 7.2.2, SQLite다. 버전은 `.python-version`과 `requirements-dev.lock`에 기록돼 있다. 첫 버전의 AI 도구는 Codex CLI 하나다.
- **확정**: 검증 언어는 Python, TypeScript, Java다. DB는 SQLite만 검증하고 서버 DB는 "미검증" 한계로 남긴다(기획서 10.3).
- **확정**: 모든 Phase 문서는 영문과 국문을 모두 쓴다. 현재 Phase만 Task로 상세화하고, 다음 Phase는 이전 Phase를 인수한 뒤 상세화한다.

## 전체 Phase 계획

| Phase | 목표와 주요 산출물 | 선행 조건 | 종료 조건 |
|---|---|---|---|
| [0 — 기준선 확인](Phase0_Baseline.md) ✅ | 현재 저장소의 환경과 전체 회귀 검사를 확인하고, 통과 테스트 기준선을 기록하고, 모듈 재사용 대응표를 확정한다. "확인만" 형태로 설치·코드 변경·AI 호출이 없다 | 기획서 1.10 확정 | 실패 테스트 0개로 기준선 기록, 모듈 대응표 확정, 사용자 인수 |
| [1 — 검사 계약과 격리](Phase1_ValidationContract.md) 🔲 | 기획서 12장 1–2단계: 언어와 무관한 검사 계약(argv, JUnit 판정, 테스트 목록 비교, skip 규칙)과 격리 방식 C(Python은 AppContainer, 그 밖은 일반 권한과 변조 탐지, 결과에 격리 수준 표시). Java 패키지 다운로드 확인 포함 | Phase 0 인수 | Python과 Java 예제를 언어별 하네스 코드 없이 같은 계약으로 판정, Java 다운로드 결과 기록, 변조 탐지 시 중단, 사용자 인수 |
| [2 — 계획 확장과 환경 세팅](Phase2_PlanningAndSetup.md) 🔲 | 기획서 12장 3–4단계: Phase 0을 포함한 계획, 기술 구성·버전 제안, 버전 고정, 영문·국문 `Phase/` 문서 생성, 승인된 명령과 관리자 작업 수동 안내·재개, Phase 0 세 형태 실행 | Phase 1 인수 | 기획서만으로 Phase 0을 포함한 Phase 문서 생성, 신규 프로젝트 세팅 후 검사 계약 충족, 준비된 프로젝트는 확인만으로 기준선 기록, 사용자 인수 |
| [3 — 개발 흐름과 품질 장치](Phase3_WorkflowAndQuality.md) 🔲 | 기획서 12장 5–6단계: AI 권한(7.1), 품질 장치(6장), 결과 보고서(8.1), 인수 시 Phase 문서 완료 처리, CLI 단순화 | Phase 2 인수 | 6장 장치마다 리뷰와 보고서에 근거가 남음, 기준 완화 차단, 실패해도 보고서 생성, 인수 시 Phase 문서 완료 처리, 사용자 인수 |
| [4 — 실사용 검증](Phase4_RealWorldValidation.md) 🔲 | 기획서 12장 7단계: Decision Desk Phase 1(신규, TypeScript와 SQLite), 기존 Python 프로젝트 1개, 모의 Java 프로젝트 1개(기획서 13.1) | Phase 3 인수 | 13장 완료 기준마다 근거 확보, 세 예제를 하네스 코드 수정 없이 인수, 첫 버전 사용자 인수 |

개발 일정과 소요 시간은 정하지 않았다.

## 요구사항 대응표

| 기획서 | 처리 계획 | 확인할 근거 |
|---|---|---|
| 2, 2.1, 2.2: 기본 흐름, 사용자 결정 지점, 명령 | Phase 2(계획, Phase 0 시작), Phase 3(개발 Phase 시작, 인수, CLI 단순화) | Phase 0과 개발 Phase의 별도 시작·인수, 시작 전에는 실행하지 않음 |
| 3: 기획서 입력, Phase 구성 규칙, Phase 문서 | Phase 2, 완료 처리는 Phase 3 | 생성된 영문·국문 문서, 대안을 포함한 기술 구성 제안, 인수 후에만 완료 표시 |
| 4: Phase 0, 버전 선택, 버전 고정, 세 형태 | Phase 2, 잠금 파일 리뷰는 Phase 3 | 승인된 명령 실행, 수동 단계 후 재개, 확인만 형태 실행, 잠금 파일 등록 |
| 5: 검사 계약 | Phase 1 | Python과 Java에서 통과·실패·테스트 0개·보고서 없음·테스트 삭제 경우 |
| 5.1: 격리 방식 C | Phase 1 | Python AppContainer 경로 유지, 기록 변조 시 중단, 격리 수준 표시 |
| 6.1–6.5: 품질 장치, 기준선 비교 | Phase 3. 테스트와 품질 위반 기준선은 Phase 2, 중복과 검사 회피 주석 기준선은 탐지기와 함께 Phase 3 | 그대로 복사한 중복 보고, 품질 검사, Reviewer 기준표, 설정 변경 분류, 검사 회피 주석 보고, 새로 생긴 문제만 차단 |
| 7, 7.1–7.3: 개발 실행과 AI 권한 | Phase 3(기존 순차 실행·제한된 수정·통합 검증 재사용) | 비밀값 제외를 포함한 전체 읽기, 파일 범위 밖 변경 시 중단, 검사 요청 한도, 최종 코드에서 전체 검사 |
| 8: 결과 보고서와 인수 | Phase 3 | 실패를 포함한 영문·국문 보고서, 필수 근거가 없으면 인수 차단 |
| 9: 상태·기록·재개 | 재사용, 모든 Phase에서 회귀 검사 | Phase 0 기준선의 기존 회귀 검사 |
| 10.3: 관리자 권한 없는 Windows, Codex CLI, SQLite | 모든 Phase | 관리자 작업 없음, 실행 기록은 OneDrive 밖 |
| 10.3, I1: 도구 공통 AI 경계, Codex 모듈, Claude Code 적합성 확인 | Phase 3 | 요청·응답·실제 권한 제한·구조화 출력 확인, 회사 로그인 또는 문서 확인만 한 한계 기록. Claude Code 정식 모듈은 첫 버전 인수 후 |
| 11: 현재 구현과의 관계 | Phase 0(모듈 대응표), Phase 1–3에서 적용 | 확정한 대응표, Phase별 변경 기록 |
| 13, 13.1: 완료 기준과 예제 | Phase 4 | 기준별 근거 대조표, 인수한 예제 3건 |

## 공통 완료 규칙

1. 하네스는 이 저장소에서 기존 AI 코딩 도구로 개발한다. Phase 문서에는 실제로 수행하고 검증한 내용만 적는다.
2. 모든 Phase에서 최종 코드로 전체 회귀 검사를 실행하고, JUnit XML 보고서로 실제 개수를 기록한다. 실패·중단·미실행·테스트 0개는 통과로 치지 않는다.
3. Phase 0 기준선과 비교한다. 통과하던 테스트가 사라지거나 실패하거나 skip으로 바뀌면 이유를 밝힌다. 동작을 의도적으로 바꿔서(예: CLI 단순화) 바뀌는 테스트는 이유와 함께 목록으로 적고 사용자 승인을 받는다.
4. 기술적 완료와 사용자 인수는 구분한다. 사용자의 명시적 인수를 기록한 뒤에만 ✅로 표시한다.
5. 실행 DB와 로그는 OneDrive 밖에 둔다. 관리자 권한 작업은 하지 않는다. Git 쓰기와 배포는 수동이며, 사용자가 요청하기 전에는 커밋하지 않는다.
6. 큰 Windows 검증은 순서대로 실행한다. 이전 Phase 3에서 동시 실행으로 권한 설정 시간 초과가 발생했다.
7. 영문과 국문을 함께 갱신한다.

## 이전 Phase 묶음

축소 MVP 0.4 기준의 이전 Phase 묶음은 [archive/lean-mvp-0.4](archive/lean-mvp-0.4/Overview.md)에 보관했다. 그중 Phase 1–3은 2026-09-18, 2026-09-21, 2026-10-07에 인수했으며, 그 코드가 이번 개발의 출발점이다. Phase 4(자체 개발)는 제품 방향이 바뀌어 2026-10-23에 취소했다. 보관 폴더의 Evidence와 Generated 파일은 기록된 해시가 계속 맞도록 수정하지 않았다. 0.4 기획서는 [Draft/archive](../Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md)에 있다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | 축소 MVP 0.4 Phase를 보관한 뒤 기획서 1.9를 기준으로 새 Phase 묶음(Phase 0–4)을 작성했다. Phase 0은 상세화하고 Phase 1–4는 목표와 종료 조건 수준으로 적었다. 구현·검사 실행·인수는 없다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-10-23 | Phase 0 기술 검증: 691개 통과, 실패·오류·skip 0, 이전 테스트 ID 집합 유지. 회귀 검사에만 Codex 0.155.1을 지정해 기준선·41개 모듈 검토 기록(기본 0.163.0은 미검증). I1·Phase 1/3 연결 주의사항 반영. 사용자 검토·인수 대기이며 소스·테스트 변경이나 Phase 1 시작은 없다. |
| 2026-10-23 | 사용자가 Phase 0 결과와 모듈 대응표를 인수했다([인수 기록](Evidence/Phase0_Acceptance.json)). Phase 0 완료, Phase 1은 P1-T1–T9로 상세화했으며 미시작이다. 검증 근거 변경·검사 재실행은 없다. dev-log 스킬이 없어 별도 로그는 생략했다. |
