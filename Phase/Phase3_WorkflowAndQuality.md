# Phase 3 — Workflow & Quality `🔲 Not Started`

> Give the AI the permissions it needs to work on a whole project, and put the quality devices, report and acceptance in place.

**Prerequisites**: [Phase 2](Phase2_PlanningAndSetup.md) accepted.

**Technology**: Harness unchanged. Example projects are reused from Phases 1–2.

**Plan status**: Outline only. Tasks are detailed after Phase 2 is accepted.

## Overview

Spec 12 steps 5–6. Redesign the AI permissions (spec 7.1), add the quality devices of spec 6, produce the human-readable report (spec 8.1), mark Phase documents complete on acceptance (spec 8.2) and simplify the CLI (spec 2.2). The existing sequential execution, bounded corrections, final validation, feedback routes and acceptance gates are reused.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | AI permissions (spec 7.1): whole-project read and search with the secret exclusion list (`.env` and `.env.*`, `*.key`, `*.pem`, `credentials`, `secrets` folder); free changes, deletion and renaming inside the plan's files and folders; stop for approval outside them; check requests (default 5 per Task, separate from the correction limit of 2); planned dependency additions run by the harness; library version conflicts handled as in spec 4.2 | 🔲 |
| 2 | Duplicate detector: token-based, exact copies only, report only, compared with the baseline (spec 6.2, H1) | 🔲 |
| 3 | Quality checks, project rules given to Developer and Reviewer, Reviewer checklist with mandatory and advisory findings and recorded outcomes (spec 6.3) | 🔲 |
| 4 | Weakening control (spec 6.4, H2): planned config changes covered by start; unplanned changes classified by the Reviewer and stopped only when they weaken a check; every config change listed in the report; suppression-comment patterns and lock-file changes tracked | 🔲 |
| 5 | Bilingual results report `Phase/Reports/PhaseN_Report.md`, 1–2 pages, produced even on failure (spec 8.1) | 🔲 |
| 6 | Acceptance that marks the Phase document complete and presents the next Phase's detailed plan (spec 3.4, 8.2) | 🔲 |
| 7 | Simplified CLI: `plan`, `start`, `status`, `approve`, `accept`, `feedback`, `resume` (spec 2.2) | 🔲 |
| 8 | Tool-independent AI adapter contract and Codex implementation; small Claude Code compatibility assessment (spec 1.10, I1). If company login is unavailable, document-only assessment with the limitation recorded. Full Claude Code implementation follows first-version acceptance | 🔲 |

## Verification & Exit Criteria

- Each spec 6 device leaves evidence in the review and the report. At minimum: a new exact-copy duplicate is reported; an unplanned weakening config change stops for approval; a non-weakening change continues and appears in the report; a new suppression comment is reported and checked by the Reviewer; a changed existing version in a lock file is checked by the Reviewer.
- Existing duplicates and violations recorded in the baseline do not block; only new problems do (spec 6.5).
- The AI cannot read files on the secret exclusion list. A change outside the plan's scope stops for approval.
- A report is produced for both a successful and a failed run.
- Acceptance is blocked when mandatory evidence is missing. On acceptance only the allowed fields of the Phase document change.
- Existing state, resume, ownership and recovery regressions still pass. Tests changed by the CLI simplification are listed with reasons.
- Assess Claude Code request/response, enforceable tool restrictions, structured output and unelevated company login/execution as specified by I1; record what was actually checked and any documentation-only limits. Include recovery parsing in the common adapter boundary.
- User acceptance.

**Results**: Not started.

## Development Notes

- The current Developer instructions forbid dependency changes, deletion and renaming; they change under deliverable 1.
- Decide here the fate of `runner` and only the legacy fake-plan portion of `model`, plus the harness repository's own quality checks. Phase 0 confirmed that `model` also holds shared errors, hashes, paths and the check contract; its Phase 1 contract work cannot wait for CLI simplification.
- The duplicate detector's accuracy is not a release condition. Renamed copies and similar logic are not detected, and the report states this limit.

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created the outline from spec 12 steps 5–6 and decisions H1–H2. Not started. |
| 2026-10-23 | Synchronized existing specification 1.10 decision I1 and Phase 0 module findings. No Phase 3 implementation or Claude Code assessment performed. |

---

# Phase 3 — 개발 흐름과 품질 장치 `🔲 미시작`

> AI가 프로젝트 전체를 보고 작업할 수 있게 권한을 주고, 품질 장치·보고서·인수를 갖춘다.

**선행 조건**: [Phase 2](Phase2_PlanningAndSetup.md) 인수.

**기술 구성**: 하네스는 그대로. 예제 프로젝트는 Phase 1–2의 것을 다시 쓴다.

**계획 상태**: 개요만 작성했다. Task는 Phase 2 인수 후 상세화한다.

## 개요

