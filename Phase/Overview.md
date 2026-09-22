# Development Phases — Lean MVP

**Revision**: 0.4 · **Date**: 2026-09-22 · **Status**: Phases 1–2 accepted and completed. Phase 3 in progress: P3-T1–T6 implemented, including minimum results, feedback and acceptance gates. Historical T4/T5 live evidence is preserved; T6 makes no new AI calls. P3-T7–T8 and Phase 4 implementation not started; Phase 3 acceptance remains pending. Current verification is recorded in [Phase 3](Phase3_Workflow.md).

## Goal & Decisions

Build the P0 local CLI described in the [lean MVP plan 0.4](../Draft/ai-development-harness-lean-mvp-plan.md). Follow its section 10 implementation order. P0 is a priority label; Phase numbers below are development stages.

- **Decided**: Windows/Python 3.12.10 + pytest 9.1.1 for harness development; SQLite for execution state, psutil 7.2.2 for process identity. Versions are recorded in `.python-version` and `requirements-dev.lock`. Phase documents contain complete English and Korean sections.
- **Proposed**: use Python + pytest for the separate real validation examples as well. The Phase 1 fake-Adapter fixture already uses this configuration.
- **Selected Adapter**: Codex CLI with ChatGPT authentication, reviewed versions 0.154.0 and 0.155.1. Planner, Developer and separate Reviewer reuse the verified text-only boundary. P3-T2 tests run in standard-user AppContainer on read-only copies. P3-T3 binds execution authorization and evidence to the approved plan, code and policy.
- **Accepted foundation/planning**: Phase 1 foundation and Phase 2 registration, actual baseline checks, real Planner, bilingual versioned plans, diagnostics and planning approval are implemented. Phase 2 acceptance covered 172 passing tests, including project phase-doc loading, template rendering, pinned rules and package resources. Planning-only use on a harness snapshot produced the [reviewed Phase 3 draft](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan.md) with one actual AI call and recorded manual corrections. The user accepted Phase 2 on 2026-09-21.
- **Phase 3 preparation**: P3-T1 added an execution contract, a two-test CLI fixture and synthetic `workflow-doctor`; 187 tests passed at that stage. Unelevated Codex allowed six raw loopback TCP connections, motivating the AppContainer alternative. [Historical evidence](Evidence/Phase3_Preparation.json).
- **Administrator-free workers**: Company policy excludes administrator setup. AppContainer synthetic probes passed with 206 tests at the candidate stage. P3-T2 added real Developer/Reviewer sessions, controller-checked patches and isolated pytest: **265 tests passed**, plus a two-call live example with eight generated-project tests and five independent checks. [Candidate evidence](Evidence/Phase3_AppContainer.json), [T2 evidence](Evidence/Phase3_Workers.json).
- **Execution admission and records (2026-09-22)**: P3-T3 implements separate `workflow-prepare`/`workflow-approve`/`workflow-status`/`workflow-cancel` commands and durable attempts, waits and evidence-linked findings. Stable SQLite transitions prevent duplicate replay; unknown measurements remain `null`. Admission does not dispatch work. All 378 tests and `pip check` passed, including 113 added cases. Local subprocess and AppContainer checks used zero live AI calls. [T3 evidence](Evidence/Phase3_Records.json).
- **Sequential execution (2026-09-22)**: P3-T4 adds `workflow-run`, a shared per-Task correction limit, explicit independent follow-up assessments and all registered checks on final content. The initial authorization remains pinned while checked patches establish the current code. A disposable two-Task example reached `technically_complete` with four distinct actual role sessions, eight passing tests in each Task/final run and six independent checks. No Planner service call or user result acceptance is claimed. T4 can continue from clean recorded boundaries; explicit interruption recovery is supplied by T5 below. Results/acceptance and runner A remain T6–T8. [T4 evidence](Evidence/Phase3_Execution.json).
- **Explicit recovery (2026-09-22)**: P3-T5 adds advisory recovery status and `workflow-resume`. It reuses artifact-verified responses, retries proven unsent requests, blocks uncertain calls without complete evidence, repairs only files matching approved before/after content and reruns interrupted validation after process-tree checks. Original attempts stay immutable; separate recovery facts drive effective call/usage totals. Same approval and correction counts survive. Named Job inspection and shared project ownership protect against surviving descendants or alternate-state-directory bypass. Final regression/live results are recorded in [Phase 3](Phase3_Workflow.md) and [T5 evidence](Evidence/Phase3_Recovery.json); Phase acceptance remains pending.
- **Results, feedback and acceptance (2026-09-22)**: P3-T6 adds read-only `workflow-report` JSON with delivered files, current validation/reuse evidence, unresolved items, manual procedures and actual record paths. Original feedback and routing history distinguish same-scope corrections from fresh planning for changed requirements. Defects retain approval and the existing correction budget; completed later Tasks are revalidated/reviewed. Every current reused requirement, including those without a Task, needs actual final-check IDs plus a user explanation; required manual checks are fixed before execution approval. Missing, stale or failed mandatory evidence blocks explicit `workflow-accept`. The gate requires the new approved policy and sealed final artifacts; legacy T4/T5 results remain historical, with a new approved workflow required for acceptance. Technical completion and user acceptance remain separate. [T6 evidence](Evidence/Phase3_Results.json); final verification is recorded in Phase 3. T7–T8 remain pending, and the T5 example's two calls are historical rather than new T6 calls.
- **Development method**: use existing coding tools for the initial foundation, then progressively use the harness. Refine these Phase documents during development; keep the `phase-doc` skill and template stable unless a necessary correction is demonstrated.

