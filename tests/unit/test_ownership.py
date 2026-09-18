import json

import pytest

from development_harness.model import HarnessError
from development_harness.processes import default_home, identity
from development_harness.runner import Harness


def ownership_paths(harness):
    directory = default_home() / "ownership"
    directory.mkdir(parents=True, exist_ok=True)
    name = harness.store.project_id
    return directory / (name + ".lock"), directory / (name + ".json")


def test_legacy_ownership_migration_preserves_active_run(workspace, tmp_path):
    harness, _, plan_path, _ = workspace
    harness.prepare(plan_path)
    lock, record = ownership_paths(harness)
    legacy = b"\0" + json.dumps({"database": str(harness.store.path), "owner": identity()}).encode()
    lock.write_bytes(legacy)
    record.unlink()
    alternate = Harness(harness.project, tmp_path / "alternate")
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.prepare(plan_path)
    assert lock.read_bytes() == legacy
    assert not record.exists()

    harness.approve()
    assert lock.read_bytes() == legacy
    assert json.loads(record.read_bytes())["database"] == str(harness.store.path)
    with pytest.raises(HarnessError, match="another state directory"):
        alternate.prepare(plan_path)


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("raw", [b"", b'{"database":', b"[]", b'{"database": 1}'])
def test_malformed_ownership_stops_without_replacing_evidence(workspace, tmp_path, legacy, raw):
    harness, _, plan_path, _ = workspace
    harness.prepare(plan_path)
    lock, record = ownership_paths(harness)
    if legacy:
        # An empty legacy payload is also the never-registered format, so use
        # whitespace for an invalid legacy record rather than that valid sentinel.
        raw = raw or b" "
        record.unlink()
        damaged = b"\0" + raw
        lock.write_bytes(damaged)
        inspected = lock
    else:
        record.write_bytes(raw)
        damaged = raw
        inspected = record
    alternate = Harness(harness.project, tmp_path / "alternate")
    for candidate in (harness, alternate):
        with pytest.raises(HarnessError, match="Invalid ownership metadata"):
            candidate.prepare(plan_path)
    assert inspected.read_bytes() == damaged
    assert alternate.store.active() is None


def test_completed_ownership_allows_switching_state_directory(workspace, tmp_path):
    harness, _, plan_path, _ = workspace
    harness.prepare(plan_path)
    harness.cancel()
    alternate = Harness(harness.project, tmp_path / "alternate")
    alternate.prepare(plan_path)
    _, record = ownership_paths(harness)
    assert json.loads(record.read_bytes())["database"] == str(alternate.store.path)
    with pytest.raises(HarnessError, match="another state directory"):
        harness.prepare(plan_path)
