# P3-T7 External CLI Example — Result Review

**Date**: 2026-09-23. **Status**: T7 accepted and completed. Live technical checks and all 632 harness regressions passed; R1/M1 confirmations and explicit user acceptance are recorded.

The separate example now rejects negative integers while preserving integer doubling and argparse errors. Only the external project's `cli.py` and `test_cli.py` changed. The repository's starting fixture is unchanged. [Machine-readable evidence](Phase3_Example.json) records artifact hashes and actual runtime locations.

## Observed behavior

These six commands were executed inside AppContainer on a content-identical copy of the final application. Each output and exit code is recorded in the independent JUnit evidence.

| Command | Exit code | stdout | stderr result |
|---|---|---|---|
| `python cli.py 3` | 0 | `6` followed by newline | Empty |
| `python cli.py 0` | 0 | `0` followed by newline | Empty |
| `python cli.py -1` | 2 | Empty | `value must be nonnegative` |
| `python cli.py -42` | 2 | Empty | `value must be nonnegative` |
| `python cli.py not-an-int` | 2 | Empty | `argument value: invalid int value: 'not-an-int'` |
| `python cli.py` | 2 | Empty | `the following arguments are required: value` |

The complete negative-input stderr is:

```text
usage: cli.py [-h] value
cli.py: error: value must be nonnegative
```

## Execution and verification

- A reviewed controller-authored plan executed one Task. New Planner AI calls: **0**.
- Real AI role calls: **2**, one Developer and one independent Reviewer, with distinct sessions. Corrections: **0**; unresolved review findings: **0**.
- The controller exited with code **99** immediately after saving the Developer response. Public `workflow-resume --steps 1` recovered that same response with **0 additional AI calls**, preserving approval and correction counts.
- Original baseline: **2 passed**. Task validation: **8 passed**. Final registered validation: **8 passed**, with sealed artifacts. Independent CLI checks: **6 passed**.
- Completed-workflow resume preserved the run and events without repeating work.
- Main workflow and independent generated-code checks used standard-user AppContainer. The original trusted fixture baseline used the existing host baseline validator.
- **Full harness regression**: **632 passed**, zero failures/errors/skips, 1206.46 seconds (JUnit). All 77 source/test files match the starting manifest; `pip check` passed.

## User acceptance recorded

After receiving the behavior and verification results above, the user explicitly accepted the example with “결과 인수한다” on 2026-09-23. The public CLI recorded the confirmations and acceptance against the unchanged final code and validation. See the [acceptance evidence](Phase3_Example_Acceptance.json).

1. **R1 — reused behavior: passed.** The user accepted the presented evidence that the final eight-test suite preserves positive/zero doubling and missing/non-integer argument rejection. The six observed commands above provide additional independent evidence.
2. **M1 — error-message inspection: passed.** The user accepted the presented negative-input outputs: empty stdout, exit code 2, and a clear message requiring nonnegative input.
3. **Result acceptance: recorded.** `workflow-accept` succeeded, and `workflow-report` returned `stage=accepted`, `ready=true`, `accepted=true` and no blockers. T7 is complete; T8 has not started and overall Phase 3 acceptance remains pending.

Recording acceptance made no new AI calls or test runs. The original technical-run snapshots and all existing validation evidence are preserved.

Final validation ID: `20f5154c0ed4480a807a3bc3cec71f0f`.
Workflow ID: `02ee4d614527425fa2235542d76637fb`.
Final content version: `26cbd75c2f3509807fa2223329257122d0544981591378ee31f60ceba63047e1`.

Read the current result without launching workers:

```powershell
$harnessPython = "$env:LOCALAPPDATA/development-tools-harness/venv/Scripts/python.exe"
$t7Example = "$env:LOCALAPPDATA/development-tools-harness/t7-live/c2cc52b6323c"
& $harnessPython -m development_harness --project "$t7Example/project" --state-dir "$t7Example/state" workflow-report
```

---

# P3-T7 외부 CLI 예제 — 결과 확인

**날짜**: 2026-09-23. **상태**: T7 인수·완료. 실제 예제 기술 검증과 하네스 회귀 검사 632개 통과. R1·M1 확인과 명시적 사용자 인수를 기록했다.

별도 예제에 음수 입력 거부 기능을 추가했고 기존 정수 두 배 출력과 argparse 오류 처리를 유지했다. 외부 프로젝트의 `cli.py`·`test_cli.py`만 변경했으며 저장소의 시작 예제 원본은 유지했다. [검증 근거 JSON](Phase3_Example.json)에 파일 해시와 실제 실행 기록 경로를 기록한다.

