"""Windows ownership locks, process identities and kill-on-close job containment."""

import ctypes
from ctypes import wintypes
import json
import msvcrt
import os
from pathlib import Path
import sqlite3
import tempfile

import psutil

from .model import HarnessError
from .store import default_home


def identity(pid=None):
    process = psutil.Process(pid or os.getpid())
    return {"pid": process.pid, "created": process.create_time()}


def alive(record):
    if not record:
        return False
    try:
        process = psutil.Process(record["pid"])
        return abs(process.create_time() - record["created"]) < 0.001 and process.is_running()
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied as exc:
        raise HarnessError("Cannot inspect a recorded process; unsafe to resume.") from exc


def _ownership_record(raw, path):
    try:
        record = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise HarnessError(f"Invalid ownership metadata; inspect before continuing: {path}") from exc
    if not isinstance(record, dict) or not isinstance(record.get("database"), str) or not record["database"]:
        raise HarnessError(f"Invalid ownership metadata; inspect before continuing: {path}")
    return record


def _write_ownership(path, record):
    # Replace only the metadata. Replacing the locked file would let another
    # process lock a different file object and bypass the existing OS lock.
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(json.dumps(record).encode())
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class ProjectLock:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        directory = default_home() / "ownership"
        directory.mkdir(parents=True, exist_ok=True)
        self.file = (directory / (self.store.project_id + ".lock")).open("a+b")
        if self.file.seek(0, 2) == 0:
            self.file.write(b"\0")
            self.file.flush()
        self.file.seek(0)
        try:
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self.file.close()
            raise HarnessError("Another process owns this project; retry after it stops.") from exc
        try:
            record_path = directory / (self.store.project_id + ".json")
            try:
                raw = record_path.read_bytes()
            except FileNotFoundError:
                # Read the original inline format without destroying it during migration.
                self.file.seek(1)
                raw = self.file.read()
                previous = _ownership_record(raw, self.file.name) if raw else {}
            else:
                previous = _ownership_record(raw, record_path)
            previous_db = previous.get("database")
            if previous_db and previous_db != str(self.store.path):
                path = Path(previous_db)
                if path.exists():
                    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                    try:
                        if db.execute("SELECT 1 FROM runs WHERE active=1").fetchone():
                            raise HarnessError("An unfinished run exists in another state directory: " + previous_db)
                    finally:
                        db.close()
            _write_ownership(record_path, {"database": str(self.store.path), "owner": identity()})
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *_):
        self.file.seek(0)
        msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        self.file.close()


class _BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t),
                ("max_working", ctypes.c_size_t), ("active", wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read", "write", "other")]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", _BasicLimits), ("io", _IoCounters),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]


class Job:
    """All validation descendants die when the controlling harness exits.

    This is process lifetime containment, NOT the Phase 2 permission sandbox.
    """
    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        specs = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in specs.items():
            fn = getattr(self.kernel, name)
            fn.argtypes, fn.restype = args, result
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise HarnessError("Cannot create validation process job.")
        limits = _ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise HarnessError("Cannot configure validation process containment.")

    def assign(self, pid):
        handle = self.kernel.OpenProcess(0x0100 | 0x0001, False, pid)
        if not handle:
            raise HarnessError("Cannot open validation process for containment.")
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle, handle):
                raise HarnessError("Cannot contain validation process; command was not started.")
        finally:
            self.kernel.CloseHandle(handle)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
