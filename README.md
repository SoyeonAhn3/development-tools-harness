[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI builds, the harness verifies, and humans approve only what matters.

A planned local CLI for semi-automated development: turn a Markdown specification into phased work, implement and test approved tasks, review the results, and present the evidence for human acceptance.

## Current status

**Phases 1–2 are accepted and completed; Phase 3 is in progress.** The Windows/Python 3.12 CLI registers prepared projects, runs baseline tests and generates versioned bilingual plans using Codex and the repository phase-doc skill. P3-T1 preparation and P3-T2 real Developer/Reviewer, controlled file changes and administrator-free isolated pytest are verified. All **265 tests passed**, plus a two-call live component example. General execution admission, orchestration, resume and acceptance remain P3-T3–T8.

The roadmap below summarizes the [lean MVP plan, revision 0.4](Draft/ai-development-harness-lean-mvp-plan.md). Phase 1 and Phase 2 usage sections identify implemented behavior.

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

Company policy rules out elevated setup. The prior unelevated Codex candidate still fails raw TCP denial; `--backend codex-unelevated` retains that investigation for reviewed CLI 0.155.1, with `--codex-path` applying only there. AppContainer diagnosis requires no Codex. T2 now reuses the existing text-only adapter for live roles and tests generated code inside AppContainer. General workflow commands remain pending; [Phase 3](Phase/Phase3_Workflow.md) records the component evidence and remaining work.

## Phase 3 component verification

T2 provides real roles and isolated tests as components. To reproduce its small example from this repository, run:

```powershell
& $harnessPython scripts/verify_t2.py --live
```

This makes two actual AI calls on a fresh fixture copy outside OneDrive. It checks the baseline, applies only allowed file changes, runs isolated tests and independent checks, and requests a separate read-only review. The output names the saved report directory. It supports the reviewed Python/pytest dependency set; tests write artifacts to scratch. General plan execution, correction/resume and acceptance await P3-T3–T8. See [T2 evidence](Phase/Evidence/Phase3_Workers.json).

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

The first MVP focuses on one project, sequential Tasks and one validation technology configuration. Harness development uses Python 3.12.10 + pytest 9.1.1. The planning Adapter uses Codex CLI with ChatGPT authentication; reviewed versions are 0.154.0 and 0.155.1. Real implementation/review and worker isolation remain Phase 3 work.

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
- [Phase 1 — execution foundation](Phase/Phase1_Foundation.md): accepted. [Phase 2 — real connection and planning](Phase/Phase2_Planning.md): accepted. [Phase 3 — workflow](Phase/Phase3_Workflow.md): in progress; P3-T1–T2 verified, P3-T3–T8 pending. [Phase 4 — dogfooding and MVP acceptance](Phase/Phase4_Dogfooding.md): outline.
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

Phase 2 user acceptance is complete. Phase 3 has an execution contract, prepared example and reproducible permission investigation. A stronger verified boundary is needed before actual Developer/Reviewer execution; the text-only Planner boundary does not establish worker/test isolation.
