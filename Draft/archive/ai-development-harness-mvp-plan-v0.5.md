> **보관 문서**
> v0.6(`../ai-development-harness-mvp-plan-v0.6.md`)으로 대체되었다.
> 주요 변경은 v0.6의 0장과 22장 개정 이력을 참조한다.

# AI Development Harness MVP 기획서

> 버전: 0.5
> 상태: 결정 확정본
> 작성일: 2026-09-13
> 수정일: 2026-09-14
> 대체 대상: `ai-development-harness-mvp-plan.md` (v0.4), `development-harness-v0.1-개발계획.md` (v0.1)
> 결정 근거: `archive/harness-decision-record.md` (D-01 ~ D-33)
> 장기 방향: `ai-development-harness-plan.md`를 Target Architecture로 유지한다
> 첫 dogfooding 대상: Decision Desk

---

## 0. 문서 사용법

이 문서의 서술은 별도 표기가 없으면 **확정**이다. 아직 확인받지 않은 내용에는 `[제안]`을 붙인다. 확정 항목을 변경할 때는 `harness-decision-record.md`에 사유와 함께 기록한다.

문서 작성 요청이나 이 문서의 존재 자체를 상세 정책의 일괄 승인으로 취급하지 않는다.

v0.4에서 같은 원칙이 4개 절에 반복 서술되던 문제를 정리했다. 검증·승인 무효화 원칙은 2.3에 한 번만 정의하고, 이후 절은 이를 참조한다.

---

## 1. 목적과 범위

### 1.1 해결하려는 문제

코드 생성은 이미 AI 실행 도구가 수행한다. 이 하네스가 제공하는 가치는 코드를 만드는 것이 아니라 **AI의 개발 행위를 통제하고, 완료 주장을 실제 실행 결과로 검증하고, 사람이 판단해야 할 순간에만 멈추는 것**이다.

목표는 모든 명령에 Enter를 반복해 누르는 개발이 아니라, 판단이 필요한 순간에 근거를 보고 승인하는 개발이다.

### 1.2 개발 흐름

```text
기획 문서
→ 기획 검토 (선택)           누락·모순 리포트
→ 전체 Phase 계획
→ 현재 Phase Task 분해
→ 사용자 계획 승인
→ Task 순차 개발
→ Workflow가 요구하는 검증
→ 필요한 경우 AI Review
→ 제한적 재시도
→ Task별 Git Commit
→ Phase 결과 자료 제시
→ 사용자 인수 또는 반려
```

사용자는 이 흐름에서 계획 승인, 고위험 결정 허가, 결과 인수 세 가지만 수행한다.

### 1.3 MVP 범위

**포함**

- 하네스와 프로젝트별 설정의 분리
- 사용자 환경에 1회 설치, 프로젝트마다 초기화
- 기획 검토 리포트 생성
- `기획 → Phase → Task` 계획 구조와 Rolling Wave Planning
- Fast / Standard / Strict 내장 Workflow
- Planner / Developer / Reviewer 역할과 Validation Runner
- SQLite 단일 실행 상태 관리
- 승인·반려 경로
- Phase 브랜치와 Task 커밋
- 중단 후 재개와 커밋 복구
- Phase 결과 자료와 인수

**축소**

- 필수 설정은 `project.yaml` 하나
- Phase와 Task만 기본 계층으로 사용
- Codex CLI Adapter 하나
- Task 순차 실행

**제외**

- 여러 Agent의 병렬 코드 수정
- 사용자 정의 Workflow DAG
- 동적 Agent Registry
- 다중 AI Provider 동시 지원
- Task별 Git worktree
- 원격 Artifact Store
- 완전한 Event Sourcing
- Web Dashboard
- 자동 Merge 및 Production 배포
- 자연어 수정 요청 (21장 확장 목록으로 이동)

---

## 2. 핵심 원칙

### 2.1 AI와 Orchestrator의 책임 분리

```text
AI
- Phase와 Task 계획 제안
- 완료 기준, 관련 Domain Rule, Risk Tag 제안
- 기획서의 누락·모순 탐지
- 코드 구현
- 코드 리뷰
- 테스트 실패 원인 분석
- 반려 사유의 유형 분류
- 재계획안 제안

Orchestrator 프로그램
- 현재 상태와 승인·반려 기록을 SQLite에 저장
- 실행 가능한 Task 선택
- Risk Tag에 정책을 적용해 Workflow 결정
- 권한과 승인 확인
- Validation 명령 실행과 종료 코드 판정
- 재시도 횟수 제한
- 완료 조건 판정
- Git과 보고서 관리
```

> AI는 판단하고 제안하며 개발한다. Orchestrator는 실행을 통제하고 결과와 상태를 SQLite에 기록한다.

AI가 직접 상태를 완료로 바꾸거나 승인 기록을 생성하지 않는다. 어떤 테이블도 AI가 직접 쓰지 않는다. 테스트 성공 여부는 프로세스 종료 코드와 설정된 성공 조건으로만 판정하며, 명령이 실행됐다는 사실만으로 성공 판정을 내리지 않는다.

### 2.2 업무 승인과 실행 권한의 분리

업무 승인은 "이 계획이나 결과를 받아들일 것인가"이고, 실행 권한은 "이 파일·명령·네트워크 동작을 기술적으로 허용할 것인가"다. 둘은 다른 층위이며 하네스가 둘 다 집행하지는 못한다.

- 업무 승인: 하네스가 관리한다.
- 파일·명령·네트워크 권한: 실제 실행 환경이 집행한다.
- 권한 부족: 차단 이유를 기록하고 중단한다.
- 자동 권한 확대나 샌드박스 해제로 오류를 우회하지 않는다.
- 하네스의 승인만으로 회사 정책이나 실행 도구의 권한을 넓히지 않는다.
- 작업 에이전트가 자신의 승인 정책을 수정해 권한을 넓히는 것을 허용하지 않는다.

`project.yaml`에 `ask`를 적는 것만으로 실행 차단이나 승인 확인이 보장되지는 않는다. 실행 도구와 Runner가 해당 경계를 실제로 집행하는지 Phase 0에서 확인한다.

MVP는 단계 사이에서 멈추고 사용자가 승인하면 재개하는 방식으로 시작한다. 실행 도구 내부의 모든 권한 확인을 하네스 화면으로 통합하지 않는다.

### 2.3 최종 코드 기준 검증

검사 결과는 **검사한 코드 Revision과 계획 hash에 묶여서만** 유효하다. 이 원칙은 Review, Validation, 승인에 공통으로 적용한다.

- Review 또는 Validation 이후 코드가 바뀌면 이전 결과를 최종 코드의 근거로 재사용하지 않는다.
- 자동 포맷 수정처럼 검사 중 파일이 바뀐 경우도 코드 변경으로 취급하고, 변경이 끝난 Revision에서 다시 검사한다.
- 시작만 기록되고 종료가 확정되지 않은 검사는 성공으로 간주하지 않는다.
- 정책상 생략한 검사는 `SKIPPED_BY_POLICY`로 기록하며 `PASS`로 표시하지 않는다.
- 미실행·중단된 필수 검사를 통과로 간주하지 않는다.
- 승인은 계획 hash에 연결한다. Task 완료 기준, 적용 규칙, 검증 명령·필수 여부, 위험 판단이 바뀌면 영향 범위의 기존 승인과 검사 결과를 다시 사용하지 않는다.
- 실패한 테스트를 삭제하거나 기준을 낮춰 통과시키는 변경은 별도 검토 대상이다.

Revision과 hash의 계산 방법은 14.5에, Workflow별 완료 조건은 8.5에 정의한다.

### 2.4 작은 설정 비용

하네스를 적용하기 위한 준비 비용이 직접 개발하는 비용보다 커지면 안 된다.

- 필수 설정 파일은 `project.yaml` 하나다.
- 여러 프로젝트가 같은 하네스 설치를 사용하며, 프로젝트마다 하네스 소스를 복사하지 않는다.
- 대부분의 설정에 안전한 기본값을 제공한다.
- 사용자는 기획 문서와 테스트 명령만 제공해도 시작할 수 있다.
- 사용자에게 내부 Task 형식, Workflow 이름, DB 구조를 이해하도록 요구하지 않는다.

### 2.5 위험도에 따른 실행

모든 Task에 같은 수의 AI 호출과 검증을 강제하지 않는다.

```text
저위험 작업  → Fast
일반 기능    → Standard
고위험 작업  → Strict
```

AI가 요청과 관련 코드의 영향을 해석하고, Orchestrator의 Workflow Router가 프로젝트 규칙에 따라 최종 Workflow를 선택한다. 사용자는 Workflow를 직접 고르지 않는다.

---

## 3. 시스템 구조

### 3.1 구성 요소

```text
사용자
  ↓
CLI 또는 /development 명령
  ↓
Orchestrator Engine
  ├─ Project Loader
  ├─ Plan Reviewer        기획 검토 리포트
  ├─ Phase/Task Planner
  ├─ Task Scheduler
  ├─ Workflow Router
  ├─ Approval Controller  승인·반려
  ├─ Validation Runner
  ├─ Retry Controller
  ├─ Git Manager
  └─ SQLite State Store
       ↓
Codex CLI Adapter
  ├─ Planner 역할
  ├─ Developer 역할
  └─ Reviewer 역할
```

### 3.2 AI 실행 도구 선택

MVP는 Codex CLI Adapter 하나만 지원한다. 선택 근거는 다음과 같다.

