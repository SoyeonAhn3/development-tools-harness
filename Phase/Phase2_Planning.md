# Phase 2 — Planning `🔲 Not Started`

> Connect one AI tool and generate a plan the user can review against the project.

**Prerequisites**: [Phase 1](Phase1_Foundation.md) accepted; AI execution tool and authentication selected before live integration.

**Technology**: Python + pytest, SQLite; inherit the version fixed in Phase 1.

**Plan status**: Outline only; detail Tasks and review scope before implementation.

## Overview

Implement project registration/baseline checks and the real Planner Adapter, following specification §§2, 5 and 7.3. Verify actual execution permissions before granting the Adapter access. Use generated plans when reviewing the next harness Phase; this is planning-only self-use.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | One real Adapter and documented permission/authentication boundaries | 🔲 |
| 2 | Project registration, configuration and baseline checks | 🔲 |
| 3 | Overall/current Phase plans, requirements mapping and relevant-code summary | 🔲 |
| 4 | Plan review/approval connection and actual Planner-call records | 🔲 |

## Verification & Exit Criteria

Detailed Tasks are deferred until Phase 1 results and the chosen AI tool are known.

- A prepared small project passes actual baseline tests and yields the overall Phase plan plus current Tasks, acceptance criteria and verification methods. Missing tools/documents/commands, failed checks and zero tests stop with actionable information.
- Plan contents identify related code and conventions, distinguish explicit rules from inferred patterns, and map requirements to current/later work, reuse or justified exclusion. Blocking ambiguities are surfaced. Reuse has a Phase and verification method, not an assumed pass.
- User approval references the reviewed plan version. Changed scope requires updated approval; unchanged approval is retained. Planning does not authorize implementation.
- Verify allowed file access and denied edits to policy/approval storage, Git writes, installation and unsupported external transfer. Permit only the selected AI service communication needed for the authorized call. Unsupported risky operations stop before execution; prompt instructions alone are not evidence of isolation.
- Record actual Planner call attempts, stage times, interruptions and approval waiting separately. Project-wide planning calls are not duplicated across Phases; unavailable token/cost data is not invented.

**Evidence**: pytest integration fixtures for registration/approval; real Adapter permission probes and a saved plan manually compared with source requirements/code. Completion requires successful checks and user acceptance.

**Results**: Not implemented; no tests, real calls or permission checks executed. Technical completion and acceptance pending.

## Planner & Project Entry

### Purpose / Implementation Files

Extend the Phase 1 package with project loading and a real Adapter. Exact module names and CLI commands will be recorded during Task detailing. Project configuration/plans stay in the project; runtime DB/logs stay outside OneDrive.

### Design Decisions

- Confirm the AI execution tool and enforcement mechanism first; a failed permission probe can block live automation without blocking further document refinement.
- Use the `phase-doc` output structure as the planning reference without modifying the skill. Produce full English/Korean Phase documents, keep current Tasks concise and later Phases at outline level.
- Keep policy and approval writes owned by the harness, separated from worker permissions. Do not rely on project-controlled instructions to grant permissions.
- Start with one prepared Python/pytest example as proposed in the overview. The user prepares dependencies; no template installer or environment repair engine is added.

### Usage Example

Register the prepared example and its specification/test command, run baseline checks, generate a plan, and inspect the requirement mapping. Exact CLI syntax is pending. Then use the Planner to draft/refine Phase 3 and record manual corrections; this does not prove the full self-development workflow.

## Prerequisites & Development Notes

Reuse Phase 1 storage, validation, approval and ownership code only after rechecking its relevant tests. Planner results must be checked against actual code. Live Developer/Reviewer orchestration and complete result acceptance are Phase 3 work. Provider choice and real boundary feasibility remain open until tested.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the real-connection and planning outline; provider choice and later Task details left explicit. |

---

# Phase 2 — 실제 연결과 계획 `🔲 미시작`

> AI 도구 한 개를 연결하고 사용자가 프로젝트와 대조해 검토할 수 있는 계획을 생성한다.

**선행 조건**: [Phase 1](Phase1_Foundation.md) 인수, 실제 연결 전에 AI 실행 도구와 인증 방식 선정.

**기술 구성**: Python + pytest, SQLite. Phase 1에서 고정한 버전을 따른다.

**계획 상태**: 개요만 작성. 구현 전에 Task 상세화와 범위 검토 필요.

## 개요

