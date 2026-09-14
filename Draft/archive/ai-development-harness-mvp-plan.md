# AI Development Harness MVP 기획서

> 대상: 바이브 코딩 사용자 및 중·소규모 프로젝트  
> 상태: Draft  
> 버전: 0.5\
> 작성일: 2026-09-13  
> 수정일: 2026-09-14  
> 개정 내용: Git 쓰기 자동화 제거, 파일 내용 기반 완료·재개 기준으로 전환, 기획 변경 이력 추가\
> 첫 dogfooding 대상: Decision Desk  
> 관련 문서: `Draft/ai-development-harness-plan.md`는 장기 Target Architecture로 유지한다.

---

## 1. 문서 목적

이 문서는 바이브 코딩 사용자와 중·소규모 프로젝트에서 실제로 사용할 수 있는 AI Development Harness의 1차 MVP 범위를 정의한다. 사용자는 전문적인 개발 프로세스나 내부 저장 구조를 몰라도 계획을 확인하고, 자연어로 수정을 요청하며, 결과를 확인할 수 있어야 한다.

기존 `ai-development-harness-plan.md`에 정의한 범용 Agent Registry, 임의 Workflow DAG, 병렬 Agent, 다중 AI Provider, 완전한 Artifact Registry 등은 장기 방향으로 유지하되 MVP에서는 구현하지 않는다.

MVP의 목표는 다음 Phase 개발 흐름을 안정적으로 완성하는 것이다.

```text
기획서 읽기
→ 전체 Phase 계획
→ 현재 Phase Task 분해
→ 사용자 계획 승인
→ Task 순차 개발
→ 빠른 검증
→ 필요한 경우 AI Review
→ Workflow에서 요구하는 후속 검증
→ 제한적 재시도
→ 최종 코드 Revision과 Task 완료 기록
→ Phase 보고서
→ 사용자 인수
```

이미 초기 설정을 마친 프로젝트에서는 자연어로 작은 수정을 요청할 수도 있다. 이 요청은 작은 Task로 변환되어 같은 실행 엔진과 상태 저장소를 사용한다.

```text
자연어 수정 요청
→ 관련 코드 확인과 Task 생성
→ Workflow 자동 선택 및 권한 확인
→ 구현·검증
→ 최종 Revision 확인·Task 완료 기록
→ 결과 안내
```

작은 수정마다 전체 Phase 계획을 다시 만들거나 사용자가 Workflow를 직접 선택하도록 요구하지 않는다.

---

## 2. 제품 판단

### 2.1 현재 방향에서 유지할 것

- 하네스와 프로젝트별 설정을 분리한다.
- 하네스는 컴퓨터의 사용자 환경에 한 번 설치하고, 사용할 프로젝트마다 초기화한다.
- 개발 계획은 `기획 → Phase → Task` 구조를 기본으로 한다.
- 전체 Phase를 먼저 계획하고 현재 Phase만 상세화한다.
- Phase, Feature, Ticket, Task를 내부적으로 Work Item이라는 공통 형식으로 표현할 수 있게 한다.
- 실행 상태와 승인 기록의 유일한 기준은 SQLite이며, Orchestrator가 이를 읽고 갱신한다.
- 테스트 성공 여부는 실제 명령 실행 결과로 판정한다.
- 위험한 행동에서만 사용자 승인을 요청한다.
- 컴퓨터를 재시작해도 개발 Run을 재개할 수 있어야 한다.
- 실제 코드와 테스트는 프로젝트 작업 폴더에 유지한다. Git 사용 여부와 모든 Git 쓰기 작업은 사용자가 수동으로 결정·수행한다.

### 2.2 MVP에서 축소할 것

- 설정은 여러 YAML이 아닌 `project.yaml` 하나로 시작한다.
- Phase와 Task를 기본 계층으로 사용한다.
- Workflow는 Fast, Standard, Strict 3종을 내장한다.
- 자연어 수정 요청은 작은 Task로 만들고 같은 내장 Workflow로 실행한다.
- Agent는 Planner, Developer, Reviewer 역할만 둔다.
- Tester는 AI Agent가 아니라 Validation Runner로 구현한다.
- 실패 분석 전용 Agent를 만들지 않고 오류 로그를 Developer에게 전달한다.
- Codex CLI Adapter 하나부터 지원한다.
- Task는 순차 실행한다.
- 커밋 없이 파일 내용 기반 Revision과 Task별 검증 결과를 연결한다.
- 산출물은 프로젝트 파일, SQLite, 간단한 Phase Report로 관리한다.

### 2.3 MVP에서 제외할 것

- 여러 Agent의 병렬 코드 수정
- 사용자가 직접 정의하는 임의 Workflow DAG
- 동적 Agent Registry UI
- 다중 AI Provider 동시 지원
- Task별 Git worktree
- 원격 Artifact Store
- 완전한 Event Sourcing
- Web Dashboard
- Git 초기화, Branch 생성·전환, staging, commit, push, PR 생성, merge 등 모든 Git 쓰기 자동화
- Production 배포
- 복잡한 비용 정산 엔진

---

## 3. 핵심 원칙

### 3.1 AI와 프로그램의 책임 분리

```text
AI
- Phase와 Task 계획 제안
- 자연어 요청 해석과 관련 코드의 변경 영향 판단
- Task 완료 기준, 관련 Domain Rule, Risk Tag 제안
- 코드 구현
- 코드 리뷰
- 테스트 실패 원인 분석
- 재계획안 제안

Orchestrator 프로그램
- 현재 상태와 승인 기록을 SQLite에 저장
- 실행 가능한 Task 선택
- Risk Tag에 정책을 적용하여 Workflow 선택 및 갱신
- 권한과 승인 확인
- Validation 명령 실행
- 재시도 횟수 제한
- 완료 조건 판정
- 코드 Revision·변경 내역과 보고서 관리
```

핵심 원칙은 다음과 같다.

> AI는 판단하고 제안하며 개발한다. Orchestrator는 실행을 통제하고 검증 결과와 상태를 SQLite에 기록한다.

SQLite는 실행 상태를 보관하고, 상태 전이와 완료 여부는 Orchestrator가 판정한다. AI가 직접 상태를 완료로 바꾸거나 승인 기록을 생성하지 않는다.

### 3.2 작은 설정 비용

중·소규모 프로젝트에서는 하네스를 적용하기 위한 준비 비용이 직접 개발하는 비용보다 커지면 안 된다.

- 필수 설정 파일은 `project.yaml` 하나로 제한한다.
- 여러 프로젝트에서 같은 하네스 설치를 사용하며, 프로젝트마다 하네스 소스나 실행 패키지를 복사하도록 요구하지 않는다.
- 대부분의 설정은 안전한 기본값을 제공한다.
- 사용자는 기획 문서와 테스트 명령만 제공해도 시작할 수 있어야 한다.
- 초기 설정 후에는 자연어로 작은 수정을 요청할 수 있어야 한다.
- 사용자에게 내부 Task 형식, Workflow 이름, DB 구조를 이해하도록 요구하지 않는다.
- 고급 설정은 선택 사항으로 둔다.

### 3.3 위험도에 따른 실행

모든 Task에 같은 수의 AI 호출과 검증을 강제하지 않는다.

```text
저위험 작업  → Fast
일반 기능    → Standard
고위험 작업  → Strict
```

AI가 요청과 관련 코드의 영향을 해석하고, Orchestrator의 Workflow Router가 프로젝트 규칙에 따라 최종 Workflow를 선택한다. 사용자는 기본적으로 Workflow를 직접 고르지 않는다. 구체적인 선택 규칙은 8.5절에 정의한다.

### 3.4 마지막 코드 기준 검증

각 Task는 선택된 Workflow에서 요구하는 검사를 최종 코드에 대해 통과해야 한다. Review 또는 Validation 이후 코드가 변경되면 이전 결과를 최종 코드의 검사 결과로 재사용하지 않는다.

- Review가 필요한 Task에서 Review 이후 코드 변경: 변경분 또는 전체 Review 필요
- Validation 이후 코드 변경: 해당 Workflow의 필수 Validation 재실행 필요
- Fast에서 정책상 생략된 Review는 정상적인 생략으로 기록하며 PASS로 표시하지 않는다.
- 승인 이후 Task 완료 기준, Domain Rule 또는 실행 정책 변경: 계획 revision과 기존 승인·검사 결과의 유효성 확인 필요

코드 Revision의 정의와 Workflow별 완료 조건은 8.4 및 8.6에서 정한다.

---

## 4. MVP 시스템 구조

```text
사용자
  ↓
CLI 또는 /development 명령
  ↓
Orchestrator Engine
  ├─ Project Loader
  ├─ Phase/Task Planner
  ├─ Task Scheduler
  ├─ Workflow Router
  ├─ Approval Controller
  ├─ Validation Runner
  ├─ Retry Controller
  ├─ Workspace Tracker
  └─ SQLite State Store
       ↓
Codex CLI Adapter
  ├─ Planner 역할
  ├─ Developer 역할
  └─ Reviewer 역할
```

### 4.1 Slash Command의 역할

`/development` 명령은 개발 로직을 직접 포함하지 않는 얇은 진입점으로 사용한다.

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

### 4.2 두 가지 요청 진입 방식

- Phase 개발: 기획서에서 전체 Phase와 현재 Phase의 Task를 계획하고 승인 후 실행한다.
- 자연어 수정: 초기 설정을 마친 프로젝트에서 요청을 작은 Task로 변환하고 Workflow를 자동 선택한다.

두 방식은 Task Scheduler, Workflow Router, Approval Controller, Validation Runner, Workspace Tracker와 SQLite State Store를 공유한다. 자연어 요청을 위한 별도 실행 엔진이나 전용 AI Agent는 추가하지 않는다.

Slash Command는 자연어의 의도를 먼저 구분한다. `/development Phase2 개발해보자`는 Phase 시작으로, `/development 상단의 폰트를 10pt로 줄여줘`는 작은 수정 요청으로 연결한다. 작은 수정은 Core CLI에서 `devh request "<요청>"`으로도 전달할 수 있다. 연결되지 않은 일반 채팅의 문장을 자동 수집하지 않는다. 명령 연결과 실행 예시는 14절에 정의한다.

### 4.3 하네스 설치와 프로젝트 초기화

기본 사용 구조는 컴퓨터의 사용자 환경에 하네스를 한 번 설치하고, 사용하는 프로젝트마다 초기화하는 방식이다. 설치된 Core CLI와 내장 역할·Skill을 여러 프로젝트가 공유하며, 프로젝트별 설정·계획·실행 상태는 구분한다.

