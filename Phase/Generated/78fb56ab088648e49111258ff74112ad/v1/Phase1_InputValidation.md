# Phase 1 — Input Validation

> Reject negative integers with a useful ValueError while preserving zero and positive integer behavior.

**Status**: Planning draft; this document does not establish implementation, verification or user acceptance.

**Prerequisites**: Verify project readiness and unresolved questions.

**Technology**: Selected by the specification: Python with the existing value.py module and pytest setup. No new dependencies. Python and pytest versions are unspecified.

## Overview

Add negative-integer validation while preserving doubling for nonnegative integers. Use the existing Python module and pytest setup. This is a planning draft; implementation, test results and user acceptance are not established.

## Deliverables

Negative, zero and positive pytest cases pass; existing doubling behavior is preserved and no dependencies, UI or network access are added.

## Tasks & Verification

| Task | Work | Acceptance | Verification | Dependencies | Files |
| --- | --- | --- | --- | --- | --- |
| T1 | Add a negative-integer guard to the existing double function | double rejects negative integers with ValueError and a message explaining that the value must be nonnegative; zero returns 0 and positive integers return twice their input. Use the existing module without adding dependencies, UI or network access. | Review the guard and unchanged multiplication behavior; verify runtime outcomes with the pytest cases in T2. These checks are proposed, not executed. | — | value.py |
| T2 | Extend existing pytest coverage and verify regression behavior | Retain the existing zero and positive assertions and add negative-integer coverage using pytest.raises to check ValueError and a meaningful message. All cases pass without new dependencies. | Run pytest test_value.py and record its actual result. Inspect changes to confirm coverage of negative, zero and positive inputs and absence of added dependencies, UI or network calls. No tests have been run during planning. | T1 | test_value.py, value.py |

**Results**: Checks above are proposed. No Phase implementation or acceptance is established by generating this plan.

## Requirements Mapping

- **R1** Preserve doubling behavior for zero and positive integers. — reuse / phase-1

The existing multiplication and tests provide behavior to retain; reuse still requires regression verification.

Run the existing assertions double(0) == 0 and double(3) == 6 after adding validation.

```text
The project already doubles nonnegative integer values. Preserve that behavior.
```

- **R2** Reject negative integers with ValueError and a useful error message. — implement / phase-1

The supplied function currently multiplies without a negative-value guard.

Use pytest.raises to assert the exception type and that the message explains the nonnegative input requirement.

```text
Reject negative integers with ValueError and a useful error message.
```

- **R3** Cover negative, zero and positive inputs with pytest tests. — implement / phase-1

Zero and positive tests exist; negative-input exception coverage must be added.

Run pytest test_value.py and confirm all three input categories are covered and pass.

```text
Cover negative, zero and positive cases with pytest tests.
```

- **R4** Use the existing Python module and pytest setup. — reuse / phase-1

The specification selects Python and pytest, and the supplied files establish the existing function and test structure.

Confirm changes target value.py and test_value.py and verify that pytest collects and runs the tests in the existing environment.

```text
Use the existing Python module and pytest setup.
```

- **R5** Keep the change within the existing module and tests without adding dependencies, UI or network access. — implement / phase-1

A local input guard and existing pytest coverage are sufficient for the requested behavior.

Review changes for added dependencies, UI components and network calls; confirm none are introduced.

```text
No new dependencies, UI or network access are required.
```

## Related Code / Implementation Files

- `value.py` (explicit): Existing double function directly multiplies its input by two without validation.

```text
def double(value):
    return value * 2
```

- `test_value.py` (explicit): Existing positive-input regression assertion.

```text
assert double(3) == 6
```

- `test_value.py` (explicit): Existing zero-input regression assertion.

```text
assert double(0) == 0
```

## Development Notes

None reported.

## Change Log

| Date | Description |
|---|---|
| 2026-09-21 | Planning Run registered; draft and revisions use its pinned writing rules. |

Writing rules: `phase-doc` 1.1 · Snapshot: `0a0eb1be9e99ed9cc0a215502462d1e9a27ae1d2192b95b8f8639edee4dba64c`

---

# Phase 1 — 입력 검증

> 0과 양의 정수의 동작을 유지하면서 유용한 메시지를 포함한 ValueError로 음의 정수를 거부한다.

**상태**: 계획 초안. 이 문서가 구현·검증·사용자 인수 완료를 뜻하지 않는다.

**선행 조건**: 프로젝트 준비 상태와 미해결 질문을 확인한다.

**기술 구성**: 명세에서 선택한 기술: 기존 value.py 모듈을 사용하는 Python 및 기존 pytest 구성. 새 의존성은 추가하지 않는다. Python과 pytest 버전은 명시되지 않았다.

## 개요

