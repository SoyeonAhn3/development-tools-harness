# AI Development Harness MVP 기획서

> 버전: 0.6
> 상태: 결정 확정본
> 작성일: 2026-09-13
> 수정일: 2026-09-14
> 대체 대상: v0.5, v0.4, `development-harness-v0.1-개발계획.md`
> 결정 근거: `archive/harness-decision-record.md` (D-01 ~ D-33)
> 장기 방향: `ai-development-harness-plan.md`를 Target Architecture로 유지한다
> 첫 dogfooding 대상: Decision Desk

---

## 0. 문서 사용법

이 문서의 서술은 별도 표기가 없으면 **확정**이다. 아직 확인받지 않은 내용에는 `[제안]`을 붙인다. 확정 항목을 변경할 때는 22장 이력에 사유와 함께 기록한다.

문서 작성 요청이나 이 문서의 존재 자체를 상세 정책의 일괄 승인으로 취급하지 않는다.

### v0.6 주요 변경

| 영역 | 변경 |
|---|---|
| Git | 하네스가 **원격 저장소를 전혀 조작하지 않는다.** push·merge 기능과 해당 승인 지점을 제거 |
| Phase 인수 | 보고 가능 조건과 인수 조건을 분리하고, 최종 코드 기준 통합 검증을 인수 게이트로 신설 (8.6) |
| 재검증 | 재구현 범위와 재검증 범위를 구분. `task_hash`는 코드 영향을 판단하지 못함을 명시 (12.5) |
| 교착 | `NO_RUNNABLE_TASK` 중단 조건 신설 |
| 데이터 모델 | 검증에 계획 hash, 결과 승인에 코드 Revision, 전체 계획 승인 대상을 연결 |
| 동시 실행 | 소유권 획득을 원자적 처리로 변경, Step별 재개 규칙 분리 |
| 권한 검증 | 하네스 내부 게이트와 실제 Adapter 경계 검증을 2단계로 분리 |
| Fast | 대상에서 버그 수정 제외 |
| 반려 | 유형을 원인으로 직결하지 않고 기존 완료 기준 포함 여부로 분기. 사용자 원문 선저장 |
| 초기화 | `init` 시 baseline 검증 결과 기록 |

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
→ Task별 로컬 Commit
→ Phase 통합 검증
→ Phase 결과 자료 제시
→ 사용자 인수 또는 반려
```

사용자는 이 흐름에서 계획 승인, 고위험 결정 허가, 결과 인수 세 가지만 수행한다. 원격 저장소 반영은 하네스 바깥에서 사용자가 직접 한다(15.3).

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
- Phase 로컬 브랜치와 Task 커밋
- 중단 후 재개와 커밋 복구
- Phase 통합 검증과 인수

**축소**

- 필수 설정은 `project.yaml` 하나
- Phase와 Task만 기본 계층으로 사용
- Codex CLI Adapter 하나
- Task 순차 실행

**제외**

- **원격 저장소 조작 전체** (push, merge, PR 생성, 배포)
- 여러 Agent의 병렬 코드 수정
- 사용자 정의 Workflow DAG
- 동적 Agent Registry
- 다중 AI Provider 동시 지원
- Task별 Git worktree
- 원격 Artifact Store
- 완전한 Event Sourcing
- Web Dashboard
- 자연어 수정 요청 (21장 확장 목록)

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
- 반려 사유의 유형 분류 제안
- 재계획안 제안

Orchestrator 프로그램
- 현재 상태와 승인·반려 기록을 SQLite에 저장
- 실행 가능한 Task 선택
- Risk Tag에 정책을 적용해 Workflow 결정
- 권한과 승인 확인
- Validation 명령 실행과 종료 코드 판정
- 재시도 횟수 제한
- 완료·인수 조건 판정
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

`project.yaml`에 `ask`를 적는 것만으로 실행 차단이 보장되지는 않는다.

#### 검증의 2단계 분리

권한 경계 검증은 성격이 다른 두 가지이며 같은 단계에서 확인할 수 없다.

| 단계 | 검증 대상 | 시점 |
|---|---|---|
| 하네스 내부 게이트 | 승인 전 실행 금지, 정책 분류, 상태 전이, 대기·재개 | Phase 0 (AI 호출 없음) |
| **실제 실행 경계** | 승인 대상 명령·파일 수정·외부 전송을 **실제 실행 전에 차단할 수 있는가** | 실제 Adapter 최소 연결 직후 |

가짜 Adapter는 지시대로 동작하므로 두 번째를 재현하지 못한다. Phase 0만으로 2.2가 검증됐다고 보지 않는다.

> **이것은 이 프로젝트에서 가장 큰 미검증 가정이다.** 하네스가 AI 실행 도구의 행동을 실제로 차단하지 못한다면, 이 제품은 통제 도구가 아니라 사후 보고 도구가 되고 11장 승인 정책의 전제가 무너진다.

따라서 실제 Adapter 경계 확인은 Phase 3까지 미루지 않고 Phase 0 직후 최소 스파이크로 수행한다(19장). 실제 권한 통제가 되지 않는 동작은 수동 처리 대상으로 명시한다.

### 2.3 최종 코드 기준 검증

검사 결과는 **검사한 코드 Revision과 계획 hash에 묶여서만** 유효하다. 이 원칙은 Review, Validation, 승인, 인수에 공통으로 적용한다.

- Review 또는 Validation 이후 코드가 바뀌면 이전 결과를 최종 코드의 근거로 재사용하지 않는다.
- 자동 포맷 수정처럼 검사 중 파일이 바뀐 경우도 코드 변경으로 취급하고, 변경이 끝난 Revision에서 다시 검사한다.
- 시작만 기록되고 종료가 확정되지 않은 검사는 성공으로 간주하지 않는다.
- 정책상 생략한 검사는 `SKIPPED_BY_POLICY`로 기록하며 `PASS`로 표시하지 않는다.
- 미실행·중단된 필수 검사를 통과로 간주하지 않는다.
- 승인은 대상의 hash에 연결한다. 완료 기준, 적용 규칙, 검증 명령·필수 여부, 위험 판단이 바뀌면 영향 범위의 기존 승인과 검사 결과를 다시 사용하지 않는다.
- **작업 정의가 같다는 이유만으로 기존 검사 결과를 재사용하지 않는다.** 정의는 그대로여도 다른 Task의 코드 변경으로 동작이 깨질 수 있다(12.5).
- 실패한 테스트를 삭제하거나 기준을 낮춰 통과시키는 변경은 별도 검토 대상이다.

Revision과 hash의 계산 방법은 14.5에, Task 완료 조건은 8.5에, Phase 인수 조건은 8.6에 정의한다.

### 2.4 작은 설정 비용

하네스를 적용하기 위한 준비 비용이 직접 개발하는 비용보다 커지면 안 된다.

- 필수 설정 파일은 `project.yaml` 하나다.
- 여러 프로젝트가 같은 하네스 설치를 사용하며, 프로젝트마다 하네스 소스를 복사하지 않는다.
- 대부분의 설정에 안전한 기본값을 제공한다.
- 사용자는 기획 문서와 테스트 명령만 제공해도 시작할 수 있다.
- 새로운 검증 단계를 추가할 때 새 설정 항목을 요구하기보다 기존 설정을 재사용한다.
- 사용자에게 내부 Task 형식, Workflow 이름, DB 구조를 이해하도록 요구하지 않는다.

### 2.5 위험도에 따른 실행

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
  ├─ Git Manager          로컬 전용
  └─ SQLite State Store
       ↓
Codex CLI Adapter
  ├─ Planner 역할
  ├─ Developer 역할
  └─ Reviewer 역할
```

Git Manager는 로컬 저장소만 다룬다. 원격 관련 기능을 포함하지 않는다(15장).

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

하네스 설치와 `/development` 연결은 별개다. 연결하지 않아도 터미널에서 `devh`로 실행할 수 있다.

```text
devh init Draft/product-plan.md
```

`init`이 수행하는 일은 다음과 같다.

1. Git 저장소 여부를 확인한다. 저장소가 아니면 `git init`을 안내하고 중단한다(14.5).
2. `.dev-harness/` 기본 설정과 계획 파일을 준비하고 로컬 SQLite를 연결한다.
3. **baseline 검증을 1회 실행해 결과를 기록한다.** 설정된 검증 명령을 현재 코드에서 그대로 실행하고 결과를 저장한다.
4. 사용자의 미커밋 변경이 있으면 목록을 표시한다.

