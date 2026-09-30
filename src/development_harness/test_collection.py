"""Standalone pytest observer copied from the controller, never from project B."""

import json
from pathlib import Path


class CollectionEvidence:
    def __init__(self, destination):
        self.destination = Path(destination)
        self.collected = []
        self.discovered = []
        self.passed = []
        self.failed = []
        self.skipped = []
        self.deselected = []
        self.collection_errors = []

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]

    def pytest_itemcollected(self, item):
        self.discovered.append(item.nodeid)

    def pytest_deselected(self, items):
        self.deselected.extend(item.nodeid for item in items)

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append(report.nodeid)

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.failed.append(report.nodeid)
        elif report.skipped:
            self.skipped.append(report.nodeid)
        elif report.when == "call":
            self.passed.append(report.nodeid)

    def pytest_sessionfinish(self, session, exitstatus):
        self.destination.write_text(json.dumps({"discovered": self.discovered, "collected": self.collected, "passed": self.passed,
            "failed": self.failed, "skipped": self.skipped, "deselected": self.deselected,
            "collection_errors": self.collection_errors, "exit_status": int(exitstatus)}, indent=2), encoding="utf-8")


def complete_collection(record, expected_modules, tests):
    """Reject omissions, deselection, missing execution and partial success."""
    if not isinstance(record, dict):
        return False
    if any(not isinstance(record.get(name), list) or not all(isinstance(item, str) for item in record[name])
           for name in ("discovered", "collected", "passed", "failed", "skipped", "deselected", "collection_errors")):
        return False
    collected, passed = record.get("collected", []), record.get("passed", [])
    return bool(collected) and (
        record.get("exit_status") == 0 and len(collected) == len(set(collected)) == tests
        and sorted(record.get("discovered", [])) == sorted(collected)
        and sorted(passed) == sorted(collected)
        and {item.split("::", 1)[0] for item in collected} == set(expected_modules)
        and all(record.get(name) == [] for name in ("failed", "skipped", "deselected", "collection_errors")))
