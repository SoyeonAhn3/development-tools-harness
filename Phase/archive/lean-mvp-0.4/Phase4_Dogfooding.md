# Phase 4 — Dogfooding `⏸ Cancelled`

> Use the verified harness to finish a small P0 feature and collect MVP acceptance evidence.

> **Cancelled (2026-10-23)**: The product direction changed to a language-independent harness ([new specification](../../../Draft/ai-development-harness-plan-v1.md)). This Phase was never started; nothing was implemented, tested or accepted. Real-project verification moves to the new [Phase 4](../../Phase4_RealWorldValidation.md). The plan below is kept only as a record.

**Prerequisites**: Met — [Phase 3](Phase3_Workflow.md) accepted on 2026-10-07; fixed runner A08 and editable target B isolated with verified permissions.

**Technology**: Python + pytest, SQLite and the same AI Adapter.

**Plan status**: Detailed seven-Task plan drafted on 2026-10-07 and awaiting user review; no Phase 4 execution has started. On 2026-10-07 the user selected execution-summary completion as the first self-development feature. P4-T5 and later Tasks will be refined from actual P4-T1–T4 results.

**Documentation check (2026-10-23)**: Phases 1–3 are accepted; Phase 4 implementation has not started. This update changes documentation only, with no new AI calls, tests or acceptance. The working-tree [lean MVP specification](../../../Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md) is empty. References to its numbered sections retain the previously documented scope; confirm the intended specification before using it for execution.

## Overview

Exercise the harness's own approved development workflow, complete the remaining report presentation and verify the first MVP on external projects. Follow specification §§8.1–11; keep P1 and MVP2 outside this Phase.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Execution-summary completion (finding outcomes and call purposes) developed by runner A08 and accepted — P4-T1–T3 | 🔲 |
| 2 | Concise 1–2-page results report developed by the next runner — P4-T5 | 🔲 |
| 3 | Accepted new-project and existing-project example Phases — P4-T6 | 🔲 |
| 4 | Next-runner promotion, core regression, version/isolation and MVP completion evidence — P4-T4, P4-T7 | 🔲 |

## Verification & Exit Criteria

Tasks follow specification §10.1 steps C–D, then external reuse and MVP checks. The frozen runner's Planner generates each self-development Phase plan; this document fixes scope, order and gates, not the generated Task content.

| Task | Planned work | Completion evidence |
|---|---|---|
| P4-T1 | Prepare self-development with existing coding tools: record the candidate selection, write the execution-summary specification, create B as a copy of this repository outside OneDrive (separate from A and runtime storage), register it with `harness-self-v1` validation, pass the baseline and fix the §10.3 core protection regression list with hashes. | Specification reviewed by the user, registration/baseline evidence, hashed core regression list. |
| P4-T2 | Generate the small Phase plan with A08's Planner (one actual Planner call) and review its requirements mapping against the specification. | Generated plan, review record and user plan approval. |
| P4-T3 | Execute with A08: `workflow-prepare` → `workflow-approve` → `workflow-run` (Developer → isolated validation → separate Reviewer → bounded corrections → final checks). Review final B source/tests, run the reviewed-host stage, confirm `HARNESS_HOST_REGRESSION`, inspect `workflow-report` and obtain `workflow-accept`. The user reflects the accepted change into this repository with Git. | Workflow records/report, isolated and reviewed-host reports, acceptance record and dogfooding notes. |
| P4-T4 | Promote the next runner: freeze A09 from the accepted repository, run installed verification, compare core protection tests with P4-T1 for weakening and run B's CLI separately on a saved-run copy. A08 is preserved. | Freeze/verification evidence, core-test comparison and the user's manual runner selection. |
| P4-T5 | Second small self-development Phase with A09: the 1–2-page human-readable results report (§9), showing project-level Planner calls separately. Detailed after P4-T4. | Same planning, execution and acceptance gates as P4-T2–T3. |
| P4-T6 | Complete one new-project and one existing-project Phase with the selected stack. Choose targets before starting. Rerun the T7 example if its evidence no longer matches the runner or accepted code. | Two accepted workflow reports with evidence. |
| P4-T7 | Map every §11 criterion to evidence, summarize §10.4 dogfooding observations and request Phase 4/MVP acceptance. | §11 evidence table and user acceptance. |

