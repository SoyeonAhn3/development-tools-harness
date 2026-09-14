# AI Development Harness 기획서

> 상태: Draft  
> 버전: 0.1  
> 작성일: 2026-09-13  
> 첫 적용 후보: Decision Desk  
> 목적: 중요한 결정만 사람이 승인하고, 나머지 개발 과정을 AI와 하네스가 반복 실행하는 범용 반자동 개발 시스템을 정의한다.

---

## 1. 개요

AI Development Harness는 완성된 기획을 실제 프로그램으로 구현하기 위해 개발 계획 수립, Phase 분해, 작업 실행, 코드 리뷰, 테스트, 재시도, Git 관리, 사용자 승인 및 진행 상태 추적을 통합하는 범용 개발 오케스트레이션 시스템이다.

이 시스템의 목표는 AI에게 프로젝트 전체를 한 번에 맡기는 것이 아니다. 프로젝트를 검증 가능한 단위로 나누고, AI가 허용된 범위에서 개발하게 하며, 하네스가 상태·권한·검증·산출물을 통제하는 것이다.

핵심 운영 원칙은 다음과 같다.

> AI는 계획을 제안하고 코드를 개발하며, Orchestrator Engine은 실행을 통제하고 증거를 기록한다. 사용자는 되돌리기 어렵거나 결과에 큰 영향을 미치는 결정만 승인한다.

---

## 2. Project Kickoff Harness와의 관계

Project Kickoff Harness와 Development Harness는 처음에는 독립 프로젝트로 개발한다.

```text
Project Kickoff Harness
아이디어 → 인터뷰 → 요구사항 → 설계 → 위험 검토 → 개발 준비

Development Harness
개발 계획 → Phase → Feature/Task → 구현 → 리뷰 → 검증 → 인수
```

두 하네스는 나중에 중간 계약 파일로 연결한다.

```text
Project Kickoff Harness
        ↓ export
development_brief.yaml
        ↓ import
Development Harness
```

Development Harness는 Kickoff Harness 없이도 동작해야 한다. 사용자가 작성한 Markdown 기획서 또는 직접 작성한 `development_brief.yaml`을 입력으로 받을 수 있어야 한다.

Decision Desk에 적용할 때는 다음 조합을 사용한다.

```text
Development Harness
        +
Decision Desk Project Profile
```

다른 프로젝트에서는 하네스를 변경하지 않고 Profile만 교체한다.

```text
Development Harness
        +
AI Analytics Project Profile
```

---

## 3. 목표와 제외 범위

### 3.1 목표

- 완성된 기획을 전체 Phase 계획으로 변환한다.
- 현재 Phase를 Feature와 실행 가능한 Task로 상세 분해한다.
- Task의 의존성과 실행 가능 상태를 계산한다.
- 역할별 AI Agent를 설정에 따라 호출한다.
- 코드 수정 권한과 위험 행동을 정책으로 통제한다.
- Reviewer와 실제 테스트 명령으로 구현을 검증한다.
- 실패 원인을 분류하고 제한된 횟수만 자동 재시도한다.
- 중요한 결정에서만 실행을 멈추고 사용자 승인을 요청한다.
- 프로세스 또는 컴퓨터 재시작 후 작업을 이어서 실행한다.
- 코드, 계획, 리뷰, 테스트 및 승인 이력을 추적 가능하게 남긴다.
- Phase별 산출물과 최종 개발 보고서를 생성한다.

### 3.2 초기 제외 범위

- 제품 기획 인터뷰 전체 자동화
- 무제한 자율 개발
- 사용자 승인 없는 Production 배포
- 첫 버전부터 여러 Agent의 병렬 코드 수정
- 모든 AI 공급자 동시 지원
- 복잡한 웹 대시보드
- 테스트 없이 AI 판단만으로 완료 처리

---

## 4. 핵심 개념

### 4.1 계획 구조, 실행 순서, 작업 방식을 분리한다

```text
계획 구조
기획 → Phase → Feature → Task

실행 순서
Task 간 depends_on 의존성 그래프

Task 작업 방식
Planner → Developer → Reviewer → Validator
```

세 구조는 서로 대체하지 않는다. Phase와 Feature는 프로젝트를 이해하고 관리하기 위한 계층이며, 의존성 그래프는 실제 실행 순서를 결정한다. Workflow는 Task 하나를 어떤 방식으로 완료하는지를 정의한다.