baseline이 없으면 첫 Task부터 "내 변경 때문에 깨진 것인지 원래 깨져 있었는지" 구분할 수 없다. 기존 프로젝트에 적용할 때 특히 중요하다. baseline이 실패 상태여도 진행은 막지 않되, 이후 검증 결과 해석에 그 사실을 함께 표시한다.

이미 초기화된 프로젝트에서 다시 실행해도 기존 설정·계획·실행 상태를 덮어쓰지 않는다.

### 3.5 현재 프로젝트 식별

- Core CLI는 현재 작업 폴더에서 Git 저장소 루트까지 탐색해 가장 가까운 `.dev-harness/project.yaml`을 기준으로 프로젝트를 식별한다.
- Slash Command는 현재 열린 프로젝트의 작업 경로를 Core CLI에 전달한다. 최근에 사용한 다른 프로젝트를 임의로 선택하지 않는다.
- 프로젝트 ID와 저장소 경로로 해당 프로젝트의 SQLite를 연결한다(14.1).
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

`plan.md`, `work-items.yaml`, `domain-rules.md`, `review-report.md`는 하네스가 생성·갱신하는 산출물이다.

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

  # 생략 시 post_review를 Phase 인수 검증에 재사용한다 (8.6)
  # phase_acceptance:
  #   - name: e2e
  #     command: npm run test:e2e
  #     required: true

approval:
  file_edit: auto
  test_execution: auto
  dependency_install: ask
  architecture_change: ask
  database_migration: ask
  external_api: ask
  local_commit: auto
  task_result: auto       # ask로 바꾸면 Task마다 결과 확인

git:
  strategy: phase-branch
```

원격 조작 관련 설정(`git_push`, `merge`, `production_deploy`)은 없다. 하네스가 해당 기능을 갖고 있지 않기 때문이다(15장).

`git.task_commit` 옵션은 제공하지 않는다. Task 커밋은 부분 반려·재개·커밋 복구의 물리적 기반이므로 끌 수 없다.

### 5.1 설정 검증

- Pydantic 또는 동등한 스키마 검증으로 읽는다.
- 필수 필드가 없으면 시작하지 않는다.
- 알 수 없는 필드는 오류로 처리한다.
- 선택된 Workflow에 필요한 검사 목록이 비어 있으면 실행 전에 설정 보완을 요청한다.
- API Key와 비밀값은 YAML에 저장하지 않는다. 환경변수 또는 운영체제 자격 증명 저장소를 사용한다.

`validation.quick`은 Fast에서 사용한다. Standard와 Strict는 `pre_review`와 `post_review`를 사용한다. AI가 임의로 `required: true` 검사를 제외할 수 없다. **설정되지 않은 검사를 실행한 것으로 보고하지 않는다.**

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
| 누락 | 개발에 필요한데 기획에 없는 결정 |
| 모순 | 문서 안에서 서로 충돌하는 서술. 근거 위치를 함께 제시 |
| 모호 | 여러 해석이 가능한 서술. 판단하지 않고 확인 대상으로 표시 |

명확한 모순만 모순으로 분류한다. 판단이 어려운 것은 모호로 분류하고 사용자에게 확인을 넘긴다. 각 항목에 기획 문서의 출처 위치를 표시한다. 검토 결과를 이유로 개발을 자동으로 막지 않는다.

### 6.3 요구사항 커버리지 `[제안]`

`devh plan` 이후 기획 문서의 요구사항이 어느 Task에도 연결되지 않았는지 검사한다. `requirement_refs`를 실행 가능한 Task의 필수 항목으로 올리면 자동 검사가 가능하다.

---

## 7. 개발 계획 구조

### 7.1 계층

```text
기획
└─ Phase
   └─ Task
      └─ AI 개발 Workflow
```

Feature는 필요한 경우 `plan.md` 안에서 Task 그룹으로만 사용한다.

### 7.2 Work Item 계약

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
| `acceptance_criteria` | 실행 가능한 Task에 하나 이상 필요하다. Developer의 구현 목표이자 Reviewer의 검토 기준이며, **반려 유형 판정의 기준**이다(12.2) |
| `requirement_refs` | 원본 요구사항의 위치. 현재는 선택 |
| `domain_rule_refs` | Task에 추가 적용할 규칙 ID |
| `risk_tags` | 위험·작업 특성 분류. 누락은 미분류로 처리하고 실행 전에 보완한다 |
| `depends_on` | 선행 Task ID. SQLite에서 완료를 확인한 뒤 실행한다 |

- **ID 문자열로 계층이나 관계를 추측하지 않는다.** 계층은 `parent_id`로만 판단한다. ID 형식은 프로젝트가 자유롭게 정한다.
- 중복 ID, 존재하지 않는 부모·의존성·규칙 참조, 순환 의존성은 계획 검증 오류로 처리한다.
- 완료 기준은 짧고 확인 가능한 문장으로 쓴다. 문장이 존재한다는 이유만으로 완료 처리하지 않는다.
- 승인과 실행 상태는 SQLite에서 관리하므로 이 파일에 `status`를 두지 않는다.

### 7.3 Rolling Wave Planning

```text
프로젝트 시작
├─ P1: Task까지 상세 계획
├─ P2: 주요 기능 수준 계획
└─ P3 이후: 목표와 종료 조건 중심 계획
```

### 7.4 Domain Rule

`.dev-harness/domain-rules.md`에 안정적인 ID로 관리한다.

```markdown
# Domain Rules

## DR-SEC-001

- 적용: 공통
- 원문: Draft/product-plan.md — 인증 보안

사용자 비밀번호는 평문으로 저장하거나 로그에 기록하지 않는다.
```

- Planner가 기획서에서 규칙과 출처를 추출하고 계획 승인에 포함한다.
- `적용: 공통` 규칙은 모든 Task에 전달한다. 참조 누락으로 공통 규칙의 적용이 사라지지 않는다.
- Context Builder가 `공통 규칙 + Task 참조 규칙`을 합쳐 Developer와 Reviewer에게 같은 내용을 전달한다.
- 규칙의 의미가 바뀌면 계획 hash가 바뀌며 2.3이 적용된다.

### 7.5 Risk Tag와 Workflow 선택

1. `risk_tags`에 `strict_when` 항목이 하나라도 있으면 Strict.
2. Strict 조건이 없고 `fast_when` 조건을 충족하면 Fast.
3. 나머지는 `default_workflow`(기본 Standard).

- 분류가 모호하면 Fast를 선택하지 않는다.
- 선택된 Workflow, 적용 Tag, 정책 근거를 SQLite에 기록한다.
- Developer와 Reviewer는 실행 중 발견한 새 위험을 보고하고, Orchestrator가 다시 판정한다.
- Fast → Standard → Strict 강화는 자동 허용한다. 자동 하향은 지원하지 않는다.
- Workflow 강화는 행동 권한 승인이 아니다.

---

## 8. 내장 Workflow와 완료 조건

### 8.1 Fast

대상: 문서 수정, 포맷 변경, 영향이 제한된 스타일 수정, 단순 설정 변경, 테스트만 추가

```text
Implement → Quick Validation → Task Commit
```

**버그 수정은 Fast 대상이 아니다.** 버그 수정은 동작 변경이며 재현·회귀 테스트가 필요하므로 Standard 이상으로 처리한다. 이 때문에 `fast_when`에서 `small_isolated_fix`를 제거했다.

AI Reviewer를 호출하지 않으며, 생략된 Review는 `SKIPPED_BY_POLICY`로 기록한다. Quick Validation은 변경 diff 확인과 `validation.quick` 실행을 수행한다. 수행하지 않은 검사나 화면 확인을 통과로 표시하지 않는다.

### 8.2 Standard

대상: 일반적인 기능 개발, 버그 수정, 기존 패턴 안의 API·UI 변경, 중간 수준의 리팩터링

```text
Implement → Pre-review Validation → Light AI Review → Post-review Validation → Task Commit
```

Reviewer는 현재 Task 요구사항과 관련 diff만 확인한다.

### 8.3 Strict

대상: 개인정보·민감정보 처리, 인증과 권한, DB Migration, 외부 API 도입, 핵심 Domain Rule, 보안 영향이 있는 변경, Architecture 변경

```text
Implement
       ↓
Pre-review Validation
       ↓ 실패
Developer 자동 수정
       ↓
Strict AI Review
       ↓ 변경 요청
Developer 수정 → Pre-review Validation → AI Re-review
       ↓ 승인
Post-review Validation
       ↓ 실패
Developer 수정 → Pre-review Validation → Delta Review → Post-review 재실행
       ↓