| 단계 | 수행 단위 | 결과 |
|---|---|---|
| 하네스 설치 | 컴퓨터의 사용자 환경에서 한 번 | 프로젝트 폴더에서 공통 `devh` 명령 사용 |
| AI 도구 연결 | 사용하는 AI 도구의 사용자 환경에서 한 번 | `/development`가 Core CLI를 호출 |
| 프로젝트 초기화 | 사용할 프로젝트마다 한 번 | `.dev-harness/` 설정·계획 파일과 프로젝트별 로컬 SQLite 준비 |

하네스는 Python CLI 패키지로 배포할 수 있도록 구성하고, 구체적인 패키지명과 설치 명령은 배포 구현 시 확정한다. 사용자에게 각 대상 프로젝트의 앱 의존성으로 하네스를 추가하거나 하네스 개발 저장소 전체를 복사하도록 요구하지 않는다.

하네스 설치와 `/development` 연결은 별개의 작업이다. Slash Command는 AI 도구에 맞는 연결 지침을 제공하며, 연결하지 않아도 터미널에서 `devh`로 실행할 수 있다. 두 진입점 모두 AI Provider 실행 도구와 인증이 사용 가능한지 확인하고, 준비되지 않았다면 필요한 설정을 안내한다.

프로젝트 초기화는 프로젝트 루트에서 다음 명령으로 수행한다.

```text
devh init Draft/product-plan.md
```

`init`은 프로젝트별 기본 설정과 계획 파일을 준비하고 로컬 SQLite를 연결한다. 하네스 실행 프로그램은 공통 설치 위치에 유지한다. 이미 초기화된 프로젝트에서 다시 실행해도 기존 설정·계획·실행 상태를 자동으로 덮어쓰거나 초기화하지 않는다.

초기화 후 터미널에서는 `devh plan`을 실행하고, AI 도구를 연결했다면 해당 프로젝트를 열어 `/development plan`으로 같은 계획 작업을 요청할 수 있다. 계획 승인 후에는 `/development start P1`, 이후에는 `/development Phase2 개발해보자`처럼 사용한다. 승인과 실행 조건은 기존 규칙을 따른다.

### 4.4 현재 프로젝트 식별

- Core CLI는 현재 작업 폴더에서 상위 폴더 방향으로 설정을 탐색하고, 가장 가까운 `.dev-harness/project.yaml`이 있는 폴더를 프로젝트 루트로 식별한다. Git 없는 폴더도 지원하며 Git 루트나 최근 프로젝트를 대신 선택하지 않는다. `devh init`은 명령을 실행한 대상 폴더를 루트로 등록하고 Git 저장소를 생성하지 않는다.
- Slash Command는 AI 도구에서 현재 열린 프로젝트의 작업 경로를 Core CLI에 전달한다. 최근에 사용한 다른 프로젝트를 임의로 선택하지 않는다.
- 설정의 프로젝트 ID와 체크아웃 식별 정보를 이용해 해당 프로젝트의 SQLite를 연결한다. 여러 프로젝트가 같은 실행 프로그램을 사용해도 진행 상태와 승인 기록은 섞이지 않는다.
- 기획 문서와 검증 명령의 기준 경로는 식별된 프로젝트 루트로 통일한다.
- 설정이 없으면 해당 프로젝트의 초기화를 안내한다. AI 도구에 여러 프로젝트가 열려 있어 대상을 특정할 수 없으면 먼저 대상을 확인한다.

---

## 5. 프로젝트 파일 구조

아래는 하네스를 적용한 대상 프로젝트의 구조다. `.dev-harness/`에는 해당 프로젝트의 설정·계획·보고서를 두며, 하네스 실행 프로그램은 4.3절의 공통 설치 위치에서 사용한다.

```text
project-root/
├─ Draft/
│  └─ product-plan.md
├─ .dev-harness/
│  ├─ project.yaml
│  ├─ plan.md
│  ├─ work-items.yaml
│  ├─ domain-rules.md
│  └─ reports/
│     └─ phase-P1.md
├─ src/
├─ tests/
└─ README.md
```

실행 중 상태와 로그는 프로젝트가 OneDrive에 있을 수 있다는 점을 고려하여 로컬 애플리케이션 데이터에 저장한다.

```text
%LOCALAPPDATA%/AI-Development-Harness/{project-id}/
├─ state.db
├─ backups/
└─ logs/
```

### 5.1 저장 책임

| 저장 대상 | 저장 위치 | 기준 역할 |
|---|---|---|
| 소스 코드와 테스트 | 프로젝트 작업 폴더 | 실제 제품 산출물 |
| 프로젝트 설정 | `project.yaml` | 실행 설정의 정의 |
| Phase·Task 정의, 의존성, 완료 조건 | `work-items.yaml` | 작업 계획의 정의 |
| 공통·Task별 Domain Rule | `domain-rules.md` | 규칙의 정의와 원문 출처 |
| 사람이 읽는 계획 설명 | `plan.md` | 계획의 설명과 판단 근거 |
| Run·Phase·Task·Step 상태, 적용 Workflow, 재시도 횟수 | SQLite | 현재 실행 상태의 유일한 기준 |
| 승인 기록, Review·Validation 결과, 연결된 코드 Revision | SQLite | 실행과 완료 판정의 근거 |
| 실행에 사용한 설정·계획·Domain Rule 사본과 revision/hash | SQLite | 해당 Run의 입력 기준선 |
| 실행 로그 | LocalAppData | 문제 분석 |
| Task·Phase 결과 | SQLite와 파일 변경 내역에서 생성한 안내·Markdown Report | 사용자 확인 및 인수 |

MVP에서는 복잡한 Artifact Registry를 만들지 않는다. SQLite에는 실행 단계별 코드 Revision, 계획 revision, Review·Validation 결과와 Task 완료 상태를 연결해 기록하고, 결과 안내와 Phase Report는 이 기록과 파일 변경 내역에서 생성한다. 사용자가 파일을 Git으로 관리할 수 있으나 Git 사용과 커밋 여부는 완료 조건이 아니다.

### 5.2 SQLite 단일 실행 상태 원칙

- `work-items.yaml`에는 작업 정의만 저장한다. `status`, 실행 단계, 재시도 횟수, 승인 여부, 검증 통과 여부를 저장하거나 동기화하지 않는다.
- `plan.md`는 계획 설명이며, 진행 상황은 SQLite를 읽는 `devh status`로 확인한다.
- 보고서의 완료 수와 검증 결과는 생성 시점의 출력물이다. 보고서나 로그를 다시 읽어 현재 실행 상태 또는 승인을 복원하지 않는다.
- 실행을 시작하기 전에 해당 Run에 적용할 설정·작업 정의·Domain Rule의 사본과 revision/hash를 SQLite에 저장하고 승인 기록과 연결한다.
- 실행 중 계획 파일이 바뀌어도 진행 중인 Run의 입력을 자동 교체하지 않는다. 변경 내용을 검토하고 영향을 받는 작업과 승인 범위에 반영한다.
- AI의 완료 선언만으로 상태를 바꾸지 않는다. Orchestrator가 해당 Workflow의 완료 조건과 실제 결과를 확인한 후 SQLite를 갱신한다.

### 5.3 로컬 저장과 복구 범위

실행 중인 DB와 로그는 기존 방침대로 OneDrive 프로젝트 폴더 밖의 로컬 애플리케이션 데이터에 둔다. 같은 이름의 프로젝트나 별도 체크아웃은 하네스가 내부 식별자로 구분하며, 사용자에게 DB 경로 설정을 요구하지 않는다.

Task 완료와 정상 중단 시 SQLite의 백업 기능으로 `backups/`에 복구용 사본을 자동 생성한다. 백업은 현재 상태를 별도로 갱신하는 저장소가 아니며, 같은 장치의 백업만으로 장치 손실까지 복구할 수 있다고 보지 않는다.

MVP의 기본 재개 범위는 같은 컴퓨터의 같은 프로젝트 폴더다. 파일 복사나 Git 복제만으로 실행 이력과 승인이 전달되지는 않는다. DB가 없으면 기존 Run을 정확히 재개할 수 없음을 알리고, 현재 파일과 계획을 확인해 새로운 Run을 준비한다. 다른 컴퓨터로 실행 상태를 이전하는 전용 기능은 이후 확장으로 둔다.

`plan.md`, `work-items.yaml`, `domain-rules.md`는 Planner가 생성·갱신하는 계획 산출물이다. 사용자가 시작 전에 별도로 작성해야 하는 필수 설정 파일을 늘리지 않는다.

---

## 6. project.yaml

MVP의 필수 설정은 하나의 파일에 모은다.

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
  max_retries: 2

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
  git_write: deny
  production_deploy: deny

workspace:
  revision_strategy: content-hash
```

### 6.1 설정 검증

`project.yaml`은 Pydantic 또는 동등한 스키마 검증으로 읽는다.

- 필수 필드 누락 시 시작하지 않는다.
- 알 수 없는 필드는 기본적으로 오류로 처리한다.
- Validation 명령이 비어 있으면 사용자에게 알린다.
- API Key와 비밀값은 YAML에 저장하지 않는다.
- 환경변수 또는 운영체제 자격 증명 저장소를 사용한다.

설정이 커질 때만 `agents.yaml`, `workflows.yaml`, `permissions.yaml` 등으로 분리한다.

`validation.quick`은 Fast에서 사용할 검사다. Standard와 Strict는 `pre_review` 및 `post_review`를 사용한다. Standard의 후속 검사 범위를 좁히는 명시적 정책이 없다면 설정된 `post_review` 명령을 모두 실행한다. AI가 임의로 `required: true` 검사를 제외할 수 없다.

Strict의 Full Validation은 프로젝트가 전체 검증용으로 설정한 명령을 모두 실행한다는 의미다. E2E나 보안 검사도 필요한 프로젝트에서는 명령을 설정해야 하며, 설정되지 않은 검사를 실행한 것으로 보고하지 않는다. 선택된 Workflow에 필요한 검사 목록이 비어 있으면 실행 전에 설정 보완을 요청한다.

---

## 7. 개발 계획 구조

### 7.1 기본 사용자 구조

```text
기획
└─ Phase
   └─ Task
      └─ AI 개발 Workflow
```

Feature는 필요한 경우 `plan.md` 안에서 Task 그룹으로 사용한다.

```text
Phase 1 — 사용자 인증

[Feature: 회원가입]
- AUTH-001 회원가입 API
- AUTH-002 회원가입 화면

