# Phase 3 — Workflow `🔲 Not Started`

> Complete one real example Phase and prepare a verified fixed runner for self-development.

**Prerequisites**: [Phase 2](Phase2_Planning.md) accepted, permissions verified and a prepared example available.

**Technology**: Python + pytest, SQLite and the selected single AI Adapter.

**Plan status**: Outline only; detail Tasks after Phase 2.

## Overview

Connect actual implementation, validation, separate review, bounded corrections and minimum result acceptance. Verify the whole flow and interruption/resume in a separate example before touching the harness through itself. Covers specification §§6–10, with final report presentation completed in Phase 4.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Real sequential Developer/Validation Runner/Reviewer workflow | 🔲 |
| 2 | Call/timing/finding records, corrections and process-aware resume | 🔲 |
| 3 | Minimum success/failure report, feedback and result acceptance | 🔲 |
| 4 | Accepted external example and verified fixed runner A | 🔲 |

## Verification & Exit Criteria

Detailed Tasks are deferred. Verify the following behavior with pytest integration/regression tests and actual example runs:

- An approved small Phase executes Tasks sequentially. The Reviewer uses a separate session and checks requirements, actual implementation and tests. Required findings must have follow-up review/validation evidence; Developer self-report is insufficient.
- Required validation runs after changes and on final Phase content. Failed, skipped, interrupted and zero-test outcomes do not pass. Corrections stop at the configured limit; environment/permission/specification problems stop without spending code-fix retries.
- Approval/evidence/result acceptance reference matching plan and code versions. Same-scope defect feedback reopens correction in the current Phase; changed requirements update the plan and approval. Store the original feedback and outcome.
- Interrupted implementation inspects partial files; interrupted validation checks remaining processes and reruns required checks. Unexpected user edits stop without overwrite, and another runner cannot acquire unsafe ownership. Metadata-only manual Git changes do not block an otherwise unchanged run.
- Actual role-call attempts, completed/incomplete times, approval waiting and findings have stable identities. Resume does not double-count calls or repeated findings. Confirmed fixes have evidence; deferred mandatory findings still block completion. Do not estimate unknown duration, tokens or money.
- Minimum reports exist for success and failure and show delivered files, validation/reuse evidence, unresolved items, manual checks and detailed-record locations. User acceptance is separate from technical completion and cannot override unmet mandatory criteria.
- A separate prepared example completes a small Phase, including stop/resume and user acceptance. Freeze A's code, dependencies and role/policy instructions; prove that B and its test processes cannot modify A or its runtime/approval storage before the next Phase.

**Results**: No implementation, live runs or acceptance evidence yet. All criteria are unverified.

## Workflow & Minimum Results

### Purpose / Implementation Files

Extend the Phase 1 runner/storage and Phase 2 Adapter. Add result generation inside the existing package and temporary integration examples under tests; exact filenames are deferred.

### Design Decisions

- Keep one sequential workflow and the proposed two-correction default; no Fast/Standard/Strict routing or parallel Tasks.
- Implement all event collection now. Provide minimum evidence access now; reserve a small remaining report summary for Phase 4 self-development.
- Recheck reused requirements at final acceptance even without an implementation Task. No broad code-analysis or coverage engine is added.
- Freeze A as a separately installed/copied runtime, not an editable installation referencing B. Place runtime records outside OneDrive; B tests use temporary records and limited permissions. Record actual isolation probes.

### Usage Example

Use a prepared small Python CLI example with baseline tests, then request one bounded input-validation change with expected normal and invalid-input behavior. Review the generated Phase, approve, execute, interrupt once, resume, inspect review/validation evidence and accept. The final example and commands are selected when detailing this Phase.

## Prerequisites & Development Notes

Reuse earlier components with regression evidence. Core protections must work with actual worker processes, not only the fake Adapter. A permissions or resume defect blocks promotion to runner A. Existing coding tools may fix such defects; record that manual intervention. This external example is preparation for full dogfooding, not the self-development milestone itself.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the full-flow outline, external example gate and fixed-runner requirements. |

---

# Phase 3 — 전체 실행 흐름 `🔲 미시작`

> 실제 예제 Phase 하나를 완료하고 자체 개발에 사용할 검증된 고정 실행본을 준비한다.

**선행 조건**: [Phase 2](Phase2_Planning.md) 인수, 권한 검증, 준비된 예제 확보.

**기술 구성**: Python + pytest, SQLite, 선정한 단일 AI Adapter.

**계획 상태**: 개요만 작성. Phase 2 이후 Task 상세화.

## 개요

실제 구현·검증·별도 리뷰·제한된 수정·최소 결과 인수를 연결한다. 하네스로 자신을 수정하기 전에 별도 예제로 전체 흐름과 중단·재개를 확인한다. 기획서 6–10장을 다루며 최종 보고서 표현은 Phase 4에서 완성한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Developer·Validation Runner·Reviewer 순차 Workflow | 🔲 |
| 2 | 호출·시간·지적 기록, 수정·프로세스 확인을 포함한 재개 | 🔲 |
| 3 | 최소 성공·실패 보고서, 피드백·결과 인수 | 🔲 |
| 4 | 인수한 외부 예제와 검증된 고정 실행용 A | 🔲 |

