# 개발 계획

Phase 3의 실제 순차 흐름, 근거 수집, 수정·재개, 최소 결과 안내와 고정 실행본 A를 위한 외부 예제 통과 조건을 상세화한다. 제공된 근거에서 Phase 2 인수는 아직 대기 중이며 해당 선행 조건과 작업 프로세스 분리 경계가 해결되어야 구현할 수 있다. Phase 3의 모든 조건은 미검증이다. 계획 승인으로 구현을 시작하지 않는다.

## 전체 Phase

### Phase2 — Phase 2 — 계획 선행 조건

Phase 3 실행 전에 계획 기능 인수와 권한 검증을 확보한다.

완료 기준: Phase 2 인수 근거가 있으며 검증된 권한의 한계가 명시되어 있다.

### Phase3 — Phase 3 — 전체 실행 흐름

실제 구현·검증·독립 리뷰·제한된 수정·재개·최소 인수를 연결한다.

완료 기준: 통합·회귀 검사와 인수된 외부 예제로 전체 흐름·중단 복구·실제 프로세스 보호를 입증하고 별도로 고정한 A를 B 및 테스트와 분리한다.

### Phase4 — Phase 4 — 자체 개발과 보고서 표현

검증된 A로 남은 작은 보고서 집계와 자체 개발을 수행한다.

완료 기준: 후속 승인된 자체 개발 Phase에서 남은 보고서 표현을 완성하며 상세 내용은 Phase 3 근거에 따라 정한다.

## 현재 Phase Task: Phase3

### P3-T1 — 선행 조건·실행 계약·준비된 CLI 예제 확정

요구사항: R1, R2, R12

파일: Phase/Phase3_Workflow.md, src/development_harness/model.py, src/development_harness/plan_schema.py, tests/fixtures/workflow_project/cli.py, tests/fixtures/workflow_project/test_cli.py, tests/fixtures/workflow_project/spec.md

선행 Task: —

완료 기준: 후속 구현 전에 Q1–Q2를 해결한다. 선행 조건 근거와 현재 Phase Task·검사·수정 한도의 실행 계약을 기록한다. workflow_project 파일 3개는 신규 제안 경로다. 제안 예제는 정수를 두 배로 출력하는 CLI이며 기본 검사는 양수·0을 다룬다. 한정된 변경 하나로 음수 입력에 명확한 오류와 0이 아닌 종료 코드를 반환하고 정상 출력을 유지한다. 실제 예제 전에 정확한 기본 검사·CLI 명령과 기대 출력을 기록한다.

검증 방법: Phase 2 인수·권한 근거를 확인하고 예제의 임시 복사본에서 python -m pytest -q로 기본 검사를 수행한다. 한정된 변경 기획과 실행 계약을 Phase 3와 대조한다. 선행 근거가 없으면 실행을 막는다.

### P3-T2 — 검증된 작업 경계로 단일 Adapter 확장

요구사항: R2, R3, R13

파일: src/development_harness/codex_adapter.py, src/development_harness/codex_probe.py, src/development_harness/processes.py, src/development_harness/gate.py, src/development_harness/validation.py, tests/integration/test_workflow_permissions.py

선행 Task: P3-T1

완료 기준: Q2에서 확정한 경계로 선정된 Adapter의 실제 Developer와 별도로 생성한 Reviewer 세션을 지원한다. 작업 권한은 승인된 대상 내용 수정으로 제한하고 제어 실행본의 승인·정책 저장소 접근을 차단하며 테스트 자손 프로세스에도 경계를 적용한다. 기존 텍스트 전용 Planner 경계를 유지한다. 통합 테스트 경로는 신규 제안이다. 활성 실행 기록을 직접 편집하지 않는다.

검증 방법: 실제 작업·자손 프로세스와 폐기 가능한 보호 대상을 사용해 허용된 대상 변경과 보호 영역 쓰기의 사전 차단을 입증한다. 프롬프트나 가짜 응답만이 아니라 선정된 실제 CLI의 역할 경계를 검증한다. Planner 기능·호환성 회귀 검사를 수행하며 경계가 없으면 실제 흐름을 차단한다.

### P3-T3 — 실제 호출·시간·지적과 버전별 실행 진입 기록