[Feature: 로그인]
- AUTH-003 로그인 API
- AUTH-004 로그인 화면
```

MVP의 실행 엔진은 Phase와 실행 가능한 Task를 우선 관리한다.

### 7.2 Work Item 공통 형식

Work Item은 Developer, Reviewer, Orchestrator가 공유하는 작업 계약이다. 실행 가능한 Task에는 구현 목표와 완료 기준을 함께 저장한다. 장기 확장성을 위해 내부 데이터에는 `type`과 `parent_id`를 둔다.

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

| 항목 | 역할과 MVP 규칙 |
|---|---|
| `acceptance_criteria` | 실행 가능한 Task에는 하나 이상 필요하다. Developer의 구현 목표와 Reviewer의 검토 기준으로 사용한다. |
| `requirement_refs` | 원본 요구사항의 ID 또는 문서 경로·절을 참조한다. MVP에서는 선택 사항이다. |
| `domain_rule_refs` | Task에 추가로 적용할 규칙 ID다. 해당 규칙이 없으면 빈 목록을 허용한다. |
| `risk_tags` | Planner가 제안하는 위험·작업 특성 분류다. 자연어 요청에서는 관련 코드를 확인한 Developer가 초안을 제안할 수 있다. 누락은 미분류로 처리하고 실행 전에 보완한다. 명시적인 빈 목록은 특별한 분류가 없다는 뜻이며 Fast의 근거가 되지 않는다. |
| `depends_on` | 선행 Task ID다. SQLite에서 모든 선행 Task가 완료됐음을 확인한 뒤 실행한다. |

- 중복 Work Item ID, 존재하지 않는 부모·의존성·규칙 참조, 순환 의존성은 계획 검증 오류로 처리한다.
- Phase는 목표와 종료 조건을 먼저 정하고, 현재 Phase의 실행 가능한 Task만 상세 완료 기준을 갖추면 된다.
- 완료 기준은 짧고 확인 가능한 문장으로 작성한다. 자연어 기준의 충족 여부는 테스트 결과와 필요한 Review로 확인하며, 문장이 존재한다는 이유만으로 완료 처리하지 않는다.
- 사용자는 기존 Phase Task 계획 승인 때 완료 기준, 관련 규칙, 위험 분류를 함께 확인한다. 독립적인 작은 자연어 요청의 범위 승인은 11.5를 따른다.
- 승인과 실행 상태는 5.1에 따라 SQLite에서 관리하므로 위 YAML 예시에는 `status`를 두지 않는다.

위 파일은 작업 정의만 표현한다. P1의 승인 여부와 AUTH-001의 준비·실행·완료 상태는 SQLite에서 조회한다. 정의 파일을 편집하는 것만으로 실행 상태나 승인 여부가 바뀌지는 않는다.

향후 Feature, Ticket, Bug, Refactor, Migration 타입을 추가해도 Orchestrator의 기본 실행 모델을 바꾸지 않는다.

Phase에 속하지 않는 자연어 수정 Task는 `parent_id`를 생략할 수 있다. 별도 Work Item 타입을 추가하지 않고 기존 `task` 타입으로 실행한다.

### 7.3 Rolling Wave Planning

처음에는 전체 Phase의 목표와 종료 조건만 계획한다. 현재 Phase만 Task 수준으로 상세화한다.

```text
프로젝트 시작
├─ P1: Task까지 상세 계획
├─ P2: 주요 기능 수준 계획
└─ P3 이후: 목표와 종료 조건 중심 계획
```

P1이 완료되면 실제 결과와 새로 발견한 위험을 반영해 P2를 상세화한다.

### 7.4 자연어 요청을 작은 Task로 만들기

초기 설정을 마친 프로젝트에서 사용자가 "상단의 폰트를 10pt로 줄여줘"처럼 요청하면, 하네스가 관련 코드를 읽고 요청 범위와 완료 조건을 정리해 Task를 생성한다.

- 사용자가 Task YAML을 직접 작성하지 않아도 된다. 하네스가 ID, 목표, 완료 조건, 관련 규칙, Risk Tag와 필요한 의존성을 작업 정의에 기록한다.
- 현재 Phase의 승인된 범위에 속하면 해당 Phase에 Task를 연결하고, 그 외의 독립적인 작은 수정은 Phase 없는 Task로 관리한다.
- 작은 수정을 위해 전체 Phase 계획을 다시 만들지 않는다. 여러 기능에 걸친 큰 요청은 작업 분해와 계획 확인으로 연결한다.
- 수정 대상이 여러 개여서 특정할 수 없으면 대상을 확인한다. 영향 범위만 불확실한 경우의 Workflow 선택은 8.5절을 따른다.
- 진행 중인 Task가 있으면 새 요청도 순차 처리한다. 기존 작업을 중단하거나 덮어쓰면서 동시에 코드를 수정하지 않는다.
- 진행 상태, 원래 요청과 연결된 승인 기록, 실행에 사용한 작업 정의 사본은 SQLite에 저장한다. 승인 규칙은 11.5절을 따른다.
- 독립 Task도 동일한 검증·재시도·완료 기록 규칙을 적용하고 완료 후 간단한 결과를 안내한다. 작업 폴더와 Git 경계는 13.1절을 따른다.

### 7.5 Domain Rule 저장과 참조

MVP의 기본 저장 위치는 `.dev-harness/domain-rules.md`다. 프로젝트에서 반복해서 지켜야 하는 업무·보안 규칙을 안정적인 ID로 관리한다. 해당 규칙이 없는 프로젝트에서는 빈 규칙 목록으로 시작할 수 있다.

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

- Planner가 원본 기획서에서 규칙과 출처를 추출하고, 기존 계획 승인에 포함한다. 별도의 규칙 승인 단계를 추가하지 않는다.
- `적용: 공통` 규칙은 모든 Task에 전달한다. `적용: Task 참조` 규칙은 `domain_rule_refs`로 선택한다. 공통 규칙은 Task의 참조 누락으로 적용이 사라지지 않는다.
- Context Builder가 `공통 규칙 + Task 참조 규칙`을 ID 기준으로 합쳐 Developer와 Reviewer에게 같은 내용을 전달한다.
- ID 중복, 존재하지 않는 참조, 원문과 추출 규칙의 충돌은 조용히 무시하지 않고 계획을 보완한다.
- 규칙의 의미가 바뀌면 계획 revision도 갱신한다. 이전 규칙으로 받은 승인·Review를 그대로 사용하지 않는다.
- 전체 기획서를 매번 전달하지 않는다. 규칙이 모호하거나 충돌할 때 관련 원문을 추가로 확인한다.

### 7.6 Risk Tag와 Workflow 선택 책임

```text
AI: Task의 위험과 작업 특성을 Risk Tag로 제안
→ 승인 확인: Phase Task는 계획 승인, 작은 자연어 요청은 11.5의 범위 승인
→ Orchestrator: project.yaml의 정책 적용
→ Fast / Standard / Strict 결정
```

Phase 계획에서는 Planner가 분류를 제안한다. 작은 자연어 요청에서는 Developer가 코드 수정 전에 관련 코드를 읽고 분류를 제안할 수 있다. 두 경우 모두 Orchestrator가 최종 Workflow를 결정한다.

Orchestrator는 다음 순서로 선택한다.

1. `risk_tags`에 `strict_when` 항목이 하나라도 있으면 Strict를 선택한다.
2. Strict 조건이 없고 `fast_when`의 저위험 조건을 충족하면 Fast를 선택한다.
3. 나머지는 `default_workflow`를 적용하며 기본값은 Standard다. Fast는 명시적인 저위험 조건이 있을 때만 선택한다.

`security`와 `small_isolated_fix`가 함께 있으면 Strict가 우선한다. 변경 줄 수가 적다는 이유로 인증·보안 관련 작업을 Fast로 낮추지 않는다. 분류가 모호하면 Fast를 선택하지 않고, 고위험 여부를 판단할 수 없으면 계획을 보완한다.

- 선택된 Workflow, 적용된 Tag와 정책 근거를 SQLite에 기록한다. Developer는 Workflow를 직접 확정하지 않는다.
- Planner의 위험 분류가 항상 정확하다고 가정하지 않는다. Developer와 Reviewer는 실행 중 발견한 새로운 위험을 보고하고, Orchestrator는 기존 Tag와 새 위험을 합쳐 다시 판정한다.
- Fast → Standard → Strict 강화는 자동 허용한다. 강화된 Workflow에서 요구하는 검토 수준과 검사 목록을 충족하기 전에는 완료하지 않는다.
- 자동 하향은 지원하지 않는다. 하향이 필요하면 위험 판단과 사유를 수정한 계획을 기존 사용자 승인 절차로 처리한다.
- Workflow 강화는 행동 권한 승인이 아니다. 새 DB Migration, 외부 전송 등 승인 대상 행동은 11장의 승인 정책을 별도로 적용한다.

---

## 8. 내장 Workflow

### 8.1 Fast

대상:

- 문서 수정
- 포맷 변경
- 특정 요소의 폰트 크기·색상·간격처럼 영향이 제한된 스타일 수정
- 단순 설정 변경
- 작은 테스트 추가
- 범위가 매우 작은 버그 수정

```text
Implement
→ Quick Validation
→ 최종 Revision 확인·Task 완료 기록
```

AI Reviewer는 기본적으로 호출하지 않는다. 위 작업 유형은 저위험 후보이며 실제 선택은 7.6의 위험 우선순위를 따른다. Quick Validation은 `validation.quick`에 설정한 검사를 실행한다.

Quick Validation은 변경 diff 확인과 프로젝트에 설정된 관련 빠른 검사를 수행한다. UI 변경은 사용할 수 있는 화면 확인 수단이 있으면 해당 영역을 확인한다. 수행하지 않은 검사나 화면 확인을 통과했다고 표시하지 않는다.

### 8.2 Standard

대상:

- 일반적인 기능 개발
- 기존 패턴 안의 API 또는 UI 변경
- 중간 수준의 리팩터링

```text
Implement
→ Pre-review Validation
→ Light AI Review
→ 필요한 Targeted/Full Validation
→ 최종 Revision 확인·Task 완료 기록
```

Reviewer는 현재 Task 요구사항과 관련 diff만 확인한다.

### 8.3 Strict

대상:

- 개인정보 또는 민감정보 처리
- 인증과 권한
- DB Migration
- 외부 API 도입
- 핵심 Domain Rule
- 보안 영향이 있는 변경
- Architecture 변경

Phase 계획에서 이미 승인된 Task라면 매번 별도의 Task 계획 승인을 받지 않는다. 다만 실행 중 새로운 고위험 결정이 발견되면 즉시 승인 대기로 전환한다.

#### 기본 순서

```text
Implement
→ Pre-review Validation
→ Strict AI Review
→ Post-review Full Validation
→ 최종 Revision 확인·Task 완료 기록
```

#### 상세 순서

```text
Implement
       ↓
Pre-review Validation
- format
- lint
- typecheck
- unit
- 필요한 경우 변경 영역 integration
       ↓ 실패
Developer 자동 수정
       ↓
Strict AI Review
       ↓ 변경 요청
Developer 수정
→ Pre-review Validation
→ AI Re-review
       ↓ 승인
Post-review Full Validation
- 전체 integration
- E2E
- security
- 프로젝트별 특수 검증
       ↓ 실패
