[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI builds, the harness verifies, and humans approve only what matters.

A planned local CLI for semi-automated development: turn a Markdown specification into phased work, implement and test approved tasks, review the results, and present the evidence for human acceptance.

## Current status

**Planning stage.** This repository currently contains planning documents, with no runnable harness, package manifest, or automated test suite. Installation and execution instructions will be added when the implementation is available.

This README summarizes the [lean MVP plan, revision 0.4](Draft/ai-development-harness-lean-mvp-plan.md) (Korean). The plan is a scope proposal; this summary does not constitute implementation approval. All capabilities below describe intended behavior, not shipped functionality.

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

The first MVP focuses on one project at a time, sequential tasks, and one technology configuration for validation. The initial technology configuration and AI execution tool still need to be selected and verified.

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

- [Lean MVP plan — revision 0.4](Draft/ai-development-harness-lean-mvp-plan.md): scope, priorities, acceptance rules, development stages, dogfooding, MVP2, and planning change history. Start here.
- [Earlier planning documents](Draft/archive/): historical designs and decisions. Their broader scope should not be assumed to apply to the lean MVP.

```text
development-tools-harness/
├── README.md
├── README_ko.md
└── Draft/
    ├── ai-development-harness-lean-mvp-plan.md
    └── archive/
```

Before implementation, confirm the P0 scope and select the initial prepared project, trial Phase, technology configuration, and AI adapter. The first adapter integration must establish which execution permissions can actually be enforced.
