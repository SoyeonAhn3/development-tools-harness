# Phase 2 — Planning & Environment Setup `🔲 Not Started`

> From a specification alone, produce Phase documents that start with Phase 0, and let Phase 0 actually prepare the environment.

**Prerequisites**: [Phase 1](Phase1_ValidationContract.md) accepted.

**Technology**: Harness unchanged. Example projects: at least one new project (Python or TypeScript) and one project that is already prepared. Chosen when this Phase is detailed.

**Plan status**: Outline only. Tasks are detailed after Phase 1 is accepted.

## Overview

Spec 12 steps 3–4. Extend the Planner so every plan starts with Phase 0 and contains the setup plan of spec 4.2, generate bilingual Phase documents in `Phase/`, and execute Phase 0 with approved commands in one of its three forms (spec 4.4).

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Plan extension: Phase 0 always first (spec 3.2); the setup plan of spec 4.2 (runtime and tools, install commands with network and administrator flags, project skeleton, DB, check commands in contract form with the check-config file list and suppression-comment patterns, lock files, project rules, baseline); requirement mapping (spec 3.3) | 🔲 |
| 2 | Technology proposal when the specification has none: one recommendation and one or two alternatives with reasons; version recommendation with LTS, end of support and compatibility; the user chooses at start (spec 3.1, 4.2) | 🔲 |
| 3 | Bilingual `Phase/Overview.md`, `Phase/PhaseN_Name.md` and a draft `Phase/ProjectRules.md` for approval (spec 3.4, 6.3) | 🔲 |
| 4 | Phase 0 execution: approved commands only; unlisted commands ask first; administrator steps become manual instructions and resume after a confirming check; no overwrite of existing files; setup is complete only when the contract passes (spec 4.3) | 🔲 |
| 5 | Three Phase 0 forms: full setup, partial setup and check-only. "Already prepared" is confirmed by actually running the checks (spec 4.4) | 🔲 |
| 6 | Version pinning with lock files and a registered lock-file list (spec 4.2) | 🔲 |
| 7 | Baseline capture: test list and existing quality-check violations handled by fixing, tool baseline or scope (spec 6.5) | 🔲 |

## Verification & Exit Criteria

- From a specification alone, a plan and bilingual Phase documents including Phase 0 are generated. Nothing is set up or implemented before start.
- A specification without a technology stack yields a proposal with alternatives, and the user's choice is recorded in the Phase document.
- A new project is set up from nothing and passes the check contract.
- A prepared project finishes Phase 0 in check-only form with a recorded baseline and no AI development call.
- A step that needs administrator rights produces manual instructions, and the run resumes after the user completes it.
- An existing failing test is reported and not accepted as baseline.
- Phase 0 is started and accepted separately from the first development Phase.
- The full regression is compared with the Phase 0 baseline; changed tests are listed with reasons.
- User acceptance.

**Results**: Not started.

## Development Notes

- The duplicate and suppression-comment baselines need their detectors, which are built in Phase 3. From Phase 3 on, Phase 0 also records those two baselines.
- Planning currently reads only listed files and writes drafts under `Phase/Generated`. Moving to `Phase/` must not overwrite user-written documents; the harness changes only status fields, dates, Task status, result summaries and change-log rows (spec 3.4).
- A plan is never edited separately; a wrong plan is regenerated from the specification (spec 2.1, A1).

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created the outline from spec 12 steps 3–4. Not started. |

---

# Phase 2 — 계획 확장과 환경 세팅 `🔲 미시작`

> 기획서만으로 Phase 0부터 시작하는 Phase 문서를 만들고, Phase 0이 실제로 환경을 준비하게 한다.

**선행 조건**: [Phase 1](Phase1_ValidationContract.md) 인수.

**기술 구성**: 하네스는 그대로. 예제 프로젝트는 신규 프로젝트(Python 또는 TypeScript) 1개 이상과 이미 준비된 프로젝트 1개. 이 Phase를 상세화할 때 정한다.

**계획 상태**: 개요만 작성했다. Task는 Phase 1 인수 후 상세화한다.

## 개요