- 비대화형 실행 모드로 프로그램에서 호출할 수 있다.
- JSON 이벤트와 결과 스키마를 제공해 Orchestrator가 결과를 구조적으로 수신할 수 있다.
- 세션 재개 기능이 있다.
- 승인과 실행 경계가 문서화되어 있어 2.2의 권한 분리를 검증할 수 있다.

참고 문서는 Codex 비대화형 실행, 승인·보안 정책, App Server 승인 처리다. 실제 구현 시 설치된 버전의 동작과 함께 검증한다. 호출은 subprocess와 JSON 출력으로 수행하며, SDK 직접 연동은 실사용에서 필요성이 확인되면 검토한다.

### 3.3 Slash Command의 역할

`/development` 명령은 개발 로직을 포함하지 않는 얇은 진입점이다.

```text
/development start P1
        ↓
Core CLI 호출
        ↓
project.yaml과 SQLite 상태 읽기
        ↓
Orchestrator가 실제 실행
```

프로젝트별 기능이나 Domain Rule을 `/development` Skill 안에 하드코딩하지 않는다.

### 3.4 설치와 프로젝트 초기화

| 단계 | 수행 단위 | 결과 |
|---|---|---|
| 하네스 설치 | 컴퓨터의 사용자 환경에서 한 번 | 프로젝트 폴더에서 공통 `devh` 명령 사용 |
| AI 도구 연결 | 사용하는 AI 도구의 사용자 환경에서 한 번 | `/development`가 Core CLI를 호출 |
| 프로젝트 초기화 | 프로젝트마다 한 번 | `.dev-harness/` 설정·계획 파일과 로컬 SQLite 준비 |

하네스는 Python CLI 패키지로 배포한다. 사용자에게 대상 프로젝트의 앱 의존성으로 하네스를 추가하거나 하네스 저장소를 복사하도록 요구하지 않는다.

하네스 설치와 `/development` 연결은 별개다. 연결하지 않아도 터미널에서 `devh`로 실행할 수 있다. 두 진입점 모두 AI 실행 도구와 인증이 사용 가능한지 확인하고, 준비되지 않았다면 필요한 설정을 안내한다.

```text
devh init Draft/product-plan.md
```

`init`은 프로젝트별 기본 설정과 계획 파일을 준비하고 로컬 SQLite를 연결한다. 이미 초기화된 프로젝트에서 다시 실행해도 기존 설정·계획·실행 상태를 덮어쓰지 않는다.

### 3.5 현재 프로젝트 식별

- Core CLI는 현재 작업 폴더에서 Git 저장소 루트까지 탐색해 가장 가까운 `.dev-harness/project.yaml`을 기준으로 프로젝트를 식별한다.
- Slash Command는 현재 열린 프로젝트의 작업 경로를 Core CLI에 전달한다. 최근에 사용한 다른 프로젝트를 임의로 선택하지 않는다.
- 프로젝트 ID와 저장소 경로로 해당 프로젝트의 SQLite를 연결한다(14.1). 여러 프로젝트가 같은 실행 프로그램을 써도 상태와 승인은 섞이지 않는다.
- 기획 문서와 검증 명령의 기준 경로는 식별된 프로젝트 루트로 통일한다.
- 설정이 없으면 초기화를 안내한다. 대상을 특정할 수 없으면 먼저 확인한다.

---

## 4. 프로젝트 파일 구조와 저장 책임

```text
project-root/
├─ Draft/
│  └─ product-plan.md
├─ .dev-harness/
│  ├─ project.yaml
│  ├─ plan.md
│  ├─ work-items.yaml
│  ├─ domain-rules.md
│  ├─ review-report.md
│  └─ reports/
│     └─ phase-P1.md
├─ src/
├─ tests/
└─ README.md
```

실행 상태와 로그는 프로젝트가 OneDrive에 있을 수 있으므로 로컬 애플리케이션 데이터에 저장한다(14.1).

| 저장 대상 | 저장 위치 | 기준 역할 |
|---|---|---|
| 소스 코드와 테스트 | Git | 실제 제품 산출물 |
| 프로젝트 설정 | `project.yaml` + Git | 실행 설정의 정의 |
| Phase·Task 정의, 의존성, 완료 조건 | `work-items.yaml` + Git | 작업 계획의 정의 |
| 공통·Task별 Domain Rule | `domain-rules.md` + Git | 규칙의 정의와 원문 출처 |
| 사람이 읽는 계획 설명 | `plan.md` + Git | 계획의 설명과 판단 근거 |
| 기획 검토 리포트 | `review-report.md` + Git | 개발 전 확인 자료 |
| 실행 상태, 승인·반려, 검사 결과, 커밋 연결 | SQLite | 현재 실행 상태의 유일한 기준 |
| 실행에 사용한 계획 사본과 hash | SQLite | 해당 Run의 입력 기준선 |
| 실행 로그 | LocalAppData | 문제 분석 |
| Phase 결과 자료 | SQLite와 Git에서 생성 | 사용자 인수 |

### 4.1 SQLite 단일 실행 상태 원칙

- `work-items.yaml`에는 작업 정의만 저장한다. `status`, 실행 단계, 재시도 횟수, 승인 여부를 저장하거나 동기화하지 않는다.
- `plan.md`는 계획 설명이며, 진행 상황은 `devh status`로 확인한다.
- 보고서와 로그를 다시 읽어 현재 실행 상태나 승인을 복원하지 않는다.
- 실행 전에 해당 Run에 적용할 계획 사본과 hash를 SQLite에 저장하고 승인 기록과 연결한다.
- 실행 중 계획 파일이 바뀌어도 진행 중인 Run의 입력을 자동 교체하지 않는다.
- AI의 완료 선언만으로 상태를 바꾸지 않는다.

### 4.2 로컬 저장과 복구 범위

Task 완료와 정상 중단 시 SQLite 백업 사본을 자동 생성한다. 백업은 같은 장치에 있으므로 장치 손실까지 복구하지는 못한다.

기본 재개 범위는 같은 컴퓨터의 같은 저장소다. Git 복제만으로 실행 이력과 승인이 전달되지는 않는다. DB가 없으면 기존 Run을 정확히 재개할 수 없음을 알리고 새 Run을 준비한다.

`plan.md`, `work-items.yaml`, `domain-rules.md`, `review-report.md`는 하네스가 생성·갱신하는 산출물이다. 사용자가 시작 전에 작성해야 하는 필수 설정 파일을 늘리지 않는다.

---

## 5. project.yaml

```yaml
schema_version: "1.0"

project:
  id: decision-desk
  name: Decision Desk
  planning_documents:
    - Draft/product-plan.md

ai:
  provider: codex-cli
  authentication: chatgpt

development:
  phases: true
  default_workflow: standard
  max_retries: 2          # [제안] 실행 데이터로 재검토

workflow_routing:
  strict_when:
    - architecture_change
    - personal_data
    - security
    - database_migration
    - external_api
    - core_domain_rule
  fast_when:
    - documentation_only
    - formatting_only
    - low_risk_configuration
    - test_only
    - small_isolated_fix

validation:
  quick:
    - name: lint
      command: npm run lint
      required: true

  pre_review:
    - name: lint
      command: npm run lint
      required: true
    - name: typecheck
      command: npm run typecheck
      required: true
    - name: unit
      command: npm test
      required: true

  post_review:
    - name: integration
      command: npm run test:integration
      required: true
    - name: build
      command: npm run build
      required: true

approval:
  file_edit: auto
  test_execution: auto
  dependency_install: ask
  architecture_change: ask
  database_migration: ask
  external_api: ask
  git_commit: auto
  git_push: ask
  merge: ask
  production_deploy: deny
  task_result: auto       # ask로 바꾸면 Task마다 결과 확인

git:
  strategy: phase-branch
  task_commit: true
```

### 5.1 설정 검증

- Pydantic 또는 동등한 스키마 검증으로 읽는다.
- 필수 필드가 없으면 시작하지 않는다.
- 알 수 없는 필드는 오류로 처리한다.
- 선택된 Workflow에 필요한 검사 목록이 비어 있으면 실행 전에 설정 보완을 요청한다.
- API Key와 비밀값은 YAML에 저장하지 않는다. 환경변수 또는 운영체제 자격 증명 저장소를 사용한다.

`validation.quick`은 Fast에서 사용한다. Standard와 Strict는 `pre_review`와 `post_review`를 사용한다. AI가 임의로 `required: true` 검사를 제외할 수 없다. 설정되지 않은 검사를 실행한 것으로 보고하지 않는다.

설정이 커질 때만 `agents.yaml`, `workflows.yaml`, `permissions.yaml` 등으로 분리한다.

---

## 6. 기획 검토

개발을 시작하기 전에 기획 문서에서 누락과 모순을 찾아 리포트로 제시한다. 선택 단계이며 건너뛸 수 있다.

```text
devh review [문서경로]
```

### 6.1 동작

- 기획 문서를 읽고 `.dev-harness/review-report.md`를 생성한다.
- 기획 문서를 자동으로 수정하지 않는다. 사용자가 직접 고친다.
- 실행 상태를 만들지 않는다. Run을 생성하지 않으므로 중단 시 다시 실행하면 된다.
- 검토를 수행하지 않아도 `devh plan`으로 진행할 수 있다.

### 6.2 리포트 구성

| 분류 | 내용 |
|---|---|
| 누락 | 개발에 필요한데 기획에 없는 결정. 예: 실패 상태 표현 방식, 데이터 보관 정책 |
| 모순 | 문서 안에서 서로 충돌하는 서술. 근거 위치를 함께 제시 |
| 모호 | 여러 해석이 가능한 서술. 판단하지 않고 확인 대상으로 표시 |

