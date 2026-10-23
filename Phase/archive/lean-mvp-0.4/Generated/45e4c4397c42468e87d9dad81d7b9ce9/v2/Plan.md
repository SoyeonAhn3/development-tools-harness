# Development plan

Detail Phase 3's real sequential workflow, evidence, correction/resume, minimum results and external-example gate to frozen runner A. This planning-only run passed 156 baseline tests and generated v1 with one real Planner call; v2 contains recorded manual review corrections. Phase 2 user acceptance is still pending. Select and probe the worker permission mechanism before live worker integration; safe controller development and disposable boundary experiments may prepare that evidence. Phase 3 implementation and acceptance are not established by this plan.

## Overall Phases

### Phase2 — Phase 2 — Planning prerequisite

Establish accepted planning and verified permissions before Phase 3 execution.

Exit criteria: Phase 2 acceptance evidence is available; its permission limits are explicit.

### Phase3 — Phase 3 — Workflow

Connect real development, validation, independent review, bounded corrections, resume and minimum acceptance.

Exit criteria: Integration/regression checks and an accepted external example demonstrate the flow, interruption recovery and actual process protections; independently frozen A is isolated from B and its tests.

### Phase4 — Phase 4 — Self-development and MVP acceptance

Use verified A for one remaining small P0 report feature, complete report summaries and verify prepared new/existing external projects.

Exit criteria: Accepted self-development and one accepted Phase each on new/existing external projects, preserved core regressions and evidence for every lean-MVP section 11 criterion. A qualifying Phase 3 example may count when its evidence still matches. Detail later using Phase 3 results.

## Current Phase Tasks: Phase3

### P3-T1 — Confirm prerequisites, investigate worker isolation and define the execution contract/example

Requirements: R1, R2, R12

Files: Phase/Phase3_Workflow.md, src/development_harness/model.py, src/development_harness/plan_schema.py, tests/fixtures/workflow_project/cli.py, tests/fixtures/workflow_project/test_cli.py, tests/fixtures/workflow_project/spec.md

Depends on: —

Acceptance: Record Phase 2 user acceptance before Phase 3 starts. Investigate the available Windows permission mechanisms with disposable targets, select a mechanism and record its limitations; do not claim isolation before actual probes. Define current-Phase Tasks, checks and a configurable correction limit (proposed default: two). Q2 gates live worker integration, while safe controller code and disposable probe development may establish the missing evidence. Proposed workflow_project files define a CLI that doubles an integer, with positive/zero baseline tests; the bounded change rejects negative input with a nonzero exit and clear error while retaining normal output. Record commands and expected outputs before the live example.

Verification: Inspect Phase 2 user acceptance; document the proposed permission mechanism and disposable probe results or unresolved limitations. Run the prepared example baseline using python -m pytest -q in a temporary copy. Review the execution contract against Phase 3. Live target-modifying workers remain blocked until the permission evidence in P3-T2 passes.

### P3-T2 — Extend the single Adapter with verified worker boundaries

Requirements: R2, R3, R13

Files: src/development_harness/codex_adapter.py, src/development_harness/codex_probe.py, src/development_harness/processes.py, src/development_harness/gate.py, src/development_harness/validation.py, tests/integration/test_workflow_permissions.py

Depends on: P3-T1

Acceptance: Using the resolved Q2 boundary, support real Developer and separately instantiated Reviewer sessions through the selected Adapter. Worker permissions limit modifications to approved target content and deny access to controller approval/policy storage; test descendants inherit the boundary. Preserve the existing text-only Planner boundary. The integration test path is proposed. No active runtime records are edited directly. The Reviewer is read-only. Developer writes stay within approved target paths. All roles and validation descendants must be denied writes to A, active policies/approval records, unrelated files and Git metadata, installation, and unapproved external transfer; allow only the selected AI service communication required by the role. Carry these existing lean-MVP constraints into the execution contract.

Verification: Use actual worker and descendant processes against disposable protected targets to prove permitted target changes and denied protected writes before effects. Verify the actual selected CLI role boundary, not just prompts or fake responses. Run Planner capability and compatibility regressions; a missing boundary blocks live workflow. Probe Reviewer writes, out-of-scope writes, Git-metadata writes, installation attempts and unapproved external endpoints in disposable fixtures; check absence of effects and inherited restrictions. Unsupported enforcement blocks that operation.