### 4.2 Work Item

Phase, Feature, Ticket, Task, Bug, Refactor, Migration을 하네스 내부에서는 공통적으로 Work Item이라고 부른다.

```yaml
id: P1-F2-T1
type: task
title: PDF 텍스트 추출기 구현
parent_id: P1-F2
executable: true
depends_on:
  - P1-F1-T2
status: ready
```

- `parent_id`: 문서 및 관리상의 포함 관계
- `depends_on`: 실제 실행 순서를 정하는 관계
- `executable`: 직접 Agent Workflow를 실행할 수 있는지 여부
- Phase와 Feature는 일반적으로 자식 상태를 집계한다.
- Task와 일부 Ticket은 일반적으로 직접 실행된다.

### 4.3 Agent, Skill, Tool, Workflow

```text
Agent        = 판단하고 행동하는 실행 주체
Skill        = Agent가 특정 작업을 수행하는 절차와 지식
Tool         = 파일 편집, 명령 실행, Git 등 실제 기능
Workflow     = Agent와 검증 단계가 연결되는 실행 순서
Orchestrator = Workflow와 상태, 권한, 재시도를 통제하는 프로그램
```

Skill은 Agent 자체가 아니다. 한 Agent는 여러 Skill을 사용할 수 있고, 하나의 Skill을 여러 Agent가 사용할 수 있다.

초기에는 같은 AI 모델을 역할별 독립 세션으로 실행할 수 있다.

```text
동일한 AI 모델
├─ Planner 역할 세션
├─ Developer 역할 세션
├─ Reviewer 역할 세션
└─ Failure Analyst 역할 세션
```

---

## 5. 파일 형식별 책임

### 5.1 YAML

프로그램이 구조적으로 해석하고 검증해야 하는 설정에 사용한다.

- Project Profile
- Agent Registry
- Workflow
- Work Item
- Validation
- Permission 및 Approval Policy
- Definition of Done의 기계적 조건

모든 YAML은 JSON Schema 또는 Pydantic 모델로 검증한다. 알 수 없는 필드나 잘못된 값은 조용히 무시하지 않고 오류로 처리한다.

### 5.2 Markdown

사람과 AI가 읽어야 하는 설명과 판단 근거에 사용한다.

- 기획서
- Architecture
- Domain Rules
- Phase 계획 설명
- Task 구현 계획
- Agent Skill 지침
- 리뷰 보고서
- Phase 완료 보고서
- 알려진 제한사항

`SKILL.md`는 상단 YAML frontmatter에 이름과 트리거 정보를 두고, 본문 Markdown에 실제 절차를 기록할 수 있다.

### 5.3 SQLite

자주 변경되는 실행 상태를 저장한다.

- Run
- 현재 Phase 및 Task 상태
- Workflow Step
- Attempt와 재시도 횟수
- 승인 대기 상태
- Event
- Artifact 위치
- Validation 결과

SQLite는 메모리 모드가 아닌 파일로 저장하며, 프로세스 및 컴퓨터 재시작 이후에도 `resume`할 수 있어야 한다.

프로젝트가 OneDrive에 있을 수 있으므로 실행 중인 DB는 기본적으로 다음과 같은 로컬 경로에 저장한다.

```text
%LOCALAPPDATA%/AI-Development-Harness/{project-id}/state.db
```

### 5.4 Git

실제 제품 산출물과 승인된 개발 기준선을 관리한다.

- 소스 코드
- 테스트
- 설정
- Migration
- Architecture 및 Domain 문서
- 승인된 Project Profile과 Work Item
- Phase 최종 보고서

---

## 6. 시스템 아키텍처

```text
사용자
  ↓
CLI / Slash Command / 향후 UI
  ↓
Orchestrator Engine
  ├─ Project Loader
  ├─ Work Item Scheduler
  ├─ Workflow Runner
  ├─ Context Builder
  ├─ Policy & Approval Controller
  ├─ Retry Controller
  ├─ Validation Runner
  ├─ Git Manager
  ├─ Artifact Manager
  └─ State Store
       ↓
Agent Runtime
  ├─ Planner
  ├─ Developer
  ├─ Reviewer
  └─ Failure Analyst / Replanner
```

### 6.1 Orchestrator Engine 책임