- **Execution-summary acceptance (P4-T3)**: New report fields are additive; existing fields keep their meanings. Unit tests use synthetic records covering each finding status, required/optional findings, a finding repeated in re-review, corrections after failed validation and after review, re-review, saved-response reuse, proven-unsent retry and an uncertain call. Copies of the completed T4, T5 and T7 run records reproduce hand-counted values; resume and reuse add no calls.
- Independently check the summary against known recorded attempts, including retries and interrupted calls; no duplicate counting on resume. Preserve unknown values and separate project-wide planning costs.
- The final report targets a 1–2-page body with detailed-record links. It includes changes/run instructions, actual validation and reused-feature results, significant failures/remaining issues, approved plan changes, manual UI checks where applicable and execution/review summaries. Mandatory unverified conditions block acceptance; failure still produces a report.
- Run preserved core regressions and a separate CLI invocation of B. Compare code/test changes, especially any weakening of approval, validation, file protection or review policy. Significant changes follow the existing approval path.
- Record runner/target versions, manual intervention, unnecessary waiting/questions, resume usability, calls/times and useful review findings. If A fails, preserve records/files, fix with existing coding tools and report that intervention; do not silently claim autonomous completion.
- Complete one accepted Phase on a prepared new-project example and one on an existing-project example using the selected stack. A qualifying Phase 3 example can count toward its category when evidence still matches the accepted code/requirements; otherwise rerun it. These are separate external projects, not the harness repository.
- Check every criterion in specification §11 against evidence. All required conditions, including final reuse checks, concurrency, resume and permission isolation, must hold before MVP acceptance.

**Results**: No self-development, example acceptance or product verification has occurred. All items remain unverified.

## Self-Development & Report Completion

### Selected Feature — Execution Summary Completion

The original candidate, per-role AI-call counts, already exists: `_role_metrics` in [results.py](../../../src/development_harness/results.py) reports attempts, confirmed calls and durations for Developer, Reviewer and validation, and `WorkflowRecords.summary` reports approval wait, finding count and blocking findings. Following the design rule below, the user selected the remaining §8.1 gaps on 2026-10-07:

1. **Finding outcomes**: count unique findings by status (`open`, `resolved`, `false_positive`, `deferred`) and by required/optional. Separate findings proposed by the Reviewer from fixes confirmed by follow-up review and fresh validation. A finding repeated in re-review counts once.
2. **Call purposes**: split Developer calls into initial implementation and corrections, and Reviewer calls into initial review and re-review. Show proven-unsent retries and saved-response reuse separately; reuse adds no call. An uncertain dispatch leaves affected totals unknown (`null`).

Out of scope: Markdown output, new commands, Planner-call display (P4-T5), token/cost estimation and state-format changes.

### Purpose / Implementation Files

Expected change: report aggregation in `src/development_harness/results.py` (`_role_metrics`, `report`) and/or `WorkflowRecords.summary` in `workflow_records.py`, plus unit tests. The approved generated plan decides the final files. Execution evidence stays in the existing runtime/report locations; no separate dogfooding management system is created.

### Design Decisions

- Reserve a genuinely remaining P0 task, not a new feature invented only for dogfooding. The selection above is recorded before execution.
- Derive purposes and outcomes from existing attempts, recovery facts and findings. Do not change the SQLite state format, so completed T4/T5/T7 records remain readable ground truth and no §10.2 migration is needed.
- The three real Phase 3 examples had zero corrections and findings. Finding/correction paths are therefore verified with synthetic records; any finding during P4-T3 becomes the first real case and is recorded.
- B is a repository copy outside OneDrive, following the Phase 2 planning dogfood. A, B and runtime storage are non-nested. Git reflection is manual after acceptance.
- Keep A's executable, dependencies, role instructions, policies and approval DB outside B's writable reach. Tests use temporary DBs. Do not replace A in an active Run.
- After B passes independent checks and user acceptance, manually choose it for the next Run and preserve A. If state formats changed, verify compatibility or use a new test Run; never automatically migrate an active Run or open its DB with an unverified version.
- Run large Windows verifications sequentially; concurrent runs caused the Phase 3 ACL-grant timeout.
- Record actual-use findings as P0 defects, necessary implementation adjustments or later candidates. Do not expand MVP scope automatically.

