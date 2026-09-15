# Phase 4 — Dogfooding `🔲 Not Started`

> Use the verified harness to finish a small P0 feature and collect MVP acceptance evidence.

**Prerequisites**: [Phase 3](Phase3_Workflow.md) accepted; fixed runner A and editable target B isolated with verified permissions.

**Technology**: Python + pytest, SQLite and the same AI Adapter.

**Plan status**: Outline only; detail the small self-development Phase first, after Phase 3.

## Overview

Exercise the harness's own approved development workflow, complete the remaining report presentation and verify the first MVP on external projects. Follow specification §§8.1–11; keep P1 and MVP2 outside this Phase.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | One accepted small P0 harness feature developed by runner A | 🔲 |
| 2 | Complete concise results report with execution/review summaries | 🔲 |
| 3 | Accepted new-project and existing-project example Phases | 🔲 |
| 4 | Core regression, version/isolation and MVP completion evidence | 🔲 |

## Verification & Exit Criteria

Detailed Tasks will use the actual remaining P0 work and Phase 3 observations.

- Initial self-development candidate: add per-role AI-call counts to the report using existing records. A generates/reviews the small Phase plan, receives approval, implements B, runs validation and separate review, presents results and obtains user acceptance. Use the existing Phase workflow even for this small change.
- Independently check the summary against known recorded attempts, including retries and interrupted calls; no duplicate counting on resume. Complete stage-time/approval-wait and finding-outcome summaries as needed for §8.1 and §9. Preserve unknown values and separate project-wide planning costs.
- The final report targets a 1–2-page body with detailed-record links. It includes changes/run instructions, actual validation and reused-feature results, significant failures/remaining issues, approved plan changes, manual UI checks where applicable and execution/review summaries. Mandatory unverified conditions block acceptance; failure still produces a report.
- Run preserved core regressions and a separate CLI invocation of B. Compare code/test changes, especially any weakening of approval, validation, file protection or review policy. Significant changes follow the existing approval path.
- Record runner/target versions, manual intervention, unnecessary waiting/questions, resume usability, calls/times and useful review findings. If A fails, preserve records/files, fix with existing coding tools and report that intervention; do not silently claim autonomous completion.
- Complete one accepted Phase on a prepared new-project example and one on an existing-project example using the selected stack. A qualifying Phase 3 example can count toward its category when evidence still matches the accepted code/requirements; otherwise rerun it. These are separate external projects, not the harness repository.
- Check every criterion in specification §11 against evidence. All required conditions, including final reuse checks, concurrency, resume and permission isolation, must hold before MVP acceptance.

**Results**: No self-development, example acceptance or product verification has occurred. All items remain unverified.

## Self-Development & Report Completion

### Purpose / Implementation Files

Use A to modify B's existing report code and its tests. Final file names depend on Phase 3. Place execution evidence in the existing runtime/report locations; do not create a separate dogfooding management system.

### Design Decisions

- Reserve a genuinely remaining P0 task, not a new feature invented only for dogfooding. If the call summary is already implemented, choose another small remaining P0 report/status/error item and document the choice before running it.
- Keep A's executable, dependencies, role instructions, policies and approval DB outside B's writable reach. Tests use temporary DBs. Do not replace A in an active Run.
- After B passes independent checks and user acceptance, manually choose it for the next Run and preserve A. If state formats changed, verify compatibility or use a new test Run; never automatically migrate an active Run or open its DB with an unverified version.
- Record actual-use findings as P0 defects, necessary implementation adjustments or later candidates. Do not expand MVP scope automatically.

### Usage Example

From frozen A, execute the small report-summary Phase against B, inspect its generated report and separately run B's regression/CLI checks. After acceptance, choose the next runtime manually. Exact commands and version identifiers will be recorded from the real execution.

## Prerequisites & Development Notes

Self-development success does not replace external reuse verification. Automated UI testing, automatic updates, Git writes/deployment, extra providers and P1/MVP2 features remain excluded. Update the Phase documents with real results while keeping the documentation skill stable.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the small P0 dogfooding candidate, final reporting and external MVP acceptance outline. |

---

# Phase 4 — 자체 개발과 MVP 인수 `🔲 미시작`

> 검증된 하네스로 작은 P0 기능을 완성하고 MVP 인수 근거를 확보한다.

**선행 조건**: [Phase 3](Phase3_Workflow.md) 인수, 고정 실행용 A와 수정 대상 B의 권한 분리 검증.

**기술 구성**: Python + pytest, SQLite, 동일한 AI Adapter.

**계획 상태**: 개요만 작성. Phase 3 이후 작은 자체 개발 Phase부터 상세화.

## 개요

하네스 자신의 승인된 개발 흐름을 사용하고 남은 보고서 표현을 완성하며 외부 프로젝트에서 첫 MVP를 검증한다. 기획서 8.1–11장을 따르고 P1·MVP2는 이 Phase에 포함하지 않는다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실행용 A로 개발하고 인수한 작은 P0 하네스 기능 한 건 | 🔲 |
| 2 | 실행·리뷰 집계를 포함한 간결한 최종 결과 보고서 | 🔲 |
| 3 | 신규·기존 외부 예제의 Phase 인수 | 🔲 |
| 4 | 핵심 회귀·버전과 분리·MVP 완료 근거 | 🔲 |