- Project Profile과 Work Item을 읽는다.
- 실행 가능한 Work Item을 계산한다.
- 현재 Workflow Step을 결정한다.
- Agent별 컨텍스트와 도구 권한을 제한한다.
- 승인 정책 위반 작업을 차단한다.
- 재시도 횟수와 비용·시간 제한을 적용한다.
- Validation 명령을 직접 실행한다.
- 성공 조건을 기계적으로 판정한다.
- 상태와 산출물을 영속적으로 기록한다.

### 6.2 AI Agent 책임

- Planner: Phase 및 Task 계획, 구현 계획 작성
- Developer: 허용된 범위의 코드와 테스트 수정
- Reviewer: 요구사항, 설계, 품질 및 변경 범위 검토
- Failure Analyst: 실패 원인 분류와 재시도 또는 재계획 제안
- 선택 Agent: Architect, Security Reviewer, Data Engineer, AI Evaluator 등

Tester의 성공·실패 판정은 가능한 한 AI가 아니라 결정론적인 Validation Runner가 담당한다. AI는 실패 로그의 원인 분석을 보조한다.

---

## 7. Project Profile 구조

```text
.dev-harness/
├─ project.yaml
├─ agents.yaml
├─ workflows.yaml
├─ validation.yaml
├─ permissions.yaml
├─ definition-of-done.yaml
├─ plans/
│  ├─ project-plan.md
│  └─ phases/
│     └─ P1.md
└─ work-items/
   ├─ P1.yaml
   ├─ P1-F1.yaml
   └─ P1-F1-T1.yaml
```

### 7.1 project.yaml 예시

```yaml
schema_version: "1.0"

project:
  id: decision-desk
  name: Decision Desk

knowledge:
  planning:
    - Draft/product-plan.md
  architecture:
    - docs/architecture.md
  domain_rules:
    - docs/domain-rules.md
  coding_rules:
    - AGENTS.md

work_items:
  directory: .dev-harness/work-items

runtime:
  agents: agents.yaml
  workflows: workflows.yaml
  validation: validation.yaml
  permissions: permissions.yaml
  definition_of_done: definition-of-done.yaml

defaults:
  workflow: standard-development
  git_strategy: phase-branch-task-commit
```

### 7.2 Agent Registry 예시

```yaml
agents:
  planner:
    enabled: true
    role: planning
    skills:
      - plan-phase
      - split-work-item
    write_allowed: false

  developer:
    enabled: true
    role: implementation
    skills:
      - implement-work-item
      - fix-validation-failure
    write_scope: work_item

  reviewer:
    enabled: true
    role: review
    skills:
      - review-code
      - review-domain-rules
    write_allowed: false

  failure-analyst:
    enabled: true
    role: failure-analysis
    skills:
      - analyze-failure
      - propose-replan
    write_allowed: false
```

Agent는 고정하지 않으며 프로젝트 Profile에 따라 Architect, Backend Developer, Frontend Developer, Security Reviewer, QA 등을 추가할 수 있다.

---

## 8. 개발 계획 수립 방식

### 8.1 전체 흐름

```text
기획서 입력
  ↓
개발 기준선 생성
  ↓
전체 Phase 계획
  ↓
현재 Phase 상세 계획
  ↓
Feature 및 Task 분해
  ↓
Task 실행
  ↓
Phase 통합 검증 및 인수
  ↓
다음 Phase 상세 계획
```

### 8.2 Rolling Wave Planning

프로젝트 시작 시 모든 Phase의 목표와 완료 조건은 정의하지만, 모든 Task를 처음부터 세부적으로 만들지는 않는다.

```text
Phase 1: Feature와 Task까지 상세 계획
Phase 2: Feature 수준 계획
Phase 3 이후: 목표와 완료 조건 중심 계획
```

현재 Phase가 끝나면 실제 구현 결과와 새로 발견한 위험을 반영하여 다음 Phase를 상세화한다. 이를 통해 오래된 세부 계획을 대량으로 유지하는 문제를 줄인다.

### 8.3 Phase 원칙

- Phase는 단순 작업 목록이 아니라 검증 가능한 목표로 정의한다.
- Phase마다 진입 조건과 종료 조건이 있어야 한다.
- 가능한 경우 사용자 또는 시스템 관점에서 통합 가능한 결과를 만든다.
- Frontend, Backend처럼 기술 영역만으로 Phase를 완전히 분리해 통합을 마지막까지 미루지 않는다.
- Phase 내부 작업이 많으면 의존성에 따라 실행 Wave를 구성한다.

---

## 9. Task Workflow

### 9.1 기본 Workflow

