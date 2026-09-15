"""SQLite journal; each state/evidence transition is one transaction."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .model import HarnessError, digest


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

    def save(self, run, kind, detail=None, *, new=False):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active = int(run["stage"] not in {"accepted", "cancelled"})
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