요구사항: R2, R6, R9

파일: src/development_harness/store.py, src/development_harness/planning.py, src/development_harness/runner.py, src/development_harness/cli.py, tests/unit/test_workflow_records.py

선행 Task: P3-T2

완료 기준: 검토한 계획과 시작 내용 식별자를 참조하는 제어 실행본 소유의 실행 진입을 추가하고 계획 전용 승인과 명시적 실행 승인을 구분한다. 고유 역할 시도·실행 여부·세션 ID·확정 및 미확정 시간·승인 대기·지적 ID를 원자적으로 저장한다. 근거를 계획·코드 버전에 연결하며 사용량은 관측값만 기록한다. 단위 테스트 경로는 신규 제안이다.

검증 방법: 임시 저장소에서 실행 전·후 및 상태·이벤트 저장 중 종료를 주입한다. 롤백 일관성·안정적인 ID·재처리 중복 집계 방지·미확정 시간과 사용량의 null 유지·오래된 버전 거부를 확인한다. 기존 plan-approve는 여전히 구현을 실행하지 않아야 한다.

### P3-T4 — 순차 실행·근거 기반 리뷰·제한된 수정 연결

요구사항: R3, R4, R5, R9

파일: src/development_harness/runner.py, src/development_harness/model.py, src/development_harness/validation.py, tests/integration/test_workflow.py

선행 Task: P3-T3

완료 기준: 승인된 Task를 의존 순서에 따라 Developer·필수 검증·별도 Reviewer 세션으로 실행한다. 리뷰는 요구사항·실제 파일·테스트를 대조한다. 필수 지적은 일치하는 후속 리뷰·검증으로만 해결하고 보류된 필수 지적도 완료를 막는다. 수정 후와 Phase 최종 내용에서 검사를 다시 수행한다. 설정 가능한 한도와 제안 기본값 2회를 사용하며 환경·권한·기획 문제 중단은 코드 수정 횟수를 소모하지 않는다. 통합 테스트 경로는 신규 제안이다.

검증 방법: 순서가 있는 Task 2개·반복 지적·거짓 수정 보고·필수 지적 보류·한도 0회와 2회·한도 소진을 검사한다. 실제 pytest로 실패·생략 및 혼합 테스트·테스트 0개·시간 초과·도구 누락을 확인한다. 검사 미충족 시 진행하지 않고 최종 근거를 최종 내용과 대조한다.

### P3-T5 — 실제 구현·검증의 안전한 재개 구현

요구사항: R7, R8, R9, R13

파일: src/development_harness/runner.py, src/development_harness/files.py, src/development_harness/processes.py, tests/integration/test_workflow_resume.py, tests/unit/test_state.py

선행 Task: P3-T4

완료 기준: 추가 변경 전에 실제 구현의 부분 파일을 확인하고 모호한 내용·사용자 편집을 보존한다. 중단된 필수 검사를 다시 실행하기 전에 작업 프로세스 식별자와 자손을 확인한다. 동시 실행·다른 저장소를 통한 위험한 소유권 획득을 막는다. 재개는 호출·지적 중복 없이 기존 기록을 사용한다. 재개 테스트 경로는 신규 제안이며 Git 작업 없이 폐기 가능한 파일시스템 예제로 메타데이터 전용 변경 동작을 검증한다.

검증 방법: 기록·실행 경계에서 실제 구현·검증 제어 프로세스를 종료하고 부분 파일을 확인하며 자손 정리 또는 재개 차단을 입증한다. 다른 상태 디렉터리를 포함해 편집기·두 번째 실행본과 경쟁시킨다. 전후 내용과 ID를 비교하고 메타데이터 전용 예제 변경은 나머지가 동일한 실행의 재개를 허용해야 한다.

### P3-T6 — 최소 결과·피드백·최종 재사용 및 인수 조건 추가

요구사항: R6, R10, R11, R14

파일: src/development_harness/results.py, src/development_harness/runner.py, src/development_harness/planning.py, src/development_harness/cli.py, tests/integration/test_workflow_results.py

선행 Task: P3-T5

