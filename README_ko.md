[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI가 구현하고, 하네스가 검증하며, 사람은 중요한 결정을 승인합니다.

Markdown 기획서를 단계별 개발 계획으로 바꾸고, 승인된 작업의 구현·테스트·리뷰를 수행한 뒤 사용자가 결과와 근거를 확인할 수 있도록 하는 반자동 개발용 로컬 CLI를 기획하고 있습니다.

## 현재 상태

**Phase 1–2는 인수·완료했습니다.** Windows/Python 3.12 CLI에서 프로젝트 등록·기본 검사·Codex와 프로젝트 phase-doc 스킬·템플릿을 통한 버전별 영문·국문 계획 생성을 수행합니다. Phase 2에는 P2-01 경로 수정과 검토된 CLI 0.154.0·0.155.1 호환성 개선을 포함합니다. 검사 172개와 실제 계획 예제를 통과했습니다. Phase 3 구현·작업 및 테스트 권한 분리는 다음 개발 범위입니다.

아래 로드맵은 [축소 MVP 계획서 0.4](Draft/ai-development-harness-lean-mvp-plan.md)를 요약합니다. Phase 1·2 사용 안내에 구현된 동작을 구분했습니다.

## Phase 1 설치와 예제

Windows, Python 3.12.10, pytest 9.1.1에서 검증했습니다. 저장소 루트의 PowerShell에서 실행하며 환경과 실행 기록은 OneDrive 밖에 둡니다.

```powershell
py -3.12 -m venv "$env:LOCALAPPDATA\development-tools-harness\venv"
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython -m pip install -r requirements-dev.lock
& $harnessPython -m pip install --no-build-isolation -e .
& $harnessPython -m pytest
& $harnessPython -m development_harness --help
```

예제를 새 폴더에 복사한 뒤 명시적인 JSON 계획을 실행합니다.

```powershell
$demoProject = Join-Path $env:TEMP ('harness-example-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/minimal_project -Destination $demoProject -Recurse
& $harnessPython -m development_harness --project $demoProject prepare --plan tests/fixtures/fake-plan.json
& $harnessPython -m development_harness --project $demoProject approve
& $harnessPython -m development_harness --project $demoProject run --steps 1
& $harnessPython -m development_harness --project $demoProject resume
& $harnessPython -m development_harness --project $demoProject status
```

마지막 상태는 `awaiting_acceptance`여야 합니다. 변경 파일, 검증 결과와 JSON 출력의 로그 경로를 확인합니다. 결과를 검토한 뒤 같은 프로젝트 인수로 `accept`를 실행합니다. `cancel`은 파일·근거를 보존하면서 새 Run을 준비할 수 있게 합니다. 동일한 승인 계획은 재승인이 필요 없습니다. 계획이나 예상 파일 내용이 바뀌면 실행을 멈추며, 내용을 확인하고 의도한 입력을 복원하거나 취소 후 새 Run을 준비합니다.

- `prepare`는 파일 기준선과 승인할 명령 후보를 기록하며 Phase 2의 기본 테스트 통과 후 진입 검사는 아직 수행하지 않습니다. `approve` 전의 `run`은 승인 대기를 유지합니다.
- [예제 입력](tests/fixtures/fake-plan.json)은 Phase, 순차 Task, 시도별 `writes`와 가짜 `review` 결과, 검증 명령 `argv` 배열을 지정합니다. `{python}`은 하네스 인터프리터로 치환합니다. `kind: "pytest"` 명령이 하나 이상 필요하며 기본 수정 한도는 2회입니다.
- Developer·Reviewer 결과는 가짜이며 실제 AI 호출은 0회입니다. 검증 명령은 사용자 권한으로 실행하므로 신뢰하는 명령이어야 합니다. Windows Job은 자식 프로세스 수명을 관리하며 계획된 권한 샌드박스가 아닙니다.
- 실행 DB·명령 로그·pytest XML은 `%LOCALAPPDATA%/development-tools-harness/runtime/` 아래에 저장합니다. `--state-dir`로 프로젝트와 OneDrive 밖의 다른 로컬 폴더를 지정해도 프로젝트 실행 소유권은 함께 적용됩니다.
- 기준선은 `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.harness-output`을 제외한 일반 파일 내용을 해시합니다. 링크 경로는 지원하지 않습니다. 기존 변경을 포함하고 예상 밖 변경은 보존합니다.
- 검사 실패·미실행·시간 초과·테스트 0개·필수 검사 생략은 통과하지 않습니다. 중단 검사는 기록된 프로세스 식별 정보를 확인한 뒤 다시 실행합니다. 알 수 없는 부분 파일 내용은 확인을 위해 중단합니다.

구현·검증 상세는 [Phase 1](Phase/Phase1_Foundation.md)에 기록했습니다. 위 editable 설치는 개발용이며 dogfooding에 필요한 고정 실행본은 Phase 3에서 준비합니다.

## 프로젝트 스킬을 사용하는 Phase 2 계획 생성

실제 pytest 기본 검사가 통과하는 프로젝트를 사용합니다. 저장소에서 계획 예제를 새 로컬 폴더로 복사해 확인할 수 있습니다.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningProject = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningProject -Recurse
& $harnessPython -m development_harness --project $planningProject doctor
& $harnessPython -m development_harness --project $planningProject register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json --planner-timeout 600
& $harnessPython -m development_harness --project $planningProject plan
& $harnessPython -m development_harness --project $planningProject plan-status
```

하네스는 자체 설치본의 [프로젝트 스킬](.agents/skills/phase-doc/SKILL.md)과 [템플릿](.agents/skills/phase-doc/references/phase-template.md)을 읽어 Planner에 전달하고, 검사한 계획 데이터를 템플릿의 `harness:*` 블록으로 문서화합니다. `Phase/Generated/<run-id>/vN/`에는 `plan.json`, `Plan.md`·`Plan_ko.md` 개요와 링크, 두 언어를 함께 담은 `PhaseN_EnglishName.md`, 작성 규칙 원문·버전·해시를 담은 `writing-profile.json`이 생성됩니다. 현재 Phase만 Task를 상세화합니다. 문서를 확인한 뒤 `plan-approve`하며 이 승인은 계획 전용입니다.

필수 `{{slots}}`를 유지하면서 템플릿 제목·배치를 수정하면 다음 `register`부터 반영됩니다. 진행 중인 Run과 `plan-revise --from <파일>` 수정본은 등록 당시 규칙을 유지합니다. 작성 규칙 기록이 없는 이전 Run은 기존 형식으로 처리합니다. 설치용 wheel에도 같은 리소스를 포함합니다. 대상 프로젝트·전역 스킬을 자동 탐색하거나 계획 생성 중 README·개발 로그를 갱신하지 않습니다. 원문 인용은 코드 근거로 표시해 상대 링크를 잘못 해석하지 않도록 했습니다. 검증 결과와 한계는 [Phase 2](Phase/Phase2_Planning.md)에 기록했습니다.

## 목표 사용 흐름

```text
준비된 프로젝트 등록·기본 검사
  → 기획문서와 관련 코드 확인
  → 전체 Phase 목표와 현재 Phase 상세 Task 제안
  → 사용자 승인
  → Task 순차 구현·테스트·리뷰·수정
  → Phase 통합 검증·결과 보고서 생성
  → 사용자 UI 확인·인수 또는 수정 요청
  → 다음 Phase 상세화·승인
```

**Phase**는 하나의 목표와 인수 조건으로 묶인 개발 단계입니다. **Task**는 해당 Phase 안에서 수행하는 개별 구현 작업입니다. 현재 Phase만 상세 작업으로 나누고, 이후 Phase는 개발 진행에 따라 구체화합니다.

승인 대상은 전체 계획, 현재 Phase, 중요한 범위·위험 변경, 최종 결과 인수입니다. 이미 승인한 계획이 그대로라면 반복 승인받지 않습니다. 사용자가 응답하지 않으면 승인 대기를 유지합니다.

## 첫 MVP 범위

첫 MVP는 한 프로젝트의 순차 Task와 한 종류의 검증 기술 구성을 다룹니다. 하네스 개발은 Python 3.12.10 + pytest 9.1.1입니다. 계획 Adapter는 ChatGPT 인증의 Codex CLI이며 검토 버전은 0.154.0과 0.155.1입니다. 실제 구현·리뷰와 작업 권한 분리는 Phase 3에서 다룹니다.

| 영역 | P0 구현 예정 동작 |
| --- | --- |
| 프로젝트 진입 | 경로·기획문서·도구·테스트 명령을 확인하고 시작 상태를 기록합니다. |
| 계획 | Phase 목표, 현재 Task, 완료 기준, 간단한 요구사항 대응표를 만듭니다. |
| 기존 코드 | 현재 Phase와 관련된 코드·규칙·재사용 근거를 조사합니다. |
| 실행 | Developer → Validation Runner → Reviewer의 단일 흐름으로 실행하고 자동 수정 횟수를 제한합니다. |
| 승인·권한 | 검토한 계획·결과 버전에 승인을 연결하고, 지원하는 실행 권한 경계를 집행합니다. |
| 상태·재개 | SQLite에 실행 상태를 기록하고, 같은 프로젝트의 동시 수정을 막으며 기록한 단계에서 재개합니다. |
| 결과 | 짧은 Phase 보고서와 재사용 검증 결과를 제공하고, 수정 또는 승인된 계획 변경으로 연결합니다. |
| 측정 | 실제 AI 호출 수, 실행 시간, 승인 대기 시간, 리뷰 지적과 해결 근거를 기록합니다. |
| Dogfooding | 동작을 확인한 하네스로 아직 남아 있는 작은 P0 자체 기능 한 건을 개발하고 인수합니다. |

### 프로젝트 시작 조건

사용자가 준비할 것은 다음과 같습니다.

- 프로젝트 폴더: 신규 개발은 기본 환경이 준비된 시작 프로젝트, 기존 기능 수정은 기존 코드베이스.
- 요구 기능과 제약조건을 담은 Markdown 기획문서.
- 설치된 런타임·의존성, 실제 실행 가능한 단위·통합 테스트 명령, 인증이 설정된 AI 실행 도구.

개발 시작 전에 기본 검사가 통과해야 합니다. 도구가 없거나 검사가 실패하거나 테스트가 발견되지 않으면 준비 또는 수정이 필요하며, 하네스가 이를 성공으로 처리해서는 안 됩니다. 구현을 막는 기획의 불확실성은 사용자에게 확인합니다.

빈 폴더에서 임의의 개발 환경을 자동 구성하는 기능은 첫 MVP에 포함하지 않습니다. Git 이력은 필수가 아닙니다. 기존 미커밋 변경도 시작 상태에 포함하며 보존해야 합니다.

### 검증과 리뷰

Developer는 구현 코드와 필요한 테스트를 작성합니다. Validation Runner는 등록된 검사를 실행하고, 별도 세션의 Reviewer는 승인된 요구사항·실제 코드·테스트를 대조합니다.

구현과 테스트가 같은 오해를 공유할 수 있으므로 모든 Task에 Reviewer를 유지합니다. 별도 리뷰는 추가 확인 수단이며 정확성을 보장하지는 않습니다. 자동 검증은 단위·통합 테스트를 중심으로 하며, 필요한 경우 기존 린트·타입 검사·빌드도 실행합니다. **브라우저 UI 테스트는 사용자가 수행합니다.**

자동 수정 횟수는 제한하며 초기 기본값으로 2회를 제안합니다. 한도를 초과하거나 환경 문제가 발생하면 실패 내역을 남기고 중단합니다. 필수 검사의 실패·미실행·중단은 통과로 처리할 수 없습니다.

재사용 기능도 별도 구현 Task 유무와 관계없이 Phase 인수 시 현재 요구사항 충족 여부를 확인합니다. 최종 Phase 검증은 실제 산출물 코드에서 수행합니다. 필수 조건 미충족을 인수 승인만으로 무시할 수 없으며, 범위를 바꾸려면 계획을 수정하고 승인받아야 합니다.

### 사용자 통제와 복구

- 승인된 일반 파일 수정과 확인된 검증 명령은 지원하는 권한 범위에서 자동 진행합니다.
- 위험 작업에는 실제 집행 가능한 실행 권한 경계가 필요합니다. 실행 전에 통제할 수 없는 작업은 차단하고 사용자 수동 처리로 넘깁니다.
- 작업 에이전트가 승인 기록이나 검증 정책을 변경해 스스로 권한을 얻을 수 없어야 합니다.
- 설정·계획·보고서는 프로젝트에 둡니다. 실행 DB와 로그는 OneDrive 밖의 로컬 저장소에 둘 계획입니다.
- 재개할 때 저장된 계획·승인·실제 파일 상태를 확인합니다. 예상과 다른 상태라면 자동 병합이나 되돌리기 대신 차이를 확인할 수 있도록 중단합니다.
- Git 초기화·브랜치 작업·staging·commit·push·PR·merge·배포는 사용자가 수동으로 수행합니다.

## Phase 산출물

각 Phase는 변경된 코드와 테스트, 검증 근거, 상세 기록 링크를 포함한 1~2페이지 내외의 보고서를 제공합니다.

보고서에는 다음 내용을 담습니다.

- 구현한 기능, 산출물 위치, 실행 방법.
- 실제 테스트 결과, 재사용 기능 확인 결과, 미검증 항목.
- 주요 오류, 시도한 수정, 남은 문제.
- 승인받은 계획 변경과 이유.
- 사용자가 수행할 UI 확인 절차와 기대 결과.
- 역할별 AI 호출 수, 실행·승인 대기 시간, 리뷰 지적과 처리 결과.

실행에 실패해도 보고서는 생성합니다. Task의 기술적 완료와 Phase의 사용자 인수는 구분합니다. 최종 산출물이 필수 검사를 충족하고 사용자가 인수하면 Phase가 완료됩니다. 커밋이나 푸시는 완료 조건에 포함하지 않습니다.

## 개발 방식: 단계적 dogfooding

1. 기존 코딩 도구로 최소 Runner·승인·검증·리뷰·기록·재개 기능을 구현합니다.
2. 별도의 작은 예제에서 중단·재개를 포함한 전체 흐름을 확인합니다.
3. 동작이 확인된 **실행용 A**를 고정하고, A로 **개발용 B**의 아직 남아 있는 작은 P0 기능을 개발합니다.
4. B를 핵심 회귀 검사와 별도 실행으로 검증한 뒤, 사용자가 이후 Run에 사용할 버전으로 선택합니다.

실행 중인 버전·정책·승인 DB는 수정 대상 파일과 테스트 환경으로부터 분리해야 합니다. 버전 교체는 수동으로 수행하며 Run 도중에는 교체하지 않습니다. 수동 개입과 발견한 문제는 기존 보고서에 기록합니다.

자체 개발 성공이 다른 프로젝트에서의 검증을 대체하지는 않습니다. MVP 완료 전에는 선정한 기술 구성의 준비된 신규 프로젝트 예제와 기존 프로젝트 예제에서 각각 한 Phase를 인수까지 진행해야 합니다.

## 확장 계획

| 단계 | 핵심 범위 |
| --- | --- |
| 첫 MVP — P0 | 승인된 Phase → 구현 → 검증 → 리뷰 → 보고 → 인수 흐름과 재개·단계적 dogfooding을 검증합니다. |
| 선택적 P1 후보 | 핵심 흐름 완성 후 짧은 기획 검토와 기본 시작 템플릿 한 개의 포함 여부를 판단합니다. |
| MVP2 기본 범위 | 선택한 템플릿으로 시작하고, 기존 실행·승인 기능을 재사용해 Phase 없는 작은 수정 요청을 처리합니다. |
| 실사용 근거에 따른 후보 | 실제 필요성이 확인되면 Fast 경로, 요구사항 대응표 점검, 코드 요약 재사용을 검토합니다. |
| 이후 범위 | 임의 스택 환경 구성, 기존 실패 허용, 고급 복구, 다중 AI 도구, 병렬 Task, 웹 대시보드. |

P0·P1·P2는 우선순위이며, **MVP2는 후속 제품 범위**입니다. 모든 P2 항목을 MVP2에서 구현한다는 의미가 아닙니다. Git·배포 자동화와 UI 자동 테스트는 기본 확장 계획에 포함하지 않습니다.

## 기획 문서

- [전체 개발 Phase 개요](Phase/Overview.md): 4개 개발 Phase, 요구사항 대응표, dogfooding 진입 조건. 각 문서에 영문·국문 전체 내용을 함께 제공합니다.
- [Phase 1 — 실행 기반](Phase/Phase1_Foundation.md): 인수 완료. [Phase 2 — 실제 연결과 계획](Phase/Phase2_Planning.md): 호환성·스킬 기반 문서 포함 인수 완료. [Phase 3 — 전체 실행 흐름](Phase/Phase3_Workflow.md): Phase 2에서 검토 초안 생성, 구현 미시작. [Phase 4 — 자체 개발과 MVP 인수](Phase/Phase4_Dogfooding.md): 개요.
- [축소 MVP 계획서 — 0.4](Draft/ai-development-harness-lean-mvp-plan.md): 범위, 우선순위, 인수 규칙, 개발 단계, dogfooding, MVP2, 기획 변경 이력. 이 문서부터 확인하세요.
- [과거 기획 문서](Draft/archive/): 이전 설계와 결정 기록입니다. 과거 문서의 더 넓은 범위가 축소 MVP에도 적용된다고 가정하지 않습니다.

```text
development-tools-harness/
├── README.md
├── README_ko.md
├── pyproject.toml
├── requirements-dev.lock
├── .agents/skills/phase-doc/
│   ├── SKILL.md
│   └── references/phase-template.md
├── src/development_harness/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Phase/
│   ├── Overview.md
│   ├── Phase1_Foundation.md
│   ├── Phase2_Planning.md
│   ├── Phase3_Workflow.md
│   └── Phase4_Dogfooding.md
└── Draft/
    ├── ai-development-harness-lean-mvp-plan.md
    └── archive/
```

Phase 2 사용자 인수를 완료했습니다. 다음은 생성된 Phase 3 초안을 검토하고 실제 Developer·Reviewer 실행 전에 작업·테스트 권한을 검증하는 단계입니다. 계획 승인은 계획 전용으로 유지합니다.