### P3-T3 — Journal real calls, timings, findings and versioned execution admission

Requirements: R2, R6, R9

Files: src/development_harness/store.py, src/development_harness/planning.py, src/development_harness/runner.py, src/development_harness/cli.py, tests/unit/test_workflow_records.py

Depends on: P3-T2

Acceptance: Add controller-owned execution admission referencing reviewed plan and starting content identities, with explicit execution authorization separate from planning-only approval. Persist unique role attempts, dispatch state, session IDs, completed/unknown time spans, approval waits and finding identities atomically. Link evidence to plan/code versions; report only observed usage. The unit test path is proposed. Finding records include severity, content, open/resolved/false-positive/deferred disposition and supporting evidence; preserve stable identities through re-review.

Verification: Inject crashes before dispatch, after dispatch and during state/event persistence in temporary stores. Assert rollback consistency, stable IDs, no duplicate counting on replay, null unknown durations/usage and stale-version rejection. Existing plan-approve must still dispatch no implementation.

### P3-T4 — Connect sequential execution, evidence-based review and bounded corrections

Requirements: R3, R4, R5, R9

Files: src/development_harness/runner.py, src/development_harness/model.py, src/development_harness/validation.py, tests/integration/test_workflow.py

Depends on: P3-T3

Acceptance: Execute approved Tasks in dependency order through Developer, required validation and separate Reviewer sessions. Review compares requirements, actual files and tests. Required findings resolve only with matching follow-up review and validation; deferred mandatory findings block completion. Rerun checks after corrections and on final Phase content. Use a configurable limit with two as the proposed default; environment, permission and specification stops consume no code-fix retry. The integration test path is proposed.

Verification: Exercise two ordered Tasks, repeated findings, a falsely claimed fix, deferred mandatory findings, limits zero/two and limit exhaustion. Real pytest cases cover failure, skipped/mixed suites, no tests, timeout and missing tools. Assert no advancement on unmet checks and verify final evidence against final content. Verify severity/disposition history and require evidence for false-positive or resolved classifications; deferred mandatory findings still prevent completion.

### P3-T5 — Make real implementation and validation resume safely

Requirements: R7, R8, R9, R13

Files: src/development_harness/runner.py, src/development_harness/files.py, src/development_harness/processes.py, tests/integration/test_workflow_resume.py, tests/unit/test_state.py

Depends on: P3-T4

Acceptance: Inspect partial real implementation before further changes, preserving ambiguous/user-edited content. Reconcile worker identities and descendants before rerunning interrupted required validation. Prevent concurrent or alternate-store unsafe ownership. Resume reuses existing records without duplicate calls/findings. The resume test path is proposed; metadata-only behavior is verified using disposable filesystem fixtures without Git operations.

Verification: Kill real implementation and validation controllers at journal/launch boundaries; inspect partial files and prove descendant cleanup or blocked resume. Race an editor and a second runner, including alternate state directories. Compare before/after content and IDs; metadata-only fixture changes must permit unchanged runs.

### P3-T6 — Add minimum results, feedback and final reuse/acceptance gates

Requirements: R6, R10, R11, R14

Files: src/development_harness/results.py, src/development_harness/runner.py, src/development_harness/planning.py, src/development_harness/cli.py, tests/integration/test_workflow_results.py

Depends on: P3-T5

Acceptance: Proposed results.py and test_workflow_results.py provide success/failure reports with delivered files, validation and reuse evidence, unresolved items, manual checks and detailed-record locations. Retain original feedback and outcome: same-scope defects reopen current-Phase correction; changed requirements require revised planning/approval. Recheck every current reused requirement at final content, including those without Tasks. Missing mandatory evidence blocks acceptance; technical completion and user acceptance remain distinct. Reserve the small summary presentation for Phase 4.