완료 기준: 신규 제안 results.py와 test_workflow_results.py에서 성공·실패 보고서에 산출 파일·검증 및 재사용 근거·미해결 항목·수동 확인·상세 기록 위치를 제공한다. 피드백 원문과 처리 결과를 유지하며 같은 범위 결함은 현재 Phase 수정을 재개하고 요구사항 변경은 계획 갱신·승인을 요구한다. Task가 없는 항목을 포함해 현재 재사용 요구사항 모두를 최종 내용에서 재확인한다. 필수 근거 누락은 인수를 막고 기술적 완료와 사용자 인수를 구분한다. 작은 집계 표현은 Phase 4에 남긴다.

검증 방법: 성공·수정 한도 소진·중단·권한 실패 보고서를 검사하고 근거 위치를 확인한다. 두 피드백 유형에서 이력 보존·버전 무효화를 검증한다. 누락·오래됨·실패 상태의 재사용 근거와 수동 확인, 완료 전 인수, 최종 파일 편집을 검사한다. 필수 조건 미충족 시 모두 인수를 차단해야 한다.

### P3-T7 — 실제 역할과 사용자 인수로 외부 예제 완료

요구사항: R1, R12, R13

파일: tests/fixtures/workflow_project/cli.py, tests/fixtures/workflow_project/test_cli.py, tests/fixtures/workflow_project/spec.md, tests/integration/test_workflow.py, Phase/Phase3_Workflow.md

선행 Task: P3-T6

완료 기준: 신규 제안 workflow_project 예제의 별도 임시 복사본과 준비된 의존성을 사용한다. 계획 검토·명시적 실행 승인·실제 Developer/Reviewer 호출·검증·한 차례 중단·재개·최소 보고서를 통해 정한 변경을 수행한다. 필수 검사 충족 후 실제 사용자 결과 인수를 받는다. 실제 명령·ID·근거·수동 개입을 기록하며 자체 개발 실적으로 계산하지 않는다.

검증 방법: 전체 pytest 회귀 검사와 실제 예제의 정상·잘못된 입력 출력, 별도 역할 세션, 최종 해시, 중단 근거와 인수를 확인한다. 실패나 인수 대기는 그대로 기록하며 자동 예제 인수로 사용자 인수를 대체하지 않는다.

### P3-T8 — 승격 전 실행본 A 고정과 분리 입증

요구사항: R13, R15

파일: pyproject.toml, src/development_harness/processes.py, src/development_harness/store.py, tests/integration/test_workflow_permissions.py, Phase/Phase3_Workflow.md

선행 Task: P3-T7

완료 기준: A를 코드·의존성·역할 및 정책 지침이 고정된 별도 설치·복사본으로 준비하고 수정 가능한 B와 독립시킨다. 실행 기록은 OneDrive 밖에 두고 B 테스트는 제한된 권한으로 임시 기록을 사용한다. 설치 모듈 위치·버전 및 내용 식별자·실제 분리 시험 결과를 기록한다. 권한·재개 결함이 있으면 승격하지 않고 수동 수정과 해당 재검사를 기록한다. 활성 승인·정책 기록을 편집하거나 자체 개발을 시작하지 않는다.

검증 방법: A가 B의 모듈을 가져오지 않고 고정 산출물 식별자가 유지되는지 확인한다. 실제 B 작업·테스트 자손 프로세스로 A와 실행·승인 저장소의 폐기 가능한 보호 복제 대상을 시험해 쓰기 거부와 임시 테스트 기록 허용을 입증한다. Phase 3 종료 전에 설치된 A의 CLI 흐름·재개를 재검사하고 외부 예제 인수를 확인한다.

## 요구사항 대응표

- **R1** 실행 전에 Phase 2 인수·권한 검증·준비된 예제를 요구한다. — reuse / Phase3
  이전 작업은 선행 조건이며 새로운 Phase 번호로 다시 시작할 작업이 아니다.
  선행 인수·권한 기록을 확인하고 준비된 기본 검사를 다시 수행한다. 제공 자료만으로 준비 완료가 입증되지 않는다.

  원문 근거: **Prerequisites**: [Phase 2](Phase2_Planning.md) accepted, permissions verified and a prepared example available.