```yaml
workflows:
  standard-development:
    steps:
      plan:
        uses: planner

      implement:
        uses: developer
        needs: [plan]

      review:
        uses: reviewer
        needs: [implement]

      validate:
        uses: project-validation
        needs: [review]
        when: review.result == "approved"
```

Workflow는 고정된 목록이 아니라 `needs`를 가진 DAG로 표현한다. 초기 구현은 순차 실행하되, 같은 선행 조건을 가진 Step을 나중에 병렬 실행할 수 있도록 데이터 모델을 준비한다.

### 9.2 Task 상태

```text
PROPOSED
  → READY
  → RUNNING
  → REVIEWING
  → VALIDATING
  → COMPLETED

예외 상태:
WAITING_APPROVAL
BLOCKED
FAILED
RETRYING
REPLAN_REQUIRED
CANCELLED
```

`COMPLETED`는 AI가 선언하지 않는다. Orchestrator가 승인된 완료 조건과 실제 Validation 결과를 확인한 후 전환한다.

### 9.3 Task Context Package

Agent에게 프로젝트 전체를 무조건 전달하지 않고 현재 작업에 필요한 정보만 구성한다.

- Work Item 요구사항
- 관련 기획 섹션
- 관련 Architecture와 Domain Rules
- 선행 Work Item 산출물
- 승인된 구현 계획
- 허용 및 금지된 파일 경로
- Acceptance Criteria
- Validation 명령
- 현재 Git 기준선과 diff

---

## 10. Validation과 Definition of Done

Validation은 실행 가능한 검사이고, Definition of Done은 최종 완료 판정이다.

### 10.1 Validation 예시

```yaml
validation:
  unit:
    type: command
    command: pytest tests/unit
    required: true
    timeout_seconds: 300

  integration:
    type: command
    command: pytest tests/integration
    required: true

  lint:
    type: command
    command: ruff check .
    required: true

  typecheck:
    type: command
    command: mypy src
    required: true

  build:
    type: command
    command: python -m build
    required: false
```

하네스는 특정 명령을 하드코딩하지 않고 Project Profile에 정의된 필수 Validation을 실행한다. AI 프로젝트는 Eval, Prompt Regression, Data Validation 등의 검증 유형을 추가할 수 있다.

### 10.2 Definition of Done 예시

```yaml
definition_of_done:
  require:
    - validation.unit.passed
    - validation.integration.passed
    - validation.lint.passed
    - review.status == approved
    - unresolved_issues.critical == 0
    - approvals.required == completed

  manual:
    - 사용자 인수 테스트가 완료되었다
```

완료 조건은 다음을 포함할 수 있다.

- 필수 Validation 통과
- Reviewer 승인
- 중요 미해결 문제 없음
- 필수 문서 및 산출물 존재
- 필수 Human Approval 완료
- 프로젝트별 수동 인수 기준 충족

---

## 11. 승인 및 권한 정책

승인은 Task 수가 아니라 행동의 위험도를 기준으로 요청한다.

```yaml
approval:
  actions:
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

permissions:
  filesystem:
    write:
      - src/**
      - tests/**
      - docs/**
    deny:
      - .env
      - secrets/**
      - infrastructure/production/**

  network:
    default: ask
```

승인 기록은 Work Item revision과 계획 hash에 연결한다. 승인 이후 계획이 실질적으로 변경되면 기존 승인을 무효화하고 다시 요청한다.

```yaml
approval:
  id: APR-004
  action: database_migration
  work_item_id: PAYMENT-003
  plan_revision: 4
  plan_hash: "sha256:..."
  status: approved
```

### 11.1 기본 사용자 개입 시점

1. 전체 Phase 계획 승인
2. 현재 Phase 상세 계획 승인
3. 실행 중 발견된 고위험 결정 승인
4. Phase 결과 인수
5. Git Push, Merge 및 배포 승인

일반적인 코드 수정, 테스트 추가, 린트 수정 및 승인된 설계 범위 내 리팩터링은 자동 처리할 수 있다.

---

## 12. Retry 및 실패 처리

재시도는 무한 반복하지 않는다.

```yaml
retry:
  review_changes_requested:
    max_attempts: 2
    return_to: implement

  validation_failure:
    max_attempts: 3
    return_to: implement

  environment_failure:
    max_attempts: 1
    action: pause

  attempts_exhausted:
    action: human_escalation
```

