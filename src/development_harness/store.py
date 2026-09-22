"""SQLite journal; each state/evidence transition is one transaction."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .model import HarnessError, digest


INACTIVE_STAGES = {"accepted", "cancelled", "plan_approved", "superseded"}


def default_home():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "development-tools-harness" / "runtime"


def check_home(home, project):
    home = Path(home).resolve()
    if home.is_relative_to(project) or any(p.lower().startswith("onedrive") for p in home.parts):
        raise HarnessError("Runtime storage must be outside the project and OneDrive.")
    return home


class Store:
    def __init__(self, project, home=None):
        self.project = Path(project).resolve()
        if not self.project.is_dir():
            raise HarnessError(f"Project directory does not exist: {self.project}")
        self.project_id = digest(os.path.normcase(str(self.project)))
        self.home = check_home(home or default_home(), self.project)
        self.directory = self.home / self.project_id
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "state.sqlite3"
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise HarnessError(f"Unsupported state format {version}; existing database was not migrated.")
            if version == 1:
                # Opening an existing journal for status/report must not write
                # its schema-version header or silently rebuild missing tables.
                db.execute("SELECT id, active, data FROM runs LIMIT 0")
                db.execute("SELECT id, run_id, recorded, kind, data FROM events LIMIT 0")
                if not db.execute("SELECT 1 FROM sqlite_master WHERE type='index' AND name='one_active_run'").fetchone():
                    raise HarnessError("State ownership index is missing; inspect the existing database.")
            else:
                db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, active INTEGER NOT NULL, data TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_run ON runs(active) WHERE active=1;
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
                    recorded REAL NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL
                );
                PRAGMA user_version=1;
                """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, run_id=None):
        with self.connect() as db:
            row = (db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone() if run_id
                   else db.execute("SELECT data FROM runs ORDER BY rowid DESC LIMIT 1").fetchone())
        if row is None:
            raise HarnessError("No run found. Use prepare first.")
        return json.loads(row[0])

    def active(self):
        with self.connect() as db:
            row = db.execute("SELECT data FROM runs WHERE active=1").fetchone()
        return json.loads(row[0]) if row else None

    def latest(self, kind):
        """Select by recorded run kind without changing the active run."""
        with self.connect() as db:
            rows = db.execute("SELECT data FROM runs ORDER BY rowid DESC").fetchall()
        for row in rows:
            run = json.loads(row[0])
            if run.get("kind") == kind:
                return run
        raise HarnessError("No " + kind + " run found.")

    def transition(self, run_id, event_id, kind, detail, update):
        """Atomically update a fresh run and append one replay-safe event.

        The callback only changes the in-memory run. Files and external calls
        cannot be made atomic by this transaction and must be journaled first.
        A replay returns current state, never a stale snapshot supplied by a caller.
        """
        if not isinstance(event_id, str) or not event_id:
            raise HarnessError("A stable transition identity is required.")
        detail = json.dumps(detail, ensure_ascii=True, sort_keys=True, allow_nan=False)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise HarnessError("Run no longer exists.")
            run = json.loads(row[0])
            previous = db.execute("SELECT run_id, kind, data FROM events WHERE id=?", (event_id,)).fetchone()
            if previous is not None:
                if (previous["run_id"] != run_id or previous["kind"] != kind or
                        json.loads(previous["data"]) != json.loads(detail)):
                    raise HarnessError("Transition identity was reused with different evidence.")
                return run
            update(run)
            if run.get("id") != run_id:
                raise HarnessError("A transition cannot change the run identity.")
            active = int(run["stage"] not in INACTIVE_STAGES)
            db.execute("UPDATE runs SET active=?, data=? WHERE id=?",
                       (active, json.dumps(run, ensure_ascii=True, allow_nan=False), run_id))
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                       (event_id, run_id, time.time(), kind, detail))
            return run

    def supersede_and_create(self, run_id, event_id, kind, detail, new_run, update_old):
        """Replace the active workflow and journal both links in one transaction.

        No filesystem changes or external calls belong in ``update_old``. A
        failed insert/event rolls back supersession as well as the new run.
        """
        if not isinstance(event_id, str) or not event_id:
            raise HarnessError("A stable replanning transition identity is required.")
        if (not isinstance(new_run, dict) or not isinstance(new_run.get("id"), str) or not new_run["id"]
                or new_run["id"] == run_id or new_run.get("kind") != "planning"
                or new_run.get("stage") != "baseline_pending" or new_run.get("approval") is not None
                or new_run.get("project_id") != self.project_id or new_run.get("project") != str(self.project)
                or new_run.get("feedback_source", {}).get("workflow_run_id") != run_id):
            raise HarnessError("Replanning must create a distinct unapproved planning baseline.")
        detail = json.dumps(detail, ensure_ascii=True, sort_keys=True, allow_nan=False)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data, active FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise HarnessError("Source workflow no longer exists.")
            previous = db.execute("SELECT run_id, kind, data FROM events WHERE id=?", (event_id,)).fetchone()
            old = json.loads(row["data"])
            if previous is not None:
                if (previous["run_id"] != run_id or previous["kind"] != kind
                        or json.loads(previous["data"]) != json.loads(detail)):
                    raise HarnessError("Replanning transition identity was reused with different evidence.")
                replacement_id = old.get("replanning", {}).get("planning_run_id")
                if replacement_id != new_run["id"]:
                    raise HarnessError("Replanning replay refers to a different replacement run.")
                replacement = db.execute("SELECT data FROM runs WHERE id=?", (replacement_id,)).fetchone()
                if replacement is None:
                    raise HarnessError("Recorded replacement planning run is missing.")
                return json.loads(replacement["data"])
            if old.get("kind") != "workflow" or old.get("stage") != "replanning_required" or row["active"] != 1:
                raise HarnessError("Only the active workflow awaiting requirement replanning can be superseded.")
            update_old(old)
            if (old.get("id") != run_id or old.get("stage") != "superseded"
                    or old.get("replanning", {}).get("planning_run_id") != new_run["id"]):
                raise HarnessError("Replanning must preserve and link the superseded workflow identity.")
            db.execute("UPDATE runs SET active=0, data=? WHERE id=?",
                       (json.dumps(old, ensure_ascii=True, allow_nan=False), run_id))
            db.execute("INSERT INTO runs VALUES (?, 1, ?)",
                       (new_run["id"], json.dumps(new_run, ensure_ascii=True, allow_nan=False)))
            now = time.time()
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)", (event_id, run_id, now, kind, detail))
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                       (event_id + ":registered", new_run["id"], now, "replanning_registered", detail))
            return new_run

    def save(self, run, kind, detail=None, *, new=False):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active = int(run["stage"] not in INACTIVE_STAGES)
            data = json.dumps(run, ensure_ascii=True)
            if new:
                db.execute("INSERT INTO runs VALUES (?, ?, ?)", (run["id"], active, data))
            else:
                changed = db.execute("UPDATE runs SET active=?, data=? WHERE id=?", (active, data, run["id"]))
                if changed.rowcount != 1:
                    raise HarnessError("Run no longer exists.")
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                       (uuid.uuid4().hex, run["id"], time.time(), kind, json.dumps(detail or {}, ensure_ascii=True)))

    def events(self, run_id):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM events WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
        return [{**dict(row), "data": json.loads(row["data"])} for row in rows]