### Usage Example

Run A08 as `& "$runnerA/runtime/python.exe" -I -B "$runnerA/run.py" --project <B> <command>`. The command sequence is `register` → `plan` → `plan-status` (review) → `plan-approve` → `workflow-prepare` → `workflow-approve` → `workflow-run` (`workflow-resume` if interrupted) → `workflow-report` → reviewed-host self-test and `workflow-manual` for `HARNESS_HOST_REGRESSION` → `workflow-accept`. Exact arguments, run IDs and version identifiers will be recorded from the real execution.

## Prerequisites & Development Notes

Self-development success does not replace external reuse verification. Automated UI testing, automatic updates, Git writes/deployment, extra providers and P1/MVP2 features remain excluded. Update the Phase documents with real results while keeping the documentation skill stable.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the small P0 dogfooding candidate, final reporting and external MVP acceptance outline. |
| 2026-10-07 | Recorded the prerequisite as met by Phase 3 acceptance on 2026-10-07; runner A08. Detailed planning and self-development have not started. |
| 2026-10-07 | Drafted the detailed seven-Task plan (P4-T1–T7). Recorded the user-selected first self-development feature, execution-summary completion (finding outcomes and call purposes), after confirming per-role call counts already exist. Added acceptance checks, the no-state-format-change decision and the A08 → A09 order. Awaiting user review; no execution, AI calls or tests. |
| 2026-10-23 | Synchronized current status and remaining Phase 4 work with both READMEs; noted the empty working-tree specification. No implementation, test run or acceptance. Separate dev-log omitted because the skill is unavailable. |
| 2026-10-23 | Cancelled because of the direction change to plan 1.7 and archived. Nothing was started. |

---

# Phase 4 — 자체 개발과 MVP 인수 `⏸ 취소`

> 검증된 하네스로 작은 P0 기능을 완성하고 MVP 인수 근거를 확보한다.

> **취소 (2026-10-23)**: 제품 방향이 언어에 묶이지 않는 하네스([새 기획서](../../../Draft/ai-development-harness-plan-v1.md))로 바뀌었다. 이 Phase는 시작하지 않았으며 구현·검사·인수한 것이 없다. 실제 프로젝트 검증은 새 [Phase 4](../../Phase4_RealWorldValidation.md)로 옮긴다. 아래 계획은 기록으로만 남긴다.

**선행 조건**: 충족 — 2026-10-07 [Phase 3](Phase3_Workflow.md) 인수, 고정 실행용 A08과 수정 대상 B의 권한 분리 검증.

**기술 구성**: Python + pytest, SQLite, 동일한 AI Adapter.

**계획 상태**: 2026-10-07 Task 7개의 상세 계획을 작성했으며 사용자 검토를 기다린다. Phase 4 실행은 시작하지 않았다. 2026-10-07 사용자가 첫 자체 개발 기능으로 실행 요약 보완을 선택했다. P4-T5 이후 Task는 P4-T1–T4 실제 결과를 반영해 구체화한다.

**문서 점검(2026-10-23)**: Phase 1–3은 인수 완료이며 Phase 4 구현은 미시작이다. 이번 변경은 문서 갱신이며 새 AI 호출·검사·인수는 없다. 작업 트리의 [축소 MVP 기획서](../../../Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md)는 비어 있다. 해당 장 번호 참조는 기존에 기록한 범위를 유지한 것이며 실행에 사용하기 전에 의도한 기획서를 확인해야 한다.

## 개요

