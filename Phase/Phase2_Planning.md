# Phase 2 — Planning `🚧 In Progress`

> Connect one AI tool and generate a plan the user can review against the project.

**Prerequisites**: [Phase 1](Phase1_Foundation.md) accepted. The user selected ChatGPT authentication through Codex CLI and authorized implementation on 2026-09-18. Planner capability enforcement has been verified with the installed CLI.

**Technology**: Python + pytest, SQLite; inherit the version fixed in Phase 1.

**Plan status**: The implemented scope passed automated checks and the small live example. Planning-only dogfooding stopped on open issue P2-01; its fix and further verification are deferred at the user's request. Task 2.6 and Phase acceptance remain pending. Requirements come from the user-selected specification; related code in the designated project may also be analyzed. Decision Desk is the first later real-use project, after harness dogfooding. Temporary test projects remain integration fixtures.

## Overview

Implement project registration/baseline checks and the real Planner Adapter, following specification §§2, 5 and 7.3. Verify actual execution permissions before granting the Adapter access. Use generated plans when reviewing the next harness Phase; this is planning-only self-use.

## Deliverables

| # | Module / Artifact | Status |
|---|---|---|
| 1 | One real Adapter and documented permission/authentication boundaries | ✅ Verified |
| 2 | Project registration, configuration and baseline checks | ✅ Verified |
| 3 | Overall/current Phase plans, requirements mapping and relevant-code summary | ✅ Verified |
| 4 | Plan review/approval connection and actual Planner-call records | ✅ Verified |

## Verification & Exit Criteria

| Task | Work / Acceptance criteria | Verification |
|---|---|---|
| 2.1 | Connect the installed Codex CLI using existing ChatGPT authentication; enforce and record a Planner permission boundary before project analysis. | Local capability/permission probes and a minimal real call; prohibited access must fail before effects. |
| 2.2 | Register a specification, explicit related-code inputs and validation commands; preserve user files and keep runtime state outside OneDrive. | Invalid paths, links, unavailable inputs, concurrent registration and configuration changes. |
| 2.3 | Run actual baseline validation before planning; stop on failed, missing, skipped, interrupted or zero tests. | Real subprocess fixtures and existing validation regressions. |
| 2.4 | Generate and validate overall/current Phase plans, requirement mapping, code evidence, uncertainties and English/Korean documents. | Structured-output validation, source-reference checks and manual comparison of a real generated plan. |
| 2.5 | Record attempts, interrupted calls and approval waiting; bind approval to the reviewed input/plan versions without starting implementation. | Resume, stale evidence, idempotent approval, malformed responses and provider failures. |
| 2.6 | Verify the integrated CLI and use the Planner on the harness's next Phase; record manual corrections and remaining boundaries. | Full regression suite, temporary example and planning-only dogfooding. User result acceptance remains separate. |

- A prepared small project passes actual baseline tests and yields the overall Phase plan plus current Tasks, acceptance criteria and verification methods. Missing tools/documents/commands, failed checks and zero tests stop with actionable information.
- Plan contents identify related code and conventions, distinguish explicit rules from inferred patterns, and map requirements to current/later work, reuse or justified exclusion. Blocking ambiguities are surfaced. Reuse has a Phase and verification method, not an assumed pass.
- User approval references the reviewed plan version. Changed scope requires updated approval; unchanged approval is retained. Planning does not authorize implementation.
- Verify allowed file access and denied edits to policy/approval storage, Git writes, installation and unsupported external transfer. Permit only the selected AI service communication needed for the authorized call. Unsupported risky operations stop before execution; prompt instructions alone are not evidence of isolation.
- Record actual Planner call attempts, stage times, interruptions and approval waiting separately. Project-wide planning calls are not duplicated across Phases; unavailable token/cost data is not invented.

**Evidence**: pytest integration fixtures for registration/approval; real Adapter permission probes and a saved plan manually compared with source requirements/code. Completion requires successful checks and user acceptance.