## Phase Plan

| Phase | Goal & Main Deliverables | Prerequisite | Exit Condition |
|---|---|---|---|
| [1 — Foundation](Phase1_Foundation.md) ✅ | Python/test setup, SQLite state, versioned approvals, fake Adapter, validation runner, ownership and resume | Review the overall plan and Phase 1 scope | Met: 63 tests passed and the user accepted the foundation on 2026-09-18 |
| [2 — Planning](Phase2_Planning.md) ✅ | Real Planner, permission/I/O checks, project registration, baseline, plans and code/requirements mapping | Phase 1 accepted; AI tool selected | Met: 172 tests and live planning verified, including project phase-doc integration; user accepted on 2026-09-21 |
| [3 — Workflow](Phase3_Workflow.md) 🚧 | Eight Tasks: Developer → validation → separate Reviewer, corrections, records, resume, results and runner A. P3-T1–T6 implemented; T7–T8 pending | Phase 2 accepted; verified worker boundaries and version-bound execution admission | A separate example completes a small Phase including interruption/resume; runner A is verified and frozen |
| [4 — Dogfooding](Phase4_Dogfooding.md) | One small P0 self-development Phase, final report summaries, new/existing project acceptance and regressions | Phase 3 accepted; A/B isolation verified | Self-development is accepted and all MVP section 11 criteria have evidence |

Phases 1–2 are completed; Phase 3 has an authorized eight-Task plan with 18 requirements and implemented P3-T1–T6 preparation, roles, records, sequential execution, explicit recovery, minimum results and acceptance gates. Workflow records advertise execution capability, while explicit execution approval remains required. Technical completion is separate from Phase 3 user acceptance. Phase 4 remains an outline to refine using actual Phase 3 results. No development dates or effort estimates are committed.

## Requirements Mapping