Task Commit
```

Pre-review Validation과 Post-review Validation의 실제 내용은 `project.yaml`에 설정된 명령이다. E2E나 보안 검사는 프로젝트가 해당 명령을 설정한 경우에만 실행되며, 설정하지 않았다면 수행한 것으로 보고하지 않는다(5.1).

Pre-review Validation의 필수 검사가 실패하면 Reviewer를 호출하지 않는다.

### 8.4 Workflow 자동 선택

구현 전에 관련 코드를 읽어 실제 변경 영향과 위험 신호를 확인한다. 이 단계에서는 소스 코드를 수정하지 않는다.

```text
계획된 Task 확인
→ 관련 코드 확인
→ 변경 종류·영향 범위·위험 신호를 구조화된 결과로 반환
→ Workflow Router가 프로젝트 규칙과 대조
→ Workflow 및 필요한 승인 확인
→ 구현 시작
```

영향 범위를 확신할 수 없으면 Fast를 선택하지 않고 Standard를 적용한다. 구현 중 새 위험이 발견되면 Workflow를 상향하고, 상향된 Workflow의 검토·검증을 통과해야 완료할 수 있다.

### 8.5 Task 완료 조건

| Workflow | Commit 전에 최종 Revision에서 충족할 조건 |
|---|---|
| Fast | Quick Validation의 필수 검사 통과. Review는 `SKIPPED_BY_POLICY` |
| Standard | Pre-review Validation 통과, Light 또는 유효한 Delta Review PASS, Post-review Validation 통과 |
| Strict | Pre-review Validation 통과, Strict 또는 유효한 Delta Review PASS, Post-review Validation 통과 |

모든 Workflow에 다음이 함께 적용된다.

- 승인된 Task 계약이 유효하고 선행 Task가 완료되어 있어야 한다.
- 필요한 Review가 있다면 미해결 필수 수정 요청이 없어야 한다.
- 2.3의 검증 원칙을 충족해야 한다.
- 조건을 충족하면 Commit을 진행할 수 있다. Task `COMPLETED`는 Commit 내용 확인과 SQLite 기록까지 끝난 뒤 확정한다.

### 8.6 Phase 인수 조건

**보고 가능 조건과 인수 조건은 다르다.**

- 실패·차단 상태에서도 진행 결과와 문제를 보고할 수 있다.
- 인수는 별도 조건을 충족해야 한다.

Phase를 `ACCEPTED`로 만들려면 다음을 모두 충족해야 한다.

1. **승인 범위의 모든 실행 가능 Task가 `COMPLETED`다.** `BLOCKED`나 `FAILED` Task가 남아 있으면 인수할 수 없다.
2. **최종 코드 기준 Phase 통합 검증을 통과했다.** 아래 8.6.1 참조.
3. 통합 검증 결과가 현재 코드 Revision과 승인된 계획 hash에 연결되어 있다.
4. 사용자가 결과 자료를 확인하고 승인했다.

일부 기능을 제외하고 인수하려면 **먼저 범위와 완료 기준을 변경하고 승인을 받는다.** 보고서에 미완료 항목을 적었다는 이유로 인수 조건을 대신하지 않는다. 이는 2.3의 "미실행 필수 검사를 통과로 간주하지 않는다"를 Phase 층위에 적용한 것이다.

`DENY_STOP`으로 Task를 중단할 때는 그 자리에서 **해당 Task를 Phase 범위에서 제외할지** 함께 확인한다. 제외를 선택하면 계획 hash가 갱신되고 범위 변경 승인으로 처리된다. 제외하지 않으면 그 Task는 인수를 막는 미완료 항목으로 남는다.

#### 8.6.1 Phase 통합 검증

Phase 결과 승인을 요청하기 직전, **현재 최종 코드**에서 통합 검증을 1회 실행한다.

- 사용할 명령은 `validation.post_review`다. 별도 설정을 요구하지 않는다.
- `validation.phase_acceptance`를 설정한 프로젝트는 그것으로 대체한다.
- Phase 안에 Fast Task만 있어도 실행한다. Task 단위로는 통합 검증을 거치지 않았기 때문이다.
- 필수 검사가 하나라도 실패하면 결과 승인을 요청하지 않는다.

이 검증이 12.5의 안전망이다. 개별 Task의 재검증 범위를 코드 의존성까지 정확히 계산하는 것은 MVP 범위 밖이므로, 인수 게이트에서 최종 코드 전체를 한 번 확인한다.

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
| 일반 기능·버그 수정 | Light Review 1회 |
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

Delta Review는 이전 Review 기록과 대상 Revision을 연결하고 기존 필수 수정 요청의 해결 여부를 확인한다. 최신 diff가 PASS라는 이유만으로 과거의 미해결 요청을 삭제하지 않는다.

### 9.4 비용 제한

- Task당 Review 호출 횟수를 제한한다.
- Task diff가 너무 크면 Review 전에 Task를 다시 나눈다.

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

```text
Planner   → plan-project / plan-phase / review-plan-document
Developer → implement-task / fix-failure
Reviewer  → review-diff
```

---

## 11. 승인 정책

### 11.1 승인 지점

| # | 지점 | 대상 | 연결 hash |
|---|---|---|---|
| ① | 전체 Phase 계획 | Phase 목표·순서·종료 조건 | `roadmap_hash` |
| ② | 현재 Phase Task 계획 | Task, 완료 기준, Domain Rule, Risk Tag | `plan_hash` |
| ③ | 실행 중 새로 발견된 고위험 결정 | 해당 행동 | `plan_hash` |
| ④ | Phase 완료 결과 | Phase 산출물 인수 | `plan_hash` + `code_revision` |
| ⑤ | Task 완료 결과 (선택) | `approval.task_result: ask`일 때만 | `task_hash` + `code_revision` |

v0.5에 있던 Push·Merge 승인 지점은 제거했다. 하네스가 해당 기능을 갖고 있지 않다(15.3).

승인 단위는 사용자가 이해할 수 있는 수준으로 한다. 승인된 범위 안의 하위 작업은 자동 진행한다. 기존 승인 계획이 유효하면 같은 내용을 다시 승인받지 않는다.

### 11.2 자동 허용

- 승인된 범위 안의 파일 수정
- 테스트 추가 및 실행
- lint와 format 수정
- 승인된 설계 안의 작은 리팩터링
- 로컬 전용 브랜치에 대한 Task Commit

### 11.3 승인 필요

- 새 Dependency 설치
- Architecture 변경
- DB Migration
- 외부 API 사용
- 개인정보 외부 전송
- 테스트 삭제 또는 기준 완화
- Phase 범위·완료 기준 변경

원격 저장소 반영은 승인 대상이 아니라 **하네스가 수행하지 않는 동작**이다.

### 11.4 승인 기록과 무효화

- 승인 요청과 결과는 SQLite에만 기록하며 대상 hash에 연결한다. YAML이나 Markdown에 적힌 승인 표현을 승인 기록으로 취급하지 않는다.
- **결과 승인에는 사용자가 확인한 코드 Revision과 보고서를 함께 연결한다.** 인수 이후 코드가 바뀌면 기존 인수를 그대로 사용하지 않는다.
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
2. **반려해도 폐기하지 않는다.** 코드·커밋·브랜치를 자동으로 되돌리지 않는다.
3. **사용자 입력을 먼저 보존한다.** 분류에 실패해도 사용자 피드백이 유실되지 않는다.
4. **유형을 곧바로 원인으로 취급하지 않는다.** 같은 유형이라도 기존 완료 기준 안인지 밖인지에 따라 처리가 다르다.
5. **AI는 분류를 제안만 한다.** 상태 전이는 사용자 확인 후 Orchestrator가 수행한다.

### 12.2 반려 유형과 처리

**승인 ①② 계획 반려** — 구현 전이므로 코드 영향이 없다.

| 유형 | 의미 | 재진입 지점 |
|---|---|---|
| `SCOPE` | 무엇을 만들지가 틀림 | Planner 전체 재계획 |
| `DECOMPOSE` | 범위는 맞으나 분해가 잘못됨 | Planner 재분해, 목표는 유지 |
| `CRITERIA` | 완료 기준이 부족하거나 틀림 | `acceptance_criteria`만 수정 |
| `RISK` | 위험 분류·Workflow가 부적절 | `risk_tags` 수정 후 Workflow 재선택 |
| `ORDER` | 의존성·순서가 틀림 | `depends_on`만 수정 |

**승인 ③ 고위험 결정 반려**

| 유형 | 의미 | 처리 |
|---|---|---|
| `DENY_ALT` | 이 방법은 불가, 다른 방법을 찾는다 | 거부된 방법을 제약으로 전달하고 재구현 |
| `DENY_STOP` | 이 Task를 중단한다 | Task `BLOCKED`. 범위 제외 여부를 함께 확인(8.6) |
| `DENY_REPLAN` | 계획 자체를 다시 세운다 | Phase `REPLAN_REQUIRED` |

**승인 ④⑤ 결과 반려** — 유형만으로 처리를 결정하지 않고, **기존 완료 기준에 포함된 항목인지**를 함께 판정한다.

| 유형 | 기존 완료 기준 안 | 기존 완료 기준 밖 |
|---|---|---|
| `NOT_WORKING` | 해당 Task를 `REWORK_REQUIRED`로 | — |
| `QUALITY` | 기존 기준 미달 → `REWORK_REQUIRED` | 새 기준 추가 → **완료 기준 변경 + 재승인** |
| `MISSING` | 원래 요구사항인데 구현 누락 → **기존 Task의 미완료**, `REWORK_REQUIRED` | 계획에 없던 요청 → **범위 변경 + 재승인** 후 새 Task |
| `WRONG_REQ` | Phase `REPLAN_REQUIRED` | Phase `REPLAN_REQUIRED` |
| `ABANDON` | Phase `ABANDONED` | Phase `ABANDONED` |

이 구분이 없으면 반려를 통해 승인 절차 없이 새 요구사항이 들어오는 경로가 생긴다. Task는 요구사항 단위이지 작업 시도 단위가 아니므로, 기존 기준 안의 재작업은 새 Task를 만들지 않고 해당 Task를 되돌린다. 시도 이력은 SQLite에 별도로 보존한다.

`ABANDON` 시 브랜치와 커밋을 보존하며 삭제는 사용자가 직접 한다. 폐기된 Phase에 의존하는 후속 Phase는 실행하지 않고 계획 수정을 요청한다.

### 12.3 반려 입력 흐름

사용자는 유형 이름을 알 필요가 없다.

```text
devh reject APR-004
   ↓
