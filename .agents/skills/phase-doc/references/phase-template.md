# Phase 문서 신규 생성 템플릿
# 유형 = "신규 생성" 판정 시 로드

직접 문서 작성에는 아래 표준 예시를 사용한다. 하네스의 계획 생성에는 파일 끝의 `harness:*` 블록을 사용한다. 해당 블록의 `{{name}}`은 호스트가 검증한 계획 값으로 한 번만 치환하는 슬롯이며 실행 코드가 아니다. 제목·설명·배치를 편집할 수 있지만 필수 슬롯을 제거하면 새 Run 등록이 중단된다. 현재 Phase만 Task 표를 상세하게 채우며 나머지는 개요와 종료 조건을 유지한다.

파일 쓰기 도구로 `Phase/PhaseN_[EnglishName].md`를 아래 표준 구조로 생성한다.
파일명은 반드시 영어 PascalCase로 작성한다. (예: Phase1_Foundation.md, Phase2_CoreEngine.md)

**문서 구조**: 상단 영어(English) → 구분선 → 하단 한국어(Korean) 순서로 배치한다.
영어/한국어 섹션은 동일한 내용을 각 언어로 작성하며, 반드시 동기화를 유지한다.

필요한 내용과 약간의 디테일 수준으로 작성한다. 현재 Phase의 Task만 상세화하고, 확정되지 않은 구현은 예정·미정으로 표시한다. 예시 행과 자리표시자는 실제 내용으로 대체한다. 스킬 분류는 해당 산출물이 있을 때만 작성하며, 불필요한 구조·코드 블록은 추가하지 않는다.

---

```markdown
# Phase N — [Phase Name] `[Status]`

> [One-line description of this phase]

**Completed**: YYYY-MM-DD  (only when completed)
**Status**: ✅ Completed | 🚧 In Progress | 🔲 Not Started
**Prerequisites**: Phase N-1 completion status
**Technology**: [Decided language and test tools]

---

## Overview

[2-4 line description of what this Phase achieves]

---

## Deliverables

| # | Skill / Module | Status | Skill Type |
|---|---|---|---|
| N | `skill-name` | ✅/🔲 | general/project-specific |

---

## Tasks & Verification

| Task | Work | Acceptance Criteria | Verification | Status |
|---|---|---|---|---|
| N.1 | [Brief scope] | [Observable expected behavior] | [Test/command or manual check] | 🔲 |

**Results**: [Actual verification evidence, remaining work, and user acceptance when required; mark unexecuted checks explicitly]

---

## [Skill/Module Name]

### Purpose
### Implementation Files
### Core Classes / Structure (code block)
### Design Decisions
### Usage Examples

---

## Phase N Skill Classification

| Skill | Classification | Reason |
|---|---|---|

---

## Prerequisites & Dependencies

---

## Development Notes

---

## Change Log

| Date | Description |
|---|---|
| YYYY-MM-DD | Initial creation |

---
---

# Phase N — [Phase 이름] `[상태]`

> [Phase 한 줄 설명]

**완료일**: YYYY-MM-DD  (완료 시에만)
**상태**: ✅ 완료 | 🚧 진행 중 | 🔲 미시작
**선행 조건**: Phase N-1 완료 여부
**기술 구성**: [결정된 언어와 테스트 도구]

---

## 개요

[이 Phase가 무엇을 달성하는지 2~4줄 설명]

---

## 완료 예정 / 완료 항목

| # | Skill / 모듈 | 상태 | 스킬 타입 |
|---|---|---|---|
| N | `skill-name` | ✅/🔲 | general/project-specific |

---

## Task 및 검증

| Task | 작업 내용 | 완료 기준 | 검증 방법 | 상태 |
|---|---|---|---|---|
| N.1 | [간단한 작업 범위] | [확인 가능한 기대 동작] | [테스트·명령 또는 수동 확인] | 🔲 |

**결과**: [실제 검증 근거, 남은 작업, 필요한 사용자 인수 결과. 미실행 검사는 명시]

---

## [스킬/모듈명]

### 목적
### 구현 파일
### 핵심 클래스 / 구조 (코드 블록)
### 설계 결정 사항
### 사용 예시

---

## Phase N 스킬 범용/전용 분류

| 스킬 | 분류 | 이유 |
|---|---|---|

---

## 선행 조건 및 의존성

---

## 개발 시 주의사항

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| YYYY-MM-DD | 최초 작성 |
```

## 하네스 계획 출력 템플릿

<!-- harness:overview:en -->
# Development Phase Plan

{{overview}}

## Overall Phases

{{phases}}

## Phase Documents

{{documents}}

## Requirements Mapping

{{requirements}}

## Questions and Prerequisites

{{questions}}

Planning approval does not authorize implementation. Reuse proposals require actual final verification.

Writing rules: `phase-doc` {{skill_version}} · Snapshot: `{{profile_hash}}`
<!-- /harness:overview:en -->

<!-- harness:overview:ko -->
# 개발 Phase 계획

{{overview}}

## 전체 Phase

{{phases}}

## Phase 문서

{{documents}}

## 요구사항 대응표

{{requirements}}

## 확인할 사항과 선행 조건

{{questions}}

계획 승인은 구현 실행을 승인하지 않는다. 재사용 제안에도 실제 최종 검증이 필요하다.

작성 규칙: `phase-doc` {{skill_version}} · 원문 식별자: `{{profile_hash}}`
<!-- /harness:overview:ko -->

<!-- harness:phase:en -->
# Phase {{number}} — {{title}}

> {{goal}}

**Status**: Planning draft; this document does not establish implementation, verification or user acceptance.

**Prerequisites**: {{prerequisites}}

**Technology**: {{technology}}

## Overview

{{scope}}

## Deliverables

{{deliverables}}

## Tasks & Verification

{{tasks}}

**Results**: Checks above are proposed. No Phase implementation or acceptance is established by generating this plan.

## Requirements Mapping

{{requirements}}

## Related Code / Implementation Files

{{code_context}}

## Development Notes

{{questions}}

## Change Log

| Date | Description |
|---|---|
| {{date}} | Planning Run registered; draft and revisions use its pinned writing rules. |

Writing rules: `phase-doc` {{skill_version}} · Snapshot: `{{profile_hash}}`
<!-- /harness:phase:en -->

<!-- harness:phase:ko -->
# Phase {{number}} — {{title}}

> {{goal}}

**상태**: 계획 초안. 이 문서가 구현·검증·사용자 인수 완료를 뜻하지 않는다.

**선행 조건**: {{prerequisites}}

**기술 구성**: {{technology}}

## 개요

{{scope}}

## 완료 예정 항목

{{deliverables}}

## Task 및 검증

{{tasks}}

**결과**: 위 검사는 수행할 계획이다. 계획 생성으로 해당 Phase의 구현이나 인수가 완료된 것은 아니다.

## 요구사항 대응표

{{requirements}}

## 관련 코드 / 구현 파일

{{code_context}}

## 개발 시 주의사항

{{questions}}

## 변경 이력

| 날짜 | 내용 |
|---|---|
| {{date}} | 계획 Run 등록. 초안·수정본은 해당 Run에 고정한 작성 규칙을 사용한다. |

작성 규칙: `phase-doc` {{skill_version}} · 원문 식별자: `{{profile_hash}}`
<!-- /harness:phase:ko -->