Developer 수정
→ Pre-review Validation
→ 수정 diff에 대한 Delta Review
→ Post-review Validation 재실행
       ↓
최종 Revision 확인·Task 완료 기록
```

### 8.4 마지막 코드 기준선 규칙

- Pre-review Validation의 필수 검사가 실패하면 Reviewer를 호출하지 않는다.
- 검사 후 코드가 변경되면 해당 Workflow에서 필요한 Validation과 Review를 새 Revision에 대해 다시 수행한다.
- Review가 필요한 Task는 수정 범위에 따라 Delta Review 또는 전체 Review를 수행한다. Fast에 생략된 Review를 새로 강제하지는 않으며, 위험도 상승 시에는 강화된 Workflow를 따른다.
- Full Validation이 필요한 Task는 수정 후 Full Validation을 다시 실행한다.
- 검사 중 파일이 변경된 결과는 그대로 PASS로 확정하지 않는다. 자동 포맷 수정 등은 코드 수정으로 취급하고 변경이 끝난 Revision에서 다시 검사한다.

### 8.5 Workflow 자동 선택

Workflow 선택은 요청의 길이나 수정할 코드의 줄 수만으로 결정하지 않는다. AI가 요청을 읽고 임시로 분류한 뒤, 관련 코드를 읽어 실제 변경 영향과 위험 신호를 확인한다. 이 단계에서는 소스 코드를 수정하지 않는다.

```text
요청 읽기와 임시 분류
→ 관련 코드 확인
→ 변경 종류·영향 범위·위험 신호를 구조화된 결과로 반환
→ Workflow Router가 프로젝트 규칙과 대조
→ Workflow 및 필요한 승인 확인
→ 구현 시작
```

자연어 수정에서는 Developer 역할의 짧은 사전 판단으로 이 과정을 수행한다. 별도 분류 Agent나 전체 Phase Planner, Reviewer를 매번 호출하지 않는다. Phase 계획에서 생성된 Task도 구현 전 관련 코드와 위험을 확인해 같은 선택 규칙을 적용한다.

7.6의 Risk Tag 정책에 코드 확인 결과를 반영한다. 영향 범위를 확신할 수 없으면 임시 저위험 분류를 그대로 사용하지 않으며, 다음 순서로 선택한다.

1. 인증·권한·중요 데이터 처리 등 고위험 신호를 해당 Risk Tag로 반영하고, `workflow_routing.strict_when` 조건에 해당하면 Strict를 선택한다.
2. 고위험 신호는 없지만 영향 범위를 확신하기 어렵다면 Standard를 선택한다. 불확실한 작업을 Fast로 처리하지 않는다.
3. 특정 요소의 스타일이나 문서처럼 변경 영향이 명확히 제한되고 `fast_when` 조건을 충족하는 작업은 Fast를 선택한다.
4. 그 외 일반 기능 변경은 기본 Workflow인 Standard를 적용한다.

| 요청 예시 | 코드에서 확인한 영향 | Workflow 예시 |
|---|---|---|
| 상단의 폰트를 10pt로 줄여줘 | 특정 제목의 스타일만 변경 | Fast |
| 앱 전체 글자 크기를 화면 크기에 맞춰 바꿔줘 | 공통 스타일과 여러 화면에 영향 | Standard |
| 관리자 페이지 로그인 검사를 없애줘 | 인증과 접근 권한에 영향 | Strict |

실제 Workflow는 프로젝트 규칙과 코드 확인 결과에 따라 달라질 수 있다. Strict 선택은 해당 요청에 대한 실행 허가를 뜻하지 않으며, 보안 영향이 있는 요청은 승인 정책에 따라 별도로 판단한다.

선택한 Workflow와 판단 근거는 SQLite에 기록한다. 구현 중 예상보다 넓은 변경이나 새 위험이 발견되면 범위를 다시 검토하고 필요 시 Workflow를 상향한다. 상향된 Workflow에서 요구하는 검토·검증을 통과해야 완료할 수 있다. Workflow 상향만으로 사용자에게 재승인을 요구하지는 않으며, 요청 범위 변경이나 새 승인 대상 행동이 있을 때 확인한다.

### 8.6 Revision과 Task 완료 조건

Revision은 검사 대상 코드의 내용을 식별하는 값이다. 하네스는 Git 커밋을 생성하지 않으며 Git 없이도 동일한 검증·완료 판정을 수행한다.

- 코드 Revision은 검사 대상 파일의 정규화된 상대 경로와 내용 hash를 정렬한 manifest로 계산한다. 새 소스 파일, 삭제, 테스트, 실행 설정, 의존성 잠금 파일도 포함한다.
- 실제 작업 폴더의 내용을 직접 읽어 계산한다. Git index·tree 생성이나 staging을 사용하지 않으며 `.git` 메타데이터는 코드 Revision에서 제외한다. 변경 내역은 Run·Task 시작 기준선과 현재 파일을 비교한다. hash만으로 이전 내용을 복원할 수 없으므로 diff에 필요한 대상 파일 기준선은 보호된 로컬 실행 저장소에 보존하고 비밀값·불필요한 데이터는 제외한다.
- 로그·캐시·검증 보고서 등 생성물은 제외 범위를 명시한다. 검사 중 로그가 추가됐다는 이유로 코드 Revision이 바뀌게 만들지 않는다.
- Review·Validation 시작과 종료, 완료 기록 직전에 Revision을 확인한다. 하네스는 검사 중 다른 코드 수정 단계를 동시에 실행하지 않는다.
- 결과에는 코드 Revision뿐 아니라 승인된 `plan_revision`과 적용 Workflow를 연결한다. 코드가 같아도 완료 기준·규칙·검증 정책이 달라지면 이전 결과를 그대로 재사용하지 않는다.

다음 값은 완료 판정을 이해하기 위한 요약이다.

```text
current_revision   = R2  # 현재 코드
reviewed_revision  = R1  # 마지막으로 유효한 Review가 확인한 코드
validated_revision = R1  # 필수 Validation을 모두 통과한 코드

Strict Task: R2에 대한 Review와 Validation이 없으므로 완료 불가
```

실제 저장은 검사별로 한다. 예를 들어 `pre_review.unit`, `post_review.integration` 각각의 Revision, 실행 결과와 종료 여부를 기록한다. `validated_revision`은 필요한 검사가 모두 통과했을 때만 같은 Revision으로 판정하며, 마지막 명령 하나의 성공으로 갱신하지 않는다.

| Workflow | Task 완료 전에 최종 Revision에서 충족할 조건 |
|---|---|
| Fast | Quick Validation의 필수 검사 통과. 기본 Review는 `SKIPPED_BY_POLICY`로 기록한다. |
| Standard | Pre-review Validation 통과, Light/유효한 Delta Review PASS, 정책이 요구하는 후속 Validation 통과 |
| Strict | Pre-review Validation 통과, Strict/유효한 Delta Review PASS, Post-review Full Validation 통과 |

모든 Workflow에 다음 조건도 적용한다.

- 승인된 Task 계약이 유효하고, 선행 Task가 완료되어 있어야 한다.
- 필요한 Review가 있다면 미해결 필수 수정 요청이 없어야 한다.
- 필요한 검사 목록은 Orchestrator가 정책에 따라 확정하고 기록한다. 생략·미실행·중단된 필수 검사를 PASS로 간주하지 않는다.
- 조건을 충족하고 최종 Revision이 검사 결과와 일치하면 13.4절에 따라 SQLite에 Task `COMPLETED`를 기록한다. 커밋 여부는 완료 조건이 아니며 Phase의 사용자 인수는 별도로 유지한다.

Strict Task에서 R1 검토 후 Developer가 R2로 수정한 경우의 흐름은 다음과 같다.

```text
R1 Review / Validation 결과는 이력으로 보존하되 R2의 완료 근거로 사용하지 않음
→ R2 Pre-review Validation
→ R2 Delta Review 또는 전체 Review
→ R2 Post-review Full Validation
→ 최종 Revision과 필수 결과 확인
→ 최종 파일 Revision과 검사 결과 일치 확인
→ SQLite에 COMPLETED 기록
```

이 규칙은 선택된 Workflow에서 요구하는 Review·Validation에 적용한다. Fast에 AI Review나 Full Validation을 추가로 강제하지 않는다.

---

## 9. AI Review 토큰 절약 정책

Reviewer 호출은 품질을 높이지만 모든 Task에서 전체 프로젝트를 읽게 하면 비용과 시간이 커진다.

### 9.1 Reviewer 입력 제한

Reviewer에게 다음만 제공한다.

- Work Item 설명
- Acceptance Criteria
- 공통 Domain Rule과 Task가 참조하는 Domain Rule
- 구현 계획 요약
- 현재 Task 기준선 대비 파일 diff (Git 유무와 무관하게 제공)
- Pre-review Validation 결과 요약
- diff가 의존하는 최소 코드
- 검토 대상 코드 Revision과 계획 revision
- Delta Review라면 이전 검토 기준선, 수정 diff, 미해결 수정 요청

기본적으로 다음은 제외한다.

- 전체 기획서
- 전체 대화 기록
- 관련 없는 소스 코드
- 전체 테스트 로그
- Developer의 긴 작업 과정
- 이전 Task의 모든 산출물

### 9.2 Review 호출 기준

| 변경 유형 | Review 정책 |
|---|---|
| 문서·포맷·단순 설정 | 생략 가능 |
| 테스트만 추가 | 선택적 Review |
| 일반 기능 | Light Review 1회 |
| 고위험 기능 | Strict Review |
| Review 후 작은 수정 | Delta Review |

### 9.3 Reviewer 출력

긴 설명 대신 구조화된 결과를 요구한다.

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

Orchestrator는 Review 호출 시점의 Task ID, 코드 Revision, 계획 revision, Workflow를 결과에 연결해 저장한다. AI가 출력한 Revision 문자열만 신뢰하여 연결하지 않는다.

Delta Review는 이전 Review 기록과 대상 Revision을 연결하고, 기존 필수 수정 요청의 해결 여부까지 확인한다. 이전 기록이 없거나 수정 범위가 크게 달라졌다면 전체 Review를 수행한다. 최신 수정 diff가 PASS라는 이유만으로 과거의 미해결 요청을 삭제하지 않는다.

### 9.4 추가 비용 제한

- Task당 Review 호출 횟수를 제한한다.
- 재검토는 이전 검토가 유효하고 범위가 제한적일 때 수정 diff 중심으로 수행한다. 기준선이 없거나 영향이 커진 경우에는 전체 Review를 수행한다.
- Task diff가 너무 크면 Review 전에 Task를 다시 나눈다.
- 일반 Review에는 비용 효율적인 모델을 사용할 수 있도록 장기 확장 지점을 둔다.

---

## 10. Agent와 Skill

### 10.1 MVP Agent 역할

```text
Planner
- 전체 Phase 계획
- 현재 Phase Task 분해
- 완료 기준, 원문·Domain Rule 참조, Risk Tag 제안
- 필요한 경우 재계획