- 명확한 모순만 모순으로 분류한다. 판단이 어려운 것은 모호로 분류하고 사용자에게 확인을 넘긴다.
- 각 항목에 기획 문서의 출처 위치를 표시한다.
- 검토 결과를 이유로 개발을 자동으로 막지 않는다.

### 6.3 요구사항 커버리지 `[제안]`

`devh plan` 이후 기획 문서의 요구사항이 어느 Task에도 연결되지 않았는지 검사한다. `requirement_refs`를 실행 가능한 Task의 필수 항목으로 올리면 자동 검사가 가능하다. 계획 단계에서 요구사항 누락을 잡는 유일한 장치이므로 도입을 제안한다.

---

## 7. 개발 계획 구조

### 7.1 계층

```text
기획
└─ Phase
   └─ Task
      └─ AI 개발 Workflow
```

Feature는 필요한 경우 `plan.md` 안에서 Task 그룹으로만 사용한다. 실행 엔진은 Phase와 실행 가능한 Task를 관리한다.

### 7.2 Work Item 계약

Work Item은 Developer, Reviewer, Orchestrator가 공유하는 작업 계약이다.

```yaml
work_items:
  - id: P1
    type: phase
    title: 사용자 인증
    executable: false

  - id: AUTH-001
    type: task
    title: 회원가입 API
    parent_id: P1
    group: 회원가입
    executable: true
    acceptance_criteria:
      - 이메일과 비밀번호로 회원가입할 수 있다
      - 중복 이메일과 잘못된 이메일 형식을 거부한다
      - 비밀번호는 평문으로 저장하지 않는다
    requirement_refs:
      - "Draft/product-plan.md#회원가입"
    domain_rule_refs:
      - DR-SEC-001
      - DR-USER-001
    risk_tags:
      - security
      - personal_data
    depends_on: []
```

| 항목 | 규칙 |
|---|---|
| `acceptance_criteria` | 실행 가능한 Task에 하나 이상 필요하다. Developer의 구현 목표이자 Reviewer의 검토 기준이다 |
| `requirement_refs` | 원본 요구사항의 위치. 현재는 선택, 6.3의 제안이 채택되면 필수 |
| `domain_rule_refs` | Task에 추가 적용할 규칙 ID |
| `risk_tags` | 위험·작업 특성 분류. 누락은 미분류로 처리하고 실행 전에 보완한다. 명시적 빈 목록은 Fast의 근거가 되지 않는다 |
| `depends_on` | 선행 Task ID. SQLite에서 완료를 확인한 뒤 실행한다 |

- **ID 문자열로 계층이나 관계를 추측하지 않는다.** `P1-T5`처럼 보이는 ID를 파싱해 부모를 유추하지 않으며, 계층은 `parent_id`로만 판단한다. ID 형식은 프로젝트가 자유롭게 정한다.
- 중복 ID, 존재하지 않는 부모·의존성·규칙 참조, 순환 의존성은 계획 검증 오류로 처리한다.
- Phase는 목표와 종료 조건을 먼저 정하고, 현재 Phase의 실행 가능한 Task만 상세 완료 기준을 갖추면 된다.
- 완료 기준은 짧고 확인 가능한 문장으로 쓴다. 문장이 존재한다는 이유만으로 완료 처리하지 않는다.
- 승인과 실행 상태는 SQLite에서 관리하므로 이 파일에 `status`를 두지 않는다.

### 7.3 Rolling Wave Planning

```text
프로젝트 시작
├─ P1: Task까지 상세 계획
├─ P2: 주요 기능 수준 계획
└─ P3 이후: 목표와 종료 조건 중심 계획
```

P1이 완료되면 실제 결과와 새로 발견한 위험을 반영해 P2를 상세화한다.

### 7.4 Domain Rule

`.dev-harness/domain-rules.md`에 안정적인 ID로 관리한다.

```markdown
# Domain Rules

## DR-SEC-001

- 적용: 공통
- 원문: Draft/product-plan.md — 인증 보안

사용자 비밀번호는 평문으로 저장하거나 로그에 기록하지 않는다.

## DR-USER-001

- 적용: Task 참조
- 원문: Draft/product-plan.md — 회원가입

이미 등록된 이메일로 새 계정을 생성할 수 없다.
```

- Planner가 기획서에서 규칙과 출처를 추출하고 계획 승인에 포함한다. 별도 규칙 승인 단계를 두지 않는다.
- `적용: 공통` 규칙은 모든 Task에 전달한다. 참조 누락으로 공통 규칙의 적용이 사라지지 않는다.
- Context Builder가 `공통 규칙 + Task 참조 규칙`을 합쳐 Developer와 Reviewer에게 같은 내용을 전달한다.
- ID 중복, 존재하지 않는 참조, 원문과의 충돌은 계획 보완 대상이다.
- 규칙의 의미가 바뀌면 계획 hash가 바뀌며 2.3이 적용된다.
- 전체 기획서를 매번 전달하지 않는다. 규칙이 모호하거나 충돌할 때 원문을 추가로 확인한다.

### 7.5 Risk Tag와 Workflow 선택

```text
Planner가 Risk Tag 제안
→ 사용자 계획 승인
→ Orchestrator가 project.yaml 정책 적용
→ Fast / Standard / Strict 결정
```

Orchestrator의 선택 순서는 다음과 같다.

1. `risk_tags`에 `strict_when` 항목이 하나라도 있으면 Strict.
2. Strict 조건이 없고 `fast_when` 조건을 충족하면 Fast.
3. 나머지는 `default_workflow`(기본 Standard).

- `security`와 `small_isolated_fix`가 함께 있으면 Strict가 우선한다. 변경 줄 수가 적다는 이유로 인증·보안 작업을 Fast로 낮추지 않는다.
- 분류가 모호하면 Fast를 선택하지 않는다.
- 선택된 Workflow, 적용 Tag, 정책 근거를 SQLite에 기록한다. Developer가 Workflow를 확정하지 않는다.
- Developer와 Reviewer는 실행 중 발견한 새 위험을 보고하고, Orchestrator가 다시 판정한다.
- Fast → Standard → Strict 강화는 자동 허용한다. 자동 하향은 지원하지 않는다.
- Workflow 강화는 행동 권한 승인이 아니다. 승인 대상 행동은 11장을 별도로 적용한다.

---

## 8. 내장 Workflow

### 8.1 Fast

대상: 문서 수정, 포맷 변경, 영향이 제한된 스타일 수정, 단순 설정 변경, 작은 테스트 추가, 범위가 매우 작은 버그 수정

```text
Implement → Quick Validation → Task Commit
```

AI Reviewer를 호출하지 않으며, 생략된 Review는 `SKIPPED_BY_POLICY`로 기록한다. Quick Validation은 변경 diff 확인과 `validation.quick` 실행을 수행한다. 수행하지 않은 검사나 화면 확인을 통과로 표시하지 않는다.

### 8.2 Standard

대상: 일반적인 기능 개발, 기존 패턴 안의 API·UI 변경, 중간 수준의 리팩터링

```text
Implement → Pre-review Validation → Light AI Review → Post-review Validation → Task Commit
```

Reviewer는 현재 Task 요구사항과 관련 diff만 확인한다.

### 8.3 Strict

대상: 개인정보·민감정보 처리, 인증과 권한, DB Migration, 외부 API 도입, 핵심 Domain Rule, 보안 영향이 있는 변경, Architecture 변경

```text
Implement
       ↓
Pre-review Validation (format, lint, typecheck, unit, 필요 시 변경 영역 integration)
       ↓ 실패
Developer 자동 수정
       ↓
Strict AI Review
       ↓ 변경 요청
Developer 수정 → Pre-review Validation → AI Re-review
       ↓ 승인
Post-review Full Validation (전체 integration, E2E, security, 프로젝트별 특수 검증)
       ↓ 실패
Developer 수정 → Pre-review Validation → Delta Review → Post-review 재실행
       ↓
Task Commit
```

Pre-review Validation의 필수 검사가 실패하면 Reviewer를 호출하지 않는다.

Phase 계획에서 승인된 Task라면 매번 별도의 Task 계획 승인을 받지 않는다. 실행 중 새로운 고위험 결정이 발견되면 즉시 승인 대기로 전환한다.

### 8.4 Workflow 자동 선택

Workflow는 요청의 길이나 수정할 코드의 줄 수로 결정하지 않는다. 구현 전에 관련 코드를 읽어 실제 변경 영향과 위험 신호를 확인한다. 이 단계에서는 소스 코드를 수정하지 않는다.

```text
계획된 Task 확인
→ 관련 코드 확인
→ 변경 종류·영향 범위·위험 신호를 구조화된 결과로 반환
→ Workflow Router가 프로젝트 규칙과 대조
→ Workflow 및 필요한 승인 확인
→ 구현 시작
```

영향 범위를 확신할 수 없으면 Fast를 선택하지 않고 Standard를 적용한다. 구현 중 예상보다 넓은 변경이나 새 위험이 발견되면 Workflow를 상향하고, 상향된 Workflow의 검토·검증을 통과해야 완료할 수 있다. Workflow 상향만으로 사용자에게 재승인을 요구하지는 않으며, 요청 범위 변경이나 새 승인 대상 행동이 있을 때 확인한다.

### 8.5 Task 완료 조건