| Source Requirement | Planned Coverage | Verification Evidence |
|---|---|---|
| §2, §4: prepared project, initialization and baseline | Phases 1–2 | Path/tool/command checks; actual passing, failing and zero-test examples |
| §5: plans, requirement coverage, code/reuse investigation | Phase 2; acceptance checks in Phases 3–4 | Plan inspection against specification/code; actual final checks for reused requirements |
| §6: sequential implementation, validation, separate review and bounded correction | Phases 1 and 3 | Fake failure scenarios followed by real small-Phase execution |
| §7: versioned approval, feedback, permissions and manual Git | Phases 1–3; final regression in Phase 4 | Approval invalidation, same-scope correction versus scope change, denied-operation checks |
| §8: SQLite, ownership, baseline preservation and resume | Phase 1; real-process integration in Phases 2–3 | Competing processes, interruption, file mismatch and metadata-only Git change scenarios |
| §8.1: AI calls, timing, review findings and resolution evidence | Minimal actual-call records in Phase 2; complete records in Phase 3; summaries in Phase 4 | Records checked for retries, interruptions and duplicate findings/calls |
| §9: reports, reused-function checks and user acceptance | Minimum in Phase 3; complete in Phase 4 | Final code/plan-linked evidence; failed and unverified mandatory conditions block completion |
| §10–11: isolated dogfooding, new/existing examples and MVP acceptance | Phases 3–4 | Frozen runner version, self-development report, two accepted external example Phases and core regressions |

P1 specification review and distributed templates, MVP2 standalone requests, and other P2 features are excluded. Developer fixtures are test assets, not the P1 template product.

## Dogfooding & Shared Completion Rules

1. These first documents are created using the skill with existing coding tools. This is preparation, not completed harness dogfooding.
2. Once Phase 2 produces plans, use its output when reviewing the next harness Phase. Record manual corrections; this only exercises planning.
3. Phase 3 must first prove the full flow in a separate example, including stop/resume. Freeze runner A outside the editable development target B, with separate protected runtime records.
4. In Phase 4, A develops a small remaining P0 feature in B. The initial candidate is the per-role AI-call summary in the results report. Record events and show minimum results before then; reserve only the report enhancement for this self-development exercise.
5. Validate B separately with preserved core regressions; the user accepts it and manually chooses it for a subsequent run. Never replace A during an active run.

For every implementation Phase, required checks must run on the final code and match the approved plan. Record failed, interrupted, missing and zero-test outcomes accurately. User acceptance is separate from technical completion; neither a document update nor an approval can turn missing evidence into a pass. Reused mandatory functionality also needs final verification.

Preserve pre-existing changes, stop on unexpected file differences, and keep runtime DB/logs outside OneDrive. Actual permissions must prevent workers and tests from modifying the running policies or approval DB; a different folder alone is insufficient. Git writes, deployment and UI checks remain manual. Significant scope/risk changes follow the specification's approval rules; unchanged approved work does not require repeated approval.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created four development Phases from lean MVP 0.4 and the agreed Python + pytest choice. No implementation or product verification performed. |
| 2026-09-15 | Phase 1 authorized and implemented; 43 tests passed. Recorded concrete environment and remaining acceptance/real-integration boundaries. |
| 2026-09-18 | Fixed Phase 1 review findings R1–R3 and verified 63 tests. User acceptance remains pending. |
| 2026-09-18 | User explicitly accepted Phase 1, including review fixes. Marked Phase 1 completed; Phases 2–4 remain not started. |
| 2026-09-21 | Synchronized Phase 2 implementation/compatibility and successful planning-only dogfooding: 156 tests, one Planner call, reviewed Phase 3 draft and manual corrections. Phase 2 user acceptance and Phase 3 worker isolation remain pending. |
| 2026-09-21 | Added authorized project phase-doc integration: pinned skill/template rules, bilingual Phase documents and wheel resources. All 172 tests and one small live example passed; earlier planning evidence remains unchanged. |
| 2026-09-21 | User explicitly accepted Phase 2 with “phase2 인수”, including Tasks 2.1–2.7, P2-01 and compatibility improvements. Marked Phase 2 completed; Phases 3–4 implementation remains not started. Generated-plan approvals are separate from this development acceptance. |
| 2026-09-21 | User authorized Phase 3. Completed P3-T1 contract/example preparation and synthetic worker investigation; 187 tests passed. Recorded the unelevated network-denial failure and preserved the P3-T2 live-execution gate. Phase 4 remains unstarted. |
| 2026-09-21 | Excluded administrator setup under company policy. Added and verified the standard-user AppContainer diagnostic; 206 tests passed. Preserved existing project/Run/events and the live-admission gate; documented the remaining adapter/isolated-validation integration. |
| 2026-09-21 | Verified P3-T2 real Developer/Reviewer, controlled patches and isolated pytest: 265 tests and a two-call live example passed. P3-T3–T8 and Phase acceptance remain pending. |
| 2026-09-22 | Implemented and verified P3-T3 version-bound execution admission and durable records with zero live AI calls. All 378 tests and pip check passed. Planning approval remains planning-only, automatic execution/recovery remain disabled, and P3-T4–T8 are next. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Implemented P3-T4 sequential execution, bounded corrections, explicit review assessments and final checks; verified a four-call live example with two Tasks. Current regression evidence is linked from Phase 3. T5–T8 and Phase acceptance remain pending. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Added P3-T5 explicit interruption recovery, artifact-proven reuse, checked partial repair, process/ownership guards and immutable attempt history with separate recovery facts. Current verification is linked from Phase 3; T6–T8 and Phase acceptance remain pending. Updated both languages and README. Separate dev-log omitted because the skill is unavailable. |
| 2026-09-22 | Added P3-T6 minimum JSON reports, preserved feedback routes, final reuse/manual evidence and explicit acceptance gates. Kept historical T1–T5 evidence and zero new T6 AI calls distinct. Updated both languages and README; T7–T8 and Phase acceptance remain pending. Separate dev-log omitted because the skill is unavailable. |