Developer
- 자연어 수정 요청의 관련 코드 확인과 변경 영향 분류
- Task 범위 내 구현
- 테스트 추가
- Validation 또는 Review 실패 수정
- 실행 중 발견한 새로운 위험과 승인 필요 행동 보고

Reviewer
- diff 기반 독립 검토
- 요구사항, 설계, 보안, Domain Rule 확인
- 미해결 수정 요청 확인 및 새 위험 보고
```

### 10.2 Tester 처리

Tester는 별도 AI Agent로 만들지 않는다.

```text
Validation Runner
  실제 명령 실행
       ↓ 실패
오류 로그를 Developer에게 전달
       ↓
Developer가 수정
```

AI는 실패 원인과 수정 방법을 판단하지만 테스트의 성공 여부는 프로세스 종료 코드와 설정된 기준으로 판정한다.

### 10.3 Skill 관계

Skill은 Agent 자체가 아니라 Agent가 사용하는 작업 매뉴얼이다.

```text
Planner Agent
└─ plan-project / plan-phase Skill

Developer Agent
└─ implement-task / fix-failure Skill

Reviewer Agent
└─ review-diff Skill
```

MVP에서는 동적 Agent Registry를 구현하지 않고 내장 역할과 Skill 구성을 사용한다. 설정 형식은 향후 역할 추가가 가능하도록 확장성을 남긴다.

---

## 11. 승인 정책

사용자는 작업마다 승인하지 않고 결과를 크게 바꾸거나 되돌리기 어려운 결정만 승인한다.

### 11.1 기본 승인 지점

1. 전체 Phase 계획
2. 현재 Phase Task 계획
3. 실행 중 새로 발견된 고위험 결정
4. Phase 완료 결과

위 계획 승인 지점은 Phase 개발 흐름에 적용한다. 독립적인 작은 자연어 수정의 승인 방식은 11.5절을 따른다.

Git 쓰기는 이 승인 흐름의 대상이 아니다. 하네스는 Branch·commit·push·PR·merge 등을 수행하지 않으며, 사용자가 별도로 수동 실행한다. `git_write: deny`는 MVP의 고정 경계로 설정 변경이나 행동 승인으로 완화하지 않는다.

### 11.2 자동 허용 예시

- 승인된 범위 안의 파일 수정
- 테스트 추가 및 실행
- lint와 format 수정
- 승인된 설계 안의 작은 리팩터링

### 11.3 승인 필요 예시

- 새 Dependency 설치
- Architecture 변경
- DB Migration
- 외부 API 사용
- 개인정보 외부 전송
- 테스트 삭제 또는 기준 완화
- Phase 범위 변경
- Production 배포

### 11.4 승인 무효화

승인 요청과 승인·거절 결과는 SQLite에만 기록하며, 승인 대상 작업과 계획 revision 또는 hash에 연결한다. 승인받은 내용이 실질적으로 변경되면 영향을 받는 범위의 기존 승인을 다시 사용하지 않는다. YAML이나 Markdown에 적힌 승인 표현을 실제 승인 기록으로 취급하지 않는다.

승인은 `plan_revision`과 연결한다. MVP에서는 승인 대상 Phase 또는 독립 Task에 적용되는 계획·Task 정의, 공통·참조 Domain Rule, 실행 설정을 묶어 revision 또는 hash로 식별한다. 실행 상태·로그·보고서는 계획 revision 계산에서 제외하며, 관련 없는 독립 Task 추가만으로 기존 승인을 무효화하지 않는다.

Task 완료 기준, 적용 규칙, 검증 명령·필수 여부, 위험 판단 등 승인받은 내용이 변경되면 기존 승인을 다시 사용하지 않는다. 변경된 계획은 기존 승인 절차로 확인하고, 이전 Review·Validation은 새 계획의 완료 근거로 사용하지 않는다. MVP에서는 세밀한 결과 재사용보다 보수적인 재검증을 우선한다.

실행 중 새 위험 발견으로 검토 수준만 자동 강화하는 것은 7.6에 따른다. 실제 작업 범위나 승인 대상 행동이 추가되면 계획 또는 행동 승인을 별도로 확인한다.

### 11.5 자연어 수정 요청의 승인

초기 설정을 마친 프로젝트에서 사용자가 직접 요청한 명확하고 작은 수정은 그 요청을 작업 범위에 대한 승인 근거로 삼을 수 있다. Orchestrator가 원래 사용자 요청과 해석한 범위, Task revision을 SQLite에 기록하고 권한 정책을 확인한 뒤 실행한다. 별도의 전체 Phase 계획 승인이나 같은 요청에 대한 반복 확인은 요구하지 않는다.

- "상단의 폰트를 10pt로 줄여줘"처럼 대상과 변경 내용이 명확하고 자동 허용 정책에 해당하는 수정은 바로 실행한다.
- 수정 대상이나 원하는 결과가 모호하면 필요한 내용을 확인한다.
- Phase 범위의 실질적 변경, 외부 전송, 신규 의존성 등 기존 정책의 `ask` 대상은 승인을 확인하고, `deny` 대상은 실행하지 않는다.
- AI가 추정한 동의만으로 승인 기록을 만들지 않는다. 사용자가 요청하지 않은 범위 확장에 기존 요청을 승인 근거로 재사용하지 않는다.
- Fast·Standard·Strict는 검증 강도를 결정하며, 행동 권한은 승인 정책으로 별도 판단한다.

---

## 12. Retry와 실패 처리

```yaml
development:
  max_retries: 2
```

### 12.1 자동 재시도

- lint 또는 typecheck 실패
- Unit Test 실패
- 명확한 Reviewer 수정 요청
- 변경 범위 안에서 해결 가능한 Integration Test 실패

### 12.2 자동 재시도 중단

- 동일 원인 반복
- 최대 재시도 횟수 초과
- Architecture 변경 필요
- 기획 또는 Domain Rule이 모호함
- 외부 서비스 장애
- 사용자 권한 또는 Secret 필요
- 승인 대상 행동 필요

중단 시 다음 상태 중 하나로 전환한다.

```text
WAITING_APPROVAL
BLOCKED
REPLAN_REQUIRED
FAILED
```

SQLite에 상태와 마지막 성공 Step, 진행 중 Step, 코드·계획 Revision을 기록한다. 재개할 때는 다음 정합성 검사와 중단 복구 규칙을 먼저 적용한다.

### 12.3 Resume 정합성 검사

`devh resume`는 저장된 Run과 실제 프로젝트 폴더가 같은 작업 상태를 가리키는지 확인한 뒤 실행한다.

| 비교 대상 | 확인 내용 |
|---|---|
| Project와 작업 루트 | Project ID 및 실제 프로젝트 경로. 같은 ID의 다른 복제본을 잘못 재개하지 않는다. |
| 선택적 Git 정보 | Git이 있으면 Branch·HEAD·상태를 읽기 전용 참고 정보로 확인한다. Git이 없어도 실행·재개할 수 있다. |
| 코드 Revision과 작업 폴더 | 새 파일·수정·삭제를 포함한 실제 파일 내용이 저장한 체크포인트의 예상 상태와 일치하는지 확인한다. |
| 계획 revision | Task 완료 기준, Domain Rule, 실행 설정이 승인된 계획과 같은지 확인한다. |
| 현재 Task와 Step | Task가 해당 Run·계획에 속하며, 실행 단계·승인·선행 의존성이 유효한지 확인한다. |

하네스는 결과물을 커밋하지 않으므로 미커밋 변경은 정상이다. 파일 목록이나 Git의 `dirty` 여부만 비교하지 않고 저장한 코드 내용과 대조한다. 사용자가 수동 commit·staging·Branch 전환을 했더라도 프로젝트 식별, 코드·계획 Revision과 실행 입력이 같다면 Git 메타데이터 변화만으로 승인·검증을 무효화하거나 재개를 막지 않는다.

```text
devh resume
→ SQLite Run 조회
→ 실제 계획·작업 폴더 상태 조회 (Git 정보는 선택적 참고)
→ 중단된 Step 및 Task 완료 기록 확인
→ 저장된 예상 상태와 일치: 필요한 단계부터 재개
→ 설명되지 않는 불일치: 실행 중단 후 차이와 복구 안내 표시
```

| 상황 | 처리 |
|---|---|
| 체크포인트와 코드·계획이 같음 | 완료가 확인된 Step은 재사용하고 다음 단계로 진행 |
| 예상하지 못한 코드 또는 실행 입력 변경 | `BLOCKED`, 사유 `STATE_MISMATCH`. 저장된 값·현재 값과 변경 파일을 표시 |
| 완료 기준·규칙 등 계획 내용 변경 | `REPLAN_REQUIRED`. 계획을 갱신하고 기존 승인 절차 적용 |
| 검증은 성공했으나 Task 완료 기록이 없음 | 13.4에 따라 저장된 검사 결과·Revision·승인을 확인하고 완료 기록 복구 |

불일치 시 자동으로 파일을 덮어쓰거나 Git을 되돌리지 않는다. 코드만 바뀌었다면 영향과 필요한 재검증을 확인하고, 범위·완료 기준 등 계획이 달라진 경우 재계획·승인을 적용한다. 사용자가 변경을 유지하려면 계획·작업 상태를 확인한 뒤 필요한 검사를 새로 수행한다.

### 12.4 실행 중 종료된 Step

- Review나 Validation 실행 중 종료되어 결과 확정 기록이 없다면 성공으로 간주하지 않는다. 현재 Revision을 확인하고 해당 검사를 다시 실행한다.
- Developer 실행 중 종료됐다면 남아 있는 파일을 보존한다. 마지막 체크포인트와 다른 부분을 확인하기 전 자동으로 구현을 반복하지 않는다. 예상하지 못한 변경은 `STATE_MISMATCH`로 안내한다.
- 재개는 Retry 횟수나 승인 기록을 초기화하지 않는다. 이미 소비한 재시도 횟수를 유지한다.
- 중복 Run이 같은 작업 폴더를 동시에 수정하지 못하도록 실행 소유권을 확인한다. 중단된 기존 프로세스가 살아 있다면 새 실행을 시작하지 않는다.

사용자의 수동 변경은 Task 범위에 속하는지 확인한다. 관련 없는 변경을 임의로 되돌리거나 하네스의 작업 결과로 귀속하지 않는다. AI 세션의 내부 작업 과정을 그대로 복원할 필요는 없으며, 저장된 Task·현재 코드·마지막 실행 결과로 필요한 단계부터 진행한다.

---

## 13. 산출물 관리와 Git 경계

### 13.1 작업 폴더와 Git 경계

하네스의 완료 범위는 검증된 개발 산출물과 사용자 인수까지다. Git 사용, Branch 관리, staging, commit, push, PR, merge는 사용자가 수동으로 결정·수행한다.

- 하네스는 Git 저장소를 초기화하거나 Git 쓰기 명령을 실행하지 않는다. 이 경계는 Orchestrator와 작업 에이전트 모두에 적용한다.
- Git이 있다면 상태·diff·HEAD 등 읽기 전용 정보만 보조적으로 활용한다. Git이 없어도 초기화·개발·검증·결과 인수·재개가 가능해야 한다.
- Phase Task와 독립 자연어 Task는 식별된 프로젝트 작업 폴더에서 순차 실행한다. 독립 요청을 위해 Branch나 형식적인 Phase를 만들지 않는다.
- Run·Task 시작 시 파일 기준선을 기록하고 사용자 기존 변경을 보존한다. Task 변경 내역은 해당 기준선 대비 계산하며 기존 사용자 변경과 구분한다.
- Git 쓰기 정책을 승인 가능한 선택지로 제시하지 않는다. 필요한 Git 작업은 사용자가 하네스 밖에서 직접 수행한다.

### 13.2 Task 완료 기록

Task 완료 시 다음을 SQLite에 저장한다. 실제 제품 산출물은 작업 폴더의 파일이며, Task 완료 상태와 검증 근거는 SQLite가 관리한다.

- Task ID와 상태
- 적용 Workflow, Risk Tag와 선택 근거
- 승인된 계획 revision
- 시작 기준선과 최종 코드 Revision
- 변경 파일 목록
- Review 결과 요약과 검사한 Revision, Delta Review의 이전 기록 연결
- Validation 명령별 결과와 검사한 Revision, 정책상 생략한 검사와 사유
- 재시도 횟수
- 사용된 승인 ID
- 알려진 제한사항

### 13.3 Phase Report

Phase Report는 SQLite의 실행 기록과 파일 변경 내역을 읽어 생성한다. 보고서를 편집하거나 삭제해도 SQLite의 실행 상태와 승인 기록은 바뀌지 않는다.

```markdown
# Phase P1 완료 보고서