**Results (2026-09-18)**: All **123 tests passed** (63 existing, 60 new); `pip check` reported no broken requirements. A minimal authenticated live call and one real example planning call succeeded. The example's two baseline tests passed; one AI attempt produced a bilingual plan with five mapped requirements and two Tasks. Manual comparison confirmed the proposed negative-input validation matches the specification and existing positive/zero behavior. Test approval was idempotent, fake execution was blocked, and the source files stayed unchanged. This fixture approval is not user acceptance of Phase 2.

- Permission checks use the actual Codex executable against a loopback provider: eight synthetic requests, zero AI calls, and seven forced tool categories rejected. No marker file was written. Every real planning call repeats this check and pins the executable hash.
- Regression coverage includes stale specification/code/configuration, unexpected user files, hard links, artifact tampering, revision approval invalidation, blocking questions, malformed/duplicate JSON, baseline failures and interrupted publication. Actual inert subprocesses verify timeout/interrupt cleanup and unknown completion time; they do not consume AI calls.
- Local evidence lives under `%LOCALAPPDATA%/development-tools-harness/`: `phase2-tests.xml`, `phase2-probes/live-smoke-result.json`, and `phase2-demo/d98457898bca4153a09473f370ea0a47/`. The example run is `ebbf7cd2ca4e40a786da97b55614c685`; `approval-checks.json` records the CLI approval/blocked-execution checks.

### Open issue P2-01 — Long Windows runtime path (fix deferred)