- **R2** Python·pytest·SQLite로 기존 Runner·저장 계층·단일 Adapter를 확장하고 패키지에 결과 생성, tests 아래에 임시 예제를 둔다. — implement / Phase3
  기존 모듈은 기반을 제공하지만 실제 실행은 명시적으로 부재한다.
  패키지 배치를 확인하고 선정된 기술 구성으로 이전 구성요소 회귀 검사를 수행한다.

  원문 근거: Extend the Phase 1 runner/storage and Phase 2 Adapter. Add result generation inside the existing package and temporary integration examples under tests; exact filenames are deferred.

- **R3** 승인된 Task를 순차 실행하고 별도 세션에서 요구사항·구현·테스트를 리뷰하며 필수 수정에는 독립적인 후속 근거를 요구한다. — implement / Phase3
  제공된 Runner는 현재 합성 Developer·Reviewer 결과를 사용한다.
  실제 역할 호출 순서를 확인하고 리뷰·검증 없는 수정 자기 보고의 거부를 검사한다.

  원문 근거: An approved small Phase executes Tasks sequentially. The Reviewer uses a separate session and checks requirements, actual implementation and tests. Required findings must have follow-up review/validation evidence; Developer self-report is insufficient.

- **R4** 변경 후와 최종 내용에서 검증하며 실패·생략·중단·테스트 0개는 통과로 처리하지 않는다. — implement / Phase3
  검증 분류를 재사용하면서 실제 구현과 최종 완료 조건에 연결한다.
  실제 결과별 예제를 실행하고 최종 근거 해시가 최종 코드와 일치하는지 확인한다.

  원문 근거: Required validation runs after changes and on final Phase content. Failed, skipped, interrupted and zero-test outcomes do not pass.

- **R5** 제안 기본값 2회를 유지하는 설정 한도로 수정을 제한하고 환경·권한·기획 문제는 코드 수정 횟수 소모 없이 중단한다. — implement / Phase3
  실제 역할 실패에는 기존 합성 수정 처리 외에 명시적인 분류가 필요하다.
  한도 소진과 코드 외 중단 사유를 검사하고 제안 기본값이 실행 계약에 기록되는지 확인한다.

  원문 근거: Corrections stop at the configured limit; environment/permission/specification problems stop without spending code-fix retries.

- **R6** 승인·근거·인수를 일치하는 계획·코드 버전에 연결하고 피드백을 보존하며 결함과 요구사항 변경을 올바르게 처리한다. — implement / Phase3
  기존 계획 승인은 계획 전용이며 실행·결과 연결과 피드백은 확장이 필요하다.
  오래된 버전·두 피드백 경로·피드백 원문 보존과 처리 결과 기록을 검사한다.

  원문 근거: Approval/evidence/result acceptance reference matching plan and code versions. Same-scope defect feedback reopens correction in the current Phase; changed requirements update the plan and approval. Store the original feedback and outcome.

- **R7** 재개 시 부분 구현·잔여 검사 프로세스를 확인하고 예상 밖 사용자 편집을 보존하며 위험한 소유권 획득을 막는다. — implement / Phase3
  알려진 합성 쓰기만으로 실제 작업 변경의 안전한 복구가 입증되지 않는다.
  임시 저장소에서 실제 프로세스 종료·편집 경쟁·실행본 경쟁을 검사한다.

  원문 근거: Interrupted implementation inspects partial files; interrupted validation checks remaining processes and reruns required checks. Unexpected user edits stop without overwrite, and another runner cannot acquire unsafe ownership.

- **R8** 수동 Git 메타데이터만 바뀐 경우 내용이 동일한 실행을 허용한다. — reuse / Phase3
  내용 스냅샷이 이미 .git을 제외하지만 최종 회귀 근거는 여전히 필요하다.
  Git 명령 없이 실제 흐름 재개에서 메타데이터 디렉터리·포인터 파일 예제 회귀 검사를 다시 수행한다.

  원문 근거: Metadata-only manual Git changes do not block an otherwise unchanged run.