## 결과

- 완료 Task: 8/8
- 자동 재시도: 2회
- 사용자 승인: 1건

## 검증

- Unit Test: 통과
- Integration Test: 통과
- Type Check: 통과
- Lint: 통과

## 주요 결정

- 로컬 OCR 사용
- 원본 문서 분석 후 삭제

## 알려진 제한사항

- 일부 오래된 문서 양식 미검증

## 산출물

- 변경 파일: src/ocr/, tests/unit/ocr/, tests/integration/ocr/
- 결과물 위치: 현재 프로젝트 작업 폴더
- 상세 변경 목록과 검증 근거: 해당 Run의 기록
```

### 13.4 Task 완료 기록과 중단 복구

파일 변경과 SQLite 갱신은 별도 작업이다. 검증 후 완료 기록 전에 종료될 수 있으므로 저장된 증거와 실제 파일을 대조한다.

```text
Workflow별 최종 검증 조건 충족
→ 코드·계획 Revision과 승인 유효성 재확인
→ SQLite 트랜잭션으로 최종 Revision·검사 근거·COMPLETED 기록
→ 다음 Task
```

- 완료 기록 직전에 코드가 바뀌었으면 완료 절차를 멈추고 새 Revision에서 필요한 검사를 수행한다.
- 완료 기록 전에 종료됐다면 현재 파일·계획·실행 입력이 저장된 검사 대상과 일치하는지 확인한다. 필수 검사와 승인이 모두 유효할 때만 완료 기록을 확정하며 구현을 중복 실행하지 않는다.
- 성공 결과가 DB에 확정되지 않은 검사는 성공으로 추정하지 않고 다시 실행한다. 로그의 성공 문구만으로 완료를 복원하지 않는다.
- 완료 기록이 이미 있다면 같은 기록을 사용한다. 이후 코드가 바뀌었다면 과거 완료 사실은 이력으로 보존하되 현재 코드의 통과 근거로 재사용하지 않는다.
- 예상하지 못한 파일 변경은 `STATE_MISMATCH`로 중단한다. 사용자 변경을 덮어쓰거나 Git을 되돌리지 않는다.
- Report는 SQLite에서 다시 생성할 수 있는 출력물이다. 보고서 생성 실패가 코드 재구현이나 Git 동작으로 이어지지 않으며, 사용자 인수 전에는 보고서 생성을 재시도한다.

복구에 필요한 현재 작업 기록만 SQLite에 저장하며 완전한 Event Sourcing은 도입하지 않는다. Git 쓰기와 Git·DB 간 완료 동기화는 구현하지 않는다.

---

## 14. 사용자 명령 초안

MVP에서는 다음 명령만 우선 지원한다.

```text
devh init <planning-document>
devh plan
devh start <phase-id>
devh run
devh request "<자연어 수정 요청>"
devh status
devh approve <approval-id>
devh reject <approval-id>
devh resume [run-id]
devh close <phase-id>
devh report <phase-id>
```

Slash Command는 같은 Core CLI를 호출한다.

```text
/development init Draft/product-plan.md
/development plan
/development start P1
/development status
/development approve APR-001
/development resume
/development close P1
/development Phase2 개발해보자
/development 상단의 폰트를 10pt로 줄여줘
```

Slash Command는 기존 명령을 먼저 식별한다. 자연어로 입력된 경우에는 의도를 구분하여 해당 Core CLI 명령으로 전달하며, 모든 문장을 새로운 수정 Task로 만들지 않는다.

| 사용자 입력 | 내부 연결 |
|---|---|
| `/development Phase2 개발해보자` | 계획에서 대상 Phase를 확인한 뒤 `devh start P2` |
| `/development 다음 Phase 시작해줘` | 계획과 SQLite 상태에서 다음 Phase를 확인한 뒤 `devh start <phase-id>` |
| `/development 상단의 폰트를 10pt로 줄여줘` | `devh request "상단의 폰트를 10pt로 줄여줘"` |
| `/development 어디까지 됐어?` | `devh status` |

명령과 구분이 필요한 수정 요청에는 `/development request "<요청>"`을 사용할 수 있다. Phase 이름은 실제 계획의 ID와 대조하며, 대상을 특정할 수 없으면 확인한다. 해석 이후의 실행 가능 여부와 승인 판단은 Core Orchestrator가 담당한다. 일반 채팅과 연결하는 별도 UI는 MVP에서 요구하지 않는다.

### 14.1 자연어 폰트 수정 실행 예시

초기 설정을 마친 프로젝트에서 사용자가 다음과 같이 요청한다. 이 예시에서는 상단 제목을 하나로 식별할 수 있고 다른 Task가 실행 중이지 않다고 가정한다.

```text
/development 상단의 폰트를 10pt로 줄여줘
```

```text
사용자 요청 수신
   ↓
Developer가 관련 화면과 스타일을 읽기만 하며 확인
   ↓
특정 상단 제목의 폰트 크기만 변경하는 Task 생성
- 완료 조건: 해당 제목의 font-size가 10pt로 적용됨
- 범위: 해당 제목의 스타일
- Risk Tag: small_isolated_fix (해당 제목의 스타일만 변경)
   ↓
Orchestrator가 Fast 선택 및 자동 허용 정책 확인
   ↓
요청에 근거한 승인과 실행 입력·상태를 SQLite에 저장
   ↓
Developer가 해당 스타일 수정
   ↓
Quick Validation
- 실제 변경 diff와 요청 범위 확인
- 관련된 빠른 검사 실행
- 화면 확인 수단이 있는 경우 해당 영역 확인
   ↓
필수 검사와 최종 Revision 확인 후 SQLite에 Task 완료 기록 (13.4)
   ↓
변경 결과와 실제 수행한 검사를 사용자에게 안내
```

전체 Phase 계획과 별도 AI Reviewer 호출은 생략한다. 사용자는 Fast라는 이름이나 내부 Task 형식을 알 필요가 없다. 진행 안내는 다음처럼 표현할 수 있다.

```text
상단 제목의 글자 크기를 10pt로 변경하겠습니다.
간단한 스타일 수정으로 진행합니다.
```

완료 안내에는 변경 내용, 실제 검사 결과와 산출물 위치를 제공한다. 화면을 직접 확인하지 않았다면 그 사실을 함께 표시한다.

코드를 확인한 결과 공통 글꼴 설정을 바꿔야 해서 여러 화면에 영향을 준다면 수정 범위를 다시 검토하거나 Standard로 상향한다. 상단 제목을 여러 개 발견해 대상을 특정할 수 없다면 먼저 확인한다. 예상보다 큰 범위 변경이나 승인 대상 행동이 필요하면 해당 행동 전에 중단한다.

### 14.2 Phase 1 이후 Phase 2 시작 예시

전체 계획에 P1과 P2가 정의되어 있고 사용자가 다음과 같이 입력했다고 가정한다.

```text
/development Phase2 개발해보자
```

명시적인 명령인 `/development start P2` 또는 터미널의 `devh start P2`도 같은 동작을 수행한다.

```text
자연어를 P2 시작 요청으로 해석
   ↓
Orchestrator가 SQLite에서 P1 완료·인수 상태와 P2 승인 기록 확인
   ↓
P2 진입 조건 확인
   ↓
P2의 상세 Task 계획이 없다면 P1 결과를 반영하여 생성
   ↓
현재 P2 계획에 유효한 승인이 없으면 사용자에게 계획을 제시하고 대기
   ↓
