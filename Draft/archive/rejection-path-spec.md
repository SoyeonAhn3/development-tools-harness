> **보관 문서**
> 이 문서의 내용은 `ai-development-harness-mvp-plan-v0.5.md`에 흡수되었다.
> v0.5 작성 과정의 설계 기록으로 보존한다. 최신 기준은 v0.5를 따른다.

# 반려 경로 명세

작성일: 2026-09-14
문서 상태: 확정 (사용자 확인 완료)
관련 결정: `harness-decision-record.md` D-14, D-21~D-23
반영 대상: `ai-development-harness-mvp-plan.md` v0.5 신설 절

---

## 1. 목적

사용자가 승인을 거절했을 때 무엇이 어떻게 되는지를 정의한다. MVP v0.4와 v0.1 모두 승인 지점만 정의하고 거절 경로가 없었다. 요구사항의 "사용자는 개발 산출물을 확인한다"에서 확인의 절반은 반려이며, 반려 경로가 없으면 승인 지점 자체가 성립하지 않는다.

## 2. 원칙

1. **반려는 실패가 아니다.** `FAILED`(시스템이 수행하지 못함)와 `REJECTED`(사람이 수용하지 않음)를 구분한다. 반려는 `max_retries` 계산에 포함하지 않는다.
2. **반려해도 폐기하지 않는다.** 코드·커밋·브랜치를 자동으로 되돌리지 않는다. 사용자가 명시적으로 요청할 때만 폐기한다.
3. **반려 유형이 다음 행동을 결정한다.** 자유 서술만으로는 재진입 지점을 정할 수 없다.
4. **AI는 반려를 분류만 한다.** 상태 전이는 사용자 확인 후 Orchestrator가 수행한다.

---

## 3. 승인 지점과 반려 유형

### 3.1 승인 ①② — 계획 반려

전체 Phase 계획과 현재 Phase Task 계획에 적용한다. 구현 전이므로 코드 영향이 없다.

| 유형 | 의미 | 재진입 지점 |
|---|---|---|
| `SCOPE` | 무엇을 만들지가 틀림 | Planner 전체 재계획 |
| `DECOMPOSE` | 범위는 맞으나 분해가 잘못됨 | Planner 재분해, 목표는 유지 |
| `CRITERIA` | 완료 기준이 부족하거나 틀림 | `acceptance_criteria`만 수정 |
| `RISK` | 위험 분류·Workflow가 부적절 | `risk_tags` 수정 후 Workflow 재선택 |
| `ORDER` | 의존성·순서가 틀림 | `depends_on`만 수정 |

재계획 범위를 유형에 맞게 좁혀 Planner에게 전달한다. `CRITERIA` 반려에 전체 계획을 다시 생성하지 않는다.

### 3.2 승인 ③ — 실행 중 고위험 결정 반려

| 유형 | 의미 | 처리 |
|---|---|---|
| `DENY_ALT` | 이 방법은 불가, 다른 방법을 찾는다 | 거부된 방법을 제약으로 전달하고 Developer 재구현 |
| `DENY_STOP` | 이 Task를 중단한다 | Task `BLOCKED`, 다음 실행 가능 Task로 진행 |
| `DENY_REPLAN` | 계획 자체를 다시 세운다 | Phase `REPLAN_REQUIRED` |

`DENY_ALT`는 거부 사유를 Developer Context에 포함해 같은 방법을 다시 제안하지 않게 한다.

### 3.3 승인 ④ — Phase 결과 반려

| 유형 | 의미 | 대상 Task 처리 | 커밋 |
|---|---|---|---|
| `NOT_WORKING` | 동작하지 않음 | `COMPLETED` → `REWORK_REQUIRED` | 보존 |
| `QUALITY` | 동작하지만 품질 미달 | `COMPLETED` → `REWORK_REQUIRED` | 보존 |
| `MISSING` | 빠진 것이 있음 | 새 Task 생성, 기존 Task는 완료 유지 | 보존 |
| `WRONG_REQ` | 요구사항을 잘못 이해함 | Phase `REPLAN_REQUIRED` | 보존 |
| `ABANDON` | Phase 자체를 버림 | Phase `ABANDONED` | 보존 |

Task는 요구사항 단위이지 작업 시도 단위가 아니다. 따라서 재작업은 새 Task를 만들지 않고 해당 Task를 되돌린다. 시도 이력은 SQLite에 별도로 보존한다. `MISSING`만 새 요구사항이므로 새 Task를 생성한다.

`ABANDON` 시 브랜치와 커밋을 보존하며 삭제는 사용자가 직접 수행한다. 폐기된 Phase에 의존하는 후속 Phase는 실행하지 않고 계획 수정을 요청한다.

### 3.4 승인 ⑤ — Push / Merge 반려

상태 전이가 없다. Phase는 `ACCEPTED`를 유지하고 브랜치는 로컬에 남는다. 이후 다시 요청할 수 있다. 재요청 시점에 코드가 변경되었으면 기존 인수를 그대로 사용하지 않는다.

### 3.5 승인 ⑥ — Task 결과 반려 (선택 기능)

`approval.task_result: ask`로 켠 경우에만 발생한다. 커밋 전 단계이므로 처리가 단순하다.