| Workflow | Commit 전에 최종 Revision에서 충족할 조건 |
|---|---|
| Fast | Quick Validation의 필수 검사 통과. Review는 `SKIPPED_BY_POLICY` |
| Standard | Pre-review Validation 통과, Light 또는 유효한 Delta Review PASS, 정책이 요구하는 후속 Validation 통과 |
| Strict | Pre-review Validation 통과, Strict 또는 유효한 Delta Review PASS, Post-review Full Validation 통과 |

모든 Workflow에 다음 조건이 함께 적용된다.

- 승인된 Task 계약이 유효하고 선행 Task가 완료되어 있어야 한다.
- 필요한 Review가 있다면 미해결 필수 수정 요청이 없어야 한다.
- 필요한 검사 목록은 Orchestrator가 정책에 따라 확정하고 기록한다.
- 2.3의 검증 원칙을 충족해야 한다.
- 조건을 충족하면 Commit을 진행할 수 있다. Task `COMPLETED`는 Commit 내용 확인과 SQLite 기록까지 끝난 뒤 확정한다.

Strict Task에서 R1 검토 후 R2로 수정한 경우의 흐름은 다음과 같다.

```text
R1 결과는 이력으로 보존하되 R2의 완료 근거로 사용하지 않음
→ R2 Pre-review Validation
→ R2 Delta Review 또는 전체 Review
→ R2 Post-review Full Validation
→ 최종 Revision과 필수 결과 확인
→ Task Commit 내용 확인
→ SQLite에 COMPLETED 기록
```

---

## 9. AI Review 정책

### 9.1 Reviewer 입력 제한

제공한다.

- Work Item 설명과 Acceptance Criteria
- 공통 Domain Rule과 Task가 참조하는 Domain Rule
- 구현 계획 요약
- 현재 Task의 Git diff
- Pre-review Validation 결과 요약
- diff가 의존하는 최소 코드
- 검토 대상 코드 Revision과 계획 hash
- Delta Review라면 이전 검토 기준선, 수정 diff, 미해결 수정 요청

제공하지 않는다.

- 전체 기획서, 전체 대화 기록, 관련 없는 소스 코드, 전체 테스트 로그, Developer의 긴 작업 과정, 이전 Task의 모든 산출물

### 9.2 Review 호출 기준

| 변경 유형 | Review 정책 |
|---|---|
| 문서·포맷·단순 설정 | 생략 |
| 테스트만 추가 | 선택적 Review |
| 일반 기능 | Light Review 1회 |
| 고위험 기능 | Strict Review |
| Review 후 작은 수정 | Delta Review |

### 9.3 Reviewer 출력

```yaml
result: changes_requested
new_risk_tags: []

findings:
  critical: []
  major:
    - id: REV-001
      file: src/parser.py
      description: 추출 실패가 정상 결과와 구분되지 않는다.
      required_change: 실패 상태를 별도 타입으로 표현한다.
  minor: []

require_changes: true
```

Orchestrator는 Review 호출 시점의 Task ID, 코드 Revision, 계획 hash, Workflow를 결과에 연결해 저장한다. AI가 출력한 Revision 문자열을 그대로 신뢰하지 않는다.

Delta Review는 이전 Review 기록과 대상 Revision을 연결하고 기존 필수 수정 요청의 해결 여부를 확인한다. 이전 기록이 없거나 수정 범위가 크게 달라졌다면 전체 Review를 수행한다. 최신 diff가 PASS라는 이유만으로 과거의 미해결 요청을 삭제하지 않는다.

### 9.4 비용 제한

- Task당 Review 호출 횟수를 제한한다.
- Task diff가 너무 크면 Review 전에 Task를 다시 나눈다.
- 일반 Review에 비용 효율적인 모델을 쓸 수 있도록 확장 지점을 둔다.

---

## 10. Agent와 Skill

```text
Planner    전체 Phase 계획, 현재 Phase Task 분해, 완료 기준·참조·Risk Tag 제안, 재계획
Developer  구현, 테스트 추가, 실패 수정, 새 위험과 승인 필요 행동 보고
Reviewer   diff 기반 독립 검토, 요구사항·설계·보안·Domain Rule 확인, 미해결 요청 확인
```

역할 이름뿐 아니라 입력, 결과 형식, 허용 도구·경로, 시간 제한을 정의한다. 같은 모델을 쓰더라도 세션을 분리하되, 역할 분리 자체가 검토의 정확성을 보장한다고 주장하지 않는다.

Tester는 AI Agent로 만들지 않는다.

```text
Validation Runner가 실제 명령 실행
       ↓ 실패
오류 로그를 Developer에게 전달
       ↓
Developer가 수정
```

Skill은 Agent가 사용하는 작업 매뉴얼이다.

```text
Planner   → plan-project / plan-phase / review-plan-document
Developer → implement-task / fix-failure
Reviewer  → review-diff
```

MVP에서는 동적 Agent Registry를 구현하지 않고 내장 역할 구성을 사용한다.

---

## 11. 승인 정책

사용자는 작업마다 승인하지 않고, 결과를 크게 바꾸거나 되돌리기 어려운 결정만 승인한다.

### 11.1 승인 지점

| # | 지점 | 대상 |
|---|---|---|
| ① | 전체 Phase 계획 | Phase 목표와 순서 |
| ② | 현재 Phase Task 계획 | Task, 완료 기준, Domain Rule, Risk Tag |
| ③ | 실행 중 새로 발견된 고위험 결정 | 해당 행동 |
| ④ | Phase 완료 결과 | Phase 산출물 인수 |
| ⑤ | Git Push와 Merge | 저장소 반영 |
| ⑥ | Task 완료 결과 (선택) | `approval.task_result: ask`일 때만 |

승인 단위는 사용자가 이해할 수 있는 수준으로 한다. 승인된 범위 안의 하위 작업은 자동 진행한다. 기존 승인 계획이 유효하면 같은 내용을 다시 승인받지 않는다.

### 11.2 자동 허용

- 승인된 범위 안의 파일 수정
- 테스트 추가 및 실행
- lint와 format 수정
- 승인된 설계 안의 작은 리팩터링
- 로컬 Task Commit

### 11.3 승인 필요

- 새 Dependency 설치
- Architecture 변경
- DB Migration
- 외부 API 사용
- 개인정보 외부 전송
- 테스트 삭제 또는 기준 완화
- Phase 범위 변경
- Git Push와 Merge
- Production 배포

### 11.4 승인 기록과 무효화

- 승인 요청과 결과는 SQLite에만 기록하며 승인 대상과 계획 hash에 연결한다. YAML이나 Markdown에 적힌 승인 표현을 승인 기록으로 취급하지 않는다.
- AI가 승인 기록을 작성하거나 변조해 사용자 승인을 대체하지 못하게 한다.
- 승인받은 내용이 실질적으로 변경되면 영향 범위의 기존 승인을 다시 사용하지 않는다(2.3).
- 승인 정책 변경이나 필수 검증 기준 완화는 일반 코드 수정과 구분해 검토한다.
- 관련 없는 독립 Task 추가만으로 기존 승인을 무효화하지 않는다(14.5).

### 11.5 무응답 처리

- 응답이 없으면 승인 대기를 유지한다. 무응답이나 시간 초과를 자동 승인으로 처리하지 않는다.
- 승인 대기 시간은 재시도 횟수에 포함하지 않는다.
- AI가 추정한 동의만으로 승인 기록을 만들지 않는다.

---

## 12. 반려 경로

### 12.1 원칙

1. **반려는 실패가 아니다.** `FAILED`(시스템이 수행하지 못함)와 반려 상태를 구분하며, 반려는 `max_retries`에 포함하지 않는다.
2. **반려해도 폐기하지 않는다.** 코드·커밋·브랜치를 자동으로 되돌리지 않는다. 사용자가 명시적으로 요청할 때만 폐기한다.
3. **반려 유형이 다음 행동을 결정한다.** 자유 서술만으로는 재진입 지점을 정할 수 없다.
4. **AI는 반려를 분류만 한다.** 상태 전이는 사용자 확인 후 Orchestrator가 수행한다.

### 12.2 승인 지점별 반려 유형

**승인 ①② 계획 반려** — 구현 전이므로 코드 영향이 없다.

| 유형 | 의미 | 재진입 지점 |
|---|---|---|
| `SCOPE` | 무엇을 만들지가 틀림 | Planner 전체 재계획 |
| `DECOMPOSE` | 범위는 맞으나 분해가 잘못됨 | Planner 재분해, 목표는 유지 |
| `CRITERIA` | 완료 기준이 부족하거나 틀림 | `acceptance_criteria`만 수정 |
| `RISK` | 위험 분류·Workflow가 부적절 | `risk_tags` 수정 후 Workflow 재선택 |
| `ORDER` | 의존성·순서가 틀림 | `depends_on`만 수정 |

재계획 범위를 유형에 맞게 좁혀 Planner에게 전달한다. `CRITERIA` 반려에 전체 계획을 다시 생성하지 않는다.

**승인 ③ 고위험 결정 반려**

| 유형 | 의미 | 처리 |
|---|---|---|
| `DENY_ALT` | 이 방법은 불가, 다른 방법을 찾는다 | 거부된 방법을 제약으로 전달하고 재구현 |
| `DENY_STOP` | 이 Task를 중단한다 | Task `BLOCKED`, 다음 Task로 진행 |
| `DENY_REPLAN` | 계획 자체를 다시 세운다 | Phase `REPLAN_REQUIRED` |

**승인 ④ Phase 결과 반려**