사용자 승인 후 의존성이 충족된 Task부터 순차 실행
```

- P1의 필수 검증이나 인수가 남아 있으면 남은 사항을 안내하고 P2를 시작하지 않는다.
- P2에 승인된 상세 계획이 있고 진입 조건이 충족되었다면 계획 승인을 반복하지 않고 개발을 시작한다.
- P2가 아직 목표 수준으로만 계획되어 있다면 Task 분해와 계획 승인을 먼저 수행한다. "Phase2 개발해보자"라는 요청을 아직 제시하지 않은 상세 계획 전체에 대한 승인으로 간주하지 않는다.
- 이미 P2의 Run이 실행 중이면 현재 상태를 안내하고 중복 실행하지 않는다. 중단된 Run이 있으면 이어서 실행하는 경로로 연결하되 기존 승인 대기와 실패 상태를 자동 해제하지 않는다.
- 각 Task의 Workflow는 8.5절에 따라 자동 선택한다. 사용자가 Phase 시작 명령에서 Fast·Standard·Strict를 지정할 필요는 없다.

MVP의 기본 입력은 `/development`를 붙인 명령 또는 Core CLI다. 일반 채팅에서 "Phase2 개발해보자"만 입력했을 때의 자동 호출은 해당 채팅 환경에 하네스 호출 연결이 구성된 경우에만 가능하다.

---

## 15. 부동산 등기부등본 분석 프로젝트 실행 예시

### 15.1 기획 입력

```text
registry-analyzer/
├─ Draft/
│  └─ registry-analysis-plan.md
└─ README.md
```

기획안의 MVP는 다음과 같다고 가정한다.

- PDF 업로드
- 텍스트 PDF 및 스캔 PDF 처리
- 표제부·갑구·을구 구조화
- 근저당, 압류, 가압류, 전세권 및 말소 여부 추출
- 위험 신호와 원문 근거 제공
- 분석 보고서 생성

### 15.2 초기화

```text
devh init Draft/registry-analysis-plan.md
```

하네스는 기획서를 읽고 저장소 구조를 확인한 후 다음 파일을 생성한다.

```text
.dev-harness/
├─ project.yaml
├─ plan.md
├─ work-items.yaml
└─ domain-rules.md
```

개발을 막거나 위험에 영향을 주는 결정만 사용자에게 확인한다.

```text
1. 스캔 PDF를 지원할 것인가?
2. OCR은 로컬 또는 외부 API 중 무엇을 사용할 것인가?
3. 원본 문서를 보관할 것인가?
4. 규칙 엔진과 LLM의 역할을 어떻게 분리할 것인가?
5. 추출 실패를 어떤 상태로 표시할 것인가?
```

초기 추천안은 다음과 같다.

- 스캔 PDF 지원
- MVP에서는 로컬 OCR
- 원본 문서는 기본적으로 분석 후 삭제
- 위험 판정은 규칙 엔진 담당
- LLM은 결과 설명 담당
- 추출 실패는 `판단 불가`로 표시

### 15.3 전체 Phase 계획

```text
P1 — 문서 입력과 텍스트 추출
P2 — 등기 항목 구조화
P3 — 위험 분석과 보고서
P4 — UI 통합과 품질 검증
```

사용자는 전체 Phase의 목표와 순서를 한 번 승인한다.

### 15.4 Phase 1 상세 Task

```text
P1-T1 프로젝트 및 PDF 모듈 기본 구조
P1-T2 PDF 파일 검증
P1-T3 텍스트 PDF 추출
P1-T4 스캔 PDF 판별
P1-T5 로컬 OCR 어댑터
P1-T6 텍스트 정규화
P1-T7 페이지 및 원문 위치 보존
P1-T8 Phase 1 통합 테스트
```

```text
P1-T1
  ↓
P1-T2
  ├─→ P1-T3 ─┐
  └─→ P1-T4 → P1-T5
              │
              ↓
            P1-T6
              ↓
            P1-T7
              ↓
            P1-T8
```

사용자는 Phase 1의 Task, 완료 조건, 관련 Domain Rule과 Risk Tag를 함께 승인한다.

### 15.5 Workflow 선택

| Task | 위험 | Workflow |
|---|---|---|
| P1-T1 기본 구조 | 낮음 | Fast |
| P1-T2 PDF 검증 | 개인정보 입력 | Strict |
| P1-T3 텍스트 추출 | 보통 | Standard |
| P1-T5 OCR 어댑터 | 민감문서 처리 | Strict |
| P1-T6 텍스트 정규화 | 보통 | Standard |

위 표는 Planner가 제안한 위험 분류에 Orchestrator가 정책을 적용한 결과다. Fast 작업은 명시된 저위험 조건을 충족한 경우로 가정한다. 실행 중 더 높은 위험이 발견되면 Workflow를 강화한다.

### 15.6 Strict Task 예시

`P1-T5 로컬 OCR 어댑터`를 실행한다.

#### Context

```text
요구사항:
- 스캔 PDF에서 페이지별 텍스트를 추출한다.
- OCR 실패 페이지를 식별한다.
- OCR confidence를 저장한다.

Domain/Security Rules:
- 원본 문서를 외부로 전송하지 않는다.
- OCR 실패와 위험 없음은 별도 상태다.
- 원문 내용을 로그에 기록하지 않는다.