하네스 자신의 승인된 개발 흐름을 사용하고 남은 보고서 표현을 완성하며 외부 프로젝트에서 첫 MVP를 검증한다. 기획서 8.1–11장을 따르고 P1·MVP2는 이 Phase에 포함하지 않는다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실행용 A08로 개발하고 인수한 실행 요약 보완(지적 처리 결과·호출 목적) — P4-T1–T3 | 🔲 |
| 2 | 다음 실행본으로 개발한 1~2페이지 결과 보고서 — P4-T5 | 🔲 |
| 3 | 신규·기존 외부 예제의 Phase 인수 — P4-T6 | 🔲 |
| 4 | 다음 실행본 승격·핵심 회귀·버전과 분리·MVP 완료 근거 — P4-T4, P4-T7 | 🔲 |

## 검증 및 종료 조건

기획서 10.1의 C–D 단계를 수행한 뒤 외부 재사용과 MVP 완료를 확인한다. 각 자체 개발 Phase의 계획은 고정 실행본의 Planner가 생성한다. 이 문서는 범위·순서·확인 조건을 정하며 생성될 Task 내용을 대신 작성하지 않는다.

| Task | 개발 내용 | 완료 근거 |
|---|---|---|
| P4-T1 | 기존 코딩 도구로 자체 개발을 준비한다. 후보 선정을 기록하고 실행 요약 기획서를 작성한다. OneDrive 밖에 A·실행 기록과 겹치지 않는 저장소 사본 B를 만들어 `harness-self-v1` 검사로 등록하고 기본 검사를 통과한다. 10.3의 핵심 보호 회귀 검사 목록을 해시와 함께 고정한다. | 사용자가 검토한 기획서, 등록·기본 검사 근거, 해시를 기록한 핵심 회귀 목록. |
| P4-T2 | A08 Planner로 작은 Phase 계획을 생성하고(실제 Planner 호출 1회) 요구사항 대응을 기획서와 대조한다. | 생성 계획, 검토 기록, 사용자 계획 승인. |
| P4-T3 | A08로 실행한다. `workflow-prepare` → `workflow-approve` → `workflow-run`(Developer → 격리 검사 → 별도 Reviewer → 제한된 수정 → 최종 검사). 최종 B 소스·테스트를 검토한 뒤 호스트 검사를 실행하고 `HARNESS_HOST_REGRESSION`을 확인한다. `workflow-report`를 확인하고 `workflow-accept`로 인수한다. 인수한 변경은 사용자가 Git으로 이 저장소에 반영한다. | Workflow 기록·보고서, 격리·호스트 검사 보고서, 인수 기록, dogfooding 기록. |
| P4-T4 | 다음 실행본으로 승격한다. 인수한 저장소에서 A09를 고정하고 설치본 검사를 실행한다. 핵심 보호 검사를 P4-T1과 비교해 완화 여부를 확인하고 저장된 Run 사본으로 B의 CLI를 별도 실행한다. A08은 보존한다. | 고정·검증 근거, 핵심 검사 비교, 사용자의 수동 실행본 선택. |
| P4-T5 | A09로 두 번째 작은 자체 개발 Phase를 수행한다. 사람이 읽는 1~2페이지 결과 보고서(9장)를 만들고 프로젝트 단위 Planner 호출을 따로 표시한다. P4-T4 이후 구체화한다. | P4-T2–T3과 같은 계획·실행·인수 조건. |
| P4-T6 | 선정한 기술 구성으로 신규 프로젝트와 기존 프로젝트에서 각각 한 Phase를 완료한다. 시작 전 대상을 정한다. T7 예제의 근거가 실행본이나 인수 코드와 더 이상 맞지 않으면 다시 실행한다. | 근거를 갖춘 인수 Workflow 보고서 2건. |
| P4-T7 | 11장의 모든 기준을 근거와 대조하고 10.4의 dogfooding 관찰을 정리해 Phase 4·MVP 인수를 요청한다. | 11장 근거 대조표, 사용자 인수. |

