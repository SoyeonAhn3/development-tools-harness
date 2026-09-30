"""Private temporary directories for the copied Windows validation runtime.

Python 3.12's mkdir(0o700) omits the AppContainer SID from its protected DACL.
This startup hook adds that SID only for new directories inside the granted
scratch tree. Windows permissions, not this compatibility hook or its environment
marker, enforce isolation. No existing ACL is edited. Host Python is untouched.
"""

import ctypes
from ctypes import wintypes
import errno
import operator
import os
from pathlib import Path
import sys


SCRATCH_ENV = "DEVELOPMENT_HARNESS_TEST_SCRATCH"
_installation = None


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("descriptor", ctypes.c_void_p),
                ("inherit", wintypes.BOOL)]


class _Windows:
    def __init__(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        void, handle, dword = ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD
        definitions = {
            "GetCurrentProcess": (kernel, [], handle),
            "CloseHandle": (kernel, [handle], wintypes.BOOL),
            "LocalFree": (kernel, [void], void),
            "CreateDirectoryW": (kernel, [wintypes.LPCWSTR, ctypes.POINTER(_SecurityAttributes)], wintypes.BOOL),
            "CreateFileW": (kernel, [wintypes.LPCWSTR, dword, dword, void, dword, dword, handle], handle),
            "GetFinalPathNameByHandleW": (kernel, [handle, wintypes.LPWSTR, dword, dword], dword),
            "OpenProcessToken": (security, [handle, dword, ctypes.POINTER(handle)], wintypes.BOOL),
            "GetTokenInformation": (security, [handle, ctypes.c_int, void, dword, ctypes.POINTER(dword)], wintypes.BOOL),
            "ConvertSidToStringSidW": (security, [void, ctypes.POINTER(wintypes.LPWSTR)], wintypes.BOOL),
            "ConvertStringSecurityDescriptorToSecurityDescriptorW":
                (security, [wintypes.LPCWSTR, dword, ctypes.POINTER(void), void], wintypes.BOOL),
        }
        for name, (library, arguments, result) in definitions.items():
            function = getattr(library, name)
            function.argtypes, function.restype = arguments, result
            setattr(self, name, function)

    @staticmethod
    def checked(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())

    def container_sid(self):
        token = wintypes.HANDLE()
        self.checked(self.OpenProcessToken(self.GetCurrentProcess(), 0x0008, ctypes.byref(token)))
        try:
            active, size = wintypes.DWORD(), wintypes.DWORD()
            self.checked(self.GetTokenInformation(token, 29, ctypes.byref(active), ctypes.sizeof(active), ctypes.byref(size)))
            if not active.value:
                return None
            self.GetTokenInformation(token, 31, None, 0, ctypes.byref(size))
            if not size.value:
                raise ctypes.WinError(ctypes.get_last_error())
            information = ctypes.create_string_buffer(size.value)
            self.checked(self.GetTokenInformation(token, 31, information, size.value, ctypes.byref(size)))
            sid = ctypes.cast(information, ctypes.POINTER(ctypes.c_void_p))[0]
            text = wintypes.LPWSTR()
            self.checked(self.ConvertSidToStringSidW(sid, ctypes.byref(text)))
            try:
                return text.value
            finally:
                self.LocalFree(text)
        finally:
            self.CloseHandle(token)

    def mkdir(self, path, sid):
        # Match Python's private owner/admin/system ACL, plus this container.
        # A protected DACL avoids inheriting unrelated users' access.
        sddl = "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)(A;OICI;FA;;;" + sid + ")"
        descriptor = ctypes.c_void_p()
        self.checked(self.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, ctypes.byref(descriptor), None))
        try:
            attributes = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            if not self.CreateDirectoryW(str(path), ctypes.byref(attributes)):
                error = ctypes.WinError(ctypes.get_last_error())
                error.filename = str(path)
                raise error
        finally:
            self.LocalFree(descriptor)

    def final_nt_path(self, path):
        # DOS/GUID volume-name lookup can be denied in AppContainer even when
        # opening the file and requesting its normalized NT name both succeed.
        handle = self.CreateFileW(str(path), 0x80, 7, None, 3, 0x02000000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            size = 512
            while True:
                buffer = ctypes.create_unicode_buffer(size)
                length = self.GetFinalPathNameByHandleW(handle, buffer, size, 2)
                self.checked(length)
                if length < size:
                    return buffer.value
                size = length + 1
        finally:
            self.CloseHandle(handle)


def _destination(path, scratch):
    raw = os.fsdecode(os.fspath(path))
    if "\0" in raw:
        raise ValueError("embedded null character")
    # GetFullPathName (used by abspath on Windows) can erase trailing dots/spaces
    # or turn reserved names into device paths. Reject those before normalization.
    supplied = Path(raw)
    if any(":" in part or part.endswith((".", " ")) or Path(part).is_reserved()
           for part in supplied.parts if part not in {supplied.anchor, ".", ".."}):
        raise PermissionError(errno.EACCES, "Unsupported temporary directory path", raw)
    destination = Path(os.path.abspath(raw))
    if destination == scratch or not destination.is_relative_to(scratch):
        return None
    for part in (destination, *destination.parents):
        if part.is_symlink() or part.is_junction():
            raise PermissionError(errno.EACCES, "Linked temporary directory path", raw)
        if part == scratch:
            break
    return destination


def install():
    """Called by the copied runtime's sitecustomize, including normal children."""
    global _installation
    if _installation is not None or os.name != "nt" or not os.environ.get(SCRATCH_ENV):
        return
    api = _Windows()
    sid = api.container_sid()
    if sid is None:
        return  # The frozen controller and ordinary development Python stay unchanged.
    scratch = Path(os.environ[SCRATCH_ENV])
    if not scratch.is_absolute() or not scratch.is_dir() or scratch.is_symlink() or scratch.is_junction():
        raise RuntimeError("Invalid controller temporary directory.")
    scratch = Path(os.path.abspath(scratch))
    original = os.mkdir
    original_final = os.path._getfinalpathname
    scratch_nt = api.final_nt_path(scratch)

    def final_path(path):
        try:
            return original_final(path)
        except PermissionError:
            destination = Path(os.path.abspath(path))
            if destination != scratch and _destination(path, scratch) is None:
                raise
            # Never replace a denied query with lexical normalization. Both the
            # root and target must be openable, and their resolved physical NT
            # names must identify this same scratch tree. No ACL is changed.
            physical = api.final_nt_path(destination)
            if physical.casefold() == scratch_nt.casefold():
                relative = ""
            elif physical.casefold().startswith(scratch_nt.casefold() + "\\"):
                relative = physical[len(scratch_nt) + 1:]
            else:
                raise PermissionError(errno.EACCES, "Resolved path leaves temporary directory", str(path))
            return "\\\\?\\" + str(scratch / relative)

    def mkdir(path, mode=0o777, *, dir_fd=None):
        if operator.index(mode) == 0o700 and dir_fd is None:
            destination = _destination(path, scratch)
            if destination is not None:
                sys.audit("os.mkdir", os.fspath(path), mode, -1)
                return api.mkdir(destination, sid)
        return original(path, mode, dir_fd=dir_fd)

    os.mkdir = mkdir
    os.path._getfinalpathname = final_path
    # Windows rewrites TEMP/TMP for AppContainer startup. Restore the actual
    # controller grant before tempfile is first used, also in child interpreters.
    os.environ.update(TEMP=str(scratch), TMP=str(scratch))
    import tempfile
    tempfile.tempdir = None
    _installation = (scratch, mkdir, sid, final_path)


def require(scratch):
    """Fail before importing project tests if startup initialization was skipped."""
    expected = Path(os.path.abspath(scratch))
    if (_installation is None or _installation[0] != expected or os.mkdir is not _installation[1]
            or os.path._getfinalpathname is not _installation[3]):
        raise RuntimeError("AppContainer temporary-directory compatibility was not initialized.")
    return {"scratch": str(expected), "appcontainer_sid": _installation[2]}
