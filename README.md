[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI builds, the harness verifies, and humans approve only what matters.

A local development tool for any language. Give it a completed development specification: it splits the work into Phases starting with Phase 0 (environment), sets up the language and tools the specification names when you say start, develops and tests, presents the deliverables, and marks the Phase complete when you accept. Its purpose is to reduce duplicate, wrong and low-quality code.

## Current status

- **Specification 1.10 finalized (2026-10-23).** The [new specification](Draft/ai-development-harness-plan-v1.md) replaces lean MVP 0.4 and removes the language restriction.
- **Phase 0 was accepted and completed on 2026-10-23.** Environment checks and all 691 regression tests passed (no failures or skips); the exact test-ID set matches the previous record. The baseline and 41-module map are accepted. [Phase 1](Phase/Phase1_ValidationContract.md) now has a detailed plan; implementation has not started. Regression used preserved Codex CLI 0.155.1; the machine default 0.163.0 remains unverified. See the [Phase 0 record](Phase/Phase0_Baseline.md).
- **Existing code is reused.** The CLI built under lean MVP 0.4 (Phases 1–3 accepted on 2026-09-18, 2026-09-21 and 2026-10-07) is the starting point. It currently supports Python and pytest projects only. That Phase set is archived in [Phase/archive/lean-mvp-0.4](Phase/archive/lean-mvp-0.4/Overview.md); its Phase 4 (self-development) was cancelled.

## How it will work

```text
1. You give a specification
2. The harness builds Phases and bilingual Phase documents, always starting with Phase 0
3. You review and say "start"
4. Phase 0 sets up the environment and records a baseline
5. Development Phases: develop, test, quality checks, separate review, bounded corrections
6. The harness presents a report
7. You accept (the Phase is marked complete) or request changes
```

- **No language knowledge in the harness.** It judges results only through exit codes, JUnit XML test reports and file hashes. The specification and the AI carry the language knowledge.
- **Quality devices.** Search before writing, a reuse rationale, an exact-copy duplicate report, quality checks, project rules, an independent Reviewer with a fixed checklist, and blocking of weakened checks. Existing problems are recorded as a baseline; only new problems block.
- **Control stays with you.** Nothing runs before start. Unplanned installs, network use and system changes need approval. Versions do not change without approval. Administrator operations, Git writes and deployment are manual.
- **First-version verification.** Python, TypeScript and Java. Only SQLite is verified; server databases remain an unverified limitation.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| [0 — Baseline](Phase/Phase0_Baseline.md) | Check the current environment and full regression, record the baseline, confirm the module map | ✅ |
| [1 — Validation Contract & Isolation](Phase/Phase1_ValidationContract.md) | Language-independent check contract, isolation option C, Java download check; verify with one minimal Python fixture and one minimal Java fixture | 🔲 |
| [2 — Planning & Environment Setup](Phase/Phase2_PlanningAndSetup.md) | Plans with Phase 0, technology and version proposals, Phase documents, Phase 0 execution | 🔲 |
| [3 — Workflow & Quality](Phase/Phase3_WorkflowAndQuality.md) | AI permissions, quality devices, report, acceptance, simplified CLI | 🔲 |
| [4 — Real-World Validation](Phase/Phase4_RealWorldValidation.md) | Decision Desk Phase 1, an existing Python project, a mock Java project | 🔲 |

## Using the current CLI

Until the new Phases change it, the CLI works as in lean MVP 0.4: Windows, Python 3.12.10, pytest projects only, with commands such as `register`, `plan`, `plan-approve`, `workflow-prepare`, `workflow-approve`, `workflow-run` and `workflow-accept`. Setup and usage are in the archived [README for 0.4](Phase/archive/lean-mvp-0.4/README_v0.4.md). The planned simplified commands are `plan`, `start`, `status`, `approve`, `accept`, `feedback` and `resume` (specification 2.2).

## Project structure

```text
development-tools-harness/
├── README.md
├── README_ko.md
├── pyproject.toml
├── requirements-dev.lock
├── .agents/skills/
│   ├── phase-doc/                      # Phase document rules and template
│   └── harness-github-push/
├── src/development_harness/            # harness CLI (41 modules)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Phase/
│   ├── Overview.md
│   ├── Phase0_Baseline.md              # ✅ Accepted 2026-10-23
│   ├── Phase1_ValidationContract.md    # 🔲 Not Started
│   ├── Phase2_PlanningAndSetup.md      # 🔲 Not Started
│   ├── Phase3_WorkflowAndQuality.md    # 🔲 Not Started
│   ├── Phase4_RealWorldValidation.md   # 🔲 Not Started
│   └── archive/lean-mvp-0.4/           # previous Phases, evidence, README snapshots
└── Draft/
    ├── ai-development-harness-plan-v1.md   # current specification (1.10)
    └── archive/                            # lean MVP 0.4 and earlier plans
```

## Documents

- [Specification 1.10](Draft/ai-development-harness-plan-v1.md): product definition, flow, Phase 0, check contract, quality devices, permissions, report, scope and the decision record. Written in Korean.
- [Phase overview](Phase/Overview.md): Phase plan, requirements mapping and shared completion rules. Each Phase document has full English and Korean sections.
- [Archived lean MVP 0.4 Phases](Phase/archive/lean-mvp-0.4/Overview.md) and the [0.4 specification](Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md): history of the existing code. Their recorded evidence is unchanged.
- [Earlier planning documents](Draft/archive/): historical designs; their scope does not apply to the current specification.
