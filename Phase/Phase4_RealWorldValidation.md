# Phase 4 — Real-World Validation `🔲 Not Started`

> Use the harness on real projects in three languages and check every first-version completion criterion.

**Prerequisites**: [Phase 3](Phase3_WorkflowAndQuality.md) accepted.

**Technology**: Harness unchanged. Example stacks: TypeScript with SQLite (Decision Desk), Python (existing project), Java (mock project). Server-side language for Decision Desk is proposed by the Planner and confirmed by the user.

**Plan status**: Outline only. Tasks and example targets are fixed after Phase 3 is accepted.

## Overview

Spec 12 step 7. Instead of self-development, validate the harness on the examples of spec 13.1 and map every spec 13 criterion to evidence. The harness code is not changed while an example runs.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | Decision Desk Phase 1: new project from its specification only. Its specification leaves the stack open, so the technology proposal and confirmation (spec 3.1) are verified too. SQLite. Screen checks are manual | 🔲 |
| 2 | One existing Python project chosen at start (candidates: Verbatim, Enterprise-rag). Phase 0 in partial or check-only form | 🔲 |
| 3 | One mock Java project, topic chosen at start. New project | 🔲 |
| 4 | Spec 13 criterion-to-evidence table, including failures and unverified items | 🔲 |

## Verification & Exit Criteria

- For each example, Phase 0 and at least one development Phase are accepted without changing harness code during the example.
- If a harness defect appears, record it, fix it with existing coding tools and rerun the affected example from the start of its Phase.
- Every spec 13 criterion has evidence. Failed or unverified items are listed, not counted as passed.
- User acceptance of the first version.

**Results**: Not started.

## Development Notes

- Decision Desk specification: `decision-desk/develop-plan/decision-desk-기획문서.md` in the folder next to this repository (v2, 2026-09-29). Its Phase 1 has 11 items and its section 13 has about 40 completion cases. Its referenced change-history file is missing; check this before starting.
- Server DBs (MSSQL, PostgreSQL) stay an unverified limitation (spec 10.3).

## Change Log

| Date | Description |
|---|---|
| 2026-10-23 | Created the outline from spec 12 step 7 and spec 13.1. Replaces the cancelled self-development Phase. Not started. |

---

# Phase 4 — 실사용 검증 `🔲 미시작`

> 세 언어의 실제 프로젝트에 하네스를 써 보고, 첫 버전 완료 기준을 모두 확인한다.

**선행 조건**: [Phase 3](Phase3_WorkflowAndQuality.md) 인수.

**기술 구성**: 하네스는 그대로. 예제 구성은 TypeScript와 SQLite(Decision Desk), Python(기존 프로젝트), Java(모의 프로젝트). Decision Desk의 서버 언어는 Planner가 제안하고 사용자가 확인한다.

**계획 상태**: 개요만 작성했다. Task와 예제 대상은 Phase 3 인수 후 확정한다.

## 개요

기획서 12장 7단계다. 자체 개발 대신 기획서 13.1의 예제로 하네스를 검증하고, 13장의 완료 기준마다 근거를 연결한다. 예제를 진행하는 동안 하네스 코드는 고치지 않는다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | Decision Desk Phase 1: 기획서만 있는 신규 프로젝트. 기획서에 기술 구성이 정해져 있지 않아 기술 구성 제안·확인 절차(기획서 3.1)도 함께 검증한다. SQLite. 화면 확인은 수동 | 🔲 |
| 2 | 시작할 때 고르는 기존 Python 프로젝트 1개(후보: Verbatim, Enterprise-rag). Phase 0은 부분 세팅 또는 확인만 | 🔲 |
| 3 | 시작할 때 주제를 정하는 모의 Java 프로젝트 1개. 신규 | 🔲 |
| 4 | 기획서 13장 기준별 근거 대조표. 실패와 미검증 항목 포함 | 🔲 |

## 검증 및 종료 조건

- 예제마다 Phase 0과 개발 Phase 1개 이상을, 예제 진행 중 하네스 코드를 고치지 않고 인수한다.
- 하네스 결함이 나오면 기록하고, 기존 코딩 도구로 고친 뒤 해당 예제를 그 Phase 처음부터 다시 실행한다.
- 13장의 모든 기준에 근거가 있다. 실패하거나 확인하지 못한 항목은 통과로 치지 않고 목록으로 남긴다.
- 첫 버전 사용자 인수.

**결과**: 미시작.

## 개발 시 주의사항

- Decision Desk 기획서: 이 저장소 옆 폴더의 `decision-desk/develop-plan/decision-desk-기획문서.md`(v2, 2026-09-29). Phase 1은 11개 항목, 13장 완료 사례는 약 40개다. 기획서가 참조하는 변경 이력 파일이 없으므로 시작 전에 확인한다.
- 서버 DB(MSSQL, PostgreSQL)는 미검증 한계로 남긴다(기획서 10.3).

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-10-23 | 기획서 12장 7단계와 13.1로 개요를 작성했다. 취소한 자체 개발 Phase를 대체한다. 미시작. |