- **실행 요약 인수 조건(P4-T3)**: 보고서 필드는 추가만 하며 기존 필드의 의미는 유지한다. 단위 테스트는 합성 기록으로 각 지적 상태, 필수·선택 지적, 재검토에서 반복된 지적, 검사 실패 후·리뷰 후 수정, 재검토, 저장 응답 재사용, 미전송이 증명된 재시도, 미확정 호출을 다룬다. 완료된 T4·T5·T7 Run 기록 사본에서 손으로 센 값을 재현하며 재개·재사용은 호출을 늘리지 않는다.
- 재시도·중단 호출을 포함해 알려진 실제 시도 기록과 요약을 별도로 대조하며 재개 중복 집계를 막는다. 알 수 없는 값은 유지하고 전체 계획 비용은 구분한다.
- 최종 보고서는 상세 기록 링크와 1~2페이지 내외 본문을 목표로 한다. 개발 결과·실행법, 실제 검사·재사용 결과, 주요 실패·남은 문제, 승인된 계획 변경, 해당하는 수동 UI 확인, 실행·리뷰 요약을 포함한다. 필수 미검증 항목은 인수를 막으며 실패 시에도 보고서를 생성한다.
- 보존한 핵심 회귀 검사와 별도 CLI 실행으로 B를 확인한다. 코드·테스트 변경을 비교하며 승인·검증·파일 보호·리뷰 정책의 완화를 특히 확인한다. 중요한 변경은 기존 승인 경로를 따른다.
- 실행용·수정 대상 버전, 수동 개입, 불필요한 대기·질문, 재개 사용성, 호출·시간, 유효한 리뷰 지적을 기록한다. A가 실패하면 기록·파일을 보존하고 기존 코딩 도구로 수정해 수동 개입을 보고한다. 자율 완료로 잘못 표시하지 않는다.
- 선정한 기술 구성의 준비된 신규 프로젝트와 기존 프로젝트에서 각각 한 Phase를 인수한다. Phase 3 예제가 조건에 맞고 인수할 코드·요구사항에 근거가 여전히 유효하면 해당 범주의 실적으로 사용할 수 있으며, 아니면 다시 실행한다. 하네스 저장소가 아닌 별도 외부 프로젝트로 검증한다.
- 기획서 11장의 모든 완료 기준과 근거를 대조한다. 최종 재사용 검증·동시 실행 방지·재개·권한 분리를 포함한 모든 필수 조건을 충족한 뒤 MVP를 인수한다.

**결과**: 자체 개발·예제 인수·제품 검증은 수행하지 않았다. 모든 항목은 미검증이다.

## 자체 개발과 보고서 완성

### 선정 기능 — 실행 요약 보완

처음 후보였던 역할별 AI 호출 수는 이미 구현돼 있다. [results.py](../../../src/development_harness/results.py)의 `_role_metrics`가 Developer·Reviewer·검증별 시도 수·확인된 호출 수·시간을 보여주고, `WorkflowRecords.summary`가 승인 대기·지적 수·완료를 막는 지적을 보여준다. 아래 설계 원칙에 따라 2026-10-07 사용자가 8.1장의 남은 항목을 선택했다.

1. **지적 처리 결과**: 고유 지적을 상태(`open`, `resolved`, `false_positive`, `deferred`)와 필수·선택으로 나눠 센다. Reviewer가 제안한 지적과 후속 리뷰·새 검사로 수정이 확인된 지적을 구분한다. 재검토에서 반복된 지적은 한 번만 센다.
2. **호출 목적**: Developer 호출을 최초 구현과 수정으로, Reviewer 호출을 최초 리뷰와 재검토로 나눈다. 미전송이 증명된 재시도와 저장 응답 재사용은 따로 표시하며 재사용은 호출에 더하지 않는다. 미확정 호출이 있으면 영향받는 합계는 알 수 없음(`null`)으로 둔다.

제외 범위: Markdown 출력, 새 명령, Planner 호출 표시(P4-T5), 토큰·금액 추정, 상태 저장 형식 변경.

### 목적 / 구현 파일

예상 변경 위치는 `src/development_harness/results.py`(`_role_metrics`, `report`) 또는 `workflow_records.py`의 `WorkflowRecords.summary` 집계와 단위 테스트다. 최종 파일은 승인된 생성 계획이 정한다. 실행 근거는 기존 실행 기록·보고서 위치에 남기며 별도 dogfooding 관리 시스템은 만들지 않는다.

