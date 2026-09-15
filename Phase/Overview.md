# Development Phases — Lean MVP

**Revision**: 0.2 · **Date**: 2026-09-15 · **Status**: Phase 1 technically verified; user acceptance pending. Phases 2–4 not started.

## Goal & Decisions

Build the P0 local CLI described in the [lean MVP plan 0.4](../Draft/ai-development-harness-lean-mvp-plan.md). Follow its section 10 implementation order. P0 is a priority label; Phase numbers below are development stages.

- **Decided**: Windows/Python 3.12.10 + pytest 9.1.1 for harness development; SQLite for execution state, psutil 7.2.2 for process identity. Versions are recorded in `.python-version` and `requirements-dev.lock`. Phase documents contain complete English and Korean sections.
- **Proposed**: use Python + pytest for the separate real validation examples as well. The Phase 1 fake-Adapter fixture already uses this configuration.
- **Pending before Phase 2 integration**: select one AI execution tool, authentication method, and enforceable permission boundary. The current coding environment does not automatically determine the product's Adapter.
- **Current repository**: Phase 1 package/CLI, transactional SQLite state, fake Adapter, actual command validation, approval/file protection and resume are implemented. All 43 tests and a separate CLI demonstration passed. Real AI integration and permission isolation remain unimplemented.
- **Development method**: use existing coding tools for the initial foundation, then progressively use the harness. Refine these Phase documents during development; keep the `phase-doc` skill and template stable unless a necessary correction is demonstrated.

## Phase Plan

| Phase | Goal & Main Deliverables | Prerequisite | Exit Condition |
|---|---|---|---|
| [1 — Foundation](Phase1_Foundation.md) | Python/test setup, SQLite state, versioned approvals, fake Adapter, validation runner, ownership and resume | Review the overall plan and Phase 1 scope | Core failure/preservation scenarios pass and the user accepts the foundation |
| [2 — Planning](Phase2_Planning.md) | One real Adapter and permission checks; project registration, baseline checks, plans, requirements mapping and code summary | Phase 1 accepted; AI tool selected | A prepared project yields a reviewable plan; unapproved execution and unsupported risky actions are blocked |
| [3 — Workflow](Phase3_Workflow.md) | Developer → validation → separate Reviewer, bounded corrections, records, minimum reporting and acceptance | Phase 2 accepted | A separate example completes a small Phase including interruption/resume; runner A is verified and frozen |
| [4 — Dogfooding](Phase4_Dogfooding.md) | One small P0 self-development Phase, final report summaries, new/existing project acceptance and regressions | Phase 3 accepted; A/B isolation verified | Self-development is accepted and all MVP section 11 criteria have evidence |

Only Phase 1 has detailed Tasks now. Detail each later Phase using actual results before starting it. No dates or effort estimates are committed before Adapter feasibility is known.

## Requirements Mapping

| Source Requirement | Planned Coverage | Verification Evidence |
|---|---|---|
| §2, §4: prepared project, initialization and baseline | Phases 1–2 | Path/tool/command checks; actual passing, failing and zero-test examples |
| §5: plans, requirement coverage, code/reuse investigation | Phase 2; acceptance checks in Phases 3–4 | Plan inspection against specification/code; actual final checks for reused requirements |
| §6: sequential implementation, validation, separate review and bounded correction | Phases 1 and 3 | Fake failure scenarios followed by real small-Phase execution |
| §7: versioned approval, feedback, permissions and manual Git | Phases 1–3; final regression in Phase 4 | Approval invalidation, same-scope correction versus scope change, denied-operation checks |
| §8: SQLite, ownership, baseline preservation and resume | Phase 1; real-process integration in Phases 2–3 | Competing processes, interruption, file mismatch and metadata-only Git change scenarios |
| §8.1: AI calls, timing, review findings and resolution evidence | Minimal actual-call records in Phase 2; complete records in Phase 3; summaries in Phase 4 | Records checked for retries, interruptions and duplicate findings/calls |
| §9: reports, reused-function checks and user acceptance | Minimum in Phase 3; complete in Phase 4 | Final code/plan-linked evidence; failed and unverified mandatory conditions block completion |
| §10–11: isolated dogfooding, new/existing examples and MVP acceptance | Phases 3–4 | Frozen runner version, self-development report, two accepted external example Phases and core regressions |

P1 specification review and distributed templates, MVP2 standalone requests, and other P2 features are excluded. Developer fixtures are test assets, not the P1 template product.

## Dogfooding & Shared Completion Rules

