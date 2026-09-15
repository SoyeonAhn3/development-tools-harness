import json
import sqlite3

import pytest

from development_harness.files import snapshot
from development_harness.model import HarnessError
from development_harness.runner import Harness
from development_harness.store import Store


def test_no_implementation_before_approval_and_reopen(workspace):
    harness, _, path, _ = workspace
    run = harness.prepare(path)
    assert harness.execute()["stage"] == "awaiting_approval"
    assert (harness.project / "value.py").read_text() == "VALUE = 0\n"
    reopened = Harness(harness.project, harness.store.home)
    assert reopened.store.get()["id"] == run["id"]
    assert reopened.store.get()["approval"] is None


def test_state_and_event_rollback_together(workspace):
    harness, _, path, _ = workspace
    run = harness.prepare(path)
    with harness.store.connect() as db:
        db.execute("CREATE TRIGGER reject_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    run["stage"] = "implementing"
    with pytest.raises(sqlite3.IntegrityError):
        harness.store.save(run, "broken_transition")
    assert harness.store.get()["stage"] == "awaiting_approval"
    assert len(harness.store.events(run["id"])) == 1


def test_unknown_schema_not_migrated(workspace):
    harness, _, _, _ = workspace
    with harness.store.connect() as db:
        db.execute("PRAGMA user_version=999")
    with pytest.raises(HarnessError, match="Unsupported state"):
        Store(harness.project, harness.store.home)
    with harness.store.connect() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 999


def test_approval_binds_plan_and_preserves_changed_files(workspace):
    harness, plan, path, save = workspace
    harness.prepare(path)
    plan["phase"] = "changed"
    save()
    with pytest.raises(HarnessError, match="Plan changed"):
        harness.approve()
    assert (harness.project / "value.py").read_text() == "VALUE = 0\n"


def test_preexisting_edits_are_baseline_new_edits_block(workspace):
    harness, _, path, _ = workspace
    (harness.project / "user.txt").write_text("preexisting")
    run = harness.prepare(path)
    assert "user.txt" in run["baseline"]
    (harness.project / "user.txt").write_text("new change")
    with pytest.raises(HarnessError, match="Unexpected file"):
        harness.approve()
    assert (harness.project / "user.txt").read_text() == "new change"


def test_git_metadata_only_does_not_invalidate(workspace, fast_validation):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    git = harness.project / ".git"
    git.mkdir()
    (git / "HEAD").write_text("ref: refs/heads/manual-change\n")
    assert harness.execute()["stage"] == "awaiting_acceptance"
    assert harness.accept()["stage"] == "accepted"


def test_changed_approved_plan_stops_resume(workspace):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    path.write_text(path.read_text() + "\n")
    with pytest.raises(HarnessError, match="Plan changed"):
        harness.execute()
    assert harness.store.get()["attempts"] == []


def test_git_worktree_pointer_is_metadata_not_code(workspace, fast_validation):
    harness, _, path, _ = workspace
    pointer = harness.project / ".git"
    pointer.write_text("gitdir: first-location")
    harness.prepare(path)
    harness.approve()
    pointer.write_text("gitdir: moved-location")
    assert harness.execute()["stage"] == "awaiting_acceptance"


def test_partial_write_journal_resumes_only_known_content(workspace, fast_validation, monkeypatch):
    harness, plan, path, save = workspace
    plan["tasks"][0]["writes"] = [{"value.py": "VALUE = 1\n", "extra.txt": "approved\n"}]
    save()
    harness.prepare(path)
    harness.approve()
    from development_harness import runner
    original = runner.apply_write
    def interrupt(root, name, content, expected):
        if name == "extra.txt":
            raise KeyboardInterrupt
        original(root, name, content, expected)
    monkeypatch.setattr(runner, "apply_write", interrupt)
    stopped = harness.execute()
    assert stopped["journal"] is not None
    assert (harness.project / "value.py").read_text() == "VALUE = 1\n"
    monkeypatch.setattr(runner, "apply_write", original)
    assert harness.execute()["stage"] == "awaiting_acceptance"
    assert (harness.project / "extra.txt").read_text() == "approved\n"
    developers = [a for a in harness.store.get()["attempts"] if a["role"] == "developer"]
    assert len(developers) == 1
    assert developers[0]["duration"] is None


def test_unknown_partial_content_is_not_overwritten(workspace, monkeypatch):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    def partial(root, name, content, expected):
        (root / name).write_text("PARTIAL USER OR INTERRUPTED CONTENT")
        raise KeyboardInterrupt
    monkeypatch.setattr("development_harness.runner.apply_write", partial)
    harness.execute()
    with pytest.raises(HarnessError, match="require inspection"):
        harness.execute()
    assert (harness.project / "value.py").read_text() == "PARTIAL USER OR INTERRUPTED CONTENT"


def test_mandatory_review_corrections_bounded_and_stable(workspace, fast_validation):
    harness, plan, path, save = workspace
    plan["tasks"][0]["review"] = ["changes"]
    save()
    harness.prepare(path)
    harness.approve()
    run = harness.execute()
    assert run["stage"] == "failed"
    assert run["corrections"] == 2
    assert len(run["findings"]) == 1
    assert len([a for a in run["attempts"] if a["role"] == "developer"]) == 3
    with pytest.raises(HarnessError, match="not complete"):
        harness.accept()


def test_sequential_tasks_and_separate_result_acceptance(workspace, fast_validation):
    harness, plan, path, save = workspace
    plan["tasks"].append({"id": "task-2", "writes": [{"extra.txt": "second"}], "review": ["changes", "pass"]})
    save()
    harness.prepare(path)
    approved = harness.approve()
    assert harness.approve()["approval"] == approved["approval"]
    run = harness.execute()
    assert run["stage"] == "awaiting_acceptance"
    assert [t["id"] for t in run["completed_tasks"]] == ["task-1", "task-2"]
    assert run["findings"]["task-2:required-change"]["validation_ids"]
    assert len(run["final_evidence"]) == 1
    assert harness.status()["actual_ai_calls"] == 0
    assert harness.accept()["stage"] == "accepted"


def test_final_file_change_prevents_acceptance(workspace, fast_validation):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    harness.execute()
    (harness.project / "value.py").write_text("user changed final result")
    with pytest.raises(HarnessError, match="Unexpected file"):
        harness.accept()


def test_cancel_preserves_files_and_allows_new_run(workspace):
    harness, _, path, _ = workspace
    first = harness.prepare(path)
    before = snapshot(harness.project)
    with pytest.raises(HarnessError, match="unfinished run"):
        harness.prepare(path)
    harness.cancel()
    second = harness.prepare(path)
    assert first["id"] != second["id"]
    assert harness.store.get(first["id"])["stage"] == "cancelled"
    assert snapshot(harness.project) == before


def test_missing_final_evidence_cannot_be_accepted(workspace, fast_validation):
    harness, _, path, _ = workspace
    harness.prepare(path)
    harness.approve()
    run = harness.execute()
    run["final_evidence"] = []
    harness.store.save(run, "test_removed_evidence")
    with pytest.raises(HarnessError, match="evidence is missing"):
        harness.accept()