기획서 12장 3–4단계다. Planner가 모든 계획을 Phase 0부터 시작하고 기획서 4.2의 세팅 계획을 담도록 확장한다. 영문·국문 Phase 문서를 `Phase/`에 만들고, Phase 0을 세 형태(기획서 4.4) 중 하나로 승인된 명령만 써서 실행한다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 계획 확장: Phase 0을 항상 첫 Phase로(기획서 3.2). 기획서 4.2의 세팅 계획(런타임과 도구, 네트워크·관리자 권한 여부를 적은 설치 명령, 프로젝트 골격, DB, 검사 설정 파일 목록과 검사 회피 주석 패턴을 포함한 계약 형식의 검사 명령, 잠금 파일, 프로젝트 규칙, 기준선). 요구사항 대응표(기획서 3.3) | 🔲 |
| 2 | 기획서에 기술 구성이 없을 때 제안: 추천 1개와 대안 1–2개를 이유와 함께 제시. LTS, 지원 종료 시점, 호환성을 적은 버전 추천. 사용자는 시작할 때 고른다(기획서 3.1, 4.2) | 🔲 |
| 3 | 영문·국문 `Phase/Overview.md`, `Phase/PhaseN_Name.md`, 승인용 `Phase/ProjectRules.md` 초안(기획서 3.4, 6.3) | 🔲 |
| 4 | Phase 0 실행: 승인된 명령만 실행, 목록에 없는 명령은 먼저 묻기, 관리자 작업은 수동 안내 후 확인 검사를 거쳐 재개, 기존 파일 덮어쓰기 금지, 검사 계약을 통과해야 세팅 완료(기획서 4.3) | 🔲 |
| 5 | Phase 0 세 형태: 전체 세팅, 부분 세팅, 확인만. "이미 준비됨"은 검사를 실제로 실행해 확인한다(기획서 4.4) | 🔲 |
| 6 | 잠금 파일로 버전 고정, 잠금 파일 목록 등록(기획서 4.2) | 🔲 |
| 7 | 기준선 수집: 테스트 목록, 기존 품질 검사 위반을 수정·도구 기준선·검사 범위로 처리(기획서 6.5) | 🔲 |

## 검증 및 종료 조건

- 기획서만으로 Phase 0을 포함한 계획과 영문·국문 Phase 문서가 생성된다. 시작 전에는 세팅이나 구현을 하지 않는다.
- 기술 구성이 없는 기획서에서는 대안을 포함한 제안이 나오고, 사용자의 선택이 Phase 문서에 기록된다.
- 신규 프로젝트를 아무것도 없는 상태에서 세팅하고 검사 계약을 통과한다.
- 준비된 프로젝트는 AI 개발 호출 없이 확인만 형태로 Phase 0을 마치고 기준선을 기록한다.
- 관리자 권한이 필요한 단계에서는 수동 절차를 안내하고, 사용자가 처리한 뒤 재개한다.
- 기존 실패 테스트는 보고되고 기준선으로 인정되지 않는다.
- Phase 0과 첫 개발 Phase를 각각 따로 시작하고 인수한다.
- 전체 회귀 검사를 Phase 0 기준선과 비교하고, 바뀐 테스트는 이유와 함께 적는다.
- 사용자 인수.

**결과**: 미시작.

## 개발 시 주의사항

- 중복과 검사 회피 주석의 기준선은 탐지기가 있어야 만들 수 있고, 탐지기는 Phase 3에서 만든다. Phase 3부터는 Phase 0이 이 두 기준선도 기록한다.
- 지금 계획 기능은 지정한 파일만 읽고 초안을 `Phase/Generated`에 쓴다. `Phase/`로 옮길 때 사용자가 쓴 문서를 덮어쓰면 안 된다. 하네스는 상태, 날짜, Task 상태, 결과 요약, 변경 이력 행만 바꾼다(기획서 3.4).
- 계획만 따로 고치지 않는다. 계획이 틀리면 기획서에서 다시 생성한다(기획서 2.1, A1).

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | 기획서 12장 3–4단계로 개요를 작성했다. 미시작. |