1. These first documents are created using the skill with existing coding tools. This is preparation, not completed harness dogfooding.
2. Once Phase 2 produces plans, use its output when reviewing the next harness Phase. Record manual corrections; this only exercises planning.
3. Phase 3 must first prove the full flow in a separate example, including stop/resume. Freeze runner A outside the editable development target B, with separate protected runtime records.
4. In Phase 4, A develops a small remaining P0 feature in B. The initial candidate is the per-role AI-call summary in the results report. Record events and show minimum results before then; reserve only the report enhancement for this self-development exercise.
5. Validate B separately with preserved core regressions; the user accepts it and manually chooses it for a subsequent run. Never replace A during an active run.

For every implementation Phase, required checks must run on the final code and match the approved plan. Record failed, interrupted, missing and zero-test outcomes accurately. User acceptance is separate from technical completion; neither a document update nor an approval can turn missing evidence into a pass. Reused mandatory functionality also needs final verification.

Preserve pre-existing changes, stop on unexpected file differences, and keep runtime DB/logs outside OneDrive. Actual permissions must prevent workers and tests from modifying the running policies or approval DB; a different folder alone is insufficient. Git writes, deployment and UI checks remain manual. Significant scope/risk changes follow the specification's approval rules; unchanged approved work does not require repeated approval.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created four development Phases from lean MVP 0.4 and the agreed Python + pytest choice. No implementation or product verification performed. |
| 2026-09-15 | Phase 1 authorized and implemented; 43 tests passed. Recorded concrete environment and remaining acceptance/real-integration boundaries. |

---

# 개발 Phase — 축소 MVP

**문서 버전**: 0.2 · **작성일**: 2026-09-15 · **상태**: Phase 1 기술 검증 완료·사용자 인수 대기. Phase 2–4 미시작.

## 목표와 결정 사항

[축소 MVP 계획서 0.4](../Draft/ai-development-harness-lean-mvp-plan.md)의 P0 로컬 CLI를 개발한다. 기획서 10장의 구현 순서를 따른다. P0는 우선순위이며 아래 Phase 번호는 개발 단계다.

- **확정**: 하네스 개발은 Windows/Python 3.12.10 + pytest 9.1.1, 실행 상태는 SQLite, 프로세스 식별은 psutil 7.2.2를 사용한다. 버전은 `.python-version`과 `requirements-dev.lock`에 기록했다. Phase 문서는 영문·국문 전체 내용을 함께 작성한다.
- **제안**: 별도 실제 검증 예제도 Python + pytest로 통일한다. Phase 1 가짜 Adapter 예제는 이미 이 구성을 사용한다.
- **Phase 2 연결 전 결정**: AI 실행 도구 한 개, 인증 방식, 실제로 집행 가능한 권한 경계. 현재 사용하는 코딩 환경이 제품의 Adapter 선택을 자동으로 결정하지 않는다.
- **현재 저장소**: Phase 1 패키지·CLI, 트랜잭션 기반 SQLite 상태, 가짜 Adapter, 실제 명령 검증, 승인·파일 보호와 재개를 구현했다. 검사 43개와 별도 CLI 시연이 통과했다. 실제 AI 연결과 권한 분리는 미구현이다.
- **개발 방식**: 초기 기반은 기존 코딩 도구로 만들고 하네스 사용 범위를 점진적으로 넓힌다. 개발 중에는 Phase 문서를 보완하며, 필요한 수정 근거가 있는 경우 외에는 `phase-doc` 스킬과 템플릿을 유지한다.

## 전체 Phase 계획

| Phase | 목표와 주요 산출물 | 선행 조건 | 종료 조건 |
|---|---|---|---|
| [1 — 실행 기반](Phase1_Foundation.md) | Python·테스트 환경, SQLite 상태, 버전에 연결된 승인, 가짜 Adapter, 검사 실행, 실행 소유권·재개 | 전체 계획과 Phase 1 범위 검토 | 핵심 실패·파일 보존 시나리오 검증 및 사용자 인수 |
| [2 — 실제 연결과 계획](Phase2_Planning.md) | 실제 Adapter 한 개와 권한 확인, 프로젝트 등록·기본 검사·계획·대응표·코드 요약 | Phase 1 인수, AI 도구 선정 | 준비된 프로젝트에서 검토 가능한 계획 생성, 미승인 실행·지원하지 않는 위험 동작 차단 |
| [3 — 전체 실행 흐름](Phase3_Workflow.md) | 구현 → 검증 → 별도 리뷰, 제한된 수정, 실행 기록, 최소 보고·인수 | Phase 2 인수 | 별도 예제의 작은 Phase를 중단·재개 포함 완료하고 실행용 A 검증·고정 |
| [4 — 자체 개발과 MVP 인수](Phase4_Dogfooding.md) | 작은 P0 자체 기능 개발, 최종 보고서 집계, 신규·기존 프로젝트 인수·회귀 검증 | Phase 3 인수, A/B 분리 검증 | 자체 개발 인수 및 기획서 11장 전체 완료 기준의 근거 확보 |