---

# 개발 Phase — 축소 MVP

**문서 버전**: 0.4 · **작성일**: 2026-09-22 · **상태**: Phase 1–2 인수·완료. Phase 3 진행 중: 최소 결과·피드백·인수 조건을 포함한 P3-T1–T6 구현. T4·T5 실제 호출 근거는 과거 이력으로 보존하고 T6의 새 AI 호출은 없다. P3-T7–T8·Phase 4 구현 미시작이며 Phase 3 인수는 대기 중이다. 현재 검증 결과는 [Phase 3](Phase3_Workflow.md)에 기록한다.

## 목표와 결정 사항

[축소 MVP 계획서 0.4](../Draft/ai-development-harness-lean-mvp-plan.md)의 P0 로컬 CLI를 개발한다. 기획서 10장의 구현 순서를 따른다. P0는 우선순위이며 아래 Phase 번호는 개발 단계다.

- **확정**: 하네스 개발은 Windows/Python 3.12.10 + pytest 9.1.1, 실행 상태는 SQLite, 프로세스 식별은 psutil 7.2.2를 사용한다. 버전은 `.python-version`과 `requirements-dev.lock`에 기록했다. Phase 문서는 영문·국문 전체 내용을 함께 작성한다.
- **제안**: 별도 실제 검증 예제도 Python + pytest로 통일한다. Phase 1 가짜 Adapter 예제는 이미 이 구성을 사용한다.
- **선정 Adapter**: ChatGPT 인증의 Codex CLI이며 검토된 버전은 0.154.0·0.155.1이다. Planner·Developer·별도 Reviewer가 검증된 텍스트 전용 경계를 재사용한다. P3-T2 테스트는 일반 사용자 AppContainer의 읽기 전용 복사본에서 실행한다. P3-T3는 실행 승인·근거를 승인한 계획·코드·정책에 연결한다.
- **인수한 기반·계획 기능**: Phase 1 기반과 Phase 2 등록·실제 기본 검사·실제 Planner·영문 및 국문 버전별 계획·진단·계획 승인을 구현했다. Phase 2 인수에는 프로젝트 phase-doc 읽기·템플릿 출력·규칙 고정·설치 리소스를 포함한 검사 172개 통과가 반영됐다. 하네스 복사본에서 실제 AI 호출 1회로 [검토용 Phase 3 초안](Generated/45e4c4397c42468e87d9dad81d7b9ce9/v2/Plan_ko.md)을 만들고 수동 보완을 기록했다. 2026-09-21 Phase 2 사용자 인수를 완료했다.
- **Phase 3 준비**: P3-T1 실행 계약·기본 검사 2개인 CLI 예제·합성 `workflow-doctor`를 추가했고 당시 검사 187개를 통과했다. unelevated Codex가 직접 루프백 TCP 연결 6개를 허용해 AppContainer 대안을 준비했다. [이전 근거](Evidence/Phase3_Preparation.json).
- **관리자 설정 없는 작업 실행**: 회사 정책상 관리자 설정은 제외한다. AppContainer 후보 합성 시험 단계에서 검사 206개를 통과했다. P3-T2는 실제 Developer·Reviewer 세션, 하네스의 변경 검사와 격리된 pytest를 추가했다. **검사 265개**, 실제 호출 2회의 예제에서 변경 후 검사 8개·독립 검사 5개를 통과했다. [후보 근거](Evidence/Phase3_AppContainer.json), [T2 근거](Evidence/Phase3_Workers.json).
- **실행 승인·기록(2026-09-22)**: P3-T3에서 별도 `workflow-prepare`·`workflow-approve`·`workflow-status`·`workflow-cancel` 명령과 호출 시도·대기·근거 기반 지적 기록을 구현했다. 안정된 SQLite 전이로 재처리 중복을 막고 미확정 측정은 `null`로 유지한다. 준비·승인만으로 작업을 호출하지 않는다. 추가 113개를 포함한 전체 검사 378개와 `pip check`를 통과했다. 로컬 자식 프로세스·AppContainer 검사에서 실제 AI 호출은 0회였다. [T3 근거](Evidence/Phase3_Records.json).
- **순차 실행(2026-09-22)**: P3-T4는 `workflow-run`, Task별 공통 수정 한도, 후속 독립 리뷰의 명시적 지적 평가와 최종 코드의 전체 등록 검사를 추가한다. 최초 승인은 고정하고 검증된 변경 이력으로 현재 코드를 연결한다. 임시 Task 2개 예제가 서로 다른 실제 역할 세션 4회, Task별·최종 검사 각 8개, 독립 검사 6개 통과로 `technically_complete`에 도달했다. Planner 서비스 호출이나 사용자 결과 인수로 기록하지 않는다. T4는 정상 저장된 단계부터 계속할 수 있으며 명시적 중단 복구는 아래 T5에서 제공한다. 결과·인수·실행용 A는 T6–T8에 남아 있다. [T4 근거](Evidence/Phase3_Execution.json).
- **명시적 복구(2026-09-22)**: P3-T5는 참고용 복구 상태와 `workflow-resume`을 추가한다. 저장 근거를 검증한 응답은 재사용하고 미전송이 증명된 요청은 실행하며 완전한 근거 없는 미확정 호출은 막는다. 승인한 변경 전·후 내용과 일치하는 파일만 부분 복구하고 프로세스와 자식 확인 후 중단 검사를 다시 실행한다. 원래 호출 이력은 유지하고 별도 복구 사실로 호출·사용량을 집계한다. 같은 승인·수정 횟수를 유지한다. 이름 있는 Job 조회와 프로젝트 공통 소유권으로 남은 자식이나 다른 상태 폴더를 통한 우회를 막는다. 최종 회귀·실제 예제 결과는 [Phase 3](Phase3_Workflow.md)와 [T5 근거](Evidence/Phase3_Recovery.json)에 기록하며 Phase 인수는 대기 중이다.
- **결과·피드백·인수(2026-09-22)**: P3-T6는 변경 파일, 현재 검사·재사용 근거, 미해결 항목, 수동 절차와 실제 기록 경로를 보여주는 읽기 전용 `workflow-report` JSON을 추가한다. 피드백 원문·처리 이력을 보존하며 같은 범위 결함 수정과 요구사항 변경에 따른 새 계획을 구분한다. 결함 수정은 승인·기존 수정 한도를 유지하고 이미 완료한 후속 Task도 다시 검사·리뷰한다. Task가 없는 항목을 포함한 현재 재사용 요구사항마다 실제 최종 검사 ID와 사용자 설명이 필요하며 필수 수동 확인은 실행 승인 전에 고정한다. 필수 근거가 누락·이전 버전·실패 상태면 명시적 `workflow-accept`를 막는다. 새 승인 정책과 봉인된 최종 근거를 요구하므로 이전 T4·T5 결과는 과거 이력으로 보존하고 인수하려면 새 승인 Workflow가 필요하다. 기술적 완료와 사용자 인수는 구분한다. [T6 근거](Evidence/Phase3_Results.json), 최종 검증 결과는 Phase 3에 기록한다. T7–T8은 대기 중이며 T5 예제의 호출 2회는 새로운 T6 호출이 아니다.
- **개발 방식**: 초기 기반은 기존 코딩 도구로 만들고 하네스 사용 범위를 점진적으로 넓힌다. 개발 중에는 Phase 문서를 보완하며, 필요한 수정 근거가 있는 경우 외에는 `phase-doc` 스킬과 템플릿을 유지한다.

