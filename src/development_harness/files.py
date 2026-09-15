"""Content identities and checked fake writes. Never use Git to restore files."""

import contextlib
import hashlib
import os
from pathlib import Path

from .model import EXCLUDED, HarnessError, digest, relative_path


def is_link(path):
    return path.is_symlink() or path.is_junction()


def target(root, name):
    relative_path(name)
    path = root / name
    for part in (path, *path.parents):
        if part == root:
            break
        if is_link(part):
            raise HarnessError(f"Linked paths are not supported: {part}")
    if not path.resolve().is_relative_to(root):
        raise HarnessError(f"Path leaves the project: {name}")
    return path


def snapshot(root):
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED)
        files = [name for name in files if name.lower() not in EXCLUDED]
        for name in dirs + files:
            if is_link(base / name):
                raise HarnessError(f"Linked paths are not supported in the content baseline: {base / name}")
        for name in sorted(files):
            path = base / name
            before = path.stat()
            content = path.read_bytes()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise HarnessError(f"File changed while reading the baseline: {path}")
            result[path.relative_to(root).as_posix()] = hashlib.sha256(content).hexdigest()
    return result


def differences(expected, actual):
    return [name for name in sorted(expected.keys() | actual.keys()) if expected.get(name) != actual.get(name)]


def require_snapshot(root, expected):
    actual = snapshot(root)
    changed = differences(expected, actual)
    if changed:
        raise HarnessError("Unexpected file changes; preserved without overwrite: " + ", ".join(changed))
    return digest(actual)


@contextlib.contextmanager
def exclusive_file(path, exists):
    # On the supported Windows runtime, deny concurrent write/delete access while
    # checking and writing. Compare-and-replace alone would leave an editor race.
    if os.name != "nt":
        raise HarnessError("Phase 1 file writes are supported on Windows only.")
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0x80000000 | 0x40000000, 1, None, 3 if exists else 1, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        raise HarnessError(f"Cannot exclusively open file; preserved: {path} ({ctypes.get_last_error()})")
    fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
    with os.fdopen(fd, "r+b") as stream:
        yield stream


def apply_write(root, name, content, expected):
    path = target(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    target(root, name)
    with exclusive_file(path, expected is not None) as stream:
        current = stream.read()
        if expected is not None and hashlib.sha256(current).hexdigest() != expected:
            raise HarnessError(f"File changed before write; preserved: {name}")
        stream.seek(0)
        stream.write(content.encode("utf-8"))
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())