- **R9** 실제 이벤트 전체를 지금 수집하고 호출·시간·대기·지적 ID를 안정적으로 유지하며 재개 중복·미확정 추정을 피하고 보류 필수 지적도 완료를 막는다. — implement / Phase3
  보고서 집계 일부를 Phase 4에 남겨도 전체 수집은 지금 필요하다.
  종료·반복 리뷰 후 이벤트 기록을 대조하고 미확정 null·실제 실행 횟수·수정 근거를 확인한다.

  원문 근거: Actual role-call attempts, completed/incomplete times, approval waiting and findings have stable identities. Resume does not double-count calls or repeated findings. Confirmed fixes have evidence; deferred mandatory findings still block completion. Do not estimate unknown duration, tokens or money.

- **R10** 최소 성공·실패 보고서를 제공하고 필수 기준 우회 없이 기술적 완료와 사용자 인수를 구분한다. — implement / Phase3
  현재 상태 출력은 요구된 실제 흐름 결과 인터페이스가 아니다.
  성공·실패 보고서의 필수 필드를 확인하고 필수 조건 미충족 인수를 거부한다.

  원문 근거: Minimum reports exist for success and failure and show delivered files, validation/reuse evidence, unresolved items, manual checks and detailed-record locations. User acceptance is separate from technical completion and cannot override unmet mandatory criteria.

- **R11** 구현 Task가 없는 재사용 요구사항도 최종 인수에서 재확인한다. — implement / Phase3
  요구사항 대응표만으로 최종 검증이 되지 않는다.
  필수 재사용 전용 요구사항을 포함하고 근거 누락·오래됨이 인수를 막는지 입증한다.

  원문 근거: Recheck reused requirements at final acceptance even without an implementation Task.

- **R12** 기본 테스트와 한정된 입력 검증 변경을 갖춘 별도 Python CLI 예제에서 중단·재개와 실제 사용자 인수까지 완료한다. — implement / Phase3
  기획서가 예제 선정을 Phase 3 상세화에 맡겼으므로 제안 예제를 검토 가능한 후보로 제공한다.
  외부 복사본의 실제 명령·정상 및 잘못된 입력 동작·역할 근거·중단·사용자 인수를 기록한다.

  원문 근거: Use a prepared small Python CLI example with baseline tests, then request one bounded input-validation change with expected normal and invalid-input behavior. Review the generated Phase, approve, execute, interrupt once, resume, inspect review/validation evidence and accept.

- **R13** 실제 프로세스로 핵심 보호를 검증하고 권한·재개 결함 시 A 승격을 막으며 수동 개입을 기록한다. — implement / Phase3
  기존 Job 제어는 명시적으로 권한 샌드박스를 제공하지 않는다.
  승격 전에 실제 프로세스 권한·재개 근거와 결함·개입 기록을 요구한다.

  원문 근거: Core protections must work with actual worker processes, not only the fake Adapter. A permissions or resume defect blocks promotion to runner A. Existing coding tools may fix such defects; record that manual intervention.

- **R14** 최소 근거 조회는 지금 제공하고 작은 보고서 집계는 Phase 4에 남긴다. — implement / Phase3
  표현 완성을 기다리며 근거 접근을 미룰 수 없다.
  최소 보고서 참조에서 전체 이벤트 근거를 조회하고 남은 집계 경계를 문서화한다.

  원문 근거: Implement all event collection now. Provide minimum evidence access now; reserve a small remaining report summary for Phase 4 self-development.

- **R15** 의존성·지침을 포함해 A를 독립 고정하고 기록은 OneDrive 밖에 두며 B 테스트는 제한된 임시 기록을 사용한다. B가 A와 실행·승인 저장소를 변경하지 못함을 입증한다. — implement / Phase3
  경로 분리만으로 요구된 쓰기 경계가 집행되지 않는다.
  설치 위치·고정 식별자를 확인하고 승격 전에 실제 B·자손 분리 시험을 기록한다.

  원문 근거: Freeze A as a separately installed/copied runtime, not an editable installation referencing B. Place runtime records outside OneDrive; B tests use temporary records and limited permissions. Record actual isolation probes.

- **R16** Phase 4 자체 개발에서 보고서 집계 표현을 완성한다. — defer / Phase4
  명시적으로 남긴 후속 작업이며 외부 예제는 자체 개발 실적이 아닌 준비다.
  후속 승인된 자체 개발 계획에서 집계를 Phase 3 이벤트 기록과 대조한다.

  원문 근거: reserve a small remaining report summary for Phase 4 self-development.