## 전체 Phase 계획

| Phase | 목표와 주요 산출물 | 선행 조건 | 종료 조건 |
|---|---|---|---|
| [1 — 실행 기반](Phase1_Foundation.md) ✅ | Python·테스트 환경, SQLite 상태, 버전에 연결된 승인, 가짜 Adapter, 검사 실행, 실행 소유권·재개 | 전체 계획과 Phase 1 범위 검토 | 충족: 검사 63개 통과, 2026-09-18 사용자 인수 |
| [2 — 실제 연결과 계획](Phase2_Planning.md) ✅ | 실제 Planner·권한 및 입출력 확인·등록·기본 검사·계획·코드 및 요구사항 대응 | Phase 1 인수, AI 도구 선정 | 충족: 프로젝트 phase-doc 연결 포함 검사 172개와 실제 계획 검증, 2026-09-21 사용자 인수 |
| [3 — 전체 실행 흐름](Phase3_Workflow.md) 🚧 | Task 8개: 구현 → 검증 → 별도 리뷰, 수정·기록·재개·결과·실행용 A. P3-T1–T6 구현, T7–T8 대기 | Phase 2 인수, 작업 권한 검증과 버전별 실행 승인 연결 | 별도 예제의 작은 Phase를 중단·재개 포함 완료하고 실행용 A 검증·고정 |
| [4 — 자체 개발과 MVP 인수](Phase4_Dogfooding.md) | 작은 P0 자체 기능 개발, 최종 보고서 집계, 신규·기존 프로젝트 인수·회귀 검증 | Phase 3 인수, A/B 분리 검증 | 자체 개발 인수 및 기획서 11장 전체 완료 기준의 근거 확보 |