## 실제 동작

최종 응용프로그램과 내용이 같은 복사본을 AppContainer에서 실행한 결과다. 각 출력과 종료 코드는 독립 JUnit 근거에 보존했다.

| 명령 | 종료 코드 | stdout | stderr 결과 |
|---|---|---|---|
| `python cli.py 3` | 0 | `6`과 줄바꿈 | 없음 |
| `python cli.py 0` | 0 | `0`과 줄바꿈 | 없음 |
| `python cli.py -1` | 2 | 없음 | `value must be nonnegative` |
| `python cli.py -42` | 2 | 없음 | `value must be nonnegative` |
| `python cli.py not-an-int` | 2 | 없음 | `argument value: invalid int value: 'not-an-int'` |
| `python cli.py` | 2 | 없음 | `the following arguments are required: value` |

음수 입력의 전체 stderr는 다음과 같다.

```text
usage: cli.py [-h] value
cli.py: error: value must be nonnegative
```

## 실행·검증 결과

- 검토한 제어 프로그램 작성 계획으로 Task **1개**를 실행했다. 새 Planner AI 호출은 **0회**다.
- 실제 AI 역할 호출은 Developer **1회**, 별도 Reviewer **1회**로 총 **2회**이며 세션이 서로 다르다. 수정 **0회**, 미해결 리뷰 지적 **0개**다.
- Developer 응답 저장 직후 제어 프로그램을 종료 코드 **99**로 중단했다. 공개 `workflow-resume --steps 1`로 **추가 AI 호출 없이** 같은 응답을 복구했고 승인·수정 횟수를 유지했다.
- 시작 검사 **2개**, Task 검사 **8개**, 최종 등록 검사 **8개**, 독립 CLI 검사 **6개**가 통과했다. 최종 등록 검사의 근거 해시를 봉인했다.
- 완료 후 재개를 다시 실행해 작업·이벤트가 중복되지 않음을 확인했다.
- 본 Workflow 및 생성 코드의 독립 검사는 일반 사용자 AppContainer를 사용했다. 변경 전 신뢰된 시작 예제는 기존 호스트 기본 검사기를 사용했다.
- **하네스 전체 회귀 검사**: **632개 통과**, 실패·오류·생략 0개, JUnit 기준 1206.46초. 소스·테스트 77개 파일이 시작 시점 해시와 일치하며 `pip check`도 통과했다.

## 사용자 인수 기록

위 동작과 검증 결과를 전달받은 사용자가 2026-09-23 “결과 인수한다”로 예제를 명시적으로 인수했다. 공개 CLI로 변경 없는 최종 코드·검사에 확인과 인수를 연결해 기록했다. [인수 근거](Phase3_Example_Acceptance.json)를 참고한다.

1. **R1 — 재사용 동작: 통과.** 최종 검사 8개가 양수·0의 두 배 출력과 인수 누락·비정수 거부를 유지한다는 제시된 근거를 사용자가 인수했다. 위 실제 명령 6개의 결과는 추가 독립 근거다.
2. **M1 — 오류 설명 확인: 통과.** 두 음수 입력 모두 stdout 없이 종료 코드 2를 반환하고 음수를 허용하지 않는다고 설명하는 제시된 결과를 사용자가 인수했다.
3. **결과 인수: 기록 완료.** `workflow-accept`가 성공했고 `workflow-report`에서 `stage=accepted`, `ready=true`, `accepted=true`, 차단 조건 없음을 확인했다. T7은 완료이며 T8은 미시작, Phase 3 전체 인수는 대기 중이다.

이번 인수 기록에서 새 AI 호출이나 테스트 실행은 없었다. 원래 기술 실행 시점의 보고서와 기존 검증 근거를 보존했다.

최종 검사 ID: `20f5154c0ed4480a807a3bc3cec71f0f`.
Workflow ID: `02ee4d614527425fa2235542d76637fb`.
최종 코드 버전: `26cbd75c2f3509807fa2223329257122d0544981591378ee31f60ceba63047e1`.

작업자를 호출하지 않고 현재 결과를 조회한다.

```powershell
$harnessPython = "$env:LOCALAPPDATA/development-tools-harness/venv/Scripts/python.exe"
$t7Example = "$env:LOCALAPPDATA/development-tools-harness/t7-live/c2cc52b6323c"
& $harnessPython -m development_harness --project "$t7Example/project" --state-dir "$t7Example/state" workflow-report
```