- **Observed**: On 2026-09-18, planning-only dogfooding on a separate harness snapshot passed all 123 baseline tests, then stopped while creating `<attempt-id>.schema.json`. The call directory was 217 characters and the complete schema path was 262 characters. This environment returned `[Errno 2] No such file or directory` at `codex_adapter.py`'s schema write; the path length is the identified cause to address.
- **Impact**: The Planner process had not been dispatched (`dispatched=false`), so this dogfooding attempt made zero AI calls and produced no Phase 3 plan. The successful small example and prior test results remain valid; they do not establish that this longer-path case works. Task 2.6's harness planning dogfooding remains incomplete.
- **Evidence**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/2085ced4918341da99a99ed03df06676/plan.json`; run `729a78364bd746bbb2be2439996ae018`, attempt `97677feca038475aae33826fb18cb3b7`.
- **Proposed follow-up, not implemented**: Shorten filenames inside each unique call directory, add a regression for the reproduced path length, then rerun the relevant checks and harness planning dogfooding. Confirm the log/schema paths remain traceable to their attempt records.
- **User decision**: Record only for now. Do not apply the filename change or add/run its regression until development of this issue resumes. Phase 2 remains in progress; this note is neither a fix nor acceptance evidence.

## Planner & Project Entry

### Purpose / Implementation Files

Project configuration/plans stay in the project; runtime DB/logs stay outside OneDrive.

| File | Responsibility |
|---|---|
| `src/development_harness/project.py` | Register explicit UTF-8 specification/code inputs, check paths/links/secrets and size limits, hash project inputs, preserve versioned artifacts. |
| `src/development_harness/codex_adapter.py` | Inspect ChatGPT login/version, apply the text-only capability profile, execute/stop the CLI and validate response events. |
| `src/development_harness/codex_probe.py` | Use a local synthetic provider to inspect the real tool manifest and force prohibited calls before any project analysis. |
| `src/development_harness/plan_schema.py` | Validate bilingual JSON, requirement/code source quotations, identifiers and Task dependencies; render English/Korean documents. |
| `src/development_harness/planning.py` | Coordinate registration, baseline checks, planning, interrupted recovery, revisions and input/version-bound human approval. |
| `src/development_harness/cli.py` | Expose planning commands alongside the explicit Phase 1 fixture commands. |
| `model.py`, `store.py`, `runner.py` in the same package | Share validation rules/storage/ownership; prevent real planning records from entering fake execution. |
| `tests/unit/test_planning.py`, `tests/integration/test_planning_cli.py` | Planning regressions, real baseline subprocesses, cleanup and installed-CLI permission probes. |

`harness-project.json` stores relative input paths, validation commands, model and timeout. Each reviewed version creates `Phase/Generated/<run-id>/vN/plan.json`, `Plan.md` and `Plan_ko.md`. The runtime retains exact transmitted inputs, call logs, baseline evidence and approval hashes. A planning attempt counts one dispatched CLI invocation, not an estimated number of underlying HTTP requests. Interrupted calls retain unknown end/duration; approval waiting is accumulated separately. No cost estimate is invented.

### Design Decisions

- Use Codex CLI with ChatGPT login. Authentication stays managed by Codex; no token is copied into project configuration or the harness database. A failed permission probe blocks live project analysis without blocking implementation and regression work.
- Verified version: **Codex CLI 0.154.0**, configured model **gpt-6-astra**, reasoning effort `medium`. The model defaults to the local Codex model setting or explicit `--model`. Other CLI versions fail closed until compatibility is reviewed; there is no silent API-key/provider fallback.
- The Planner receives a bounded JSON packet through stdin: at most 128,000 bytes per selected file and 320,000 bytes total. All file/process/web/app/agent tools, plugins, hooks, user/project rules and host skill discovery are disabled; the CLI also runs with read-only writes and approval policy `never`. Its actual model tool manifest was empty. The host harness alone writes validated generated documents.
- A restrictive Windows read allowlist required the elevated Windows sandbox backend in this environment. No elevated setup was performed. The verified Phase 2 boundary is the removed model tool capabilities plus read-only write enforcement, **not a general OS read/network allowlist**. Baseline commands still run as trusted user-supplied commands. Isolation of Developer/test processes from runner A and approval storage remains a Phase 3 gate.
- Analyze only the designated specification and related project code. Treat project content as input data, not permission policy; do not include unrelated projects or credentials. Actual input files and versions must be inspectable.
- Introduce project/planning modules alongside the Phase 1 fake-runner contract; real plan approval must never launch fake implementation.
- Use temporary Python/pytest projects for integration checks, then planning-only harness dogfooding. Decision Desk follows self-development verification; its offline file/browser requirements need a later compatible validation setup.
- Use the `phase-doc` output structure as the planning reference without modifying the skill. Produce full English/Korean Phase documents, keep current Tasks concise and later Phases at outline level.
- Keep policy and approval writes owned by the harness, separated from worker permissions. Do not rely on project-controlled instructions to grant permissions.
- Start with one prepared Python/pytest example as proposed in the overview. The user prepares dependencies; no template installer or environment repair engine is added.

### Usage Example

From the repository root, after the README setup and `codex login` (skip login if already authenticated):

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningExample = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningExample -Recurse
& $harnessPython -m development_harness --project $planningExample doctor
& $harnessPython -m development_harness --project $planningExample register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json
& $harnessPython -m development_harness --project $planningExample plan
& $harnessPython -m development_harness --project $planningExample plan-status
```

Review the versioned `Plan.md`/`Plan_ko.md` and mapping before `plan-approve`. This command approves planning only. `baseline` runs tests without AI; `plan-resume` retries interrupted work explicitly. To revise, copy `plan.json` to a separate file outside the input baseline, edit it, and use `plan-revise --from <file>`; changed content creates a new version requiring approval. Resolve blocking questions there. `plan-cancel` preserves files/evidence and releases the run for a new registration. If source/configuration changes, inspect, cancel the unfinished run if necessary, then register again; stale approval is never reused.

## Prerequisites & Development Notes