"무엇이 문제인가요?" 자연어 입력
   ↓
원문을 rejections에 즉시 저장 (status = RECORDED, 유형 미정)
   ↓
AI가 유형·대상 Task·기존 완료 기준 포함 여부를 분류 (status = CLASSIFIED)
   ↓
사용자에게 해석 결과 제시
   ↓
사용자 확인 → status = CONFIRMED → 상태 전이
```

**사용자 입력은 분류 이전에 저장한다.** 분류에 실패하거나 되묻는 중에도 피드백이 유실되지 않는다. 승인은 그동안 대기를 유지한다.

```text
다음과 같이 이해했습니다.

  대상    P1-T5 로컬 OCR 어댑터
  유형    동작하지 않음
  판정    P1-T5의 완료 기준 "OCR 실패와 정상 결과를 구분한다"에 해당합니다.
          기존 범위 안이므로 범위 변경 없이 재작업합니다.
  지시    OCR 실패 페이지가 빈 문자열로 반환되어 정상 결과와 구분되지 않음
  영향    P1-T5를 재작업 대상으로 되돌립니다. 나머지 7개 Task의 완료는 유지됩니다.
          Phase 인수 전에 통합 검증을 다시 수행합니다.
          P1-T5의 기존 커밋은 삭제하지 않습니다.

이대로 진행할까요?
```

- 사용자 확인 전에는 어떤 상태도 바꾸지 않는다. 확인 행위가 반려 기록의 근거가 된다.
- 대상 Task를 특정할 수 없거나 기존 기준 포함 여부가 모호하면 진행하지 않고 되묻는다.
- 분류를 건너뛰려면 `devh reject APR-004 --type quality --tasks P1-T5 --note "..."`를 사용한다.
- 반려 취소는 지원하지 않는다.

### 12.4 부분 반려

- 지정된 Task만 `REWORK_REQUIRED`로 전환하고 나머지 Task의 완료와 커밋은 유지한다.
- 재작업 Task가 완료되면 8.6의 Phase 통합 검증을 거쳐 결과 승인을 다시 요청한다.
- 재요청 시 결과 자료에 이전 반려 내용과 처리 결과를 포함한다.

### 12.5 재구현 범위와 재검증 범위

**두 범위는 다르다.** 아래 표는 **재구현** 범위를 정한다.

| 변경 대상 | 재구현 대상 |
|---|---|
| 특정 Task 정의만 변경 | 해당 Task |
| 공통 Domain Rule 변경 | 해당 Phase의 모든 Task |
| 실행 설정(검증 명령·필수 여부) 변경 | 해당 Phase의 모든 Task |
| 변경 없는 Task | 재구현하지 않음 |

판정은 `task_hash` 비교로 수행한다.

**그러나 `task_hash`는 작업 정의의 변경만 감지하며 코드 영향은 판단하지 못한다.** OCR Task가 반환 형식을 바꾸면 그 형식을 사용하는 분석·보고서 Task는 정의가 그대로여도 동작이 깨질 수 있다. 정의가 같다는 이유로 기존 테스트 결과를 재사용해서는 안 된다.

따라서 재검증은 다음 규칙을 따른다.

- 재작업한 Task는 해당 Workflow의 검증을 다시 수행한다.
- 변경 코드에 명백히 영향을 받는 후속 기능이 확인되면 그 범위도 재검증한다.
- **Phase 인수 전에는 재작업 여부와 무관하게 최종 코드에서 Phase 통합 검증을 수행한다(8.6.1).** 이것이 코드 영향 분석의 한계를 메우는 안전망이다.

### 12.6 반복 제한

- **계획 반려 3회 초과**: 자동 재계획을 중단하고 `PLAN_BLOCKED`로 보고한다.
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

### 13.3 실행 가능한 Task 소진

`DENY_STOP`이나 `FAILED`로 Task가 중단되면, 그 Task에 의존하는 후속 Task는 `PENDING`에 머문다. `PENDING`은 종결 상태가 아니므로 Phase가 무기한 `IN_PROGRESS`에 남는 교착이 발생한다.

이를 막기 위해 별도 중단 조건을 둔다.

> **`NO_RUNNABLE_TASK`** — `READY` 상태의 Task가 없고, `PENDING` Task의 선행 조건이 `BLOCKED`·`FAILED`로 인해 충족될 수 없으면 Run을 중단하고 사용자에게 보고한다.

보고 내용에는 차단된 Task, 그로 인해 진행할 수 없는 Task 목록, 가능한 선택지(차단 해제 / 범위 제외 후 재승인 / 재계획)를 포함한다. 이 상태에서도 결과 보고는 가능하지만 인수는 8.6의 조건을 충족해야 한다.

---

## 14. 데이터 모델

### 14.1 저장 위치와 원칙

```text
%LOCALAPPDATA%/AI-Development-Harness/{project.id}-{repo-path-hash}/
├─ state.db
├─ backups/        최근 10개 순환
└─ logs/           검증 명령 전체 로그
```

- **파생값을 중복 저장하지 않는다.** `validated_revision` 같은 값은 검사 이력에서 계산하며 `tasks`에 사본을 두지 않는다.
- **상태와 단계를 분리한다.** 진행 위치는 `current_step`으로 관리한다.
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
| `STALLED` | `NO_RUNNABLE_TASK`로 진행 불가 |
| `INTEGRATION_VALIDATING` | Phase 통합 검증 중 |
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
| `EXCLUDED` | 범위 변경 승인으로 Phase 범위에서 제외됨 |
| `FAILED` | 재시도 한도 초과·실행 환경 문제 |
| `COMPLETED` | 완료 조건 충족 및 커밋 확인 |

`FAILED`(시스템이 수행하지 못함), `REWORK_REQUIRED`(사용자가 수용하지 않음), `EXCLUDED`(승인을 거쳐 범위에서 뺌)는 모두 다른 상태다. 인수 조건에서 `EXCLUDED`만 미완료로 계산하지 않는다.

**Step**

```text
Fast      implement → quick_validate → commit
Standard  implement → pre_validate → review → post_validate → commit
Strict    implement → pre_validate → review → post_validate → commit
```

`step_status`는 `STARTED` / `PASSED` / `FAILED`다.

### 14.3 상태 전이

```text
Phase
  PLANNING → PLAN_PENDING_APPROVAL
  PLAN_PENDING_APPROVAL ─approve→ PLAN_APPROVED → IN_PROGRESS
                        ─reject→ PLAN_REJECTED → PLANNING
                                 (3회 초과) → PLAN_BLOCKED
  IN_PROGRESS ─실행 가능 Task 소진→ STALLED
  IN_PROGRESS ─모든 범위 내 Task COMPLETED→ INTEGRATION_VALIDATING
  INTEGRATION_VALIDATING ─통과→ RESULT_PENDING_APPROVAL
                         ─실패→ IN_PROGRESS (수정 Task)
  RESULT_PENDING_APPROVAL ─approve→ ACCEPTED
                          ─NOT_WORKING/QUALITY/MISSING(기준 안)→ RESULT_REJECTED → IN_PROGRESS
                          ─QUALITY/MISSING(기준 밖)→ 범위 변경 승인 → PLAN_PENDING_APPROVAL
                          ─WRONG_REQ→ REPLAN_REQUIRED → PLANNING
                          ─ABANDON→ ABANDONED
  STALLED ─차단 해제→ IN_PROGRESS
          ─범위 제외 승인→ IN_PROGRESS
          ─재계획→ REPLAN_REQUIRED