허용 경로:
- src/ocr/**
- tests/unit/ocr/**
- tests/integration/ocr/**
```

#### Implement

Developer가 OCR Interface와 로컬 구현체, Unit Test를 작성한다.

#### Pre-review Validation

```text
ruff check .        PASS
mypy src            PASS
pytest tests/unit   PASS
```

실패하면 Reviewer를 호출하지 않고 Developer에게 로그를 전달한다.

#### Strict Review

Reviewer는 Task 요구사항, 관련 규칙, 기준선 대비 파일 diff와 필요한 최소 코드, Validation 요약을 읽는다.

첫 Review에서 다음 문제를 발견했다고 가정한다.

```text
CHANGES_REQUESTED

1. OCR 실패 페이지가 빈 문자열로 반환된다.
2. 빈 문자열이 정상 추출 결과와 구분되지 않는다.
3. confidence 범위가 검증되지 않는다.
```

Developer가 다음처럼 수정한다.

- OCR 상태를 `SUCCESS`, `PARTIAL`, `FAILED`로 분리
- 실패 사유 코드 추가
- confidence를 0.0~1.0 범위로 검증

Pre-review Validation과 AI Re-review를 다시 실행한다.

#### Post-review Validation

```text
전체 Integration Test   PASS
PDF E2E Test            PASS
개인정보 로그 검사       PASS
```

현재 코드와 Review·필수 Validation의 Revision이 같고 계획 승인도 유효한지 확인한다. 통과하면 13.4의 절차로 최종 Revision과 검사 근거를 연결하고 SQLite의 `P1-T5` 상태를 `COMPLETED`로 갱신한다. 커밋은 생성하지 않는다.

### 15.7 실행 중 승인

Developer가 외부 OCR API 도입이 필요하다고 판단하면 하네스가 중단한다.

```text
WAITING_APPROVAL

요청:
외부 OCR API와 SDK 도입

영향:
- 등기부등본 원본의 외부 전송 가능성
- API 비용 발생
- API Key 필요
- 개인정보 처리 정책 필요

추천:
MVP에서는 로컬 OCR 유지
```

사용자가 결정을 내리면 저장된 Run을 재개한다. 컴퓨터를 재부팅한 경우에도 12.3의 정합성 검사와 중단 복구를 적용한 뒤 필요한 단계부터 진행한다.

### 15.8 Phase 1 종료

모든 P1 Task가 완료되면 다음을 통합 검증한다.

- 텍스트 PDF 처리
- 스캔 PDF OCR
- 손상된 PDF 오류 처리
- 페이지 및 원문 위치 보존
- OCR 실패와 위험 없음의 구분
- 원문 데이터의 로그 노출 방지

하네스는 Phase Report를 생성한다.

```text
완료 Task: 8/8
자동 재시도: 2회
사용자 승인: 1건
Validation: 전체 통과
알려진 제한사항: 오래된 일부 등기 양식 미검증
```

사용자는 Phase 결과를 확인하고 인수한다. Git commit·push 등의 여부와 실행은 사용자가 별도로 수동 결정·수행하며 Phase 인수 조건에 포함하지 않는다.

### 15.9 다음 Phase

Phase 1에서 확인한 실제 문서 형식과 OCR 품질을 반영하여 Phase 2를 상세 Task로 분해한다.

```text
P2-T1 공통 등기 항목 타입
P2-T2 표제부 파서
P2-T3 갑구 파서
P2-T4 을구 파서
P2-T5 말소 상태 판별
P2-T6 원문 근거 연결
P2-T7 정답 샘플 검증
```

등기 항목 파싱과 위험 판정은 핵심 Domain Rule이므로 Strict Workflow를 적용한다. 법률적 의미의 정확성은 AI Review만으로 확정하지 않고 Phase 인수 조건에 사람의 도메인 검토를 포함한다.

---

## 16. MVP 개발 Phase

Phase 1 착수 전에 Work Item 계약, 규칙 참조, Workflow별 완료 조건, Revision과 재개 규칙을 데이터 모델에 반영한다. 각 실행 기능은 아래 Phase에 맞춰 구현하며, 별도의 요구사항 관리 시스템이나 전용 Workflow 하향 승인 기능은 추가하지 않는다.

### Harness Phase 1 — Foundation

- Python CLI 구조
- 공통 설치용 CLI 패키지 구조와 `devh` 실행 진입점
- `project.yaml` 스키마와 검증
- `plan.md`, `work-items.yaml`, `domain-rules.md` 구조와 참조 검증
- 실행 상태와 승인 기록을 전담하는 SQLite State Store
- 실행 입력 사본 저장과 로컬 DB 백업
- 파일 내용 기반 코드·계획 Revision 및 검사 결과·Task 완료 기록 모델
- Git 없는 프로젝트를 포함한 작업 폴더 정합성 검사와 재개 판단
- `init`, `status`, `resume` 명령
- 현재 프로젝트 탐색과 프로젝트별 초기화·상태 구분
- 재초기화 시 기존 설정·계획·실행 상태 보존

### Harness Phase 2 — Planning

- Markdown 기획서 읽기
- 전체 Phase 계획 생성
- 현재 Phase Task 분해
- Task 의존성
- Acceptance Criteria와 원문·Domain Rule 참조 생성
- 공통·Task별 Domain Rule 추출과 Risk Tag 제안
- 계획 승인과 revision
- 자연어 수정 요청을 작은 Task 정의로 변환
- 자연어의 Phase 시작·상태 조회·작은 수정 의도 구분

### Harness Phase 3 — Execution

- Codex CLI Adapter
- AI 도구의 사용자 환경에서 `/development`를 Core CLI에 연결
- 동일한 Task 계약과 Domain Rule로 Developer·Reviewer Context 구성
- Risk Tag 기반 Fast/Standard/Strict 선택과 실행 중 위험 갱신
- Developer와 Reviewer 역할 분리
- Revision에 연결된 Review·Validation Runner와 Workflow별 완료 판정
- Retry 제한
- 최종 Revision 기반 Task 완료 기록과 중단 복구
- 독립 자연어 요청의 순차 실행과 Task 결과 안내

### Harness Phase 4 — Delivery

- 하네스 설치·AI 도구 연결·프로젝트 초기화 사용 안내
- Phase 통합 검증
- Phase Report
- Git 작업과 분리된 Phase 결과 인수
- Decision Desk Phase 하나 dogfooding

---

## 17. MVP 완료 조건

- 하네스를 한 번 설치한 뒤 여러 프로젝트에서 같은 `devh`를 사용할 수 있다.
- 하네스 소스를 대상 프로젝트에 복사하지 않고 프로젝트별 초기화를 수행할 수 있다.
- `/development` 연결 여부와 관계없이 Core CLI를 사용할 수 있으며, 연결 시 현재 프로젝트 경로를 전달한다.
- 서로 다른 프로젝트의 설정·실행 상태·승인을 구분하고, 재초기화 시 기존 기록을 보존한다.
- 필수 설정 파일 하나로 프로젝트를 초기화할 수 있다.
- Markdown 기획서에서 전체 Phase 계획을 생성할 수 있다.
- 현재 Phase를 실행 가능한 Task로 분해할 수 있다.
- Phase 개발은 계획 승인 후, 작은 자연어 수정은 사용자 요청에 근거한 범위 승인과 권한 확인 후에만 소스 코드를 수정한다.
- 초기 설정 후 자연어 수정 요청을 작은 Task로 만들어 같은 실행 엔진에서 실행할 수 있다.
- `/development Phase2 개발해보자`를 P2 시작으로 연결하고, 진입 조건과 계획 승인을 확인한 뒤 실행할 수 있다.
- "상단의 폰트를 10pt로 줄여줘"처럼 영향이 제한된 수정은 전체 Phase 계획과 별도 AI Review 없이 Fast로 실행할 수 있다.
- 실행 가능한 Task는 확인 가능한 완료 기준을 가지며 Phase 계획 또는 자연어 요청의 범위 승인과 연결된다.
- Developer와 Reviewer에게 같은 계획 revision의 공통·참조 Domain Rule을 전달한다.
- 존재하지 않는 규칙·의존성 참조와 순환 의존성이 있는 계획은 실행하지 않는다.
- 의존성이 완료된 Task만 실행한다.
- Orchestrator가 Risk Tag와 정책에 따라 Fast, Standard, Strict를 선택하고 근거를 기록한다.
- 실행 중 새 위험이 발견되면 Workflow를 강화하며, 필요한 행동 승인은 별도로 확인한다.
- 관련 코드에서 영향과 위험을 확인하며, 불확실한 작업을 Fast로 실행하지 않는다.
- 자연어 수정 요청도 적용 Workflow·판단 근거·승인·검증·최종 코드 Revision을 SQLite 기록과 연결한다.
- Pre-review Validation 실패 시 Reviewer를 호출하지 않는다.
- Reviewer는 전체 프로젝트가 아닌 관련 diff 중심으로 검토한다.
- 선택된 Workflow에 필요한 Review·Validation이 최종 코드 Revision과 유효한 계획 revision에 연결되어야 완료한다.
- Fast의 정책상 Review 생략은 정상 처리하되, 미실행 필수 검사를 PASS로 표시하지 않는다.
- Review 이후 수정 시 이전 필수 수정 요청을 유지한 채 Delta 또는 전체 Review를 수행한다.
- 실패 시 설정된 횟수만 자동 재시도한다.
- 승인 대상 행동에서 실행을 중단한다.
- 실행 상태와 승인 기록은 SQLite만을 기준으로 관리하며 YAML·Markdown과 이중 관리하지 않는다.
- `work-items.yaml`에는 실행 상태 없이 작업 정의만 저장한다.
- 실행에 사용한 계획 사본과 승인 기록을 SQLite에서 연결할 수 있다.
- 컴퓨터 재부팅 후 작업 폴더·계획·SQLite 상태를 확인하고 Run을 재개할 수 있다.
- 예상하지 못한 상태 불일치는 차이를 표시하고 중단하며 자동 덮어쓰기·되돌리기를 하지 않는다.
- 검증 후 Task 완료 기록 전 중단을 복구하며 Task 구현을 중복 실행하지 않는다.
- 실행 중 중단된 검사를 성공으로 간주하지 않는다.
- Task마다 최종 파일 Revision과 검증 결과를 연결하며 Git 없이도 완료할 수 있다.
- 하네스와 작업 에이전트는 Git 초기화·Branch 생성 및 전환·staging·commit·push·PR·merge를 수행하지 않는다.
- 사용자의 수동 Git 작업이 코드·계획·실행 입력을 바꾸지 않았다면 Git 메타데이터 변화만으로 재개를 차단하지 않는다.
- Phase 종료 시 결과, 테스트, 결정, 제한사항을 보고서로 제공한다.
- Decision Desk의 실제 Phase 하나를 처음부터 끝까지 실행할 수 있다.

---

## 18. MVP 이후 확장 순서

실사용에서 필요성이 확인된 기능만 다음 순서로 확장한다.

1. 추가 AI Provider Adapter
2. 별도 작업 폴더 격리 (Git 쓰기 자동화 제외)
3. 독립 Failure Analyst
4. Security Reviewer 및 Domain Reviewer
5. Agent Registry 외부 설정
6. Workflow DAG 사용자 설정
7. 병렬 Task 실행
8. 원격 Artifact Store
9. Web Dashboard
10. Project Kickoff Harness 연동

---

## 19. 핵심 결정 요약

1. 현재 문서는 바이브 코딩 사용자와 중·소규모 프로젝트용 1차 MVP 기준이다.
2. 기존 기획서는 장기 Target Architecture로 보존한다.
3. 필수 설정은 `project.yaml` 하나로 시작한다.
4. 사용자 계획 구조는 `기획 → Phase → Task`를 기본으로 한다.
5. 전체 Phase는 먼저 계획하고 현재 Phase만 상세화한다.
6. Workflow는 Fast, Standard, Strict 세 가지를 내장하며, AI의 요청·코드 해석을 바탕으로 Orchestrator가 자동 선택한다.
7. Strict는 `Implement → Pre-review Validation → AI Review → Post-review Full Validation → 최종 Revision 확인·완료 기록` 순서로 실행한다.
8. Review 이후 수정에는 Delta Review를 적용한다.
9. Reviewer는 관련 요구사항과 diff만 읽어 토큰 사용을 제한한다.
10. Tester는 AI Agent가 아니라 Validation Runner로 시작한다.
11. Agent 역할은 Planner, Developer, Reviewer만 우선 제공한다.
12. Task는 순차 실행한다.
13. 일반 수정은 자동화하고 중요한 결정만 사용자에게 승인받는다.
14. 실행 상태와 승인 기록의 유일한 기준은 SQLite다. 코드는 작업 폴더, 작업 정의는 YAML, 결과 안내와 보고서는 SQLite·파일 변경 내역에서 생성한 출력물로 관리한다.
15. Git 쓰기는 하네스 범위에서 제외한다. 사용자가 Git 사용과 commit·push 등을 수동 결정·실행하며 하네스는 결과물과 검증 근거까지 제공한다.
16. Decision Desk의 실제 Phase 하나를 첫 dogfooding 목표로 삼는다.
17. 초기 설정 후 자연어 수정 요청은 작은 Task로 만들고 같은 실행 엔진에서 처리한다. 작은 수정마다 전체 Phase 계획을 다시 만들지 않는다.
18. 명확하고 작은 사용자 요청은 해당 범위의 승인 근거로 SQLite에 기록하며, 기존 승인 정책의 `ask`·`deny`를 우회하지 않는다.
19. YAML에는 작업 정의만 저장하고, 실행 상태·승인·검증 결과는 SQLite에만 기록한다. 보고서와 로그에서 현재 상태를 복원하지 않는다.
20. SQLite 상태와 실제 작업 파일을 확인하여 재개하며, 기존 변경 보존과 중복 실행 방지를 기본 동작으로 제공한다. Git은 선택적 읽기 전용 참고 정보다.
21. 자연어의 Phase 시작과 작은 수정 요청을 구분하며, Phase 시작 요청만으로 아직 제시하지 않은 상세 계획의 승인을 대신하지 않는다.
22. 하네스는 컴퓨터의 사용자 환경에 한 번 설치하고, 사용할 프로젝트마다 `devh init`으로 초기화한다.
23. `/development` 연결은 사용하는 AI 도구에서 별도로 설정하며, 연결하지 않아도 Core CLI를 사용할 수 있다.
24. 현재 프로젝트의 설정과 로컬 SQLite를 찾아 실행한다. 공통 하네스 설치를 공유해도 프로젝트별 상태와 승인은 구분한다.
25. Work Item은 완료 기준, 요구사항·규칙 참조, Risk Tag와 의존성을 담는 실행 계약이다.
26. Domain Rule은 ID와 원문 출처로 관리하고, 공통 규칙과 Task별 규칙을 같은 계획 revision에서 전달한다.
27. Workflow별 필수 Review·Validation을 최종 코드 Revision과 연결하여 완료를 판정한다.
28. Resume는 실제 프로젝트 파일과 저장된 실행 상태를 대조하고, 유효한 최종 Revision·검사 결과·승인을 확인하여 중단된 완료 기록을 복구한다.
29. AI는 위험을 제안·갱신하고 Orchestrator가 Workflow를 결정한다. 자동 강화는 허용하고 자동 하향은 지원하지 않는다.


---

## 20. 기획 변경 이력

이 절은 기존 계획이 무엇에서 무엇으로 바뀌었는지 추적한다. 현재 요구사항은 본문을 기준으로 하며 과거 내용은 변경 이력으로만 남긴다. 후속 제안은 채택 전까지 확정 변경으로 기록하지 않는다.

| 변경 ID | 날짜 | 버전 | 기존 계획 | 변경한 계획 | 이유·결정 근거 | 영향 범위 |
|---|---|---|---|---|---|---|
| CHG-001 | 2026-09-14 | 0.4 → 0.5 | Phase Branch·Task Commit·Phase PR 자동 관리, Push·Merge는 사용자 승인 후 처리 | Git 쓰기 자동화 전부 제외. Git 사용과 commit·push 등은 사용자가 수동 결정·수행하고 하네스는 산출물과 검증 근거까지 제공 | 사용자의 Git 자동화 삭제 요청 | 실행 흐름, 구조, 설정, 승인 정책, Git 경계, 예시, 구현 Phase, 완료 기준 |
| CHG-002 | 2026-09-14 | 0.4 → 0.5 | Task Commit 생성·확인 후 COMPLETED, COMMIT_PENDING 복구 | 파일 내용 기반 Revision·검사 근거·승인을 확인해 SQLite에 완료 기록. 중단 시 저장된 증거와 현재 파일을 대조 | CHG-001에 따른 완료·재개 기준 정합성 보완 | 5장, 8.6절, 12.3절, 13장, 16~17장, 19장 |
| CHG-003 | 2026-09-14 | 0.4 → 0.5 | Git 루트를 기준으로 프로젝트 탐색, Git·Commit 중심 보고 | project.yaml이 있는 폴더를 루트로 식별하며 Git 없이 동작. 보고서는 파일 변경 내역·검증 기록에서 생성 | Git 사용을 선택 사항으로 만들기 위한 연관 수정. 신규·기존 프로젝트 상세 진입 정책은 별도 제안 대상 | 4.4절, 5장, 13장 |

Fast 검증 세부 기준, Phase 인수 보고서 보강, 신규·기존 프로젝트 진입 절차, 위험 작업 통제의 구체적 구현 방식은 이번 개정에서 새 확정 사항으로 추가하지 않았다. 기존 본문을 유지한 상태에서 후속 논의 대상으로 검토한다.