| 유형 | 의미 | 대상 Task 처리 | 커밋 |
|---|---|---|---|
| `NOT_WORKING` | 동작하지 않음 | `COMPLETED` → `REWORK_REQUIRED` | 보존 |
| `QUALITY` | 동작하지만 품질 미달 | `COMPLETED` → `REWORK_REQUIRED` | 보존 |
| `MISSING` | 빠진 것이 있음 | 새 Task 생성, 기존 완료는 유지 | 보존 |
| `WRONG_REQ` | 요구사항을 잘못 이해함 | Phase `REPLAN_REQUIRED` | 보존 |
| `ABANDON` | Phase 자체를 버림 | Phase `ABANDONED` | 보존 |

Task는 요구사항 단위이지 작업 시도 단위가 아니다. 재작업은 새 Task를 만들지 않고 해당 Task를 되돌리며, 시도 이력은 SQLite에 별도로 보존한다. `MISSING`만 새 요구사항이므로 새 Task를 만든다.

`ABANDON` 시 브랜치와 커밋을 보존하며 삭제는 사용자가 직접 한다. 폐기된 Phase에 의존하는 후속 Phase는 실행하지 않고 계획 수정을 요청한다.

**승인 ⑤ Push/Merge 반려** — 상태 전이가 없다. Phase는 `ACCEPTED`를 유지하고 브랜치는 로컬에 남는다. 재요청 시점에 코드가 바뀌었으면 기존 인수를 그대로 사용하지 않는다.

**승인 ⑥ Task 결과 반려** — 커밋 전이므로 커밋하지 않고 `REWORK_REQUIRED`로 전환한다.

### 12.3 반려 입력 흐름

사용자는 유형 이름을 알 필요가 없다.

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

### 12.4 부분 반려

- 지정된 Task만 `REWORK_REQUIRED`로 전환하고 나머지 Task의 완료와 커밋은 유지한다.
- 재작업 Task가 모두 완료되면 Phase 결과 승인을 다시 요청한다.
- 재요청 시 결과 자료에 이전 반려 내용과 처리 결과를 포함한다.
- Task 하나의 문제로 Phase 전체를 다시 검증하지 않는다.

### 12.5 반려 후 유효성 재확인

| 변경 대상 | 무효화 범위 |
|---|---|
| 특정 Task 정의만 변경 | 해당 Task의 승인·검증 결과 |
| 공통 Domain Rule 변경 | 해당 Phase의 모든 Task |
| 실행 설정(검증 명령·필수 여부) 변경 | 해당 Phase의 모든 Task |
| 변경 없는 Task | 완료 유지 |

판정은 `task_hash` 비교로 수행한다(14.5). 이미 커밋된 Task를 무조건 전부 무효화하면 Phase 하나가 통째로 다시 실행되어 실사용이 불가능하다.

### 12.6 반복 제한

- **계획 반려 3회 초과**: 자동 재계획을 중단하고 `PLAN_BLOCKED`로 보고한다. 같은 입력으로 AI를 반복 호출해도 결과가 달라지지 않는다.
- **같은 Task 3회 이상 결과 반려**: 재작업은 계속하되 Phase 범위 재검토를 제안한다.
- 반려 횟수는 `max_retries`와 별도로 집계한다.

---

## 13. Retry와 실패 처리

### 13.1 자동 재시도 대상

- lint 또는 typecheck 실패
- Unit Test 실패
- 명확한 Reviewer 수정 요청
- 변경 범위 안에서 해결 가능한 Integration Test 실패

재시도 여부의 최종 판정은 Orchestrator가 한다. AI는 실패 원인과 수정 방향을 분석하며, 그 분석만으로 재시도 한도나 완료 기준을 바꿀 수 없다.

### 13.2 자동 재시도 중단

- 동일 원인 반복
- 최대 재시도 횟수 초과
- Architecture 변경 필요
- 기획 또는 Domain Rule이 모호함
- 외부 서비스 장애
- 사용자 권한 또는 Secret 필요
- 승인 대상 행동 필요

권한 부족, 도구 미설치, 기획 모순을 코드 수정 반복으로 해결하려 하지 않는다. 한도 초과 시 현재 결과, 실패 원인, 시도 내역과 필요한 판단을 보고한다.

중단 시 `WAITING_APPROVAL`, `BLOCKED`, `REPLAN_REQUIRED`, `FAILED` 중 하나로 전환하고 상태·단계·Revision을 SQLite에 기록한다.

---

## 14. 데이터 모델

### 14.1 저장 위치

```text
%LOCALAPPDATA%/AI-Development-Harness/{project.id}-{repo-path-hash}/
├─ state.db
├─ backups/        최근 10개 순환
└─ logs/           검증 명령 전체 로그
```

`{repo-path-hash}`는 저장소 절대 경로의 짧은 해시다. 같은 `project.id`를 가진 다른 체크아웃을 구분하면서 디렉토리 이름은 사람이 읽을 수 있게 유지한다.

설계 원칙은 다음과 같다.

- **파생값을 중복 저장하지 않는다.** `validated_revision`, `reviewed_revision` 같은 값은 검사 이력에서 계산하며 `tasks`에 사본을 두지 않는다.
- **상태와 단계를 분리한다.** 상태는 Workflow와 무관하게 공통이고, 진행 위치는 `current_step`으로 관리한다.
- **AI는 어떤 테이블도 직접 쓰지 않는다.**
- **시작만 기록된 검사는 성공이 아니다.**

### 14.2 상태 정의

**Phase**

| 상태 | 의미 |
|---|---|
| `PLANNING` | 계획 작성 중 |
| `PLAN_PENDING_APPROVAL` | 계획 승인 대기 |
| `PLAN_REJECTED` | 계획 반려됨, 재계획 대상 |
| `PLAN_BLOCKED` | 계획 반려 3회 초과 |
| `PLAN_APPROVED` | 승인됨, 실행 가능 |
| `IN_PROGRESS` | Task 실행 중 |
| `RESULT_PENDING_APPROVAL` | 결과 승인 대기 |
| `RESULT_REJECTED` | 결과 반려됨, 재작업 대상 |
| `REPLAN_REQUIRED` | 요구사항 오해로 재계획 필요 |
| `ACCEPTED` | 사용자 인수 완료 |
| `ABANDONED` | Phase 폐기, 브랜치·커밋 보존 |

**Task**

| 상태 | 의미 |
|---|---|
| `PENDING` | 선행 Task 미완료 |
| `READY` | 실행 가능 |
| `RUNNING` | 실행 중 (세부 위치는 `current_step`) |
| `WAITING_APPROVAL` | 승인 대상 행동에서 정지 |
| `REWORK_REQUIRED` | 반려로 재작업 대상 |
| `BLOCKED` | `DENY_STOP` 또는 해결 불가로 중단 |
| `FAILED` | 재시도 한도 초과·실행 환경 문제 |
| `COMPLETED` | 완료 조건 충족 및 커밋 확인 |

**Step** — Workflow가 단계 순서를 정의하며 상태 집합은 공통이다.

```text
Fast      implement → quick_validate → commit
Standard  implement → pre_validate → review → post_validate → commit
Strict    implement → pre_validate → review → post_validate → commit
```

`step_status`는 `STARTED` / `PASSED` / `FAILED`다. 재개 시 `STARTED`로 남은 단계는 현재 Revision에서 다시 실행한다.

### 14.3 상태 전이

```text
Phase
  PLANNING → PLAN_PENDING_APPROVAL
  PLAN_PENDING_APPROVAL ─approve→ PLAN_APPROVED → IN_PROGRESS
                        ─reject→ PLAN_REJECTED → PLANNING
                                 (3회 초과) → PLAN_BLOCKED
  IN_PROGRESS ─모든 Task 종결→ RESULT_PENDING_APPROVAL
  RESULT_PENDING_APPROVAL ─approve→ ACCEPTED
                          ─NOT_WORKING/QUALITY/MISSING→ RESULT_REJECTED → IN_PROGRESS
                          ─WRONG_REQ→ REPLAN_REQUIRED → PLANNING
                          ─ABANDON→ ABANDONED

Task
  PENDING ─선행 완료→ READY ─Run 선택→ RUNNING
  RUNNING ─승인 대상 행동→ WAITING_APPROVAL ─approve→ RUNNING
                                           ─DENY_ALT→ RUNNING (제약 추가)
                                           ─DENY_STOP→ BLOCKED
  RUNNING ─완료 조건 + 커밋 확인→ COMPLETED
  RUNNING ─재시도 한도 초과→ FAILED
  COMPLETED ─결과 반려→ REWORK_REQUIRED → RUNNING (attempt_no + 1)
  BLOCKED ─사용자 해제→ READY
```

"모든 Task 종결"은 `COMPLETED`, `BLOCKED`, `FAILED`를 포함한다. 미완료 Task가 있어도 결과 승인을 요청할 수 있으며, 결과 자료에 미완료 항목과 사유를 명시한다.

### 14.4 스키마