실패 유형을 다음과 같이 구분한다.

- 구현 오류
- 코드 리뷰 지적
- 테스트 실패
- 환경 및 도구 실패
- 외부 서비스 장애
- 불안정한 테스트
- 권한 부족
- 기획 또는 설계 문제

기획이나 설계 문제가 원인이면 반복적인 코드 수정 대신 `REPLAN_REQUIRED` 상태로 전환한다.

---

## 13. 산출물 및 상태 관리

### 13.1 저장 원칙

```text
코드와 승인된 계획       → Git
현재 실행 상태           → SQLite
리뷰·테스트·시도 증거    → Artifact Store
최종 결과                → Phase Report 및 PR
중요 결정                → 불변 Approval/Decision Record
```

### 13.2 Runtime Artifact 구조

```text
%LOCALAPPDATA%/AI-Development-Harness/{project-id}/
├─ state.db
└─ runs/
   └─ RUN-001/
      ├─ manifest.json
      ├─ events.jsonl
      ├─ tasks/
      │  └─ P1-F1-T1/
      │     ├─ plan.md
      │     ├─ context-manifest.json
      │     ├─ attempts/
      │     │  ├─ 001/
      │     │  │  ├─ diff.patch
      │     │  │  ├─ developer-result.json
      │     │  │  └─ review-result.json
      │     │  └─ 002/
      │     ├─ validation-result.json
      │     └─ result.json
      └─ phase-report.md
```

원본 프롬프트나 민감한 문서 내용은 기본적으로 장기 보관하지 않는다. 저장이 필요한 로그는 비밀값과 개인정보를 제거하고 Project Profile의 보존 정책을 적용한다.

### 13.3 Artifact Manifest

각 산출물은 생성 주체와 입력 기준선을 추적할 수 있어야 한다.

```yaml
artifact:
  id: ART-00142
  type: validation-result
  run_id: RUN-001
  work_item_id: P1-F1-T1
  step: validate
  attempt: 2
  plan_revision: 3
  git_base_sha: a18c4f2
  git_result_sha: e9187db
  location: tasks/P1-F1-T1/validation-result.json
  sha256: "..."
  status: passed
```

### 13.4 Event Log

상태 변경은 덮어쓰기만 하지 않고 이벤트로 기록한다.

```json
{"event":"run_started","work_item":"P1-F1-T1","run_id":"RUN-001"}
{"event":"step_started","step":"implement","attempt":1}
{"event":"review_completed","result":"changes_requested"}
{"event":"step_retried","step":"implement","attempt":2}
{"event":"validation_passed","validation":"unit"}
```

---

## 14. Git 운영 전략

초기 버전에서는 다음 방식을 기본값으로 한다.

```text
Phase당 Branch 하나
Work Item당 Commit 하나
Phase당 PR 하나
Merge는 사용자 승인
```

```text
main
 └─ phase/P1-document-processing
     ├─ commit: INGEST-001
     ├─ commit: EXTRACT-001
     ├─ commit: OCR-001
     └─ commit: NORMALIZE-001
```

병렬 개발이 필요해지면 Task별 branch 또는 Git worktree를 만들고 Phase branch에서 통합한다. 첫 버전에서는 충돌과 통합 복잡도를 줄이기 위해 순차 실행을 우선한다.

---

## 15. 사용자 명령 초안

Slash Command는 실제 Workflow를 하드코딩하지 않고 Core Engine을 호출하는 얇은 진입점으로 구현한다.

```text
/development init <planning-document>
/development plan
/development phase-plan <phase-id>
/development phase-start <phase-id>
/development start <work-item-id>
/development run --ready
/development status
/development approve <approval-id>
/development reject <approval-id>
/development resume [run-id]
/development phase-close <phase-id>
/development report [phase-id|run-id]
```

내부 CLI가 별도로 존재할 수 있다.

```text
devh init
devh plan
devh run
devh status
devh approve
devh resume
devh report
```

---

## 16. 부동산 등기부등본 분석 프로젝트 실행 예시

### 16.1 입력

```text
registry-analyzer/
├─ Draft/
│  └─ registry-analysis-plan.md
└─ README.md
```

기획안의 MVP는 다음과 같다고 가정한다.

- PDF 업로드
- 텍스트 및 OCR 추출
- 표제부·갑구·을구 구조화
- 근저당, 압류, 가압류, 전세권 및 말소 여부 추출
- 위험 신호와 원문 근거 표시
- 분석 보고서 생성