| 유형 | 처리 |
|---|---|
| `NOT_WORKING` / `QUALITY` | 커밋하지 않고 `REWORK_REQUIRED`로 전환 |
| `WRONG_REQ` | Task 정의 수정 후 계획 승인 절차 |

---

## 4. 반려 입력 흐름

사용자는 유형 이름을 알 필요가 없다. 자연어로 입력하고 하네스가 분류한 결과를 확인한다.

```text
devh reject APR-004
   ↓
"무엇이 문제인가요?" 자연어 입력
   ↓
AI가 분류: 반려 유형 / 대상 Task / 재작업 지시 요약
   ↓
사용자에게 해석 결과 제시
   ↓
사용자 확인 → SQLite 기록 → 상태 전이
```

제시 형식 예시.

```text
다음과 같이 이해했습니다.

  대상    P1-T5 로컬 OCR 어댑터
  유형    동작하지 않음
  지시    OCR 실패 페이지가 빈 문자열로 반환되어 정상 결과와 구분되지 않음
  영향    P1-T5를 재작업 대상으로 되돌립니다. 나머지 7개 Task의 완료는 유지됩니다.
          P1-T5의 기존 커밋은 삭제하지 않습니다.

이대로 진행할까요?
```

- 사용자 확인 전에는 어떤 상태도 바꾸지 않는다. 확인 행위가 반려 기록의 근거가 된다.
- 대상 Task를 특정할 수 없거나 유형이 모호하면 진행하지 않고 되묻는다.
- 분류를 건너뛰려면 `devh reject APR-004 --type quality --tasks P1-T5 --note "..."`를 사용한다.
- 반려 취소는 지원하지 않는다. 잘못 반려했다면 재작업 없이 다시 승인 요청 흐름을 진행한다.

---

## 5. 부분 반려

Phase 결과 반려에서 대상 Task를 지정할 수 있다.

- 지정된 Task만 `REWORK_REQUIRED`로 전환한다.
- 나머지 Task의 완료와 커밋은 유지한다.
- 재작업 Task가 모두 완료되면 Phase 결과 승인을 다시 요청한다.
- 재요청 시 결과 자료에는 이전 반려 내용과 처리 결과를 포함한다.

Task 하나의 문제로 Phase 전체를 다시 검증하지 않는다.

---

## 6. 반려 후 유효성 재확인

계획이 반려되어 수정되면 `plan_revision`이 증가한다. 무효화 범위는 다음과 같다.

| 변경 대상 | 무효화 범위 |
|---|---|
| 특정 Task 정의만 변경 | 해당 Task의 승인·검증 결과 |
| 공통 Domain Rule 변경 | 해당 Phase의 모든 Task |
| 실행 설정(검증 명령·필수 여부) 변경 | 해당 Phase의 모든 Task |
| 변경 없는 Task | 완료 유지 |

판정은 Task 정의의 hash 비교로 수행한다. 이미 커밋된 Task를 무조건 전부 무효화하면 Phase 하나가 통째로 다시 실행되어 실사용이 불가능하다.

---

## 7. 반복 제한

- **계획 반려 3회 초과**: 자동 재계획을 중단하고 하네스가 계획을 수립하지 못하는 상태로 보고한다. 같은 입력으로 AI를 반복 호출해도 결과가 달라지지 않는다.
- **같은 Task 3회 이상 결과 반려**: 재작업은 계속하되 Phase 범위 재검토를 제안한다.
- 반려 횟수는 `max_retries`와 별도로 집계한다.

---

## 8. 기록

SQLite에 다음을 저장한다.

| 항목 | 내용 |
|---|---|
| 반려 기록 | 승인 ID, 대상(Phase 또는 Task 목록), 유형, 사용자 자연어 원문, AI 분류 결과, 사용자 확인 시각, 당시 `plan_revision` |
| 시도 이력 | Task별 시도 번호, 시작·종료, 결과, 커밋 SHA, 무효화 사유 |
| 반려 횟수 | Phase별 계획 반려 횟수, Task별 결과 반려 횟수 |

Phase Report에는 반려 횟수, 유형, 사유 요약, 재작업 결과를 포함한다.

---

## 9. 상태

반려와 관련된 상태만 정의한다. 전체 상태 전이도는 별도 작업(D-19)에서 작성한다.

```text
Phase
  PLAN_PENDING_APPROVAL ──reject──> PLAN_REJECTED ──replan──> PLAN_PENDING_APPROVAL
  RESULT_PENDING_APPROVAL ──reject──> RESULT_REJECTED ──rework──> IN_PROGRESS
                                   └─ WRONG_REQ ──> REPLAN_REQUIRED
                                   └─ ABANDON ──> ABANDONED
  RESULT_PENDING_APPROVAL ──approve──> ACCEPTED

Task
  COMPLETED ──reject──> REWORK_REQUIRED ──> IN_PROGRESS
  IN_PROGRESS ──DENY_STOP──> BLOCKED
```

`REJECTED` 계열과 `FAILED`는 다른 상태다. `FAILED`는 재시도 한도 초과나 실행 환경 문제이며, `REJECTED`는 사용자 판단이다.

---

## 10. 명령

```text
devh reject <approval-id>
devh reject <approval-id> --note "<자연어 사유>"
devh reject <approval-id> --type <유형> --tasks <task-ids> --note "<사유>"
devh rejections [phase-id]
```