Task
  PENDING ─선행 완료→ READY ─Run 선택→ RUNNING
  RUNNING ─승인 대상 행동→ WAITING_APPROVAL ─approve→ RUNNING
                                           ─DENY_ALT→ RUNNING (제약 추가)
                                           ─DENY_STOP→ BLOCKED
  BLOCKED ─범위 제외 승인→ EXCLUDED
          ─사용자 해제→ READY
  RUNNING ─완료 조건 + 커밋 확인→ COMPLETED
  RUNNING ─재시도 한도 초과→ FAILED
  COMPLETED ─결과 반려(기준 안)→ REWORK_REQUIRED → RUNNING (attempt_no + 1)
```

`INTEGRATION_VALIDATING`을 거치지 않고 `RESULT_PENDING_APPROVAL`로 진입하는 경로는 없다.

### 14.4 스키마

```sql
-- 메타. project_id, repo_path, schema_version, harness_version, baseline 결과
CREATE TABLE schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- 프로젝트 단위 실행 소유권. 단일 행만 존재한다.
CREATE TABLE project_lock (
  id               INTEGER PRIMARY KEY CHECK (id = 1),
  run_id           TEXT NOT NULL,
  run_token        TEXT NOT NULL,   -- 실행마다 새로 생성하는 UUID
  owner_pid        INTEGER NOT NULL,
  owner_started_at TEXT NOT NULL,   -- PID 재사용 구분용 프로세스 시작 시각
  heartbeat_at     TEXT NOT NULL,
  acquired_at      TEXT NOT NULL
);

CREATE TABLE runs (
  id         TEXT PRIMARY KEY,
  run_token  TEXT NOT NULL,
  phase_id   TEXT NOT NULL,
  status     TEXT NOT NULL,          -- ACTIVE / SUSPENDED / CLOSED
  branch     TEXT NOT NULL,
  plan_hash  TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at   TEXT
);

CREATE TABLE phases (
  id                TEXT PRIMARY KEY,
  title             TEXT NOT NULL,
  status            TEXT NOT NULL,
  plan_hash         TEXT,
  roadmap_hash      TEXT,            -- 승인 ①의 대상
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
  step_status     TEXT,
  workflow        TEXT,
  workflow_reason TEXT,
  task_hash       TEXT NOT NULL,
  attempt_no      INTEGER NOT NULL DEFAULT 1,
  retry_count     INTEGER NOT NULL DEFAULT 0,
  reject_count    INTEGER NOT NULL DEFAULT 0,
  excluded_by     TEXT,              -- EXCLUDED 상태를 만든 승인 ID
  updated_at      TEXT NOT NULL,
  FOREIGN KEY (phase_id) REFERENCES phases(id)
);

CREATE TABLE task_attempts (
  id                 INTEGER PRIMARY KEY,
  task_id            TEXT NOT NULL,
  attempt_no         INTEGER NOT NULL,
  run_id             TEXT,
  started_at         TEXT NOT NULL,
  ended_at           TEXT,
  outcome            TEXT,           -- COMPLETED / REWORK / BLOCKED / FAILED
  commit_sha         TEXT,
  invalidated_reason TEXT,
  UNIQUE (task_id, attempt_no)
);

