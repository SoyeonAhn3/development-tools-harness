"""The production validator location must work without a short injected cache."""

import copy
from pathlib import Path

from development_harness.store import default_home
from development_harness.workflow import Workflow
from test_workflow import FIRST, admitted_factory, developer, reviewer, scripted_workers


def test_default_storage_and_validator_complete_real_checks(admitted_factory):
    fixture = admitted_factory(tasks=1)
    # Reuse this disposable project's approved fixture records in the actual
    # default Store. There are no workflow attempts or executable overrides.
    workflow = Workflow(fixture.project)
    planning = fixture.store.latest("planning")
    admitted = fixture.get()
    fixture.cancel()  # Release the original state directory's ownership lease.
    workflow.store.save(copy.deepcopy(planning), "imported_disposable_planning_fixture", new=True)
    workflow.store.save(copy.deepcopy(admitted), "imported_disposable_workflow_fixture", new=True)
    worker = scripted_workers([developer(text=FIRST), reviewer()])
    assert workflow.store.home == default_home()
    result = workflow.execute(worker_factory=worker)
    assert result["stage"] == "technically_complete", result.get("reason")
    validations = [attempt for attempt in result["attempts"] if attempt["role"] == "validation"]
    assert len(validations) == 2
    assert all(attempt["outcome"] == "passed" and attempt["tests"] == 1 for attempt in validations)
    assert all(Path(attempt["record"]).is_file() for attempt in validations)
    assert all(Path(attempt["record"]).is_relative_to(default_home()) for attempt in validations)
    assert result["execution"]["corrections"] == {"T1": 0}
    assert len(worker.calls) == 2 and not worker.pending