- **R17** Workflow 분기와 병렬 Task를 제외한다. — exclude / —
  기획서가 해당 대안을 명시적으로 제외한다.
  실행 경로가 단일 순차 흐름인지 확인한다.

  원문 근거: Keep one sequential workflow and the proposed two-correction default; no Fast/Standard/Strict routing or parallel Tasks.

- **R18** 범용 코드 분석·커버리지 엔진을 제외한다. — exclude / —
  명시된 범위 제한이며 근거 기반 재사용 검사로 처리한다.
  변경 내용을 확인해 재사용 검증이 대응된 요구사항 범위에 머무르는지 확인한다.

  원문 근거: No broad code-analysis or coverage engine is added.

## 관련 코드

- `src/development_harness/runner.py` (explicit): 기존 순차 Runner는 합성이며 계획 실행을 거부하므로 실제 실행은 확장이 필요하다.

  the only AI implementation here is synthetic.

- `src/development_harness/planning.py` (explicit): 기존 승인은 명시적으로 계획 전용이며 실행 승인과 구분해야 한다.

  "scope": "planning_only"

- `src/development_harness/codex_adapter.py` (explicit): 현재 Adapter는 Developer 파일 접근이 아닌 텍스트 전용 Planner 설정을 집행한다.

  Project tools are disabled, not prompt-restricted.

- `src/development_harness/processes.py` (explicit): Windows 잠금·프로세스 식별자는 재사용할 수 있지만 Job 수명 제어는 권한 분리가 아니다.

  This is process lifetime containment, NOT the Phase 2 permission sandbox.

- `src/development_harness/store.py` (explicit): SQLite 상태·이벤트 전이는 트랜잭션을 공유하며 실행 기록 위치 검사도 이미 있다.

  each state/evidence transition is one transaction.

- `src/development_harness/validation.py` (explicit): 검증은 프로젝트 명령 실행 전에 프로세스 식별자를 기록하며 시간 초과 기록은 미확정 구간 규칙에 맞춰야 한다.

  Persist PID identity BEFORE allowing any project command.

- `src/development_harness/files.py` (inferred): 검사된 쓰기·내용 스냅샷은 실제 작업 결과 대조에서 재사용할 파일 보존 기반으로 보인다.

  Unexpected file changes; preserved without overwrite:

- `tests/integration/test_cli.py` (inferred): 기존 통합 예제는 제어 프로세스 강제 종료·자손 정리를 다루며 현재 통과 근거가 아닌 회귀 검사 후보를 제공한다.

  def test_force_killed_harness_stops_descendants_and_resumes

- `tests/unit/test_state.py` (inferred): 파일시스템 전용 메타데이터 예제로 Git 작업 없이 동일 내용 재개를 검증할 수 있다.

  def test_git_worktree_pointer_is_metadata_not_code

- `pyproject.toml` (explicit): 기존 패키지는 Python 3.12로 제한하고 pytest·psutil을 고정하므로 A 고정 시 유지·검증한다.

  requires-python = ">=3.12,<3.13"

- `Phase/Phase2_Planning.md` (explicit): 관련 근거는 Phase 2 인수 대기와 제한된 Planner 경계를 보고하며 Phase 3 실행을 승인하지 않는다.

  Task 2.6 and Phase acceptance remain pending.

## 확인할 사항

- Q1 (blocking): Phase 2 인수를 입증하는 근거는 무엇인가요? 제공된 Phase 2 기록에는 Task 2.6과 사용자 인수가 대기 중이므로 아직 Phase 3 실행 선행 조건을 충족할 수 없습니다.

- Q2 (blocking): Developer·테스트의 B 접근을 허용하면서 A와 실행·승인 저장소 쓰기를 차단할 준비된 Windows 권한 수단은 무엇인가요? 제공된 텍스트 전용 Planner 설정과 Job 수명 제어는 이 경계를 입증하지 못하므로 실제 작업 실행 전에 실행 계약의 수단 선정과 실제 시험 근거가 필요합니다.

계획 승인은 구현 실행을 승인하지 않습니다. 재사용은 계획이며 검증 완료 근거가 아닙니다.