Verification: Test success, correction exhaustion, interruption and permission-failure reports; follow their evidence locations. Submit both feedback types and verify preserved history/version invalidation. Test missing/stale/failed reuse evidence and manual checks, acceptance before completion and final file edits. All must fail closed where mandatory criteria are unmet.

### P3-T7 — Complete the external example with actual roles and user acceptance

Requirements: R1, R12, R13

Files: tests/fixtures/workflow_project/cli.py, tests/fixtures/workflow_project/test_cli.py, tests/fixtures/workflow_project/spec.md, tests/integration/test_workflow.py, Phase/Phase3_Workflow.md

Depends on: P3-T6

Acceptance: Use a separate temporary copy of the proposed workflow_project fixture and prepared dependencies. Execute the specified bounded change through plan review, explicit execution approval, actual Developer/Reviewer calls, validation, one interruption, resume and minimum report. Obtain genuine user result acceptance only after mandatory checks. Record actual commands, IDs, evidence and any manual intervention; do not count this as self-development.

Verification: Run the full pytest regression suite and inspect actual example normal/invalid-input outputs, distinct role sessions, final hashes, interruption evidence and acceptance. Record failures or pending acceptance honestly; automated fixture acceptance is insufficient.

### P3-T8 — Freeze and prove runner A isolation before promotion

Requirements: R13, R15

Files: pyproject.toml, src/development_harness/processes.py, src/development_harness/store.py, tests/integration/test_workflow_permissions.py, Phase/Phase3_Workflow.md

Depends on: P3-T7

Acceptance: Prepare A as a separate installation/copy with fixed code, dependencies and role/policy instructions, independent of editable B. Keep runtime records outside OneDrive; B tests use temporary records under limited permissions. Record installed module origins, version/content identities and actual isolation probe results. No promotion with permission/resume defects; record manual fixes and repeat affected checks. Do not edit active approval/policy records or begin self-development.

Verification: Verify A imports no module from B and its fixed artifacts retain their identities. Run real B workers and test descendants against disposable protected counterparts of A and its runtime/approval storage; prove denied writes and allowed temporary test records. Recheck installed A's CLI workflow/resume and inspect the external-example acceptance before Phase 3 exit.

## Requirements mapping

- **R1** Require accepted Phase 2, verified permissions and a prepared example before execution. — reuse / Phase3
  Earlier work is a prerequisite, not work to restart under new Phase numbering.
  Inspect prerequisite acceptance and permission records and rerun the prepared baseline; supplied evidence does not establish readiness.

  Source: **Prerequisites**: [Phase 2](Phase2_Planning.md) accepted, permissions verified and a prepared example available.

- **R2** Extend existing runner/storage and the single Adapter using Python, pytest and SQLite; place results in the package and temporary examples under tests. — implement / Phase3
  Existing modules provide foundations but real execution is explicitly absent.
  Review package placement and run earlier component regressions with the selected stack.

  Source: Extend the Phase 1 runner/storage and Phase 2 Adapter. Add result generation inside the existing package and temporary integration examples under tests; exact filenames are deferred.

- **R3** Run approved Tasks sequentially with separate-session review of requirements, implementation and tests; required fixes need independent follow-up evidence. — implement / Phase3
  The supplied runner currently uses synthetic Developer and Reviewer outcomes.
  Inspect actual ordered role calls and test rejection of self-reported fixes without review/validation.

  Source: An approved small Phase executes Tasks sequentially. The Reviewer uses a separate session and checks requirements, actual implementation and tests. Required findings must have follow-up review/validation evidence; Developer self-report is insufficient.

- **R4** Validate after changes and on final content; failed, skipped, interrupted and zero-test checks cannot pass. — implement / Phase3
  Reuse validation classification while connecting it to real implementation and final gates.
  Run real outcome fixtures and verify final evidence hashes match final code.

  Source: Required validation runs after changes and on final Phase content. Failed, skipped, interrupted and zero-test outcomes do not pass.

- **R5** Bound corrections by configuration, retaining the proposed two-correction default; stop environment, permission and specification problems without code-fix retries. — implement / Phase3
  Real role failures require explicit classification beyond existing synthetic correction handling.
  Test limit exhaustion and distinct non-code stop reasons; confirm the proposed default is recorded in the execution contract.

  Source: Corrections stop at the configured limit; environment/permission/specification problems stop without spending code-fix retries.