## 검증 및 종료 조건

실제 남은 P0 작업과 Phase 3 관찰 결과를 바탕으로 상세 Task를 작성한다.

- 첫 자체 개발 후보는 기존 기록을 이용한 보고서의 역할별 AI 호출 수 요약이다. A로 작은 Phase 계획 생성·검토, 사용자 승인, B 구현, 검증·별도 리뷰, 결과 보고·사용자 인수를 수행한다. 작은 변경도 기존 Phase 흐름으로 실행한다.
- 재시도·중단 호출을 포함해 알려진 실제 시도 기록과 요약을 별도로 대조하며 재개 중복 집계를 막는다. 8.1·9장에 필요한 단계 시간·승인 대기·리뷰 지적 처리 결과 집계도 완성한다. 알 수 없는 값은 유지하고 전체 계획 비용은 구분한다.
- 최종 보고서는 상세 기록 링크와 1~2페이지 내외 본문을 목표로 한다. 개발 결과·실행법, 실제 검사·재사용 결과, 주요 실패·남은 문제, 승인된 계획 변경, 해당하는 수동 UI 확인, 실행·리뷰 요약을 포함한다. 필수 미검증 항목은 인수를 막으며 실패 시에도 보고서를 생성한다.
- 보존한 핵심 회귀 검사와 별도 CLI 실행으로 B를 확인한다. 코드·테스트 변경을 비교하며 승인·검증·파일 보호·리뷰 정책의 완화를 특히 확인한다. 중요한 변경은 기존 승인 경로를 따른다.
- 실행용·수정 대상 버전, 수동 개입, 불필요한 대기·질문, 재개 사용성, 호출·시간, 유효한 리뷰 지적을 기록한다. A가 실패하면 기록·파일을 보존하고 기존 코딩 도구로 수정해 수동 개입을 보고한다. 자율 완료로 잘못 표시하지 않는다.
- 선정한 기술 구성의 준비된 신규 프로젝트와 기존 프로젝트에서 각각 한 Phase를 인수한다. Phase 3 예제가 조건에 맞고 인수할 코드·요구사항에 근거가 여전히 유효하면 해당 범주의 실적으로 사용할 수 있으며, 아니면 다시 실행한다. 하네스 저장소가 아닌 별도 외부 프로젝트로 검증한다.
- 기획서 11장의 모든 완료 기준과 근거를 대조한다. 최종 재사용 검증·동시 실행 방지·재개·권한 분리를 포함한 모든 필수 조건을 충족한 뒤 MVP를 인수한다.

**결과**: 자체 개발·예제 인수·제품 검증은 수행하지 않았다. 모든 항목은 미검증이다.

## 자체 개발과 보고서 완성

### 목적 / 구현 파일

A로 B의 기존 보고서 코드와 테스트를 수정한다. 실제 파일명은 Phase 3 결과에 따른다. 실행 근거는 기존 실행 기록·보고서 위치에 남기며 별도 dogfooding 관리 시스템은 만들지 않는다.

### 설계 결정 사항

- 자체 개발만을 위해 새 기능을 추가하지 않고 실제로 남은 P0 작업을 선택한다. 호출 요약이 이미 구현됐다면 남은 보고서·상태·오류 안내 중 작은 P0 항목을 선정해 실행 전에 문서화한다.
- A의 실행 파일·의존성·역할 지침·정책·승인 DB는 B가 쓸 수 없는 곳에 둔다. 테스트는 임시 DB를 사용하며 활성 Run의 A를 교체하지 않는다.
- B의 별도 검사와 사용자 인수 후 다음 Run의 실행 버전을 수동 선택하고 A를 보존한다. 상태 형식이 바뀌면 호환성을 확인하거나 새 시험 Run을 사용한다. 활성 Run을 자동 이전하거나 미검증 버전으로 DB를 열지 않는다.
- 실사용 발견 사항은 P0 결함·필요한 구현 조정·후속 후보로 기록하며 MVP 범위를 자동으로 확대하지 않는다.

### 사용 예시

고정 A에서 B를 대상으로 작은 보고서 집계 Phase를 실행하고 생성 보고서를 확인한 뒤 B의 회귀 검사·CLI를 별도로 실행한다. 인수 후 다음 실행본을 수동 선택한다. 실제 명령과 버전 식별자는 실행 결과에서 기록한다.

## 선행 조건 및 개발 시 주의사항

자체 개발 성공이 외부 프로젝트 재사용성 검증을 대체하지 않는다. 자동 UI 테스트·자동 업데이트·Git 쓰기와 배포·추가 제공자·P1과 MVP2는 제외한다. 실제 결과는 Phase 문서에 반영하고 문서 작성 스킬은 유지한다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 작은 P0 dogfooding 후보, 최종 보고서와 외부 MVP 인수 개요 최초 작성. |