Phase 1–2는 완료했으며 Phase 3는 Task 8개·요구사항 18개의 개발 계획을 승인받고 P3-T1–T6 준비·역할·기록·순차 실행·명시적 복구·최소 결과·인수 조건을 구현했다. Workflow 기록은 실행 기능 제공을 표시하지만 명시적 실행 승인은 계속 필요하다. 기술적 완료와 Phase 3 사용자 인수는 별개다. Phase 4는 Phase 3 실제 결과를 반영할 개요로 유지한다. 개발 일정·소요 시간은 확정하지 않았다.

## 요구사항 대응표

| 기획서 요구사항 | 처리 계획 | 확인할 근거 |
|---|---|---|
| 2·4장: 준비된 프로젝트, 초기화·기본 검사 | Phase 1–2 | 경로·도구·명령 확인, 실제 통과·실패·테스트 0개 예제 |
| 5장: 계획·요구사항 대응·코드와 재사용 조사 | Phase 2, Phase 3–4 인수 시 검증 | 기획·코드와 계획 대조, 재사용 요구사항의 실제 최종 검사 |
| 6장: 순차 구현·검증·별도 리뷰·제한된 수정 | Phase 1·3 | 가짜 실패 시나리오와 실제 작은 Phase 실행 |
| 7장: 버전별 승인·피드백·권한·Git 수동 처리 | Phase 1–3, Phase 4 최종 회귀 검증 | 승인 무효화, 같은 범위 수정과 범위 변경 구분, 금지 동작 차단 검사 |
| 8장: SQLite·소유권·기준선 보존·재개 | Phase 1, Phase 2–3 실제 프로세스 연결 | 두 프로세스 경쟁·중단·파일 불일치·Git 메타데이터만 변경된 상황 |
| 8.1장: AI 호출·시간·리뷰 지적과 처리 근거 | Phase 2 실제 호출 최소 기록, Phase 3 전체 기록, Phase 4 집계 | 재시도·중단·동일 지적과 호출의 중복 여부 대조 |
| 9장: 보고서·재사용 검증·사용자 인수 | Phase 3 최소 구현, Phase 4 완성 | 최종 코드·계획에 연결된 근거, 필수 조건 실패·미검증 시 완료 차단 |
| 10–11장: 분리된 자체 개발·신규와 기존 예제·MVP 인수 | Phase 3–4 | 고정 실행 버전, 자체 개발 보고서, 외부 예제 두 Phase 인수와 핵심 회귀 검사 |