기획서 12장 5–6단계다. AI 권한(기획서 7.1)을 재설계하고, 6장의 품질 장치를 추가하고, 사람이 읽는 보고서(기획서 8.1)를 만들고, 인수하면 Phase 문서를 완료 처리하고(기획서 8.2), CLI를 단순화한다(기획서 2.2). 기존의 순차 실행, 제한된 수정, 통합 검증, 피드백 경로, 인수 조건은 재사용한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | AI 권한(기획서 7.1): 비밀값 제외 목록(`.env`와 `.env.*`, `*.key`, `*.pem`, `credentials`, `secrets` 폴더)을 뺀 프로젝트 전체 읽기·검색. 계획의 파일·폴더 안에서는 자유로운 변경·삭제·이름 변경, 그 밖은 멈추고 승인. 검사 요청(Task당 기본 5회, 수정 한도 2회와 별개). 계획된 의존성 추가는 하네스가 실행. 라이브러리 버전 충돌은 기획서 4.2대로 처리 | 🔲 |
| 2 | 중복 탐지기: 토큰 단위, 그대로 복사한 코드만, 보고만, 기준선과 비교(기획서 6.2, H1) | 🔲 |
| 3 | 품질 검사, Developer와 Reviewer에 주는 프로젝트 규칙, 필수·권고 지적과 처리 결과를 남기는 Reviewer 기준표(기획서 6.3) | 🔲 |
| 4 | 기준 완화 차단(기획서 6.4, H2): 계획에 적힌 설정 변경은 시작 승인에 포함, 계획 밖 변경은 Reviewer가 분류해 완화일 때만 중단, 모든 설정 변경을 보고서에 표시, 검사 회피 주석 패턴과 잠금 파일 변경 추적 | 🔲 |
| 5 | 영문·국문 결과 보고서 `Phase/Reports/PhaseN_Report.md`, 1–2페이지, 실패해도 생성(기획서 8.1) | 🔲 |
| 6 | 인수하면 Phase 문서를 완료 처리하고 다음 Phase 상세 계획을 제시(기획서 3.4, 8.2) | 🔲 |
| 7 | 단순화한 CLI: `plan`, `start`, `status`, `approve`, `accept`, `feedback`, `resume`(기획서 2.2) | 🔲 |
| 8 | 도구 공통 AI 연결 계약과 Codex 구현, Claude Code 소규모 적합성 확인(기획서 1.10, I1). 회사 로그인이 불가능하면 문서로만 확인하고 한계를 기록한다. Claude Code 정식 구현은 첫 버전 인수 후 진행 | 🔲 |

## 검증 및 종료 조건

- 6장의 장치마다 리뷰와 보고서에 근거가 남는다. 최소한 다음을 확인한다. 새로 그대로 복사한 중복이 보고된다. 계획 밖의 완화 설정 변경은 멈추고 승인을 받는다. 완화가 아닌 변경은 계속 진행되고 보고서에 나온다. 새 검사 회피 주석이 보고되고 Reviewer가 확인한다. 잠금 파일에서 기존 버전이 바뀌면 Reviewer가 확인한다.
- 기준선에 기록된 기존 중복과 위반은 막지 않고, 새로 생긴 문제만 막는다(기획서 6.5).
- AI는 비밀값 제외 목록의 파일을 읽지 못한다. 계획 범위 밖의 변경은 멈추고 승인을 받는다.
- 성공한 실행과 실패한 실행 모두 보고서가 생성된다.
- 필수 근거가 없으면 인수가 막힌다. 인수하면 Phase 문서에서 허용된 항목만 바뀐다.
- 기존 상태·재개·소유권·복구 회귀 검사가 계속 통과한다. CLI 단순화로 바뀐 테스트는 이유와 함께 적는다.
- I1에 따라 Claude Code 요청·응답, 실제 도구 제한, 구조화 출력, 회사 환경의 일반 권한 로그인·실행을 확인하고 실제 확인 범위와 문서 확인만 한 한계를 기록한다. 호출 복구의 이벤트 해석도 공통 연결 경계에 포함한다.
- 사용자 인수.

**결과**: 미시작.

## 개발 시 주의사항

- 지금 Developer 지침은 의존성 변경, 삭제, 이름 변경을 금지한다. 산출물 1에서 바뀐다.
- `runner`와 `model` 중 기존 가짜 계획 처리 부분의 존치, 하네스 저장소 자체의 품질 검사 도입 여부를 여기서 정한다. Phase 0에서 `model`에 공용 오류·해시·경로·검사 계약도 있음을 확인했다. Phase 1의 검사 계약 변경을 CLI 단순화 때까지 미루면 안 된다.
- 중복 탐지 정확도는 출시 조건이 아니다. 이름만 바꾼 복사와 비슷한 로직은 찾지 못하며, 보고서에 이 한계를 적는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | 기획서 12장 5–6단계와 결정 H1–H2로 개요를 작성했다. 미시작. |
| 2026-10-23 | 기존 기획서 1.10의 I1 결정과 Phase 0 모듈 확인 결과를 반영했다. Phase 3 구현이나 Claude Code 적합성 확인을 수행한 것은 아니다. |