기획서 2·5·7.3장에 따라 프로젝트 등록·기본 검사와 실제 Planner Adapter를 구현한다. Adapter에 접근 권한을 주기 전에 실제 실행 권한을 검증한다. 생성한 계획을 다음 하네스 Phase 검토에 활용하며, 이 단계는 계획 기능만 자체 사용하는 것이다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Adapter 한 개와 권한·인증 경계 기록 | 🔲 |
| 2 | 프로젝트 등록·설정·기본 검사 | 🔲 |
| 3 | 전체·현재 Phase 계획, 요구사항 대응표, 관련 코드 요약 | 🔲 |
| 4 | 계획 검토·승인 연결과 실제 Planner 호출 기록 | 🔲 |

## 검증 및 종료 조건

세부 Task는 Phase 1 결과와 AI 도구 선정 후 작성한다.

- 준비된 작은 프로젝트에서 실제 기본 테스트가 통과하고 전체 Phase와 현재 Task·완료 기준·검증 방법을 생성한다. 도구·문서·명령 누락, 검사 실패·테스트 0개는 준비할 내용을 안내하고 중단한다.
- 계획에 관련 코드·규칙을 기록하고 명시 규칙과 추정 패턴을 구분한다. 요구사항을 현재·후속 작업, 재사용 또는 근거 있는 제외에 연결하고 구현을 막는 불확실성을 표시한다. 재사용은 Phase·검증 방법에 연결하며 통과로 추정하지 않는다.
- 사용자 승인은 검토한 계획 버전에 연결한다. 범위가 바뀌면 갱신된 승인이 필요하며 동일한 승인은 유지한다. 계획 생성 자체가 구현을 승인하지 않는다.
- 허용 파일 접근, 정책·승인 저장소 변경 차단, Git 쓰기·설치·지원하지 않는 외부 전송 차단을 확인한다. 승인된 호출에 필요한 선택 AI 서비스 통신만 허용한다. 지원하지 않는 위험 작업은 실행 전에 중단하며 프롬프트 지침만으로 분리를 입증하지 않는다.
- 실제 Planner 호출 시도·단계 시간·중단·승인 대기를 구분해 기록한다. 전체 계획 호출을 여러 Phase에 중복 합산하지 않으며 제공되지 않은 토큰·비용을 만들지 않는다.

**검증 근거**: 등록·승인의 pytest 통합 예제, 실제 Adapter 권한 시험, 생성 계획과 원문 요구사항·코드의 수동 대조. 검사 통과와 사용자 인수가 완료 조건이다.

**결과**: 구현 전이며 테스트·실제 호출·권한 검사는 수행하지 않았다. 기술적 완료와 인수 대기.

## Planner와 프로젝트 진입

### 목적 / 구현 파일

Phase 1 패키지에 프로젝트 읽기와 실제 Adapter를 추가한다. 정확한 모듈명과 CLI 명령은 Task 상세화 때 기록한다. 프로젝트 설정·계획은 프로젝트에, 실행 DB·로그는 OneDrive 밖에 둔다.

### 설계 결정 사항

- AI 실행 도구와 권한 집행 방법부터 확정한다. 권한 시험 실패 시 실제 자동 실행은 막되 문서 보완은 계속할 수 있다.
- `phase-doc` 출력 구조를 계획 작성 기준으로 사용하고 스킬은 수정하지 않는다. Phase 문서는 영문·국문 전체로 작성하며 현재 Task는 간결하게, 이후 Phase는 개요로 유지한다.
- 정책·승인 기록 쓰기는 하네스가 담당하고 작업 에이전트의 권한과 분리한다. 프로젝트에서 바꿀 수 있는 지침에 권한 부여를 의존하지 않는다.
- 전체 개요에서 제안한 준비된 Python/pytest 예제 한 개로 시작한다. 의존성은 사용자가 준비하며 템플릿 설치기·환경 복구 엔진은 추가하지 않는다.

### 사용 예시

준비된 예제·기획서·테스트 명령을 등록하고 기본 검사 후 계획을 생성해 대응표를 확인한다. 정확한 CLI 문법은 미정이다. 이후 Planner로 Phase 3 초안·보완안을 만들고 수동 수정을 기록한다. 이것만으로 전체 자체 개발 흐름이 검증되지는 않는다.

## 선행 조건 및 개발 시 주의사항

Phase 1의 저장·검증·승인·소유권 코드는 관련 테스트를 다시 확인한 뒤 재사용한다. Planner 결과는 실제 코드와 대조한다. 실제 Developer·Reviewer 실행 연결과 전체 결과 인수는 Phase 3 범위다. 제공자 선택과 실제 권한 경계의 실현 가능성은 시험 전까지 미결정이다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 실제 연결·계획 개요 최초 작성. 제공자 선정과 후속 Task 상세화는 미결정으로 명시. |