## 검증 및 종료 조건

상세 Task는 이후 작성한다. pytest 통합·회귀 검사와 실제 예제 실행으로 다음 동작을 확인한다.

- 승인된 작은 Phase의 Task를 순차 실행한다. Reviewer는 별도 세션에서 요구사항·실제 구현·테스트를 대조한다. 필수 지적에는 후속 리뷰·검증 근거가 필요하며 Developer 자기 보고만으로 해결하지 않는다.
- 변경 후 필요한 검사를 다시 수행하고 Phase 최종 내용에서도 검증한다. 실패·생략·중단·테스트 0개는 통과하지 않는다. 수정은 설정한 한도에서 멈추며 환경·권한·기획 문제는 코드 수정 재시도를 소모하지 않고 중단한다.
- 승인·검증 근거·결과 인수는 일치하는 계획·코드 버전에 연결한다. 같은 범위의 결함 피드백은 현재 Phase 수정으로, 요구사항 변경은 계획 갱신·승인으로 처리한다. 피드백 원문과 처리 결과를 저장한다.
- 구현 중단 시 부분 파일을 확인한다. 검사 중단 시 잔여 프로세스를 확인하고 필요한 검사를 다시 실행한다. 예상 밖 사용자 변경은 덮어쓰지 않고 중단하며 다른 Runner의 안전하지 않은 소유권 획득을 막는다. Git 메타데이터만 수동 변경된 경우 나머지 입력이 같으면 재개를 막지 않는다.
- 실제 역할별 호출 시도·확정된 시간과 미완료 구간·승인 대기·리뷰 지적에 안정적인 식별자를 부여한다. 재개 시 호출과 동일 지적을 중복 집계하지 않는다. 수정 확인에는 근거가 필요하고 보류한 필수 지적도 완료를 막는다. 알 수 없는 시간·토큰·금액을 추정하지 않는다.
- 성공·실패 모두 최소 보고서를 제공하고 산출물, 검사·재사용 근거, 미해결 항목, 수동 확인, 상세 기록 위치를 표시한다. 사용자 인수와 기술적 완료를 구분하며 인수로 미충족 필수 조건을 무시하지 않는다.
- 별도 준비된 예제에서 중단·재개와 사용자 인수를 포함해 작은 Phase를 완료한다. A의 코드·의존성·역할 지침·정책을 고정하고, 다음 Phase 전에 B와 테스트 프로세스가 A 및 실행·승인 저장소를 변경하지 못함을 입증한다.

**결과**: 구현·실제 Run·인수 근거가 없다. 모든 조건은 미검증이다.

## Workflow와 최소 결과 안내

### 목적 / 구현 파일

Phase 1 Runner·저장 계층과 Phase 2 Adapter를 확장한다. 기존 패키지 안에 결과 생성을 추가하고 테스트 아래에 임시 통합 예제를 둔다. 정확한 파일명은 상세화 시 정한다.

### 설계 결정 사항

- 단일 순차 Workflow와 기본 수정 2회 제안을 유지한다. Fast·Standard·Strict 분기와 병렬 Task는 추가하지 않는다.
- 이벤트 수집은 이 단계에서 모두 구현한다. 최소 검증 근거 조회도 준비하며 보고서의 작은 미완료 집계 항목은 Phase 4 자체 개발 대상으로 남긴다.
- 구현 Task가 없는 재사용 요구사항도 최종 인수에서 다시 확인한다. 범용 코드 분석·커버리지 엔진은 추가하지 않는다.
- A는 별도 설치·복사본으로 고정하며 B를 참조하는 editable 설치를 사용하지 않는다. 실행 기록은 OneDrive 밖에, B 테스트 기록은 임시 공간에 두고 권한을 제한한다. 실제 분리 시험 결과를 기록한다.

### 사용 예시

기본 테스트가 준비된 작은 Python CLI 예제에서 정상·잘못된 입력의 기대 동작이 명확한 입력 검증 변경 하나를 요청한다. 생성 Phase 검토·승인·실행 후 한 차례 중단하고 재개해 리뷰·검증 근거 확인과 인수까지 진행한다. 최종 예제와 명령은 이 Phase 상세화 때 정한다.

## 선행 조건 및 개발 시 주의사항

이전 구성요소는 회귀 근거와 함께 재사용한다. 핵심 보호 동작은 가짜 Adapter뿐 아니라 실제 작업 프로세스에서도 동작해야 한다. 권한·재개 결함이 있으면 실행용 A로 확정하지 않는다. 기존 코딩 도구로 결함을 고칠 수 있으며 수동 개입을 기록한다. 이 외부 예제는 전체 dogfooding 준비이며 자체 개발 실적 자체는 아니다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 전체 흐름 개요, 외부 예제 통과 조건과 고정 실행본 요구사항 최초 작성. |