- **R6** Bind approvals, evidence and acceptance to matching plan/code versions; preserve feedback and route defects versus requirement changes correctly. — implement / Phase3
  Existing planning approval is planning-only; execution/result linkage and feedback need extension.
  Test stale versions, both feedback routes and immutable original feedback with recorded outcomes.

  Source: Approval/evidence/result acceptance reference matching plan and code versions. Same-scope defect feedback reopens correction in the current Phase; changed requirements update the plan and approval. Store the original feedback and outcome.

- **R7** Inspect partial implementation and residual validation processes on resume; preserve unexpected user edits and prevent unsafe ownership. — implement / Phase3
  Known synthetic writes do not establish safe recovery for real worker changes.
  Use real process termination, editor races and competing runners with temporary stores.

  Source: Interrupted implementation inspects partial files; interrupted validation checks remaining processes and reruns required checks. Unexpected user edits stop without overwrite, and another runner cannot acquire unsafe ownership.

- **R8** Allow unchanged-content runs after metadata-only manual Git changes. — reuse / Phase3
  Content snapshots already exclude .git; behavior still requires final regression evidence.
  Rerun metadata-directory and pointer-file fixture regressions with real workflow resume, without Git commands.

  Source: Metadata-only manual Git changes do not block an otherwise unchanged run.

- **R9** Collect all real events now with stable call, time, wait and finding identities; avoid resume duplicates and unknown estimates; mandatory deferred findings still block completion. — implement / Phase3
  Full collection is needed now even though a report summary remains for Phase 4.
  Reconcile event records after crashes and repeated reviews; inspect null unknowns, actual dispatch counts and fix evidence.

  Source: Actual role-call attempts, completed/incomplete times, approval waiting and findings have stable identities. Resume does not double-count calls or repeated findings. Confirmed fixes have evidence; deferred mandatory findings still block completion. Do not estimate unknown duration, tokens or money.

- **R10** Provide minimum success/failure reports and separate technical completion from user acceptance without bypassing mandatory criteria. — implement / Phase3
  Current status output is not the required real-workflow results interface.
  Inspect every required report field for success/failure and reject acceptance with unmet mandatory criteria.

  Source: Minimum reports exist for success and failure and show delivered files, validation/reuse evidence, unresolved items, manual checks and detailed-record locations. User acceptance is separate from technical completion and cannot override unmet mandatory criteria.

- **R11** Recheck reused requirements on final acceptance even when they have no implementation Task. — implement / Phase3
  Requirement mapping alone is not final verification.
  Include a mandatory reuse-only requirement and prove missing or obsolete evidence prevents acceptance.

  Source: Recheck reused requirements at final acceptance even without an implementation Task.

- **R12** Complete a separate prepared Python CLI example with baseline tests, a bounded input-validation change, interruption/resume and real user acceptance. — implement / Phase3
  The specification leaves example selection to Phase 3 detailing; the proposed fixture supplies a reviewable candidate.
  Record actual commands, normal/invalid behavior, role evidence, interruption and user acceptance for the external copy.

  Source: Use a prepared small Python CLI example with baseline tests, then request one bounded input-validation change with expected normal and invalid-input behavior. Review the generated Phase, approve, execute, interrupt once, resume, inspect review/validation evidence and accept.

- **R13** Verify core protections with actual processes; block A promotion on permission/resume defects and record manual intervention. — implement / Phase3
  Existing Job containment explicitly does not provide a permission sandbox.
  Require actual-process permission/resume evidence and a defect/intervention record before promotion.

  Source: Core protections must work with actual worker processes, not only the fake Adapter. A permissions or resume defect blocks promotion to runner A. Existing coding tools may fix such defects; record that manual intervention.

- **R14** Provide minimum evidence access now while reserving a small report summary for Phase 4. — implement / Phase3
  Evidence accessibility cannot wait for presentation completion.
  Follow minimum-report references to complete event evidence and document the remaining summary boundary.

  Source: Implement all event collection now. Provide minimum evidence access now; reserve a small remaining report summary for Phase 4 self-development.