Phase 1 storage, validation, approval and ownership regressions passed. Source quotations and mapping structure are checked automatically, but full semantic requirement coverage still needs human review. Live Developer/Reviewer orchestration and complete result acceptance are Phase 3 work. Decision Desk has not been registered or executed. Its eventual browser/application stack needs suitable baseline commands; current admission requires an actual pytest check. A project-local Git skill is a user development aid, not a Git capability granted to the harness agents.

## Change Log

| Date | Description |
|---|---|
| 2026-09-15 | Created the real-connection and planning outline; provider choice and later Task details left explicit. |
| 2026-09-18 | User authorized Phase 2 after selecting ChatGPT/Codex, specification plus related project code, harness dogfooding before Decision Desk, and the proposed implementation scope. Recorded Tasks 2.1–2.6 before implementation. No separate dev-log skill is available. |
| 2026-09-18 | Implemented real planning, bounded inputs, capability probes, baseline admission, bilingual evidence and versioned approval/recovery. Verified 123 tests and the actual example. Added the project-local `harness-github-push` skill without committing/pushing. Separate dev-log omitted because the skill is unavailable. Phase acceptance remains pending. |
| 2026-09-18 | Recorded P2-01 after harness planning dogfooding stopped before AI dispatch on a 262-character schema path. At the user's request, deferred the filename change, regression and rerun; Task 2.6 remains incomplete. |

---

# Phase 2 — 실제 연결과 계획 `🚧 진행 중`

> AI 도구 한 개를 연결하고 사용자가 프로젝트와 대조해 검토할 수 있는 계획을 생성한다.

**선행 조건**: [Phase 1](Phase1_Foundation.md) 인수 완료. 사용자는 ChatGPT 인증을 사용하는 Codex CLI를 선정하고 2026-09-18 구현을 승인했다. 설치된 CLI에서 Planner 도구 권한 집행을 검증했다.

**기술 구성**: Python + pytest, SQLite. Phase 1에서 고정한 버전을 따른다.

**계획 상태**: 구현 범위의 자동 검사와 작은 실제 예제 검증을 마쳤다. 하네스 계획 기능 dogfooding은 미해결 P2-01에서 중단됐으며 사용자 요청으로 수정·추가 검증을 보류한다. Task 2.6과 Phase 사용자 인수는 대기 중이다. 요구사항은 사용자가 지정한 기획문서를 기준으로 하며 지정 프로젝트의 관련 코드도 분석할 수 있다. 하네스 dogfooding 이후 Decision Desk를 첫 실사용 프로젝트로 진행한다. 임시 테스트 프로젝트는 통합 검사용으로 유지한다.

## 개요

기획서 2·5·7.3장에 따라 프로젝트 등록·기본 검사와 실제 Planner Adapter를 구현한다. Adapter에 접근 권한을 주기 전에 실제 실행 권한을 검증한다. 생성한 계획을 다음 하네스 Phase 검토에 활용하며, 이 단계는 계획 기능만 자체 사용하는 것이다.

## 완료 예정 / 완료 항목

| # | 모듈 / 산출물 | 상태 |
|---|---|---|
| 1 | 실제 Adapter 한 개와 권한·인증 경계 기록 | ✅ 검증 |
| 2 | 프로젝트 등록·설정·기본 검사 | ✅ 검증 |
| 3 | 전체·현재 Phase 계획, 요구사항 대응표, 관련 코드 요약 | ✅ 검증 |
| 4 | 계획 검토·승인 연결과 실제 Planner 호출 기록 | ✅ 검증 |

## 검증 및 종료 조건

