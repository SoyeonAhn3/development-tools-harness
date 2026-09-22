"""Only verified code failures may consume automatic correction attempts."""

import xml.etree.ElementTree as ET

import pytest

from development_harness.isolated_validation import failure_classification
from development_harness.validation import pytest_result


def report(tmp_path, problems):
    suite = ET.Element("testsuite")
    for tag, attributes in problems:
        case = ET.SubElement(suite, "testcase", name="test_example")
        if tag:
            ET.SubElement(case, tag, attributes).text = "Untrusted stdout mentioning AssertionError is not evidence."
    path = tmp_path / "junit.xml"
    ET.ElementTree(suite).write(path, encoding="utf-8")
    return path


@pytest.mark.parametrize("message", ["AssertionError: expected result", "assert 2 == 3", "TypeError: bad call",
                                     "ValueError: unexpected application result", "KeyError: 'item'"])
def test_confirmed_code_failures_allow_correction(tmp_path, message):
    path = report(tmp_path, [("failure", {"message": message})])
    assert failure_classification("failed", path) == "code"


@pytest.mark.parametrize("tag,attributes,expected", [
    ("failure", {"message": "ModuleNotFoundError: No module named 'missing'"}, "environment"),
    ("failure", {"type": "builtins.FileNotFoundError", "message": "missing executable"}, "environment"),
    ("failure", {"message": "PermissionError: access denied"}, "permission"),
    ("failure", {"message": "[WinError 5] Access is denied"}, "permission"),
    ("error", {"message": 'failed on setup with "ModuleNotFoundError: missing"'}, "environment"),
    ("error", {"message": 'failed on teardown with "PermissionError: denied"'}, "permission"),
    ("error", {"message": 'failed on setup with "AssertionError: fixture failed"'}, "environment"),
    ("failure", {"message": "Failed: unknown precondition"}, "validation_incomplete"),
    ("failure", {}, "validation_incomplete"),
])
def test_environment_permission_and_ambiguous_faults_stop(tmp_path, tag, attributes, expected):
    path = report(tmp_path, [(tag, attributes)])
    assert pytest_result(path)[0] == "failed"
    assert failure_classification("failed", path) == expected


def test_environment_fault_wins_over_other_assertion_failures(tmp_path):
    path = report(tmp_path, [("failure", {"message": "assert False"}),
                             ("failure", {"message": "ImportError: missing library"})])
    assert failure_classification("failed", path) == "environment"


@pytest.mark.parametrize("first,outcome", [(None, "unverified"), ("failure", "failed")])
def test_mixed_skips_never_pass_or_authorize_correction(tmp_path, first, outcome):
    path = report(tmp_path, [(first, {"message": "assert False"}), ("skipped", {})])
    assert pytest_result(path)[0] == outcome
    assert failure_classification(outcome, path) == "validation_incomplete"


@pytest.mark.parametrize("outcome,kind", [("passed", None), ("interrupted", "interrupted"),
                                         ("no_tests", "validation_incomplete"),
                                         ("unverified", "validation_incomplete"),
                                         ("failed", "validation_incomplete")])
def test_no_xml_or_incomplete_result_cannot_authorize_retry(tmp_path, outcome, kind):
    assert failure_classification(outcome, tmp_path / "missing.xml") == kind