```sql
-- 메타. project_id, repo_path, schema_version, harness_version
CREATE TABLE schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Run은 Phase 실행 단위다.
-- 계획 수립과 기획 검토는 파일 산출물이므로 Run을 만들지 않는다.
CREATE TABLE runs (
  id           TEXT PRIMARY KEY,
  phase_id     TEXT NOT NULL,
  status       TEXT NOT NULL,          -- ACTIVE / SUSPENDED / CLOSED
  branch       TEXT NOT NULL,
  plan_hash    TEXT NOT NULL,
  owner_pid    INTEGER,
  heartbeat_at TEXT,
  started_at   TEXT NOT NULL,
  ended_at     TEXT
);

CREATE TABLE phases (
  id                TEXT PRIMARY KEY,
  title             TEXT NOT NULL,
  status            TEXT NOT NULL,
  plan_hash         TEXT,
  plan_reject_count INTEGER NOT NULL DEFAULT 0,
  branch            TEXT,
  start_commit      TEXT,
  end_commit        TEXT,
  updated_at        TEXT NOT NULL
);

CREATE TABLE tasks (
  id              TEXT PRIMARY KEY,
  phase_id        TEXT,
  status          TEXT NOT NULL,
  current_step    TEXT,
  step_status     TEXT,                -- STARTED / PASSED / FAILED
  workflow        TEXT,                -- fast / standard / strict
  workflow_reason TEXT,
  task_hash       TEXT NOT NULL,
  attempt_no      INTEGER NOT NULL DEFAULT 1,
  retry_count     INTEGER NOT NULL DEFAULT 0,
  reject_count    INTEGER NOT NULL DEFAULT 0,
  updated_at      TEXT NOT NULL,
  FOREIGN KEY (phase_id) REFERENCES phases(id)
);

-- 반려·재작업으로 다시 시작할 때마다 1행
CREATE TABLE task_attempts (
  id                 INTEGER PRIMARY KEY,
  task_id            TEXT NOT NULL,
  attempt_no         INTEGER NOT NULL,
  run_id             TEXT,
  started_at         TEXT NOT NULL,
  ended_at           TEXT,
  outcome            TEXT,             -- COMPLETED / REWORK / BLOCKED / FAILED
  commit_sha         TEXT,
  invalidated_reason TEXT,
  UNIQUE (task_id, attempt_no)
);

CREATE TABLE approvals (
  id                TEXT PRIMARY KEY,  -- APR-001
  kind              TEXT NOT NULL,     -- phase_plan / task_plan / risk_decision
                                       -- / phase_result / task_result / push / merge
  target_type       TEXT NOT NULL,     -- phase / task
  target_id         TEXT NOT NULL,
  plan_hash         TEXT NOT NULL,
  task_hash         TEXT,
  requested_payload TEXT NOT NULL,     -- 승인 요청 시 사용자에게 제시한 내용
  requested_at      TEXT NOT NULL,
  decision          TEXT,              -- APPROVED / REJECTED / NULL(대기)
  decided_at        TEXT,
  valid             INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE rejections (
  id                TEXT PRIMARY KEY,  -- REJ-001
  approval_id       TEXT NOT NULL,
  reject_type       TEXT NOT NULL,
  user_text         TEXT NOT NULL,     -- 사용자 자연어 원문
  ai_classification TEXT NOT NULL,     -- AI 분류 결과
  confirmed_at      TEXT NOT NULL,     -- 사용자 확인 시각
  plan_hash         TEXT NOT NULL,
  FOREIGN KEY (approval_id) REFERENCES approvals(id)
);

CREATE TABLE rejection_targets (
  rejection_id TEXT NOT NULL,
  task_id      TEXT NOT NULL,
  PRIMARY KEY (rejection_id, task_id)
);

CREATE TABLE validations (
  id            INTEGER PRIMARY KEY,
  task_id       TEXT NOT NULL,
  attempt_no    INTEGER NOT NULL,
  stage         TEXT NOT NULL,         -- quick / pre_review / post_review
  name          TEXT NOT NULL,
  command       TEXT NOT NULL,
  required      INTEGER NOT NULL,
  code_revision TEXT NOT NULL,
  started_at    TEXT NOT NULL,
  ended_at      TEXT,
  exit_code     INTEGER,
  result        TEXT NOT NULL,         -- STARTED / PASSED / FAILED
                                       -- / SKIPPED_BY_POLICY / ABORTED
  log_path      TEXT
);

CREATE TABLE reviews (
  id                 INTEGER PRIMARY KEY,
  task_id            TEXT NOT NULL,
  attempt_no         INTEGER NOT NULL,
  kind               TEXT NOT NULL,    -- light / strict / delta
  code_revision      TEXT NOT NULL,
  plan_hash          TEXT NOT NULL,
  baseline_review_id INTEGER,          -- Delta Review의 이전 기준
  result             TEXT NOT NULL,    -- STARTED / PASS / CHANGES_REQUESTED
                                       -- / ABORTED / SKIPPED_BY_POLICY
  started_at         TEXT NOT NULL,
  ended_at           TEXT
);

CREATE TABLE review_findings (
  id                    INTEGER PRIMARY KEY,
  review_id             INTEGER NOT NULL,
  severity              TEXT NOT NULL,  -- critical / major / minor
  finding_ref           TEXT,           -- REV-001
  file                  TEXT,
  description           TEXT NOT NULL,
  required_change       TEXT,
  resolved_at           TEXT,
  resolved_in_review_id INTEGER,
  FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- 커밋 직후 중단 복구용
CREATE TABLE commit_intents (
  id            TEXT PRIMARY KEY,      -- 커밋 메시지 메타데이터에 기록
  run_id        TEXT NOT NULL,
  task_id       TEXT NOT NULL,
  attempt_no    INTEGER NOT NULL,
  branch        TEXT NOT NULL,
  parent_commit TEXT NOT NULL,
  code_revision TEXT NOT NULL,
  plan_hash     TEXT NOT NULL,
  status        TEXT NOT NULL,         -- PENDING / CONFIRMED / ABANDONED
  commit_sha    TEXT,
  created_at    TEXT NOT NULL
);

-- 실행에 사용한 계획 입력 사본
CREATE TABLE plan_snapshots (
  plan_hash       TEXT PRIMARY KEY,
  phase_id        TEXT,
  work_items_yaml TEXT NOT NULL,
  domain_rules_md TEXT NOT NULL,
  project_yaml    TEXT NOT NULL,
  created_at      TEXT NOT NULL
);
```

### 14.5 Revision과 Hash

**코드 Revision** — 임시 index로 작업 폴더 전체의 Git tree hash를 계산한다.

```bash
GIT_INDEX_FILE=<임시파일> git add -A
GIT_INDEX_FILE=<임시파일> git write-tree
```

- `.gitignore`를 그대로 따르므로 제외 규칙을 다시 구현하지 않는다.
- 새 파일, 삭제, 이름 변경, 실행 권한 변경이 모두 반영된다.
- 사용자의 스테이징 영역을 건드리지 않는다.
- 추가 제외 대상은 `.dev-harness/reports/`다. 보고서 생성 때문에 코드 Revision이 바뀌지 않게 한다.
- 프로젝트는 Git 저장소여야 한다.

**task_hash** — Task 정의만으로 계산하며, 반려 후 무효화 범위를 Task 단위로 좁히는 데 사용한다.

- 포함: `id`, `title`, `acceptance_criteria`, `requirement_refs`, `domain_rule_refs`, `risk_tags`, `depends_on`
- 제외: 실행 상태, 재시도 횟수, 승인 여부

**plan_hash** — Phase 단위로 계산하며 승인을 여기에 연결한다.

- 포함: Phase 정의, 소속 Task의 `task_hash` 정렬 목록, 공통 Domain Rule 본문, 참조된 Domain Rule 본문, `validation`·`workflow_routing`·`approval` 설정
- 제외: 실행 상태, 로그, 보고서, `plan.md`의 서술 문장

`plan.md`는 사람이 읽는 설명이므로 문구 수정만으로 승인이 무효화되지 않게 한다. 전역 hash 하나를 쓰면 무관한 Phase의 Task 추가로 모든 승인이 무효화된다.

### 14.6 동시 실행 제어

- `runs.owner_pid`와 `heartbeat_at`으로 실행 소유권을 확인한다.
- `ACTIVE` Run의 프로세스가 살아 있으면 새 실행을 시작하지 않는다.
- heartbeat가 끊긴 Run은 `SUSPENDED`로 전환하고 재개 절차를 따른다.
- 파일 락은 사용하지 않는다. OneDrive 동기화 폴더에서 신뢰하기 어렵고, DB는 LocalAppData에 있어 안전하다.

### 14.7 재개 검사 순서

```text
1. runs에서 해당 프로젝트의 ACTIVE/SUSPENDED Run 조회
2. owner_pid 생존 확인
3. schema_meta.repo_path와 현재 저장소 경로 대조
4. runs.branch와 현재 HEAD 대조
5. commit_intents에 PENDING이 있으면 커밋 복구 절차 수행
6. plan_snapshots의 plan_hash와 현재 계획 파일 hash 대조
7. 코드 Revision 재계산 후 마지막 체크포인트와 대조
8. tasks.current_step / step_status로 재개 지점 결정
   - step_status = STARTED  → 해당 단계 재실행
   - step_status = PASSED   → 다음 단계
```

| 상황 | 처리 |
|---|---|
| 체크포인트와 코드·계획이 같음 | 완료가 확인된 단계는 재사용하고 다음 단계로 진행 |
| 다른 Branch 또는 예상하지 못한 코드 변경 | `BLOCKED`, 사유 `STATE_MISMATCH`. 저장값·현재값과 변경 파일 표시 |
| 완료 기준·규칙 등 계획 변경 | `REPLAN_REQUIRED`. 기존 승인 절차 적용 |
| Commit은 성공했으나 DB 기록이 없음 | 15.2에 따라 기존 Commit을 검증하고 완료 기록 복구 |