CREATE TABLE approvals (
  id                TEXT PRIMARY KEY,  -- APR-001
  kind              TEXT NOT NULL,     -- roadmap / phase_plan / risk_decision
                                       -- / phase_result / task_result / scope_change
  target_type       TEXT NOT NULL,     -- roadmap / phase / task
  target_id         TEXT NOT NULL,
  scope_hash        TEXT NOT NULL,     -- roadmap_hash / plan_hash / task_hash
  code_revision     TEXT,              -- 결과 승인에서 사용자가 확인한 코드
  report_path       TEXT,              -- 결과 승인에서 제시한 보고서
  requested_payload TEXT NOT NULL,
  requested_at      TEXT NOT NULL,
  decision          TEXT,              -- APPROVED / REJECTED / NULL(대기)
  decided_at        TEXT,
  valid             INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE rejections (
  id                TEXT PRIMARY KEY,  -- REJ-001
  approval_id       TEXT NOT NULL,
  status            TEXT NOT NULL,     -- RECORDED / CLASSIFIED / CONFIRMED
  user_text         TEXT NOT NULL,     -- 분류 이전에 먼저 저장한다
  recorded_at       TEXT NOT NULL,
  reject_type       TEXT,              -- 분류 전에는 NULL
  in_existing_scope INTEGER,           -- 기존 완료 기준 포함 여부
  resolution        TEXT,              -- REWORK / SCOPE_CHANGE / REPLAN / ABANDON
  ai_classification TEXT,
  confirmed_at      TEXT,
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
  scope         TEXT NOT NULL,         -- task / phase / baseline
  task_id       TEXT,                  -- scope=task일 때
  phase_id      TEXT,                  -- scope=phase일 때
  attempt_no    INTEGER,
  stage         TEXT NOT NULL,         -- quick / pre_review / post_review
                                       -- / phase_acceptance / baseline
  name          TEXT NOT NULL,
  command       TEXT NOT NULL,
  required      INTEGER NOT NULL,
  code_revision TEXT NOT NULL,
  plan_hash     TEXT,                  -- 검사 당시의 계획·검증 정책
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
  baseline_review_id INTEGER,
  result             TEXT NOT NULL,
  started_at         TEXT NOT NULL,
  ended_at           TEXT
);

CREATE TABLE review_findings (
  id                    INTEGER PRIMARY KEY,
  review_id             INTEGER NOT NULL,
  severity              TEXT NOT NULL,
  finding_ref           TEXT,
  file                  TEXT,
  description           TEXT NOT NULL,
  required_change       TEXT,
  resolved_at           TEXT,
  resolved_in_review_id INTEGER,
  FOREIGN KEY (review_id) REFERENCES reviews(id)
);

CREATE TABLE commit_intents (
  id            TEXT PRIMARY KEY,
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

CREATE TABLE plan_snapshots (
  snapshot_hash   TEXT PRIMARY KEY,
  kind            TEXT NOT NULL,       -- roadmap / phase
  phase_id        TEXT,                -- kind=roadmap이면 NULL
  work_items_yaml TEXT NOT NULL,
  domain_rules_md TEXT NOT NULL,
  project_yaml    TEXT NOT NULL,
  created_at      TEXT NOT NULL
);
```

주요 변경은 다음과 같다.

| 테이블 | 변경 | 이유 |
|---|---|---|
| `validations` | `plan_hash` 추가, `scope`로 Task·Phase·baseline 구분 | 검사 당시의 검증 정책을 불변 기록으로 연결. Phase 통합 검증과 baseline도 같은 테이블에 기록 |
| `approvals` | `scope_hash`로 통합, `code_revision`·`report_path` 추가, `roadmap` 대상 추가 | 결과 승인이 어떤 코드와 보고서를 대상으로 했는지 기록. 전체 Phase 계획 승인 대상 표현 |
| `rejections` | `status`·`in_existing_scope`·`resolution` 추가, `reject_type` NULL 허용 | 분류 이전에 사용자 원문을 먼저 저장. 기존 범위 안팎 구분 |
| `project_lock` | 신설 | 소유권 획득을 원자적으로 수행 |
| `tasks` | `excluded_by` 추가 | 범위 제외 승인과 연결 |
| `plan_snapshots` | `kind` 추가 | roadmap 스냅샷 수용 |

### 14.5 Revision과 Hash

**코드 Revision** — 임시 index로 작업 폴더 전체의 Git tree hash를 계산한다.

```bash
GIT_INDEX_FILE=<임시파일> git add -A
GIT_INDEX_FILE=<임시파일> git write-tree
```

- `.gitignore`를 그대로 따르므로 제외 규칙을 다시 구현하지 않는다.
- 새 파일, 삭제, 이름 변경, 실행 권한 변경이 모두 반영된다.
- 사용자의 스테이징 영역을 건드리지 않는다.
- 추가 제외 대상은 `.dev-harness/reports/`다.
- 프로젝트는 Git 저장소여야 한다. 아니면 `init`에서 안내하고 중단한다(3.4).

**task_hash** — Task 정의만으로 계산한다. 작업 정의의 변경만 감지하며 코드 영향은 판단하지 못한다(12.5).

- 포함: `id`, `title`, `acceptance_criteria`, `requirement_refs`, `domain_rule_refs`, `risk_tags`, `depends_on`
- 제외: 실행 상태, 재시도 횟수, 승인 여부

**plan_hash** — Phase 단위. 승인 ②③④를 여기에 연결한다.

- 포함: Phase 정의, 소속 Task의 `task_hash` 정렬 목록, 공통 Domain Rule 본문, 참조된 Domain Rule 본문, `validation`·`workflow_routing`·`approval` 설정
- 제외: 실행 상태, 로그, 보고서, `plan.md`의 서술 문장

**roadmap_hash** — 전체 Phase 계획. 승인 ①의 대상이다.

- 포함: 모든 Phase의 id, 목표, 순서, 종료 조건
- 제외: 각 Phase의 Task 상세

Phase 단위 `plan_hash`와 분리했으므로, 한 Phase의 Task를 상세화해도 전체 계획 승인이 무효화되지 않는다. 반대로 Phase 순서나 목표가 바뀌면 전체 계획 승인을 다시 받는다.

### 14.6 동시 실행 제어

PID와 heartbeat만으로는 중복 실행이 막히지 않는다. 두 프로세스가 동시에 "실행 중인 Run 없음"을 읽고 각각 시작할 수 있기 때문이다.

**소유권의 확인과 획득을 하나의 원자적 처리로 수행한다.**

```sql
BEGIN IMMEDIATE;
INSERT INTO project_lock (id, run_id, run_token, owner_pid, owner_started_at,
                          heartbeat_at, acquired_at)
VALUES (1, ?, ?, ?, ?, ?, ?);
COMMIT;
```

`id = 1` 제약으로 단일 행만 존재하므로, 다른 프로세스가 이미 잡았으면 INSERT가 실패한다. 조회 후 판단하는 구조를 쓰지 않는다.

- **PID만으로 프로세스를 식별하지 않는다.** PID는 재사용되므로 `run_token`(UUID)과 프로세스 시작 시각을 함께 기록해 구분한다.
- **heartbeat가 끊겼다는 이유만으로 기존 프로세스가 종료됐다고 판단하지 않는다.** 절전이나 디스크 지연으로도 끊긴다. 자동 탈취하지 않고 상황을 표시한 뒤 사용자 확인을 받는다.
- 강제 해제는 별도 명령(`devh unlock --force`)으로만 가능하다.
- **기존 에이전트·테스트 자식 프로세스가 남아 있는지 확인한다.** 테스트 러너가 살아서 파일을 쓰고 있으면 재개가 충돌한다.

### 14.7 재개

```text
1. project_lock 확인 및 소유권 획득 시도
2. runs에서 해당 프로젝트의 SUSPENDED Run 조회
3. schema_meta.repo_path와 현재 저장소 경로 대조
4. runs.branch와 현재 HEAD 대조
5. commit_intents에 PENDING이 있으면 커밋 복구 절차 수행
6. plan_snapshots의 hash와 현재 계획 파일 hash 대조
7. 코드 Revision 재계산 후 마지막 체크포인트와 대조
8. tasks.current_step / step_status로 재개 지점 결정
```

| 상황 | 처리 |
|---|---|
| 체크포인트와 코드·계획이 같음 | 완료가 확인된 단계는 재사용하고 다음 단계로 진행 |
| 다른 Branch 또는 예상하지 못한 코드 변경 | `BLOCKED`, 사유 `STATE_MISMATCH` |
| 완료 기준·규칙 등 계획 변경 | `REPLAN_REQUIRED` |
| Commit은 성공했으나 DB 기록이 없음 | 15.2에 따라 복구 |

#### 14.7.1 STARTED 단계의 재개 규칙

`step_status = STARTED`인 단계를 일괄 재실행하지 않는다. 단계마다 부작용의 성격이 다르다.

| 단계 | 재개 규칙 |
|---|---|
| **Review** | 부작용이 없다. 현재 입력을 다시 구성해 재실행한다 |
| **Validation** | 잔여 프로세스, 점유 포트, 임시 파일, 테스트 DB 상태를 먼저 확인한다. 정리된 것을 확인한 뒤 재실행한다 |
| **Implement** | **자동 재실행하지 않는다.** 부분 작성된 파일이 남아 있을 수 있으므로 마지막 체크포인트와의 차이를 먼저 확인하고, 예상하지 못한 변경은 `STATE_MISMATCH`로 안내한다. 확인 후 이어서 수행한다 |

Implement를 무조건 재실행하면 "자동으로 덮어쓰지 않는다"는 원칙과 충돌한다.

- 미커밋 변경이 있다는 이유만으로 오류로 처리하지 않는다.
- 불일치 시 자동으로 파일을 덮어쓰거나 Git을 되돌리지 않는다.
- 재개는 Retry 횟수나 승인 기록을 초기화하지 않는다.
- 사용자의 수동 변경이 Task 범위에 속하는지 확인한다.

### 14.8 백업과 스키마 버전

- Task 완료와 정상 중단 시 SQLite 백업 API로 사본을 만들고 최근 10개를 순환 보관한다.
- `schema_meta.schema_version`을 기록한다. 버전이 맞지 않으면 실행하지 않고 안내한다. 자동 마이그레이션은 v1.1로 미룬다.

---

## 15. Git 전략

### 15.1 하네스의 Git 사용 범위

```text
main                          ← 하네스가 건드리지 않음
 └─ harness/phase/P1-...      ← 하네스 전용 로컬 브랜치
     ├─ commit: P1-T1
     ├─ commit: P1-T2
     └─ commit: P1-T3
```

| 동작 | 정책 |
|---|---|
| 쓰기 대상 | `harness/phase/<phase-id>` 전용 로컬 브랜치 한정 |
| main·기존 브랜치 직접 커밋 | 금지 |
| 브랜치 생성 | 해당 Phase 계획에 유효한 승인이 있을 때만 |
| Task 커밋 | 승인된 계획 범위 안의 Task에 한해, 검증 통과 후 자동 |
| 승인이 없거나 무효화된 상태 | 커밋하지 않고 승인 대기로 정지 |
| **원격 저장소 조작** | **수행하지 않음** (15.3) |
| Phase 완료 처리 | 커밋이 있어도 8.6의 인수 조건 충족 전에는 완료가 아님 |

**커밋은 작업의 저장이고 완료는 사용자의 인수다.** 커밋은 로컬 전용 브랜치에만 쌓이므로 `git branch -D`로 흔적까지 제거할 수 있다.

Task 커밋은 Git 편의 기능이 아니라 하네스의 상태 저장 메커니즘이다. 부분 반려(12.4), 재개(14.7), 커밋 복구(15.2)가 모두 Task 단위 커밋을 전제로 한다. 따라서 끄는 옵션을 제공하지 않는다.

### 15.2 Task Commit과 중단 복구

```text
Workflow별 최종 검증 조건 충족
→ SQLite에 commit_intents 기록 (PENDING)
→ 해당 스냅샷으로 Git Commit 생성
→ 생성된 Commit의 부모·내용 및 작업 폴더 확인
→ SQLite 트랜잭션으로 Commit SHA와 COMPLETED 기록
→ 다음 Task
```

- Commit 메시지 메타데이터에 Run ID, Task ID, Commit 작업 식별자를 남긴다.
- Commit 직전 코드가 바뀌었으면 완료 절차를 멈추고 새 Revision에서 필요한 검사를 수행한다.
- `PENDING`에서 재개하면 해당 식별자·부모·내용을 가진 Commit이 실제 브랜치에 있는지 확인한다. 일치하면 기존 Commit을 연결하고 DB 기록만 복구한다.
- 다른 Commit이나 예상하지 못한 변경이 있으면 `STATE_MISMATCH`로 중단한다. 중복 Commit을 만들지 않는다.

### 15.3 원격 저장소 반영

**하네스는 push, merge, PR 생성, 배포를 수행하지 않는다.** 관련 코드와 설정을 갖고 있지 않으므로 실수로 원격을 조작할 가능성이 없다. 승인으로 막는 것보다 강한 보장이다.

Phase 인수 후 원격 반영은 사용자가 하네스 바깥에서 직접 수행한다.

```text
devh close P1        Phase 인수 (로컬 브랜치에 커밋 완료 상태)
        ↓
사용자가 결과 확인
        ↓
기존 github-push 스킬 등으로 원하는 시점에 push / merge
```

하네스는 인수 완료 시 브랜치 이름과 커밋 범위를 안내한다. 그 이후의 처리 방식(squash 여부, 대상 브랜치, PR 생성)은 사용자가 정한다.

---

## 16. 산출물과 보고

### 16.1 Task 완료 기록

- Task ID와 상태, 적용 Workflow, Risk Tag와 선택 근거
- 승인된 계획 hash와 최종 코드 Revision
- Git commit SHA와 변경 파일 목록
- Review 결과 요약, 검사한 Revision, Delta Review의 이전 기록 연결
- Validation 명령별 결과와 검사한 Revision·계획 hash, 정책상 생략한 검사와 사유
- 재시도 횟수, 사용된 승인 ID, 알려진 제한사항

### 16.2 Phase 결과 자료

Phase 결과 승인은 **사용자가 실제로 무엇이 되는지 판단할 수 있어야** 성립한다.

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

## Phase 통합 검증

- 대상 코드 Revision: `a1b2c3d`
- integration: PASS / build: PASS
- baseline 대비 신규 실패: 없음

## 실행하지 않은 검증

- 실제 브라우저 화면 확인: 수행하지 않음
- 오래된 등기 양식: 샘플 미확보로 미검증

## 사용자가 직접 확인할 항목

- 업로드 화면의 오류 메시지 문구
- 스캔 문서 처리 대기 시간의 체감 수준

## 남은 위험

- OCR 품질이 문서 상태에 따라 크게 달라질 수 있음

## 실행 요약

- 완료 Task: 8/8 (범위 제외 0)
- 자동 재시도: 2회
- 사용자 승인: 1건
- 반려: 1건 (P1-T5, 동작하지 않음 / 기존 범위 안 → 재작업 후 완료)

## Git

- Branch: harness/phase/P1-document-processing (로컬)
- Commit 범위: abc123 .. def456
- 원격 반영은 수행하지 않았습니다. 필요 시 직접 push하십시오.
```

- 보고서는 SQLite 실행 기록과 Git 정보로 생성한다.
- 자동으로 확인하지 못한 항목은 반드시 표시한다.
- 미완료·차단·범위 제외 Task가 있으면 항목과 사유를 명시한다. **다만 보고서 기재가 8.6의 인수 조건을 대신하지 않는다.**

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
devh unlock --force
devh close <phase-id>
devh report <phase-id>
```

push, merge, PR 관련 명령은 없다.

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

Slash Command는 기존 명령을 먼저 식별한다. 자연어로 입력된 경우 계획과 SQLite 상태에서 대상을 확인해 해당 명령으로 연결하며, 대상을 특정할 수 없으면 확인한다.

---

## 18. 실행 예시 — 부동산 등기부등본 분석

### 18.1 초기화와 검토

```text
devh init Draft/registry-analysis-plan.md
devh review
```

`init`이 baseline 검증을 실행해 현재 코드의 테스트 상태를 기록한다. 검토 리포트가 다음을 보고한다고 가정한다.

```text
누락  OCR 실패 시 결과 표시 방식이 정의되지 않음
누락  원본 문서 보관 정책이 없음
모순  "외부 전송 없음"과 "클라우드 OCR 활용" 서술이 충돌 (3장 / 7장)
모호  "위험 신호"의 판정 주체가 규칙 엔진인지 LLM인지 불명확
```

### 18.2 계획과 Workflow

```text
P1 — 문서 입력과 텍스트 추출
P2 — 등기 항목 구조화
P3 — 위험 분석과 보고서
P4 — UI 통합과 품질 검증
```

전체 Phase 목표·순서를 승인 ①로 한 번 확인하고(`roadmap_hash`), P1의 Task 계획을 승인 ②로 확인한다.

| Task | 위험 | Workflow |
|---|---|---|
| P1-T1 기본 구조 | 낮음 | Fast |
| P1-T2 PDF 검증 | 개인정보 입력 | Strict |
| P1-T3 텍스트 추출 | 보통 | Standard |
| P1-T5 OCR 어댑터 | 민감문서 처리 | Strict |

### 18.3 Strict Task 실행

`P1-T5 로컬 OCR 어댑터`의 Context는 요구사항, 관련 Domain Rule, 허용 경로로 구성한다.

Pre-review Validation 통과 후 Strict Review에서 다음을 지적한다.

```text
CHANGES_REQUESTED
1. OCR 실패 페이지가 빈 문자열로 반환된다
2. 빈 문자열이 정상 추출 결과와 구분되지 않는다
3. confidence 범위가 검증되지 않는다
```

Developer가 상태를 `SUCCESS` / `PARTIAL` / `FAILED`로 분리한다. Delta Review와 Post-review Validation을 통과하면 15.2 절차로 로컬 커밋한다.

### 18.4 실행 중 승인과 반려

```text
WAITING_APPROVAL

요청    외부 OCR API와 SDK 도입
영향    원본의 외부 전송 가능성 / API 비용 / API Key 필요 / 개인정보 처리 정책 필요
추천    MVP에서는 로컬 OCR 유지
```

사용자가 `DENY_ALT`로 반려하고 "로컬 OCR로 유지"를 지시하면, 거부된 방법을 제약으로 전달해 재구현한다.

### 18.5 Phase 통합 검증과 인수

모든 Task가 `COMPLETED`가 되면 `INTEGRATION_VALIDATING`으로 전환해 최종 코드에서 `post_review` 명령을 다시 실행한다. 통과하면 16.2 형식의 결과 자료를 제시한다.

사용자가 P1-T5만 부분 반려하면, 완료 기준에 포함된 항목인지 판정한 뒤 해당 Task가 `REWORK_REQUIRED`로 돌아간다. 재작업 완료 후 **통합 검증을 다시 수행하고** 결과 승인을 요청한다.

인수가 끝나면 하네스는 브랜치 이름과 커밋 범위를 안내하고 종료한다. 원격 반영은 사용자가 직접 수행한다.

---

## 19. 하네스 개발 Phase

### Phase 0 — Runner Skeleton (AI 호출 없음)

AI를 연결하기 전에 상태 기계와 승인·재개를 결정론적으로 검증한다.

- Python CLI 구조와 `devh` 진입점
- `project.yaml` 스키마 검증
- SQLite 스키마 생성과 상태 전이 구현
- 코드 Revision, `task_hash`, `plan_hash`, `roadmap_hash` 계산
- 승인 대기·승인·반려 처리와 원문 선저장
- `project_lock` 원자적 획득과 중복 실행 차단
- 중단과 재개, Step별 재개 규칙
- `NO_RUNNABLE_TASK` 교착 감지
- 가짜 Adapter로 계획·구현·리뷰 결과를 주입해 전 흐름 통과

### Phase 0.5 — 실행 경계 스파이크 (최우선)

실제 Codex CLI를 최소한으로 연결해 **2.2의 권한 경계가 실제로 집행되는지** 확인한다. 이 결과가 부정적이면 실행 구조를 바꿔야 하므로 뒤로 미루지 않는다.

- 승인 대상 명령을 실제 실행 전에 차단할 수 있는가
- 허용 경로 밖 파일 수정을 차단할 수 있는가
- 외부 네트워크 전송을 차단하거나 최소한 감지할 수 있는가
- 차단이 불가능한 동작은 무엇인가

차단할 수 없는 동작은 수동 처리 대상으로 문서에 명시하고, 해당 범위의 승인 정책을 조정한다.

### Phase 1 — Foundation

- `plan.md`, `work-items.yaml`, `domain-rules.md` 구조와 참조 검증
- 실행 입력 사본 저장과 로컬 DB 백업
- Git 저장소 정합성 검사와 재개 판단
- `init`(baseline 검증 포함), `status`, `resume`, `unlock` 명령
- 프로젝트 탐색과 프로젝트별 상태 구분

### Phase 2 — Planning

- Markdown 기획서 읽기
- 기획 검토 리포트 생성 (`devh review`)
- 전체 Phase 계획과 현재 Phase Task 분해
- Acceptance Criteria, 원문·Domain Rule 참조 생성
- Domain Rule 추출과 Risk Tag 제안
- 계획 승인·반려와 계획 hash

### Phase 3 — Execution

- Codex CLI Adapter 정식 연결
- `/development`를 Core CLI에 연결
- Developer·Reviewer Context 구성
- Risk Tag 기반 Workflow 선택과 실행 중 위험 갱신
- Revision에 연결된 Review·Validation Runner와 완료 판정
- Retry 제한
- Task Commit과 커밋 직후 중단 복구

### Phase 4 — Delivery

- Phase 통합 검증과 인수·반려
- Phase 결과 자료 생성
- 반려 분류와 범위 변경 분기
- 설치·연결·초기화 사용 안내
- Decision Desk Phase 하나 dogfooding

---

## 20. MVP 완료 조건

아래는 앞으로 수행할 검증 기준이며 실제 테스트 결과가 아니다.

**설치와 초기화**

- [ ] 한 번 설치한 뒤 여러 프로젝트에서 같은 `devh`를 사용할 수 있다
- [ ] 서로 다른 프로젝트의 설정·상태·승인이 섞이지 않는다
- [ ] `init`이 baseline 검증 결과를 기록한다
- [ ] Git 저장소가 아니면 안내하고 중단한다

**계획**

- [ ] 기획 문서에서 누락·모순·모호 항목을 리포트로 제시한다
- [ ] 전체 Phase 계획과 현재 Phase Task 분해를 생성한다
- [ ] 전체 계획 승인과 Phase 계획 승인을 서로 다른 hash로 관리한다
- [ ] 존재하지 않는 참조나 순환 의존성이 있는 계획은 실행하지 않는다
- [ ] ID 문자열을 파싱해 계층을 유추하지 않는다

**실행**

- [ ] 계획 승인 전에는 제품 코드 구현을 시작하지 않는다
- [ ] 의존성이 완료된 Task만 실행한다
- [ ] Orchestrator가 Workflow를 선택하고 근거를 기록한다
- [ ] 버그 수정을 Fast로 처리하지 않는다
- [ ] Pre-review Validation 실패 시 Reviewer를 호출하지 않는다
- [ ] 필수 검증의 실패·미실행·중단을 성공으로 처리하지 않는다
- [ ] 검토한 코드, 검증한 코드, 승인 대상 코드가 일치한다
- [ ] 실행 가능한 Task가 소진되면 교착 없이 중단하고 보고한다

**승인과 반려**

- [ ] 승인 대상 행동에서 실행을 중단한다
- [ ] 무응답을 자동 승인으로 처리하지 않는다
- [ ] 에이전트가 승인 기록이나 완료 기준을 바꿔 통과하지 못한다
- [ ] 실제 실행 경계에서 차단되지 않는 동작을 파악하고 수동 처리로 명시한다
- [ ] 반려 원문을 분류 이전에 저장한다
- [ ] 기존 완료 기준 밖의 반려를 범위 변경 승인으로 분기한다
- [ ] 부분 반려 시 지정 Task만 재작업 대상이 된다
- [ ] 반려해도 코드·커밋·브랜치를 자동으로 되돌리지 않는다

**인수**

- [ ] `BLOCKED`·`FAILED` Task가 남아 있으면 Phase를 인수할 수 없다
- [ ] 범위에서 제외하려면 완료 기준 변경과 재승인을 거친다
- [ ] Phase 인수 전에 최종 코드에서 통합 검증을 수행한다
- [ ] 결과 승인에 사용자가 확인한 코드 Revision을 연결한다
- [ ] 사용자 인수 전에는 Phase를 완료로 처리하지 않는다

**상태와 복구**

- [ ] 실행 상태와 승인 기록을 SQLite만으로 관리한다
- [ ] 두 프로세스가 동시에 같은 프로젝트를 실행하지 못한다
- [ ] heartbeat 중단만으로 기존 실행을 자동 탈취하지 않는다
- [ ] 재부팅 후 Run을 재개하며, Implement 단계를 자동 재실행하지 않는다
- [ ] Commit 직후 DB 저장 전 중단을 복구하며 중복 Commit을 만들지 않는다
- [ ] 사용자의 기존 변경과 다른 프로젝트 파일을 훼손하지 않는다

**산출물**

- [ ] Task마다 Git commit과 검증 결과를 연결할 수 있다
- [ ] Phase 결과 자료에 실행 방법, 완료 기준 충족 근거, 통합 검증 결과, 미검증 항목, 반려 이력을 포함한다
- [ ] 하네스가 push·merge·배포를 수행하지 않는다
- [ ] Decision Desk의 실제 Phase 하나를 처음부터 끝까지 실행할 수 있다

---

## 21. MVP 이후 확장 순서

1. **자연어 수정 요청** — 작은 요청을 Task로 변환해 같은 실행 엔진에서 처리
2. 요구사항 커버리지 자동 검사 (6.3)
3. 코드 의존성 기반 재검증 범위 계산 (12.5의 정밀화)
4. 추가 AI Provider Adapter
5. Task별 Git worktree
6. 독립 Failure Analyst
7. Security Reviewer 및 Domain Reviewer
8. Agent Registry 외부 설정
9. Workflow DAG 사용자 설정
10. 병렬 Task 실행
11. Web Dashboard
12. Project Kickoff Harness 연동

원격 저장소 조작은 확장 목록에 두지 않는다. 하네스의 책임 범위 밖으로 정했다(15.3).

---

## 22. 결정 근거와 개정 이력

설계 결정과 근거는 `archive/harness-decision-record.md`에 D-01 ~ D-33으로 보존되어 있다. 반려 경로와 데이터 모델의 설계 과정은 같은 폴더의 `rejection-path-spec.md`, `data-model-spec.md`에 남아 있다.

| 날짜 | 변경 | 사유 |
|---|---|---|
| 2026-09-14 | v0.5 확정 (D-01 ~ D-33) | v0.4와 v0.1의 설계 축 11개 충돌을 정리하고 반려 경로·데이터 모델·기획 검토를 신설 |
| 2026-09-14 | v0.6 — 원격 조작 제거 | Task 커밋은 상태 저장 메커니즘이므로 유지하되, push·merge 기능 자체를 없애 실수 가능성을 제거. 원격 반영은 사용자가 별도 스킬로 수행 |
| 2026-09-14 | v0.6 — Phase 인수 조건 신설 (8.6) | 보고 가능 조건과 인수 조건이 분리되지 않아 필수 검증 실패 Task가 남아도 인수가 가능했음 |
| 2026-09-14 | v0.6 — 통합 검증 게이트 (8.6.1) | `task_hash`는 코드 영향을 판단하지 못하므로, 정의가 같다는 이유로 기존 검사 결과를 재사용하면 거짓 통과가 발생 |
| 2026-09-14 | v0.6 — `NO_RUNNABLE_TASK` (13.3) | `DENY_STOP` 이후 후속 Task가 `PENDING`에 남아 Phase가 무기한 진행 중으로 머무는 교착 |
| 2026-09-14 | v0.6 — 스키마 보완 (14.4) | 검증에 계획 hash, 결과 승인에 코드 Revision, 전체 계획 승인 대상이 연결되지 않아 유효성 판정 근거가 없었음 |
| 2026-09-14 | v0.6 — 소유권·재개 규칙 (14.6~14.7) | 조회 후 시작은 원자적이지 않아 중복 실행 가능. Implement 단계 자동 재실행은 덮어쓰기 금지 원칙과 충돌 |
| 2026-09-14 | v0.6 — 실행 경계 검증 분리 (2.2, Phase 0.5) | 가짜 Adapter로는 실제 권한 차단을 검증할 수 없음. 프로젝트 최대 미검증 가정이므로 최우선 확인 |
| 2026-09-14 | v0.6 — Fast에서 버그 수정 제외 (8.1) | `validation.quick`이 lint뿐인데 버그 수정이 Fast 대상이어서 회귀 테스트 없이 커밋 가능했음 |
| 2026-09-14 | v0.6 — 반려 유형과 원인 분리 (12.2) | `MISSING`·`QUALITY`가 기존 범위 안인지 밖인지 구분되지 않아 승인 없이 범위가 늘어나는 경로 존재 |
| 2026-09-14 | v0.6 — `init` baseline 기록 (3.4) | 기존 프로젝트에서 변경 전 테스트 상태를 모르면 실패 원인을 귀속할 수 없음 |

미결 항목은 다음과 같다.

| ID | 내용 | 상태 |
|---|---|---|
| O-02 | 자동 수정 한도 2회 vs 3회 | 기본값 2회로 시작하고 실행 데이터로 재검토 |
| O-03 | Codex 호출 방식 (CLI subprocess vs SDK) | CLI subprocess로 고정, 실사용에서 판단 |
| O-04 | 신규·기존 프로젝트별 초기 분석 절차 분리 | baseline 기록만 먼저 도입. 전체 분리는 실사용 후 판단 |