### 설계 결정 사항

- 자체 개발만을 위해 새 기능을 추가하지 않고 실제로 남은 P0 작업을 선택한다. 위 선정 내용을 실행 전에 기록했다.
- 호출 목적과 지적 처리 결과는 기존 시도·복구 사실·지적 기록에서 계산한다. SQLite 상태 형식을 바꾸지 않으므로 완료된 T4·T5·T7 기록을 기준값으로 그대로 읽을 수 있고 10.2의 이전 작업이 필요 없다.
- Phase 3 실제 예제 세 건은 수정·지적이 모두 0건이었다. 지적·수정 경로는 합성 기록으로 검증하며 P4-T3에서 지적이 나오면 첫 실제 사례로 기록한다.
- B는 Phase 2 계획 dogfooding과 같이 OneDrive 밖의 저장소 사본이다. A·B·실행 기록 저장소는 서로 포함되지 않는다. Git 반영은 인수 후 수동으로 한다.
- A의 실행 파일·의존성·역할 지침·정책·승인 DB는 B가 쓸 수 없는 곳에 둔다. 테스트는 임시 DB를 사용하며 활성 Run의 A를 교체하지 않는다.
- B의 별도 검사와 사용자 인수 후 다음 Run의 실행 버전을 수동 선택하고 A를 보존한다. 상태 형식이 바뀌면 호환성을 확인하거나 새 시험 Run을 사용한다. 활성 Run을 자동 이전하거나 미검증 버전으로 DB를 열지 않는다.
- 큰 Windows 검증은 순서대로 실행한다. Phase 3에서 동시 실행으로 권한 설정 시간 초과가 발생했다.
- 실사용 발견 사항은 P0 결함·필요한 구현 조정·후속 후보로 기록하며 MVP 범위를 자동으로 확대하지 않는다.

### 사용 예시

A08은 `& "$runnerA/runtime/python.exe" -I -B "$runnerA/run.py" --project <B> <명령>`으로 실행한다. 명령 순서는 `register` → `plan` → `plan-status`(검토) → `plan-approve` → `workflow-prepare` → `workflow-approve` → `workflow-run`(중단 시 `workflow-resume`) → `workflow-report` → 호스트 자체 검사와 `HARNESS_HOST_REGRESSION`의 `workflow-manual` → `workflow-accept`이다. 실제 인수·Run ID·버전 식별자는 실행 결과에서 기록한다.

## 선행 조건 및 개발 시 주의사항

자체 개발 성공이 외부 프로젝트 재사용성 검증을 대체하지 않는다. 자동 UI 테스트·자동 업데이트·Git 쓰기와 배포·추가 제공자·P1과 MVP2는 제외한다. 실제 결과는 Phase 문서에 반영하고 문서 작성 스킬은 유지한다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 작은 P0 dogfooding 후보, 최종 보고서와 외부 MVP 인수 개요 최초 작성. |
| 2026-10-07 | Phase 3 인수(2026-10-07)로 선행 조건 충족을 기록했다. 실행용은 A08이다. 상세 계획·자체 개발은 미시작이다. |
| 2026-10-07 | Task 7개(P4-T1–T7)의 상세 계획을 작성했다. 역할별 호출 수가 이미 구현됐음을 확인하고 사용자가 선택한 첫 자체 개발 기능인 실행 요약 보완(지적 처리 결과·호출 목적)을 기록했다. 인수 조건, 상태 형식 미변경 결정과 A08 → A09 순서를 추가했다. 사용자 검토 대기 중이며 실행·AI 호출·검사는 없다. |
| 2026-10-23 | 한·영 README와 현재 상태·남은 Phase 4 작업을 동기화하고 작업 트리 기획서가 비어 있음을 기록했다. 구현·검사 실행·인수는 없다. dev-log 스킬이 없어 별도 기록은 생략했다. |
| 2026-10-23 | 기획서 1.7로 방향이 바뀌어 취소하고 보관했다. 시작한 작업은 없다. |
