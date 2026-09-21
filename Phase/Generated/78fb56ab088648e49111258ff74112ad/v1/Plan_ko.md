# 개발 Phase 계획

음이 아닌 정수를 두 배로 만드는 기존 동작을 유지하면서 음의 정수 검증을 추가한다. 기존 Python 모듈과 pytest 구성을 사용한다. 이 문서는 계획 초안이며 구현, 테스트 결과, 사용자 인수 완료를 입증하지 않는다.

## 전체 Phase

### phase-1 — 입력 검증

0과 양의 정수의 동작을 유지하면서 유용한 메시지를 포함한 ValueError로 음의 정수를 거부한다.

음수, 0, 양수에 대한 pytest 검사가 통과하고 기존 두 배 계산 동작이 유지되며 의존성, UI, 네트워크 접근이 추가되지 않는다.

## Phase 문서

- [phase-1 — 입력 검증](Phase1_InputValidation.md)

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

## 확인할 사항과 선행 조건

보고된 질문 없음.

계획 승인은 구현 실행을 승인하지 않는다. 재사용 제안에도 실제 최종 검증이 필요하다.

작성 규칙: `phase-doc` 1.1 · 원문 식별자: `0a0eb1be9e99ed9cc0a215502462d1e9a27ae1d2192b95b8f8639edee4dba64c`