현재는 Phase 1만 Task로 상세화한다. 이후 Phase는 앞 단계의 실제 결과를 반영해 착수 전에 상세화한다. Adapter 실현 가능성을 확인하기 전에는 일정·소요 시간을 확정하지 않는다.

## 요구사항 대응표

| 기획서 요구사항 | 처리 계획 | 확인할 근거 |
|---|---|---|
| 2·4장: 준비된 프로젝트, 초기화·기본 검사 | Phase 1–2 | 경로·도구·명령 확인, 실제 통과·실패·테스트 0개 예제 |
| 5장: 계획·요구사항 대응·코드와 재사용 조사 | Phase 2, Phase 3–4 인수 시 검증 | 기획·코드와 계획 대조, 재사용 요구사항의 실제 최종 검사 |
| 6장: 순차 구현·검증·별도 리뷰·제한된 수정 | Phase 1·3 | 가짜 실패 시나리오와 실제 작은 Phase 실행 |
| 7장: 버전별 승인·피드백·권한·Git 수동 처리 | Phase 1–3, Phase 4 최종 회귀 검증 | 승인 무효화, 같은 범위 수정과 범위 변경 구분, 금지 동작 차단 검사 |
| 8장: SQLite·소유권·기준선 보존·재개 | Phase 1, Phase 2–3 실제 프로세스 연결 | 두 프로세스 경쟁·중단·파일 불일치·Git 메타데이터만 변경된 상황 |
| 8.1장: AI 호출·시간·리뷰 지적과 처리 근거 | Phase 2 실제 호출 최소 기록, Phase 3 전체 기록, Phase 4 집계 | 재시도·중단·동일 지적과 호출의 중복 여부 대조 |
| 9장: 보고서·재사용 검증·사용자 인수 | Phase 3 최소 구현, Phase 4 완성 | 최종 코드·계획에 연결된 근거, 필수 조건 실패·미검증 시 완료 차단 |
| 10–11장: 분리된 자체 개발·신규와 기존 예제·MVP 인수 | Phase 3–4 | 고정 실행 버전, 자체 개발 보고서, 외부 예제 두 Phase 인수와 핵심 회귀 검사 |

P1 기획 검토·배포용 템플릿, MVP2 독립 수정 요청 및 나머지 P2는 제외한다. 개발 검증용 예제는 테스트 자산이며 P1 템플릿 제품이 아니다.

## Dogfooding과 공통 완료 규칙

1. 최초 문서는 기존 코딩 도구와 스킬로 작성한다. 준비 작업이며 하네스 dogfooding 완료 실적이 아니다.
2. Phase 2에서 계획 생성이 가능해지면 다음 하네스 Phase 검토에 생성 결과를 사용한다. 수동 보완을 기록하며, 이 단계는 계획 기능만 사용하는 것이다.
3. Phase 3에서 별도 예제로 전체 흐름과 중단·재개를 먼저 확인한다. 수정 대상 B 밖에 실행용 A를 고정하고 실행 기록을 별도로 보호한다.
4. Phase 4에서는 A로 B의 작은 미완료 P0 기능을 개발한다. 첫 후보는 결과 보고서의 역할별 AI 호출 수 요약이다. 그 전에 이벤트 기록과 최소 결과 확인을 준비하며, 보고서 개선 부분만 자체 개발 대상으로 남긴다.
5. 보존한 핵심 회귀 검사와 별도 실행으로 B를 검증한다. 사용자가 인수하고 다음 Run에 사용할 버전을 수동 선택한다. 실행 중인 A는 교체하지 않는다.

각 구현 Phase의 필수 검사는 최종 코드에서 실행하고 승인된 계획에 연결한다. 실패·중단·미실행·테스트 미발견을 정확히 기록한다. 사용자 인수와 기술적 완료를 구분하며, 문서 갱신이나 승인만으로 검증 근거가 없는 항목을 통과 처리하지 않는다. 필수 재사용 기능도 최종 검증이 필요하다.

기존 변경을 보존하고 예상 밖 파일 차이에서는 중단하며 실행 DB·로그는 OneDrive 밖에 둔다. 작업 에이전트와 테스트가 실행 중인 정책·승인 DB를 변경하지 못하도록 실제 권한으로 제한해야 하며, 폴더만 나누는 것으로 충분하지 않다. Git 쓰기·배포·UI 확인은 수동이다. 중요한 범위·위험 변경은 기획서의 승인 규칙을 따르고, 동일한 승인 범위의 작업에 반복 승인을 요구하지 않는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 축소 MVP 0.4와 합의한 Python + pytest를 바탕으로 4개 개발 Phase 작성. 구현·제품 검증은 수행하지 않음. |
| 2026-09-15 | Phase 1 승인·구현, 검사 43개 통과. 실제 개발 환경과 남은 사용자 인수·실제 연결 경계를 기록. |