P1 기획 검토·배포용 템플릿, MVP2 독립 수정 요청 및 나머지 P2는 제외한다. 개발 검증용 예제는 테스트 자산이며 P1 템플릿 제품이 아니다.

## Dogfooding과 공통 완료 규칙

1. 최초 문서는 기존 코딩 도구와 스킬로 작성한다. 준비 작업이며 하네스 dogfooding 완료 실적이 아니다.
2. Phase 2에서 계획 생성이 가능해지면 다음 하네스 Phase 검토에 생성 결과를 사용한다. 수동 보완을 기록하며, 이 단계는 계획 기능만 사용하는 것이다.
3. Phase 3에서 별도 예제로 전체 흐름과 중단·재개를 먼저 확인한다. 수정 대상 B 밖에 실행용 A를 고정하고 실행 기록을 별도로 보호한다.
4. Phase 4에서는 A로 B의 작은 미완료 P0 기능을 개발한다. 첫 후보는 결과 보고서의 역할별 AI 호출 수 요약이다. 그 전에 이벤트 기록과 최소 결과 확인을 준비하며, 보고서 개선 부분만 자체 개발 대상으로 남긴다.
5. 보존한 핵심 회귀 검사와 별도 실행으로 B를 검증한다. 사용자가 인수하고 다음 Run에 사용할 버전을 수동 선택한다. 실행 중인 A는 교체하지 않는다.

각 구현 Phase의 필수 검사는 최종 코드에서 실행하고 승인된 계획에 연결한다. 실패·중단·미실행·테스트 미발견을 정확히 기록한다. 사용자 인수와 기술적 완료를 구분하며, 문서 갱신이나 승인만으로 검증 근거가 없는 항목을 통과 처리하지 않는다. 필수 재사용 기능도 최종 검증이 필요하다.