- **R15** Freeze A independently with fixed dependencies/instructions, records outside OneDrive and restricted temporary B test records; prove B cannot modify A or its runtime/approval storage. — implement / Phase3
  Separate paths alone do not enforce the required write boundary.
  Inspect installed origins and fixed identities, then record actual B/descendant isolation probes before promotion.

  Source: Freeze A as a separately installed/copied runtime, not an editable installation referencing B. Place runtime records outside OneDrive; B tests use temporary records and limited permissions. Record actual isolation probes.

- **R16** Finish report summary presentation through Phase 4 self-development. — defer / Phase4
  Explicitly reserved later work; the external example is preparation, not the self-development milestone.
  Later compare the summary with Phase 3 event records under the approved self-development plan.

  Source: reserve a small remaining report summary for Phase 4 self-development.

- **R17** Exclude workflow routing variants and parallel Tasks. — exclude / —
  The specification explicitly excludes these alternatives.
  Review execution paths for a single sequential workflow.

  Source: Keep one sequential workflow and the proposed two-correction default; no Fast/Standard/Strict routing or parallel Tasks.

- **R18** Exclude a broad code-analysis or coverage engine. — exclude / —
  Explicit scope limit; evidence-based reuse checks suffice.
  Review changes to ensure reuse verification remains scoped to mapped requirements.

  Source: No broad code-analysis or coverage engine is added.

## Related code

- `src/development_harness/runner.py` (explicit): Existing sequential runner is synthetic and rejects planning runs; real execution requires extension.

  the only AI implementation here is synthetic.

- `src/development_harness/planning.py` (explicit): Existing approval is explicitly planning-only and should remain separate from execution authorization.

  "scope": "planning_only"

- `src/development_harness/codex_adapter.py` (explicit): The current Adapter enforces a text-only Planner profile, not Developer file access.

  Project tools are disabled, not prompt-restricted.

- `src/development_harness/processes.py` (explicit): Windows locks and process identities can be reused, but Job lifetime containment is not permission isolation.

  This is process lifetime containment, NOT the Phase 2 permission sandbox.

- `src/development_harness/store.py` (explicit): SQLite state and event transitions share transactions; runtime location checks already exist.

  each state/evidence transition is one transaction.

- `src/development_harness/validation.py` (explicit): Validation persists process identity before allowing the project command; its existing outcome classification is a foundation to reverify with real workflow integration.

  Persist PID identity BEFORE allowing any project command.

- `src/development_harness/files.py` (inferred): Checked writes and content snapshots suggest reusable file-preservation primitives for real worker reconciliation.

  Unexpected file changes; preserved without overwrite:

- `tests/integration/test_cli.py` (inferred): Existing integration fixtures cover forced controller termination and descendant cleanup, providing regression candidates rather than current passing evidence.

  def test_force_killed_harness_stops_descendants_and_resumes

- `tests/unit/test_state.py` (inferred): Filesystem-only metadata fixtures can verify unchanged-content resume without Git operations.

  def test_git_worktree_pointer_is_metadata_not_code

- `pyproject.toml` (explicit): The existing package constrains Python to 3.12 and pins pytest and psutil; retain and verify these when freezing A.

  requires-python = ">=3.12,<3.13"

- `Phase/Phase2_Planning.md` (explicit): Related evidence reports pending Phase 2 acceptance and a limited Planner boundary; it does not authorize Phase 3 execution.

  Task 2.6 and Phase acceptance remain pending.

## Questions

- Q1 (blocking): Phase 2 user acceptance remains pending. This run now supplies the Task 2.6 planning evidence (156 baseline tests, one real Planner call and reviewed v2), but that technical result does not constitute user acceptance. Record the user decision before Phase 3 starts.

- Q2 (blocking): The Windows mechanism that restricts Developer/test processes from modifying A and active runtime/approval storage is not selected or verified. Investigate it in P3-T1 and record actual allowed/denied probes in P3-T2 before live worker integration. This is a technical investigation, not a request for the user to choose a backend now.

Planning approval does not authorize implementation. Reuse is a proposal, not verified completion.