### 16.2 초기화

```text
/development init Draft/registry-analysis-plan.md
```

하네스는 기획을 다시 작성하지 않고 개발을 막는 결정만 확인한다.

- 스캔 PDF 지원 여부
- 로컬 OCR 또는 외부 OCR API
- 원본 문서 보관 정책
- 규칙 엔진과 LLM의 책임 분리
- 정확도 검증 데이터셋
- 법률적 확정 표현 제한

승인된 결과로 Project Profile, Validation 및 Permission Policy를 생성한다.

### 16.3 전체 Phase 계획

```text
P0 — 개발 기반 및 공통 타입
P1 — 문서 입력과 텍스트 추출
P2 — 등기 항목 구조화
P3 — 위험 분석과 보고서
P4 — 제품 통합과 품질 검증
```

### 16.4 현재 Phase 상세 분해

Phase 1을 다음과 같이 분해한다.

```text
P1 문서 입력과 텍스트 추출
├─ P1-F1 PDF 입력
│  ├─ P1-F1-T1 업로드 API
│  ├─ P1-F1-T2 파일 검증
│  └─ P1-F1-T3 업로드 테스트
├─ P1-F2 텍스트 PDF 처리
│  ├─ P1-F2-T1 텍스트 추출기
│  ├─ P1-F2-T2 페이지 위치 보존
│  └─ P1-F2-T3 실패 처리
├─ P1-F3 스캔 PDF 처리
│  ├─ P1-F3-T1 스캔 문서 판별
│  ├─ P1-F3-T2 OCR 어댑터
│  └─ P1-F3-T3 OCR 신뢰도 저장
└─ P1-F4 텍스트 정규화
   ├─ P1-F4-T1 공백과 줄바꿈 정규화
   ├─ P1-F4-T2 페이지 경계 보존
   └─ P1-F4-T3 정규화 테스트
```

사용자는 Phase 1의 범위와 완료 조건을 승인한다.

### 16.5 Task 실행

`P1-F2-T1`이 READY가 되면 Orchestrator가 다음 순서로 실행한다.

```text
관련 기획·설계·Domain Rules 수집
  ↓
Planner가 파일 단위 구현 계획 작성
  ↓
Policy Controller가 위험 행동 검사
  ↓
Developer가 허용된 경로에서 코드와 테스트 수정
  ↓
Reviewer가 요구사항과 Git diff 독립 검토
  ↓
Validation Runner가 프로젝트 명령 실행
  ↓
성공 시 Task Commit 및 COMPLETED
```

Reviewer가 원문 페이지 위치 누락이나 OCR 실패를 정상 결과로 처리하는 문제를 발견하면 `CHANGES_REQUESTED`를 반환한다. Developer가 수정하고 정해진 횟수 내에서 다시 검증한다.

### 16.6 승인 대기

OCR 구현 중 외부 API 도입이 제안되면 다음과 같이 멈춘다.

```text
상태: WAITING_APPROVAL

요청: 외부 OCR 서비스 도입
영향:
- 등기부등본 원본의 외부 전송 가능성
- API 비용 발생
- 신규 SDK 및 환경변수 필요
- 개인정보 처리 정책 필요

추천: MVP에서는 로컬 OCR 사용
```

사용자가 승인 또는 대안을 선택하면 저장된 Run을 재개한다.

### 16.7 Phase 종료

Phase 1의 모든 필수 Work Item이 완료되면 다음을 통합 검증한다.

- 텍스트 PDF 처리
- 스캔 PDF OCR
- 손상된 PDF 오류 처리
- 원문 페이지 위치 보존
- OCR 실패와 위험 없음의 구분
- 원문 데이터의 로그 노출 방지

하네스는 코드 commit, 리뷰 결과, Validation 결과, 승인 기록, 알려진 제한사항을 포함한 Phase Report를 생성한다. 사용자가 보고서를 확인하고 Phase 인수와 Git Push/PR을 승인한다.

### 16.8 다음 Phase

Phase 1에서 확인된 실제 OCR 품질과 실패 유형을 반영하여 Phase 2를 Feature와 Task로 상세 분해한다. 같은 과정을 반복하여 P4까지 완료한 후 프로젝트 전체 Definition of Done을 검사한다.

---

## 17. MVP 개발 로드맵

### Phase 1 — Core Foundation

