[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI builds, the harness verifies, and humans approve only what matters.

A planned local CLI for semi-automated development: turn a Markdown specification into phased work, implement and test approved tasks, review the results, and present the evidence for human acceptance.

## Current status

**Phases 1–2 are accepted and completed; Phase 3 is in progress.** The Windows/Python 3.12 CLI registers prepared projects, runs baseline tests and generates versioned bilingual plans using Codex and the repository phase-doc skill. P3-T1–T2 preparation, actual roles and isolated pytest were verified on 2026-09-21 with **265 passing tests** and a two-call live example. P3-T3 added execution authorization and durable records, verified with **378 passing tests** and `pip check` on 2026-09-22. P3-T4 connects sequential development, isolated validation, independent review, bounded corrections and final checks through `workflow-run`. P3-T5 adds explicit interruption recovery through `workflow-resume`. P3-T6 implements minimum JSON reports, feedback routing and evidence-bound user acceptance. P3-T7 external-example technical verification passed with two real role calls, one interruption/reuse, eight final tests and six independent checks. R1/M1 confirmations and explicit user acceptance were recorded on 2026-09-23, completing T7; P3-T8 fixed runner A has not started. [Implementation and verification](Phase/Phase3_Workflow.md).

The roadmap below summarizes the [lean MVP plan, revision 0.4](Draft/ai-development-harness-lean-mvp-plan.md). The usage sections identify implemented behavior.

## Phase 1 setup and example

Verified with Windows, Python 3.12.10 and pytest 9.1.1. Run these commands from the repository root in PowerShell; the environment and runtime records stay outside OneDrive.

```powershell
py -3.12 -m venv "$env:LOCALAPPDATA\development-tools-harness\venv"
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
& $harnessPython -m pip install -r requirements-dev.lock
& $harnessPython -m pip install --no-build-isolation -e .
& $harnessPython -m pytest
& $harnessPython -m development_harness --help
```

Copy the example to a fresh folder and run its explicit JSON plan:

```powershell
$demoProject = Join-Path $env:TEMP ('harness-example-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/minimal_project -Destination $demoProject -Recurse
& $harnessPython -m development_harness --project $demoProject prepare --plan tests/fixtures/fake-plan.json
& $harnessPython -m development_harness --project $demoProject approve
& $harnessPython -m development_harness --project $demoProject run --steps 1
& $harnessPython -m development_harness --project $demoProject resume
& $harnessPython -m development_harness --project $demoProject status
```

The final state should be `awaiting_acceptance`. Inspect the changed files, validation outcomes and log paths in the JSON output. After reviewing the result, run `accept` with the same project arguments. `cancel` preserves files and evidence while allowing a new run. Unchanged approved plans need no repeated approval. Changed plans or unexpected file contents stop execution; restore the intended input or cancel and prepare a new run after inspection.

- `prepare` records the file baseline and approved-command candidates; it does not yet perform Phase 2's baseline-test admission check. `run` before `approve` stays in approval waiting.
- The [example input](tests/fixtures/fake-plan.json) specifies a Phase, sequential Tasks, per-attempt `writes` and fake `review` outcomes, plus registered validation `argv` arrays. `{python}` resolves to the harness interpreter. At least one `kind: "pytest"` command is required; default correction limit is two.
- Developer/Reviewer output is synthetic; real AI calls are zero. Validation commands run with the user's permissions and must be trusted. Windows Job containment manages child-process lifetime; it is not the planned permission sandbox.
- Runtime DB, command logs and pytest XML live under `%LOCALAPPDATA%/development-tools-harness/runtime/`. `--state-dir` can choose another local directory outside the project and OneDrive; project ownership still applies across state directories.
- Baselines hash ordinary files, excluding `.git`, `.venv`, `__pycache__`, `.pytest_cache` and `.harness-output`. Linked paths are unsupported. Existing edits are included and unexpected changes are preserved.
- Tests that fail, do not execute, time out, discover zero tests or skip required cases do not pass. Interrupted checks are rerun after checking recorded process identities. Unknown partial file content stops for inspection.

Implementation and verification details are in [Phase 1](Phase/Phase1_Foundation.md). The editable installation above is a development setup; the fixed runtime required for dogfooding is prepared in Phase 3.

## Phase 2 planning with the project skill

Use a prepared project with actual passing pytest tests. From this repository, copy the planning fixture to a new local folder:

```powershell
$harnessPython = "$env:LOCALAPPDATA\development-tools-harness\venv\Scripts\python.exe"
$planningProject = Join-Path $env:TEMP ('harness-planning-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath tests/fixtures/planning_project -Destination $planningProject -Recurse
& $harnessPython -m development_harness --project $planningProject doctor
& $harnessPython -m development_harness --project $planningProject register --spec spec.md --context value.py test_value.py --validation tests/fixtures/planning-checks.json --planner-timeout 600
& $harnessPython -m development_harness --project $planningProject plan
& $harnessPython -m development_harness --project $planningProject plan-status
```

The harness reads [the project skill](.agents/skills/phase-doc/SKILL.md) and [its template](.agents/skills/phase-doc/references/phase-template.md) from its own installation and passes them to the Planner. The template's `harness:*` blocks render validated plan data. Each `Phase/Generated/<run-id>/vN/` contains `plan.json`, `Plan.md`/`Plan_ko.md` overview indexes, bilingual `PhaseN_EnglishName.md` documents and `writing-profile.json` with exact writing rules/version/hashes. Only the current Phase has detailed Tasks. Inspect the documents before `plan-approve`; approval is planning-only.

Edit template headings/layout while retaining required `{{slots}}`; changes apply on the next `register`. Existing Runs and `plan-revise --from <file>` revisions retain their pinned rules. Older Runs without a writing profile keep their original format. Wheels include the same resources. Target-project/global skills are not auto-loaded; planning does not update README or development logs. Source quotations are rendered as code evidence so relative links are not misinterpreted. See [Phase 2](Phase/Phase2_Planning.md) for verification and limitations.

## Phase 3 worker investigation

`workflow-doctor` now tests an administrator-free Windows AppContainer on fresh synthetic files and owned local listeners, including child processes. It copies Python into the disposable probe directory and creates/removes per-user application profiles. It does not call AI, edit target-project files or approve implementation. No administrator account/firewall setup is requested.

```powershell
& $harnessPython -m development_harness --project . workflow-doctor
# Reproduce the earlier Codex candidate investigation explicitly:
& $harnessPython -m development_harness --project . workflow-doctor --backend codex-unelevated
```

Read the JSON output and saved `report.json` under `evidence_directory`. Exit code 1 means a failed/incomplete probe. On this standard-user Windows 10 environment, AppContainer passed role/file/token checks and blocked all 24 parent/child TCP/UDP IPv4/IPv6 attempts against owned loopback listeners. A deadline test also stopped the process and child. `ready=true` means this synthetic candidate investigation passed; `execution_enabled=false` remains explicit. External-network and live-role behavior are not established by this command.

Company policy rules out elevated setup. The prior unelevated Codex candidate still fails raw TCP denial; `--backend codex-unelevated` retains that investigation for reviewed CLI 0.155.1, with `--codex-path` applying only there. AppContainer diagnosis requires no Codex. T2 reuses the text-only adapter for live roles and tests generated code inside AppContainer; T3 adds admission and T4 connects sequential execution below. [Phase 3](Phase/Phase3_Workflow.md) records the component evidence and remaining work.

## Phase 3 component verification

T2 provides real roles and isolated tests as components. To reproduce its small example from this repository, run:

```powershell
& $harnessPython scripts/verify_t2.py --live
```

This makes two actual AI calls on a fresh fixture copy outside OneDrive. It checks the baseline, applies only allowed file changes, runs isolated tests and independent checks, and requests a separate read-only review. The output names the saved report directory. It supports the reviewed Python/pytest dependency set; tests write artifacts to scratch. This T2 script verifies components; T4 connects execution and T5 adds interruption recovery below. T6 implements acceptance conditions; P3-T7 completed the accepted external example below. See [T2 evidence](Phase/Evidence/Phase3_Workers.json).

## Phase 3 execution, corrections and records

After reviewing and approving the plan for `$planningProject`, prepare a separate execution record:

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-prepare --max-corrections 2
& $harnessPython -m development_harness --project $planningProject workflow-status
# Authorize the recorded plan, code and policy; no task or AI call starts.
& $harnessPython -m development_harness --project $planningProject workflow-approve
# Start actual Developer/Reviewer calls and apply approved file changes.
& $harnessPython -m development_harness --project $planningProject workflow-run
& $harnessPython -m development_harness --project $planningProject workflow-status
# Optional cancellation preserves project files and all evidence.
& $harnessPython -m development_harness --project $planningProject workflow-cancel
```

Preparation requires the latest approved plan, unchanged artifacts/inputs and supported isolated pytest checks. Use `workflow-prepare --planning-run <run-id>` to identify that plan explicitly. `plan-approve` remains planning-only. Repeated preparation/approval preserves the same record, and `plan-status` still shows the planning Run. Workflow status includes attempts, waits and evidence-linked findings; unknown measurements remain `null`. Changed files or authorization data block execution approval; status reports the inspection error with exit code 1.

Preparation and approval make no AI calls or file changes. `workflow-run` executes each approved Task as Developer → controlled file application → AppContainer tests → a fresh Reviewer session. Test failures and mandatory review findings share the same per-Task correction allowance: the default is two additional attempts after the initial implementation. Missing dependencies, permission problems, unclear requirements, timeouts, skipped/empty or incomplete checks stop execution without requesting another code correction.

The initial authorization remains fixed while each controller-applied patch records the current code version. Review uses the current validation batch and original Task before-files. Every prior finding needs an explicit follow-up assessment and evidence; omission or a Developer claim cannot resolve it. Deferred mandatory findings remain blocking. After all Tasks pass, every registered check runs again on final content. A final failure stops for inspection without automatically attributing it to a Task. `technically_complete` records this technical result; explicit user acceptance is a separate step described below.

Workflow records expose `workflow_execution_enabled=true` and `orchestration_available=true`; these describe capability, not approval or completion. `workflow-run --steps 1` stops after a durably completed stage, and another `workflow-run` can continue from that boundary. After an interruption, inspect the advisory `recovery` field in `workflow-status`, then explicitly resume:

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-status
& $harnessPython -m development_harness --project $planningProject workflow-resume
```

`workflow-resume` checks the same plan, approval, files and recorded process tree under the project lock. A proven unsent request can run; a complete saved response is reused after checking its input, schema, event stream and session. Unknown dispatch without a complete verified response blocks automatic redispatch. Partial patches resume only where each file still matches its recorded before/after content; unexpected edits are preserved and stop recovery. Interrupted validation runs fresh checks before review/final completion. Approval and correction counts are retained, and cancelled or failed workflows cannot be reset by resuming. Interrupted legacy records without an `active_step` cursor require inspection.

Raw attempt history remains unchanged; separate recovery facts supply the effective call/usage summary and prevent duplicate findings. Unknown timing remains `null`. Changing `--state-dir` cannot bypass project ownership; a missing/corrupt previous state database blocks reassignment. Existing `run`/`resume` still support Phase 1 fixtures only. `workflow-run` and `workflow-resume` return a nonzero exit code when stopped or failed.

T3's historical **378 tests**, 113 added cases and zero live AI calls are preserved in [T3 evidence](Phase/Evidence/Phase3_Records.json). T4 passed **all 465 tests** and `pip check`, plus a two-Task example with four actual AI calls and six independent requirement checks. Results are recorded in [T4 evidence](Phase/Evidence/Phase3_Execution.json) and [Phase 3](Phase/Phase3_Workflow.md). To explicitly reproduce the T4 live fixture, run `& $harnessPython scripts/verify_t4.py --live`; it makes actual role calls on a new disposable project and does not establish T5 recovery or Phase 3 user acceptance.

T5 passed **535 full regression tests**, nine final recovery edge checks and `pip check`. Its disposable live example passed with **two confirmed role calls**: a real Developer response survived forced controller exit and was reused with no extra Developer call, followed by isolated validation and independent review. Task/final checks each passed eight tests, plus six independent checks. [T5 evidence](Phase/Evidence/Phase3_Recovery.json) is separate from the preserved T4 record. To explicitly reproduce this bounded live recovery check, run `& $harnessPython scripts/verify_t5.py --live`. Phase 3 user acceptance remains pending.

## Phase 3 results, feedback and acceptance

`workflow-report` prints the minimum JSON result without changing project files, workflow records or existing database bytes. It covers success, failure, interruption and permission stops, including delivered files, current test results, unresolved findings/feedback, required manual checks and actual evidence paths. Missing files and inspection errors remain visible. Richer report presentation remains Phase 4 work.

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-report
```

Declare any required manual checks before execution approval. Write a JSON array to an external file such as `$env:TEMP\harness-manual-checks.json`, using real requirement IDs from the approved current Phase:

```json
[
  {
    "id": "M1",
    "requirement_ids": ["R1"],
    "procedure": "Run the CLI with negative input and inspect stdout, stderr and exit code.",
    "expected": "No numeric stdout, an explanatory stderr message and a nonzero exit code."
  }
]
```

```powershell
# On a new workflow, before workflow-approve:
& $harnessPython -m development_harness --project $planningProject workflow-prepare --manual-checks "$env:TEMP\harness-manual-checks.json"
```

Every declared manual check is mandatory and fixed in the approved policy. After technical completion, perform the check and record its actual outcome. Every current requirement marked `reuse`, including those without an implementation Task, also needs an explicit explanation mapped to actual passing final-validation IDs from `workflow-report`. The following IDs and observations are illustrative; replace them with the report's IDs and your evidence:

```powershell
& $harnessPython -m development_harness --project $planningProject workflow-reuse --requirement R1 --validation-ids '<final-validation-id>' --outcome passed --evidence 'The final positive and zero-input tests verify the reused doubling behavior.'
& $harnessPython -m development_harness --project $planningProject workflow-manual --check M1 --outcome passed --evidence 'Observed empty stdout, a negative-input explanation on stderr and exit code 2.'
& $harnessPython -m development_harness --project $planningProject workflow-report
# Only after reviewing the result and all mandatory evidence:
& $harnessPython -m development_harness --project $planningProject workflow-accept
```

Failed, missing or stale evidence blocks acceptance. Confirmations match the plan, policy, code and final completion; a new correction invalidates old confirmations even if some files remain the same. The gate verifies final record/JUnit/log hashes, completed reviews and unresolved mandatory findings. Technical success can therefore coexist with pending manual/reuse checks. Legacy T4/T5 runs remain historical and unverified for T6 acceptance: they lack the approved `result_version=1` policy and sealed evidence, so a new approved workflow is required. Reports never upgrade or accept them automatically.

Feedback records the exact original text and routing history without calling AI. Choose one route:

```powershell
# Same-scope defect: preserve approval and use the Task's remaining correction budget.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind defect --task '<task-id>' --text 'Describe the observed defect within the approved requirement.'
& $harnessPython -m development_harness --project $planningProject workflow-run
# Changed requirements: preserve old approval as history and start fresh planning.
& $harnessPython -m development_harness --project $planningProject workflow-feedback --kind requirements --text 'Describe the changed requirement.'
# Update the registered specification file to describe the requested change before replanning.
& $harnessPython -m development_harness --project $planningProject workflow-replan
& $harnessPython -m development_harness --project $planningProject plan
```

Defect feedback shares the original per-Task limit; it does not reset the budget. After correcting an earlier Task, previously completed later Tasks receive fresh validation/review and all final checks run again. Changed requirements block the old execution approval. Update the registered specification before `workflow-replan`: feedback preserves your exact request but does not rewrite that specification, which remains the Planner's source. Review the new plan, then use `plan-approve`, `workflow-prepare` and `workflow-approve`. Replanning baseline checks for previously generated code run in AppContainer. Existing implementation files, feedback and approval history remain available.

T6 passed the full suite of **632 tests** and `pip check`, including **96 added cases**. It adds **zero actual AI calls**. Reporting on the saved T5 live example retains its two historical calls and does not constitute a new T6 live example or user acceptance. [T6 verification evidence](Phase/Evidence/Phase3_Results.json) and [Phase 3 details](Phase/Phase3_Workflow.md) record the current verification state. T7 technical verification and user acceptance are recorded below; T8 and overall Phase 3 acceptance remain pending.

## Phase 3 external example

```powershell
# From the repository root, using the prepared harness environment:
& $harnessPython scripts/verify_t7.py --live
```

This creates a fresh CLI example under `%LOCALAPPDATA%/development-tools-harness/t7-live/<id>` and runs the previously reviewed one-Task negative-input change. The plan is controller-authored, with **zero Planner calls**. It pins the current result policy and manual check M1, makes real Developer/Reviewer calls, deliberately stops after saving the Developer response, then uses public `workflow-resume` to reuse it and finish with default AppContainer validation. The script records evidence and leaves R1 reuse confirmation, M1 manual confirmation and genuine result acceptance pending. Each `--live` invocation starts a new example; inspect an existing result using its recorded project/state paths and `workflow-report`.

The 2026-09-23 example `c2cc52b6323c` reached `technically_complete`: **2 actual calls**, **8 final tests**, **6 independent CLI checks**, no corrections/findings, and preserved repository fixtures. It required no production harness source changes. Actual stdout/stderr and exit codes are in the [user review packet](Phase/Evidence/Phase3_Example_Review.md); [T7 evidence](Phase/Evidence/Phase3_Example.json) links the hashes, commands and runtime records. All 632 full-regression tests passed with zero failures, errors or skips. The user explicitly accepted the presented result with “결과 인수한다” on 2026-09-23. Public R1/M1 confirmations and `workflow-accept` completed T7; the current report has `stage=accepted` and no blockers. [Acceptance evidence](Phase/Evidence/Phase3_Example_Acceptance.json) preserves the record without new AI calls or test runs. T8 has not started and overall Phase 3 acceptance remains pending.

## Intended workflow

```text
Register a prepared project and run baseline checks
  → Read the specification and relevant code
  → Propose all Phase goals and detailed tasks for the current Phase
  → Obtain user approval
  → Implement, test, review, and revise tasks sequentially
  → Run Phase integration checks and generate a results report
  → User checks the UI and accepts the result or requests changes
  → Detail and approve the next Phase
```

A **Phase** groups work around a goal and acceptance conditions. A **Task** is an implementation unit within that Phase. Only the current Phase is broken down in detail; later Phases are refined as development progresses.

Approvals cover the overall plan, the current Phase, significant scope or risk changes, and final acceptance. An unchanged approved plan does not require repeated approval. No response means the harness continues waiting.

## First MVP scope

The first MVP focuses on one project, sequential Tasks and one validation technology configuration. Harness development uses Python 3.12.10 + pytest 9.1.1. The Adapter uses Codex CLI with ChatGPT authentication; reviewed versions are 0.154.0 and 0.155.1. Actual roles, isolation, admission, bounded sequential execution, explicit interruption recovery, minimum JSON reports, feedback and acceptance gates are implemented. The external example is accepted; the fixed runner remains Phase 3 work.

| Area | Planned P0 behavior |
| --- | --- |
| Project entry | Check paths, specification, tools, and test commands; record the starting state. |
| Planning | Produce Phase goals, current tasks, acceptance criteria, and a simple requirements mapping. |
| Existing code | Investigate relevant code, conventions, and reuse evidence for the current Phase. |
| Execution | Use one Developer → Validation Runner → Reviewer workflow with bounded correction attempts. |
| Approval and permissions | Bind approval to the reviewed plan or result version and enforce supported execution boundaries. |
| State and resume | Record execution in SQLite, prevent concurrent modification of one project, and resume from recorded stages. |
| Results | Provide a short Phase report, reuse verification, and paths for corrections or approved plan changes. |
| Measurement | Record actual AI calls, execution time, approval waiting time, and review findings with their resolution evidence. |
| Dogfooding | Use a verified harness version to develop and accept one small remaining P0 feature of the harness itself. |

### Project prerequisites

The user supplies:

- A project folder: a prepared starter project for new development, or an existing codebase for modifications.
- A Markdown specification describing the requested functionality and constraints.
- Installed runtimes and dependencies, working unit/integration test commands, and the chosen AI tool with authentication configured.

Baseline checks must pass before development begins. Missing tools, failing checks, or commands that discover no tests require preparation or correction; the harness must not silently treat them as success. Blocking specification ambiguities require clarification.

Starting from an empty folder and automatically building an arbitrary development environment are outside the first MVP. Git history is not required. Existing uncommitted work is part of the starting state and must be preserved.

### Validation and review

The Developer writes implementation code and necessary tests. The Validation Runner executes registered checks, and a Reviewer in a separate session compares the approved requirements, actual code, and tests.

The Reviewer remains part of every Task because an implementation and its tests can share the same misunderstanding. Separate review is an additional check, not a guarantee of correctness. Unit and integration tests remain the main automated checks; existing lint, type checks, and builds may also run where needed. **The user performs browser UI testing.**

Correction attempts are bounded, with two attempts proposed as the initial default. Exhausted attempts or environment problems result in a stop with the failure history. Required checks that fail, do not run, or are interrupted cannot count as passed.

Reused functionality must also be checked against the current requirements at Phase acceptance, even when it has no implementation Task. Final Phase validation runs against the resulting code. Acceptance cannot override an unmet mandatory condition; changing the scope requires an updated, approved plan.

### User control and recovery

- Approved ordinary file edits and verified validation commands proceed automatically within supported permissions.
- Risky operations require an enforceable execution boundary. Operations that cannot be controlled before execution are blocked and handed to the user for manual handling.
- Working agents must not change approval records or verification policies to grant themselves permission.
- Settings, plans, and reports live with the project. Execution databases and logs are planned for local storage outside OneDrive.
- Resume checks the saved plan, approvals, and actual file state. Unexpected differences stop execution for inspection instead of triggering automatic merges or rollbacks.
- Git initialization, branch operations, staging, commits, pushes, pull requests, merges, and deployment remain manual user actions.

## Phase deliverables

Each Phase produces changed code and tests, verification evidence, and a report targeting one to two pages with links to detailed records.

The report covers:

- Delivered functionality, artifact locations, and how to run the result.
- Actual test results, reused-feature checks, and anything still unverified.
- Significant errors, attempted fixes, and remaining issues.
- Approved plan changes and their reasons.
- UI checks the user should perform and the expected results.
- AI calls by role, execution and approval waiting times, and review findings with their outcomes.

A report is generated even when execution fails. Task technical completion and user acceptance of a Phase are separate: a Phase finishes when its final deliverables satisfy the required checks and the user accepts them. Committing or pushing is not a completion condition.

## Development approach: staged dogfooding

1. Build the minimum runner, approval, validation, review, recording, and resume behavior using existing coding tools.
2. Verify the complete flow, including interruption and resume, on a separate small example.
3. Freeze a working **runner A** and use it to develop a small remaining P0 feature in **development copy B**.
4. Validate B with core regression checks and a separate execution, then let the user select it for a later run.

The running version, its policies, and its approval database must be isolated from the files and test environment being modified. Version replacement stays manual and does not happen during a run. Manual interventions and discovered problems are recorded using the existing reports.

Successful self-development does not replace testing on other projects. MVP completion also requires one accepted Phase in each of a prepared new-project example and an existing-project example using the selected technology configuration.

## Roadmap

| Stage | Focus |
| --- | --- |
| First MVP — P0 | Prove the approved Phase → implementation → validation → review → report → acceptance flow, including resume and staged dogfooding. |
| Optional P1 candidates | A short specification review and one basic starter template, considered after the core flow works. |
| MVP2 baseline | Start from a selected template and handle small standalone change requests without creating a Phase, while reusing the execution and approval machinery. |
| Evidence-driven candidates | A Fast path, requirements-mapping checks, and reusable code summaries, only when actual usage justifies them. |
| Later scope | Arbitrary stack bootstrapping, baseline-failure exceptions, advanced recovery, multiple AI tools, parallel tasks, and a web dashboard. |

P0/P1/P2 express priority; **MVP2 is a later product scope**, not a commitment to implement every P2 item. Git/deployment automation and automated UI testing are not part of the default expansion plan.

## Planning documents

- [Development Phase overview](Phase/Overview.md): four development Phases, requirements mapping, and dogfooding entry conditions. Each document contains full English and Korean sections.
- [Phase 1 — execution foundation](Phase/Phase1_Foundation.md): accepted. [Phase 2 — real connection and planning](Phase/Phase2_Planning.md): accepted. [Phase 3 — workflow](Phase/Phase3_Workflow.md): in progress; P3-T1–T6 implemented, T7 accepted and completed, T8 not started. [Phase 4 — dogfooding and MVP acceptance](Phase/Phase4_Dogfooding.md): outline.
- [Lean MVP plan — revision 0.4](Draft/ai-development-harness-lean-mvp-plan.md): scope, priorities, acceptance rules, development stages, dogfooding, MVP2, and planning change history. Start here.
- [Earlier planning documents](Draft/archive/): historical designs and decisions. Their broader scope should not be assumed to apply to the lean MVP.

```text
development-tools-harness/
├── README.md
├── README_ko.md
├── pyproject.toml
├── requirements-dev.lock
├── .agents/skills/phase-doc/
│   ├── SKILL.md
│   └── references/phase-template.md
├── src/development_harness/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Phase/
│   ├── Overview.md
│   ├── Phase1_Foundation.md
│   ├── Phase2_Planning.md
│   ├── Phase3_Workflow.md
│   └── Phase4_Dogfooding.md
└── Draft/
    ├── ai-development-harness-lean-mvp-plan.md
    └── archive/
```

Phase 2 user acceptance is complete. Phase 3 connects actual roles, isolated tests, execution admission, durable records, bounded sequential corrections, explicit interruption recovery, minimum reports, feedback and evidence-bound result acceptance. T7 external-example technical verification passed, and R1/M1 user confirmations and explicit result acceptance are complete. Fixed runner A is P3-T8 and has not started; Phase 3 user acceptance is pending.