| Task | 작업 내용 / 완료 기준 | 검증 방법 |
|---|---|---|
| 2.1 | 설치된 Codex CLI의 ChatGPT 인증을 연결하고 프로젝트 분석 전에 Planner 권한 경계를 집행·기록한다. | 로컬 기능·권한 시험과 최소 실제 호출. 금지한 접근은 영향 발생 전에 실패해야 한다. |
| 2.2 | 기획문서·명시적인 관련 코드 입력·검증 명령을 등록한다. 사용자 파일을 보존하고 실행 상태는 OneDrive 밖에 둔다. | 잘못된 경로·링크·입력 누락·등록 경쟁·설정 변경 검사. |
| 2.3 | 계획 생성 전 실제 기본 검사를 수행한다. 실패·도구 누락·생략·중단·테스트 0개는 중단한다. | 실제 하위 프로세스 예제와 기존 검증 회귀 검사. |
| 2.4 | 전체·현재 Phase 계획, 요구사항 대응표, 코드 근거, 불확실성과 영문·국문 문서를 생성·검사한다. | 구조화된 응답·원문 참조 검사와 실제 생성 계획의 수동 대조. |
| 2.5 | 호출 시도·중단·승인 대기를 기록하고 검토한 입력·계획 버전에 승인을 연결한다. 승인으로 구현을 시작하지 않는다. | 재개·오래된 근거·동일 승인 유지·잘못된 응답·제공자 실패 검사. |
| 2.6 | 통합 CLI를 검증하고 하네스 다음 Phase 계획에 Planner를 사용한다. 수동 보완과 남은 경계를 기록한다. | 전체 회귀 검사·임시 예제·계획 기능 dogfooding. 사용자 결과 인수는 별도다. |

- 준비된 작은 프로젝트에서 실제 기본 테스트가 통과하고 전체 Phase와 현재 Task·완료 기준·검증 방법을 생성한다. 도구·문서·명령 누락, 검사 실패·테스트 0개는 준비할 내용을 안내하고 중단한다.
- 계획에 관련 코드·규칙을 기록하고 명시 규칙과 추정 패턴을 구분한다. 요구사항을 현재·후속 작업, 재사용 또는 근거 있는 제외에 연결하고 구현을 막는 불확실성을 표시한다. 재사용은 Phase·검증 방법에 연결하며 통과로 추정하지 않는다.
- 사용자 승인은 검토한 계획 버전에 연결한다. 범위가 바뀌면 갱신된 승인이 필요하며 동일한 승인은 유지한다. 계획 생성 자체가 구현을 승인하지 않는다.
- 허용 파일 접근, 정책·승인 저장소 변경 차단, Git 쓰기·설치·지원하지 않는 외부 전송 차단을 확인한다. 승인된 호출에 필요한 선택 AI 서비스 통신만 허용한다. 지원하지 않는 위험 작업은 실행 전에 중단하며 프롬프트 지침만으로 분리를 입증하지 않는다.
- 실제 Planner 호출 시도·단계 시간·중단·승인 대기를 구분해 기록한다. 전체 계획 호출을 여러 Phase에 중복 합산하지 않으며 제공되지 않은 토큰·비용을 만들지 않는다.

**검증 근거**: 등록·승인의 pytest 통합 예제, 실제 Adapter 권한 시험, 생성 계획과 원문 요구사항·코드의 수동 대조. 검사 통과와 사용자 인수가 완료 조건이다.

**결과(2026-09-18)**: 전체 **123개 검사 통과**(기존 63개, 신규 60개), `pip check` 의존성 이상 없음. 인증을 사용하는 최소 실제 호출과 실제 예제 계획 생성이 성공했다. 예제 기본 테스트 2개가 통과한 후 AI 호출 시도 1회로 요구사항 5개·Task 2개의 영문·국문 계획을 생성했다. 원문·코드 수동 대조에서 음수 입력 검증과 기존 양수·0 동작 유지가 일치했다. 검사 목적의 계획 승인·재승인은 동일하게 유지됐고 가짜 실행은 차단됐으며 소스 파일은 변경되지 않았다. 이 예제 승인은 Phase 2 사용자 인수가 아니다.