- Python CLI 기본 구조
- Project Profile 스키마
- Work Item 스키마
- YAML 검증
- SQLite State Store
- Event Log
- `init`, `status`, `resume` 명령

### Phase 2 — Planning and Approval

- 기획서 Import
- 전체 Phase 계획 생성
- 현재 Phase 상세 분해
- Work Item 의존성 계산
- Approval Policy
- 계획 revision 및 hash

### Phase 3 — Execution and Verification

- Agent Registry
- Context Package
- Planner/Developer/Reviewer 실행
- 파일 변경 범위 검사
- Validation Runner
- 제한된 Retry Loop
- Task별 Git Commit

### Phase 4 — Phase Delivery

- Phase 통합 검증
- Definition of Done Engine
- Phase Report
- Git Push 및 PR 승인
- Artifact Manifest
- 프로젝트 종료 보고서

### 이후 확장

- Task별 worktree와 병렬 실행
- 다양한 AI Provider Adapter
- Architect, Security Reviewer, QA 등 역할 확장
- Web Dashboard
- CI/CD 연동
- Project Kickoff Harness 연동
- 원격 Artifact Store

---

## 18. 하네스 자체 완료 조건

첫 번째 실사용 가능한 MVP는 다음 조건을 충족해야 한다.

- Markdown 기획서에서 Project Profile 초안을 생성할 수 있다.
- 전체 Phase 계획과 현재 Phase 상세 Work Item을 생성할 수 있다.
- 사용자가 계획을 승인하기 전에 소스 코드를 수정하지 않는다.
- 의존성이 충족된 Task만 실행한다.
- Developer와 Reviewer가 분리된 컨텍스트로 실행된다.
- 프로젝트에 설정된 Validation을 실제로 실행한다.
- Validation 실패 시 제한된 횟수만 재시도한다.
- 승인 대상 행동에서는 실행을 중단한다.
- 프로그램 및 컴퓨터 재시작 후 Run을 재개할 수 있다.
- Task별 코드 변경, 리뷰, 테스트 및 승인 증거를 추적할 수 있다.
- Phase 종료 시 사용자에게 인수 가능한 보고서를 제공한다.
- Decision Desk 프로젝트의 한 Phase를 처음부터 끝까지 dogfooding할 수 있다.

---

## 19. 초기 기술 방향

다음 구성으로 MVP를 시작하는 것을 권장한다.

- 언어: Python
- CLI: Typer 또는 동급 CLI 프레임워크
- 설정 검증: Pydantic
- 상태 저장: SQLite
- 문서: Markdown
- 설정: YAML
- 코드 기준선: Git
- AI 연동: 교체 가능한 Agent Provider Adapter
- 테스트: pytest

기술 선택은 구현 전에 별도 Architecture Decision Record로 최종 확정한다.

---

## 20. 핵심 결정 요약

1. Project Kickoff Harness와 Development Harness는 독립적으로 개발한다.
2. 두 시스템은 향후 `development_brief.yaml` 계약으로 연결한다.
3. 하네스 로직과 프로젝트별 Profile을 분리한다.
4. 사용자 계획 구조는 `기획 → Phase → Feature → Task`를 기본으로 한다.
5. 내부에서는 Phase, Feature, Ticket, Task 등을 Work Item으로 공통 처리한다.
6. 전체 Phase는 먼저 계획하고 현재 Phase만 상세 분해하는 Rolling Wave 방식을 사용한다.
7. Skill은 Agent가 사용하는 절차이며 Agent 자체가 아니다.
8. Orchestration의 핵심 통제는 자유로운 AI가 아니라 결정론적인 Engine이 담당한다.
9. Reviewer는 Developer와 분리된 컨텍스트에서 독립적으로 검토한다.
10. 테스트 성공 여부는 실제 Validation Runner가 판정한다.
11. 승인은 작업마다 받지 않고 고위험 결정에만 요청한다.
12. 재시도는 횟수를 제한하고 설계 문제는 재계획으로 전환한다.
13. 코드는 Git, 실행 상태는 SQLite, 실행 증거는 Artifact Store로 관리한다.
14. Phase당 Branch, Work Item당 Commit, Phase당 PR을 초기 기본 Git 전략으로 사용한다.
15. Decision Desk를 첫 dogfooding 프로젝트로 사용한다.

---

## 21. 참고자료

- [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills): Skill의 구성, `SKILL.md`, 선택적 scripts/references/assets 및 Agent 메타데이터 구조 참고