음이 아닌 정수를 두 배로 만드는 기존 동작을 유지하면서 음의 정수 검증을 추가한다. 기존 Python 모듈과 pytest 구성을 사용한다. 이 문서는 계획 초안이며 구현, 테스트 결과, 사용자 인수 완료를 입증하지 않는다.

## 완료 예정 항목

음수, 0, 양수에 대한 pytest 검사가 통과하고 기존 두 배 계산 동작이 유지되며 의존성, UI, 네트워크 접근이 추가되지 않는다.

## Task 및 검증

| Task | 작업 | 완료 기준 | 검증 방법 | 선행 작업 | 파일 |
| --- | --- | --- | --- | --- | --- |
| T1 | 기존 double 함수에 음의 정수 검증 추가 | double은 음의 정수에 대해 값이 음수가 아니어야 함을 설명하는 메시지와 함께 ValueError를 발생시킨다. 0은 0을 반환하고 양의 정수는 입력의 두 배를 반환한다. 의존성, UI, 네트워크 접근을 추가하지 않고 기존 모듈을 사용한다. | 검증 조건과 기존 곱셈 동작의 유지를 검토하고 T2의 pytest 사례로 실행 결과를 확인한다. 이 검사는 수행 예정이며 아직 실행되지 않았다. | — | value.py |
| T2 | 기존 pytest 검사 확장 및 회귀 동작 검증 | 기존 0과 양수 단언문을 유지하고 pytest.raises로 ValueError와 의미 있는 메시지를 확인하는 음의 정수 검사를 추가한다. 새 의존성 없이 모든 사례가 통과한다. | pytest test_value.py를 실행하고 실제 결과를 기록한다. 변경 사항을 검토하여 음수, 0, 양수 입력의 검사 여부와 의존성, UI, 네트워크 호출이 추가되지 않았음을 확인한다. 계획 단계에서는 테스트를 실행하지 않았다. | T1 | test_value.py, value.py |

**결과**: 위 검사는 수행할 계획이다. 계획 생성으로 해당 Phase의 구현이나 인수가 완료된 것은 아니다.

## 요구사항 대응표

- **R1** 0과 양의 정수를 두 배로 만드는 동작을 유지한다. — reuse / phase-1

기존 곱셈 로직과 테스트를 유지하며, 재사용하더라도 회귀 검증이 필요하다.

검증 로직 추가 후 기존 double(0) == 0 및 double(3) == 6 단언문을 실행한다.

```text
The project already doubles nonnegative integer values. Preserve that behavior.
```

- **R2** 유용한 오류 메시지를 포함한 ValueError로 음의 정수를 거부한다. — implement / phase-1

제공된 함수는 현재 음수 검증 없이 곱셈을 수행한다.

pytest.raises로 예외 유형과 메시지가 음수가 아닌 입력 조건을 설명하는지 확인한다.

```text
Reject negative integers with ValueError and a useful error message.
```

- **R3** pytest 테스트로 음수, 0, 양수 입력을 검사한다. — implement / phase-1

0과 양수 테스트가 있으므로 음수 입력의 예외 검사를 추가해야 한다.

pytest test_value.py를 실행하고 세 입력 범주가 모두 검사되며 통과하는지 확인한다.

```text
Cover negative, zero and positive cases with pytest tests.
```

- **R4** 기존 Python 모듈과 pytest 구성을 사용한다. — reuse / phase-1

명세에서 Python과 pytest를 지정했으며 제공된 파일에서 기존 함수와 테스트 구조를 확인할 수 있다.

변경 대상이 value.py와 test_value.py인지 확인하고 기존 환경에서 pytest가 테스트를 수집하고 실행하는지 검증한다.

```text
Use the existing Python module and pytest setup.
```

- **R5** 의존성, UI, 네트워크 접근을 추가하지 않고 기존 모듈과 테스트 범위에서 변경한다. — implement / phase-1

요청한 동작은 로컬 입력 검증과 기존 pytest 검사만으로 구현할 수 있다.

변경 사항에 추가된 의존성, UI 구성 요소, 네트워크 호출이 없는지 검토한다.

```text
No new dependencies, UI or network access are required.
```

## 관련 코드 / 구현 파일

- `value.py` (explicit): 기존 double 함수는 검증 없이 입력에 2를 곱한다.

```text
def double(value):
    return value * 2
```

- `test_value.py` (explicit): 기존 양수 입력 회귀 검사용 단언문.

```text
assert double(3) == 6
```

- `test_value.py` (explicit): 기존 0 입력 회귀 검사용 단언문.

```text
assert double(0) == 0
```

## 개발 시 주의사항

보고된 질문 없음.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-21 | 계획 Run 등록. 초안·수정본은 해당 Run에 고정한 작성 규칙을 사용한다. |

작성 규칙: `phase-doc` 1.1 · 원문 식별자: `0a0eb1be9e99ed9cc0a215502462d1e9a27ae1d2192b95b8f8639edee4dba64c`