- 권한 검사는 실제 Codex 실행 파일과 루프백 제공자를 사용한다. 합성 요청 8회, AI 호출 0회이며 강제로 요청한 도구 7종이 거부됐다. 금지 쓰기 표식 파일은 생성되지 않았다. 실제 계획 호출마다 검사를 반복하고 실행 파일 해시를 고정한다.
- 기획서·코드·설정 변경, 예상 밖 사용자 파일, 하드링크, 산출물 변조, 수정본 재승인, 차단 질문, 잘못된·중복 JSON, 기본 검사 실패, 문서 기록 중단을 회귀 검사했다. 실제 무해한 하위 프로세스로 시간 초과·중단 정리와 미확정 시간 기록을 확인했으며 AI 호출은 사용하지 않는다.
- 로컬 근거는 `%LOCALAPPDATA%/development-tools-harness/`의 `phase2-tests.xml`, `phase2-probes/live-smoke-result.json`, `phase2-demo/d98457898bca4153a09473f370ea0a47/`에 있다. 예제 Run은 `ebbf7cd2ca4e40a786da97b55614c685`이며 `approval-checks.json`에 CLI 승인·실행 차단 검사를 기록했다.

### 미해결 P2-01 — Windows 실행 경로 길이 문제(수정 보류)

- **재현 내용**: 2026-09-18 하네스 별도 복사본의 계획 기능 dogfooding에서 기본 테스트 123개가 통과한 뒤 `<attempt-id>.schema.json` 생성 중 중단됐다. 호출 폴더 경로는 217자, 전체 스키마 경로는 262자였다. 이 환경의 `codex_adapter.py` 스키마 쓰기에서 `[Errno 2] No such file or directory`가 발생했으며 경로 길이를 보완할 원인으로 확인했다.
- **영향**: Planner 프로세스 실행 전(`dispatched=false`)이므로 해당 dogfooding 시도의 실제 AI 호출은 0회이고 Phase 3 계획은 생성되지 않았다. 작은 실제 예제와 기존 검사 통과 결과는 유지되지만 긴 경로의 정상 동작까지 입증하지 않는다. Task 2.6의 하네스 계획 dogfooding은 미완료다.
- **근거**: `%LOCALAPPDATA%/development-tools-harness/phase2-dogfood/2085ced4918341da99a99ed03df06676/plan.json`, Run `729a78364bd746bbb2be2439996ae018`, 시도 `97677feca038475aae33826fb18cb3b7`.
- **후속 조치 제안·미구현**: 호출별 고유 폴더 안의 파일명을 짧게 바꾸고, 재현된 경로 길이의 회귀 검사를 추가한 뒤 관련 검사와 하네스 계획 dogfooding을 다시 수행한다. 로그·스키마 경로와 호출 기록의 연결도 확인한다.
- **사용자 결정**: 우선 메모만 남긴다. 이 항목의 개발을 재개하기 전까지 파일명 수정과 해당 회귀 검사 추가·실행을 보류한다. Phase 2는 진행 중이며 이 메모를 수정 완료나 인수 근거로 처리하지 않는다.

## Planner와 프로젝트 진입

### 목적 / 구현 파일

프로젝트 설정·계획은 프로젝트에, 실행 DB·로그는 OneDrive 밖에 둔다.

| 파일 | 역할 |
|---|---|
| `src/development_harness/project.py` | UTF-8 기획서·코드 입력 등록, 경로·링크·비밀정보·크기 검사, 프로젝트 입력 해시와 버전별 산출물 보존. |
| `src/development_harness/codex_adapter.py` | ChatGPT 로그인·버전 확인, 텍스트 전용 도구 정책 적용, CLI 실행·중단과 응답 이벤트 검사. |
| `src/development_harness/codex_probe.py` | 로컬 합성 제공자로 실제 도구 목록과 금지 도구 호출을 프로젝트 분석 전에 시험. |
| `src/development_harness/plan_schema.py` | 영문·국문 JSON, 요구사항·코드 원문 근거, 식별자·Task 의존 관계 검사 및 문서 생성. |
| `src/development_harness/planning.py` | 등록·기본 검사·계획 생성·중단 복구·수정·입력과 버전에 연결된 사용자 승인. |
| `src/development_harness/cli.py` | 계획 명령과 명시적인 Phase 1 예제 명령 제공. |
| 같은 패키지의 `model.py`, `store.py`, `runner.py` | 검증 규칙·저장·소유권 재사용, 실제 계획 기록의 가짜 구현 실행 차단. |
| `tests/unit/test_planning.py`, `tests/integration/test_planning_cli.py` | 계획 회귀 검사, 실제 기본 검사 프로세스, 중단 정리와 설치된 CLI 권한 시험. |