- 미커밋 변경이 있다는 이유만으로 오류로 처리하지 않는다. 파일 목록이나 dirty 여부만 비교하지 않고 저장한 코드 내용과 대조한다.
- 불일치 시 자동으로 파일을 덮어쓰거나 Git을 되돌리지 않는다.
- 재개는 Retry 횟수나 승인 기록을 초기화하지 않는다.
- 사용자의 수동 변경이 Task 범위에 속하는지 확인한다. 관련 없는 변경을 되돌리거나 Task Commit에 포함하지 않는다.

### 14.8 백업과 스키마 버전

- Task 완료와 정상 중단 시 SQLite 백업 API로 사본을 만들고 최근 10개를 순환 보관한다.
- `schema_meta.schema_version`을 기록한다. 하네스 버전과 DB 스키마 버전이 맞지 않으면 실행하지 않고 안내한다. 자동 마이그레이션은 v1.1로 미룬다.

---

## 15. Git 전략

### 15.1 쓰기 범위와 승인 종속

```text
main
 └─ harness/phase/P1-document-processing
     ├─ commit: P1-T1
     ├─ commit: P1-T2
     └─ commit: P1-T3
```

| 동작 | 조건 |
|---|---|
| 하네스가 쓰는 대상 | `harness/phase/<phase-id>` 전용 브랜치 한정 |
| main·기존 브랜치 직접 커밋 | 금지 |
| 브랜치 생성 | 해당 Phase 계획에 유효한 승인이 있을 때만 |
| Task 커밋 | 승인된 계획 범위 안의 Task에 한해, 검증 통과 후 자동 |
| 승인이 없거나 무효화된 상태 | 커밋하지 않고 승인 대기로 정지 |
| push / merge / main 반영 | 별도 승인 |
| Phase 완료 처리 | 커밋이 있어도 사용자 결과 승인 전에는 완료로 처리하지 않음 |

**커밋은 작업의 저장이고 완료는 사용자의 인수다.** 둘을 같은 것으로 취급하지 않는다. 기존 작업과 사용자 변경을 확인하고 관련 변경만 커밋한다.

### 15.2 Task Commit과 중단 복구

```text
Workflow별 최종 검증 조건 충족
→ SQLite에 commit_intents 기록 (PENDING)
  - Run ID / Task ID / 계획 hash
  - 예상 부모 Commit / Branch / 최종 코드 Revision
  - 이번 Commit 작업의 고유 식별자
→ 해당 스냅샷으로 Git Commit 생성
→ 생성된 Commit의 부모·내용 및 작업 폴더 확인
→ SQLite 트랜잭션으로 Commit SHA와 COMPLETED 기록
→ 다음 Task
```

- Commit 메시지 메타데이터에 Run ID, Task ID, Commit 작업 식별자를 남긴다.
- Commit 직전 코드가 바뀌었으면 완료 절차를 멈추고 새 Revision에서 필요한 검사를 수행한다.
- `PENDING`에서 재개하면 해당 식별자·부모·내용을 가진 Commit이 실제 브랜치에 있는지 확인한다. 일치하면 기존 Commit을 연결하고 DB 기록만 복구한다.
- Commit이 없고 브랜치·HEAD·코드가 예상한 직전 상태라면, 승인과 필수 검사 결과의 유효성을 확인한 뒤 Commit 단계만 재시도한다.
- 다른 Commit이나 예상하지 못한 변경이 있으면 `STATE_MISMATCH`로 중단한다. 중복 Commit을 만들거나 완료된 Task를 자동 재실행하지 않는다.

복구에 필요한 현재 작업 기록만 저장하며 완전한 Event Sourcing은 도입하지 않는다.

---

## 16. 산출물과 보고

### 16.1 Task 완료 기록

Task 완료 시 SQLite에 저장한다.

- Task ID와 상태, 적용 Workflow, Risk Tag와 선택 근거
- 승인된 계획 hash와 최종 코드 Revision
- Git commit SHA와 변경 파일 목록
- Review 결과 요약, 검사한 Revision, Delta Review의 이전 기록 연결
- Validation 명령별 결과와 검사한 Revision, 정책상 생략한 검사와 사유
- 재시도 횟수, 사용된 승인 ID, 알려진 제한사항

### 16.2 Phase 결과 자료

Phase 결과 승인은 **사용자가 실제로 무엇이 되는지 판단할 수 있어야** 성립한다. 완료 개수와 테스트 통과 여부만으로는 인수 판단을 할 수 없다.

```markdown
# Phase P1 결과

## 직접 확인하는 방법

- `npm run dev` 실행 후 `/upload`에서 PDF를 올려 결과를 확인한다
- 샘플: `samples/registry-text.pdf`, `samples/registry-scan.pdf`

## 완료 기준 충족 근거

| 완료 기준 | 근거 | 확인 방법 |
|---|---|---|
| 텍스트 PDF에서 페이지별 텍스트를 추출한다 | P1-T3 / tests/unit/pdf/test_text.py | 자동 |
| 스캔 PDF를 판별해 OCR로 처리한다 | P1-T4, P1-T5 / tests/integration/ocr | 자동 |
| OCR 실패와 위험 없음을 구분한다 | P1-T5 / OcrStatus 타입 | 자동 |
| 원문 데이터를 로그에 남기지 않는다 | P1-T7 / 개인정보 로그 검사 | 자동 |

## 실행하지 않은 검증

- 실제 브라우저 화면 확인: 수행하지 않음
- 오래된 등기 양식: 샘플 미확보로 미검증

## 사용자가 직접 확인할 항목

- 업로드 화면의 오류 메시지 문구
- 스캔 문서 처리 대기 시간의 체감 수준

## 남은 위험

- OCR 품질이 문서 상태에 따라 크게 달라질 수 있음

## 실행 요약

- 완료 Task: 8/8
- 자동 재시도: 2회
- 사용자 승인: 1건
- 반려: 1건 (P1-T5, 동작하지 않음 → 재작업 후 완료)

## Git

- Branch: harness/phase/P1-document-processing
- Start Commit: abc123
- End Commit: def456
```

- 보고서는 SQLite 실행 기록과 Git 정보로 생성한다. 보고서를 편집하거나 삭제해도 실행 상태와 승인 기록은 바뀌지 않는다.
- 자동으로 확인하지 못한 항목은 반드시 표시한다. 수행하지 않은 검증을 통과로 표시하지 않는다.
- 미완료 Task가 있으면 항목과 사유를 명시한다.

---

## 17. 사용자 명령

```text
devh init <planning-document>
devh review [planning-document]
devh plan
devh start <phase-id>
devh run
devh status
devh approve <approval-id>
devh reject <approval-id> [--type <t>] [--tasks <ids>] [--note "<사유>"]
devh rejections [phase-id]
devh resume [run-id]
devh close <phase-id>
devh report <phase-id>
```

Slash Command는 같은 Core CLI를 호출한다.

```text
/development init Draft/product-plan.md
/development review
/development plan
/development start P1
/development status
/development approve APR-001
/development reject APR-004
/development resume
/development close P1
```

Slash Command는 기존 명령을 먼저 식별한다. `/development 다음 Phase 시작해줘`처럼 자연어로 입력된 경우 계획과 SQLite 상태에서 대상을 확인해 해당 명령으로 연결하며, 대상을 특정할 수 없으면 확인한다. 일반 채팅의 모든 문장을 자동 수집하지 않는다.

---

## 18. 실행 예시 — 부동산 등기부등본 분석

### 18.1 초기화와 검토

```text
devh init Draft/registry-analysis-plan.md
devh review
```

검토 리포트가 다음을 보고한다고 가정한다.

```text
누락  OCR 실패 시 결과 표시 방식이 정의되지 않음
누락  원본 문서 보관 정책이 없음
모순  "외부 전송 없음"과 "클라우드 OCR 활용" 서술이 충돌 (3장 / 7장)
모호  "위험 신호"의 판정 주체가 규칙 엔진인지 LLM인지 불명확
```

사용자가 기획을 보완한 뒤 `devh plan`을 실행한다.

### 18.2 계획과 Workflow

```text
P1 — 문서 입력과 텍스트 추출
P2 — 등기 항목 구조화
P3 — 위험 분석과 보고서
P4 — UI 통합과 품질 검증
```

| Task | 위험 | Workflow |
|---|---|---|
| P1-T1 기본 구조 | 낮음 | Fast |
| P1-T2 PDF 검증 | 개인정보 입력 | Strict |
| P1-T3 텍스트 추출 | 보통 | Standard |
| P1-T5 OCR 어댑터 | 민감문서 처리 | Strict |

### 18.3 Strict Task 실행

`P1-T5 로컬 OCR 어댑터`의 Context는 요구사항, 관련 Domain Rule, 허용 경로로 구성한다.

```text
요구사항        스캔 PDF에서 페이지별 텍스트 추출, 실패 페이지 식별, confidence 저장
Domain Rule     원본 문서를 외부로 전송하지 않는다
                OCR 실패와 위험 없음은 별도 상태다
                원문 내용을 로그에 기록하지 않는다
허용 경로       src/ocr/**, tests/unit/ocr/**, tests/integration/ocr/**
```

Pre-review Validation 통과 후 Strict Review에서 다음을 지적한다.

```text
CHANGES_REQUESTED
1. OCR 실패 페이지가 빈 문자열로 반환된다
2. 빈 문자열이 정상 추출 결과와 구분되지 않는다
3. confidence 범위가 검증되지 않는다
```