기존 변경을 보존하고 예상 밖 파일 차이에서는 중단하며 실행 DB·로그는 OneDrive 밖에 둔다. 작업 에이전트와 테스트가 실행 중인 정책·승인 DB를 변경하지 못하도록 실제 권한으로 제한해야 하며, 폴더만 나누는 것으로 충분하지 않다. Git 쓰기·배포·UI 확인은 수동이다. 중요한 범위·위험 변경은 기획서의 승인 규칙을 따르고, 동일한 승인 범위의 작업에 반복 승인을 요구하지 않는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 축소 MVP 0.4와 합의한 Python + pytest를 바탕으로 4개 개발 Phase 작성. 구현·제품 검증은 수행하지 않음. |
| 2026-09-15 | Phase 1 승인·구현, 검사 43개 통과. 실제 개발 환경과 남은 사용자 인수·실제 연결 경계를 기록. |
| 2026-09-18 | Phase 1 리뷰 결함 R1–R3 수정과 검사 63개를 검증했다. 사용자 인수 대기는 유지한다. |
| 2026-09-18 | 사용자가 리뷰 보완을 포함한 Phase 1을 명시적으로 인수했다. Phase 1 완료 처리, Phase 2–4 미시작 상태 유지. |
| 2026-09-21 | Phase 2 구현·호환성 개선과 계획 dogfooding 성공을 반영했다. 검사 156개·Planner 호출 1회·Phase 3 검토 초안과 수동 보완을 기록했으며 Phase 2 사용자 인수·Phase 3 작업 권한 분리는 대기 중이다. |
| 2026-09-21 | 승인된 프로젝트 phase-doc 연결로 스킬·템플릿 규칙 고정, 영문·국문 통합 Phase 문서와 wheel 리소스를 추가했다. 검사 172개와 작은 실제 예제가 통과했으며 이전 계획 근거는 유지했다. |
| 2026-09-21 | 사용자가 “phase2 인수”로 Task 2.1–2.7, P2-01·호환성 개선을 포함한 Phase 2를 명시적으로 인수했다. Phase 2 완료 처리, Phase 3–4 구현 미시작 상태 유지. 생성한 계획의 승인은 이번 개발 결과 인수와 별도다. |
| 2026-09-21 | 사용자 승인으로 Phase 3를 시작했다. P3-T1 실행 계약·예제 준비·합성 작업 권한 조사를 마치고 검사 187개를 통과했다. unelevated 네트워크 차단 실패를 기록했으며 P3-T2 실제 실행 조건은 유지한다. Phase 4는 미시작이다. |
| 2026-09-21 | 회사 정책상 관리자 설정을 제외하고 일반 사용자 AppContainer 진단을 추가·검증했다. 검사 206개를 통과하고 기존 프로젝트·Run·이벤트와 실제 실행 조건을 유지했다. 남은 Adapter·격리된 검증 실행 연결을 기록했다. |
| 2026-09-21 | P3-T2 실제 Developer·Reviewer, 파일 변경 검사와 격리된 pytest를 검증했다. 검사 265개·실제 호출 2회의 예제를 통과했다. P3-T3–T8과 Phase 인수는 대기 중이다. |
| 2026-09-22 | 실제 AI 호출 없이 P3-T3 버전별 실행 승인·영속 기록을 구현·검증했다. 전체 검사 378개와 pip check를 통과했다. 계획 승인은 계획 전용으로 유지하고 자동 실행·복구는 비활성화했다. 다음 범위는 P3-T4–T8이다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-22 | P3-T4 순차 실행·제한된 수정·명시적 리뷰 평가·최종 검사를 구현하고 Task 2개·실제 호출 4회의 예제로 검증했다. 현재 회귀 검사 근거는 Phase 3에서 연결한다. T5–T8·Phase 인수는 대기 중이다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-22 | P3-T5 명시적 중단 복구, 근거 기반 응답 재사용, 부분 파일 검사·복구, 프로세스·소유권 검사와 원본 호출 이력을 유지하는 별도 복구 사실을 추가했다. 현재 검증 결과는 Phase 3에서 연결하며 T6–T8·Phase 인수는 대기 중이다. 영문·국문과 README를 갱신했으며 dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-09-22 | P3-T6 최소 JSON 보고서, 피드백 원문·처리 경로, 최종 재사용·수동 근거와 명시적 인수 조건을 추가했다. T1–T5 과거 근거와 T6 새 AI 호출 0회를 구분했다. 영문·국문과 README를 갱신했으며 T7–T8·Phase 인수는 대기 중이다. dev-log 스킬이 없어 별도 기록은 생략했다. |