`harness-project.json`에는 상대 입력 경로·검증 명령·모델·시간 제한을 저장한다. 검토 버전마다 `Phase/Generated/<run-id>/vN/plan.json`, `Plan.md`, `Plan_ko.md`를 만든다. 실행 저장소에는 실제 전송 입력·호출 로그·기본 검사 근거·승인 해시를 보존한다. 호출 시도는 실행한 CLI 1회를 세며 내부 HTTP 요청 횟수를 추정하지 않는다. 중단 호출의 종료·소요 시간은 미확정으로 두고 승인 대기는 별도로 누적한다. 비용은 추정하지 않는다.

### 설계 결정 사항

- Codex CLI와 ChatGPT 로그인을 사용한다. 인증은 Codex가 관리하고 프로젝트 설정·하네스 DB에 토큰을 복사하지 않는다. 권한 시험 실패 시 실제 프로젝트 분석을 막되 구현·회귀 검사는 계속한다.
- 검증 버전은 **Codex CLI 0.154.0**, 설정 모델은 **gpt-6-astra**, 추론 수준은 `medium`이다. 모델은 로컬 Codex 설정 또는 명시적 `--model`을 따른다. 다른 CLI 버전은 호환성을 검토할 때까지 차단하며 API 키·다른 제공자로 자동 전환하지 않는다.
- Planner에는 선택한 파일당 최대 128,000바이트·총 320,000바이트의 JSON 입력을 표준 입력으로 전달한다. 파일·프로세스·웹·앱·에이전트 도구, 플러그인·훅·사용자 및 프로젝트 지침·호스트 스킬 탐색을 비활성화하고 읽기 전용 쓰기 제한과 승인 정책 `never`를 적용한다. 실제 모델의 도구 목록은 비어 있었다. 검증한 생성 문서는 호스트 하네스만 기록한다.
- Windows의 제한된 읽기 허용 목록은 이 환경에서 elevated sandbox backend를 요구해 권한 상승 설정은 수행하지 않았다. Phase 2에서 검증한 경계는 모델 도구 제거와 읽기 전용 쓰기 집행이며 **일반 OS 읽기·네트워크 허용 목록이 아니다**. 기본 검사는 여전히 신뢰하는 사용자 등록 명령으로 실행한다. Developer·테스트 프로세스와 실행본 A·승인 저장소의 분리는 Phase 3 통과 조건이다.
- 지정한 기획문서와 프로젝트 관련 코드만 분석한다. 프로젝트 내용은 입력 자료이며 권한 정책이 아니다. 무관한 프로젝트·인증정보를 포함하지 않고 실제 입력 파일·버전을 확인할 수 있게 한다.
- Phase 1 가짜 실행 계약과 함께 프로젝트·계획 모듈을 추가한다. 실제 계획 승인이 가짜 구현을 실행해서는 안 된다.
- 임시 Python/pytest 프로젝트로 통합 검사한 뒤 하네스 계획 기능을 dogfooding한다. Decision Desk는 자체 개발 검증 이후 진행하며 오프라인 파일·브라우저 요구에 맞는 검증 환경은 이후 연결한다.
- `phase-doc` 출력 구조를 계획 작성 기준으로 사용하고 스킬은 수정하지 않는다. Phase 문서는 영문·국문 전체로 작성하며 현재 Task는 간결하게, 이후 Phase는 개요로 유지한다.
- 정책·승인 기록 쓰기는 하네스가 담당하고 작업 에이전트의 권한과 분리한다. 프로젝트에서 바꿀 수 있는 지침에 권한 부여를 의존하지 않는다.
- 전체 개요에서 제안한 준비된 Python/pytest 예제 한 개로 시작한다. 의존성은 사용자가 준비하며 템플릿 설치기·환경 복구 엔진은 추가하지 않는다.

