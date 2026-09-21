# Development Phase Plan

Add negative-integer validation while preserving doubling for nonnegative integers. Use the existing Python module and pytest setup. This is a planning draft; implementation, test results and user acceptance are not established.

## Overall Phases

### phase-1 — Input Validation

Reject negative integers with a useful ValueError while preserving zero and positive integer behavior.

Negative, zero and positive pytest cases pass; existing doubling behavior is preserved and no dependencies, UI or network access are added.

## Phase Documents

- [phase-1 — Input Validation](Phase1_InputValidation.md)

## Requirements Mapping

- **R1** Preserve doubling behavior for zero and positive integers. — reuse / phase-1

The existing multiplication and tests provide behavior to retain; reuse still requires regression verification.

Run the existing assertions double(0) == 0 and double(3) == 6 after adding validation.

```text
The project already doubles nonnegative integer values. Preserve that behavior.
```

- **R2** Reject negative integers with ValueError and a useful error message. — implement / phase-1

The supplied function currently multiplies without a negative-value guard.

Use pytest.raises to assert the exception type and that the message explains the nonnegative input requirement.

```text
Reject negative integers with ValueError and a useful error message.
```

- **R3** Cover negative, zero and positive inputs with pytest tests. — implement / phase-1

Zero and positive tests exist; negative-input exception coverage must be added.

Run pytest test_value.py and confirm all three input categories are covered and pass.

```text
Cover negative, zero and positive cases with pytest tests.
```

- **R4** Use the existing Python module and pytest setup. — reuse / phase-1

The specification selects Python and pytest, and the supplied files establish the existing function and test structure.

Confirm changes target value.py and test_value.py and verify that pytest collects and runs the tests in the existing environment.

```text
Use the existing Python module and pytest setup.
```

- **R5** Keep the change within the existing module and tests without adding dependencies, UI or network access. — implement / phase-1

A local input guard and existing pytest coverage are sufficient for the requested behavior.

Review changes for added dependencies, UI components and network calls; confirm none are introduced.

```text
No new dependencies, UI or network access are required.
```

## Questions and Prerequisites

None reported.

Planning approval does not authorize implementation. Reuse proposals require actual final verification.

Writing rules: `phase-doc` 1.1 · Snapshot: `0a0eb1be9e99ed9cc0a215502462d1e9a27ae1d2192b95b8f8639edee4dba64c`
