# CLI input validation

The existing Python command `python cli.py VALUE` doubles an integer.
Preserve `python cli.py 3` returning exit code 0 and stdout `6`, and
`python cli.py 0` returning exit code 0 and stdout `0`, each with a newline
and no stderr output.

Reject negative integers with a nonzero exit code, no numeric stdout and
a clear stderr message explaining that the value must be nonnegative.
Preserve argparse handling of missing or non-integer arguments.

Use the existing Python standard library and pytest. Add command-level tests
for negative input and retain the positive and zero checks. Run
`python -m pytest -q` and record its actual result. Do not add dependencies,
UI or network access. Limit implementation changes to `cli.py` and
`test_cli.py`; this specification and harness approval/configuration files
are inputs and must not be edited by the worker.

This is a prepared test fixture. Negative-input rejection is intentionally
unimplemented until the approved live Phase 3 workflow example. Fixture
baseline tests alone do not establish completion of that future change.