### 사용 예시

README 설치와 `codex login` 후 저장소 루트에서 실행한다. 이미 로그인되어 있으면 다시 인증할 필요가 없다.

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningExample = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningExample -Recurse
& $harnessPython -m development_harness --project $planningExample doctor
& $harnessPython -m development_harness --project $planningExample register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json
& $harnessPython -m development_harness --project $planningExample plan
& $harnessPython -m development_harness --project $planningExample plan-status
```

버전별 `Plan.md`·`Plan_ko.md`와 대응표를 검토한 뒤 `plan-approve`한다. 이 명령은 계획만 승인한다. `baseline`은 AI 없이 검사하고 `plan-resume`은 중단한 작업을 명시적으로 재개한다. 수정은 `plan.json`을 입력 기준선 밖의 별도 파일로 복사·편집한 후 `plan-revise --from <파일>`로 반영한다. 변경본은 새 버전이므로 재승인하며 차단 질문도 수정본에서 해결한다. `plan-cancel`은 파일·근거를 보존하고 새 등록을 허용한다. 소스·설정이 바뀌면 확인 후 필요 시 미완료 Run을 취소하고 다시 등록한다. 오래된 승인을 재사용하지 않는다.

## 선행 조건 및 개발 시 주의사항

Phase 1의 저장·검증·승인·소유권 회귀 검사가 통과했다. 원문 인용·대응 구조는 자동 검사하지만 의미상 전체 요구사항 반영 여부는 사람이 검토해야 한다. 실제 Developer·Reviewer 실행 연결과 전체 결과 인수는 Phase 3 범위다. Decision Desk는 등록·실행하지 않았다. 향후 브라우저·앱 기술 구성에 맞는 기본 검증 명령을 연결해야 하며 현재 진입에는 실제 pytest 검사가 필요하다. 프로젝트 전용 Git 스킬은 사용자 개발 보조 기능이며 하네스 에이전트에 Git 권한을 부여하지 않는다.

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-09-15 | 실제 연결·계획 개요 최초 작성. 제공자 선정과 후속 Task 상세화는 미결정으로 명시. |
| 2026-09-18 | 사용자가 ChatGPT/Codex, 기획문서와 프로젝트 관련 코드 분석, 하네스 dogfooding 후 Decision Desk 적용, 제시한 구현 범위를 확인하고 Phase 2를 승인했다. 구현 전에 Task 2.1–2.6을 기록했다. 별도 dev-log 스킬은 없다. |
| 2026-09-18 | 실제 계획, 입력 범위 제한, 도구 권한 시험, 기본 검사 진입, 영문·국문 근거, 버전별 승인·복구를 구현했다. 검사 123개와 실제 예제를 검증했다. 프로젝트 전용 `harness-github-push` 스킬을 추가했으며 커밋·푸시는 수행하지 않았다. dev-log 스킬이 없어 별도 기록은 생략했다. Phase 사용자 인수는 대기 중이다. |
| 2026-09-18 | 하네스 계획 dogfooding이 AI 실행 전 262자 스키마 경로에서 중단된 P2-01을 기록했다. 사용자 요청으로 파일명 수정·회귀 검사·재실행은 보류하며 Task 2.6은 미완료로 유지한다. |