Developer가 상태를 `SUCCESS` / `PARTIAL` / `FAILED`로 분리하고 confidence 범위를 검증한다. Pre-review Validation과 Delta Review를 다시 수행한 뒤 Post-review Full Validation을 통과하면 15.2 절차로 커밋한다.

### 18.4 실행 중 승인과 반려

Developer가 외부 OCR API 도입이 필요하다고 판단하면 중단한다.

```text
WAITING_APPROVAL

요청    외부 OCR API와 SDK 도입
영향    원본의 외부 전송 가능성 / API 비용 / API Key 필요 / 개인정보 처리 정책 필요
추천    MVP에서는 로컬 OCR 유지
```

사용자가 `DENY_ALT`로 반려하고 "로컬 OCR로 유지"를 지시하면, 거부된 방법을 제약으로 전달해 재구현한다.

### 18.5 Phase 종료

모든 Task 완료 후 16.2 형식의 결과 자료를 제시한다. 사용자가 `NOT_WORKING`으로 P1-T5만 부분 반려하면 해당 Task가 `REWORK_REQUIRED`로 돌아가고 나머지 7개의 완료는 유지된다. 재작업 완료 후 결과 승인을 다시 요청한다.

인수 후 Push와 Merge를 별도로 승인한다. 등기 항목 파싱과 위험 판정은 핵심 Domain Rule이므로 Strict를 적용하며, 법률적 정확성은 AI Review만으로 확정하지 않고 Phase 인수 조건에 사람의 도메인 검토를 포함한다.

---

## 19. 하네스 개발 Phase

### Phase 0 — Runner Skeleton (AI 호출 없음)

AI를 연결하기 전에 상태 기계와 승인·재개를 결정론적으로 검증한다. AI가 끼면 재현이 안 되어 디버깅이 불가능하다.

- Python CLI 구조와 `devh` 진입점
- `project.yaml` 스키마 검증
- SQLite 스키마 생성과 상태 전이 구현
- 코드 Revision과 `task_hash` / `plan_hash` 계산
- 승인 대기·승인·반려 처리
- 중단과 재개, 실행 소유권 확인
- **가짜 Adapter(스텁)로 계획·구현·리뷰 결과를 주입**해 전 흐름을 통과
- 2.2의 권한 경계가 실제로 집행되는지 확인

### Phase 1 — Foundation

- `plan.md`, `work-items.yaml`, `domain-rules.md` 구조와 참조 검증
- 실행 입력 사본 저장과 로컬 DB 백업
- Git 저장소 정합성 검사와 재개 판단
- `init`, `status`, `resume` 명령
- 프로젝트 탐색과 프로젝트별 상태 구분, 재초기화 시 기존 기록 보존

### Phase 2 — Planning

- Markdown 기획서 읽기
- 기획 검토 리포트 생성 (`devh review`)
- 전체 Phase 계획 생성과 현재 Phase Task 분해
- Task 의존성, Acceptance Criteria, 원문·Domain Rule 참조 생성
- Domain Rule 추출과 Risk Tag 제안
- 계획 승인·반려와 계획 hash

### Phase 3 — Execution

- Codex CLI Adapter
- `/development`를 Core CLI에 연결
- Developer·Reviewer Context 구성
- Risk Tag 기반 Workflow 선택과 실행 중 위험 갱신
- Revision에 연결된 Review·Validation Runner와 완료 판정
- Retry 제한
- Task Commit과 커밋 직후 중단 복구

### Phase 4 — Delivery

- 설치·연결·초기화 사용 안내
- Phase 통합 검증
- Phase 결과 자료와 인수·반려
- Push 및 Merge 승인
- Decision Desk Phase 하나 dogfooding

---

## 20. MVP 완료 조건

아래는 앞으로 수행할 검증 기준이며 실제 테스트 결과가 아니다.

**설치와 초기화**

- [ ] 한 번 설치한 뒤 여러 프로젝트에서 같은 `devh`를 사용할 수 있다
- [ ] 하네스 소스를 대상 프로젝트에 복사하지 않고 초기화할 수 있다
- [ ] 서로 다른 프로젝트의 설정·상태·승인이 섞이지 않으며, 재초기화 시 기존 기록이 보존된다
- [ ] 필수 설정 파일 하나로 프로젝트를 초기화할 수 있다

**계획**

- [ ] 기획 문서에서 누락·모순·모호 항목을 리포트로 제시한다
- [ ] Markdown 기획서에서 전체 Phase 계획을 생성한다
- [ ] 현재 Phase를 실행 가능한 Task로 분해한다
- [ ] 실행 가능한 Task는 확인 가능한 완료 기준을 가지며 승인과 연결된다
- [ ] 존재하지 않는 참조나 순환 의존성이 있는 계획은 실행하지 않는다
- [ ] ID 문자열을 파싱해 계층을 유추하지 않는다

**실행**

- [ ] 계획 승인 전에는 제품 코드 구현을 시작하지 않는다
- [ ] 의존성이 완료된 Task만 실행한다
- [ ] Orchestrator가 Risk Tag와 정책으로 Workflow를 선택하고 근거를 기록한다
- [ ] 실행 중 새 위험이 발견되면 Workflow를 강화하고, 행동 승인은 별도로 확인한다
- [ ] Pre-review Validation 실패 시 Reviewer를 호출하지 않는다
- [ ] Reviewer는 전체 프로젝트가 아닌 관련 diff 중심으로 검토한다
- [ ] 필수 검증의 실패·미실행·중단을 성공으로 처리하지 않는다
- [ ] 검토한 코드, 검증한 코드, 승인 대상 코드가 일치한다
- [ ] 실패 시 설정된 횟수만 자동 재시도하고, 한도 초과 시 시도 내역을 보고한다

**승인과 반려**

- [ ] 승인 대상 행동에서 실행을 중단한다
- [ ] 무응답을 자동 승인으로 처리하지 않는다
- [ ] 에이전트가 승인 기록이나 완료 기준을 바꿔 통과하지 못한다
- [ ] 권한 부족 시 제한을 자동 해제하지 않고 차단 상태를 보고한다
- [ ] 자연어 반려를 유형으로 분류해 사용자 확인 후 상태를 전이한다
- [ ] Phase 결과를 부분 반려하면 지정 Task만 재작업 대상이 된다
- [ ] 반려해도 코드·커밋·브랜치를 자동으로 되돌리지 않는다
- [ ] 계획 반려 3회 초과 시 자동 재계획을 중단한다
- [ ] 사용자 결과 승인 전에는 Phase를 완료로 처리하지 않는다

**상태와 복구**

- [ ] 실행 상태와 승인 기록을 SQLite만으로 관리하며 YAML·Markdown과 이중 관리하지 않는다
- [ ] 컴퓨터 재부팅 후 Git·Working Tree·계획·SQLite를 확인하고 Run을 재개한다
- [ ] 예상하지 못한 불일치는 차이를 표시하고 중단하며 자동 덮어쓰기를 하지 않는다
- [ ] Commit 직후 DB 저장 전 중단을 복구하며 중복 Commit을 만들지 않는다
- [ ] 사용자의 기존 변경과 다른 프로젝트 파일을 훼손하지 않는다

**산출물**

- [ ] Task마다 Git commit과 검증 결과를 연결할 수 있다
- [ ] Phase 결과 자료에 실행 방법, 완료 기준 충족 근거, 미검증 항목, 반려 이력을 포함한다
- [ ] 자동 Git Push·Merge·배포를 승인 없이 수행하지 않는다
- [ ] Decision Desk의 실제 Phase 하나를 처음부터 끝까지 실행할 수 있다

---

## 21. MVP 이후 확장 순서

실사용에서 필요성이 확인된 기능만 다음 순서로 확장한다.

1. **자연어 수정 요청** — 초기 설정을 마친 프로젝트에서 "상단의 폰트를 10pt로 줄여줘" 같은 요청을 작은 Task로 변환해 같은 실행 엔진에서 처리한다. Phase 없는 독립 Task, 의도 분류, 요청 기반 범위 승인이 필요하므로 핵심 루프 검증 후 도입한다.
2. 요구사항 커버리지 자동 검사 (6.3)
3. 추가 AI Provider Adapter
4. Task별 Git worktree
5. 독립 Failure Analyst
6. Security Reviewer 및 Domain Reviewer
7. Agent Registry 외부 설정
8. Workflow DAG 사용자 설정
9. 병렬 Task 실행
10. 원격 Artifact Store
11. Web Dashboard
12. Project Kickoff Harness 연동

---

## 22. 결정 근거

이 문서의 설계 결정과 그 근거는 `archive/harness-decision-record.md`에 D-01 ~ D-33으로 보존되어 있다. v0.5 확정 시점의 기록이며, 반려 경로와 데이터 모델의 설계 과정은 같은 폴더의 `rejection-path-spec.md`, `data-model-spec.md`에 남아 있다.

이후의 설계 변경은 이 문서를 개정하면서 아래 이력에 기록한다.

| 날짜 | 변경 | 사유 |
|---|---|---|
| 2026-09-14 | v0.5 확정 (D-01 ~ D-33) | v0.4와 v0.1의 설계 축 11개 충돌을 정리하고 반려 경로·데이터 모델·기획 검토를 신설 |

미결 항목은 다음과 같다.

| ID | 내용 | 상태 |
|---|---|---|
| O-02 | 자동 수정 한도 2회 vs 3회 | 기본값 2회로 시작하고 실행 데이터로 재검토 |
| O-03 | Codex 호출 방식 (CLI subprocess vs SDK) | CLI subprocess로 고정, 실사용에서 판단 |
