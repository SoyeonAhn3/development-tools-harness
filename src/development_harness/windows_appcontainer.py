"""Zero-capability Windows execution on disposable runtime/project copies.

Grants stay inside the controller-owned tree. Installed runtime ACLs, accounts
and firewall configuration are never changed. Workflow admission is separate.
"""

import ctypes
from ctypes import wintypes
import msvcrt
import math
import os
from pathlib import Path
import subprocess
import time
import uuid

from .model import HarnessError
from .processes import Job, identity


class _Startup(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("reserved", wintypes.LPWSTR),
                ("desktop", wintypes.LPWSTR), ("title", wintypes.LPWSTR)] + [
        (name, wintypes.DWORD) for name in ("x", "y", "width", "height", "chars_x", "chars_y", "fill", "flags")
    ] + [("show", wintypes.WORD), ("reserved_size", wintypes.WORD), ("reserved_data", ctypes.c_void_p),
         ("stdin", wintypes.HANDLE), ("stdout", wintypes.HANDLE), ("stderr", wintypes.HANDLE)]


class _StartupEx(ctypes.Structure):
    _fields_ = [("info", _Startup), ("attributes", ctypes.c_void_p)]


class _Process(ctypes.Structure):
    _fields_ = [("process", wintypes.HANDLE), ("thread", wintypes.HANDLE),
                ("pid", wintypes.DWORD), ("tid", wintypes.DWORD)]


class _Capabilities(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("capabilities", ctypes.c_void_p),
                ("count", wintypes.DWORD), ("reserved", wintypes.DWORD)]


class _Api:
    def __init__(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        userenv = ctypes.WinDLL("userenv", use_last_error=True)
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        void, size, dword, handle = ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.HANDLE
        signatures = {
            "CreateAppContainerProfile": (userenv, [wintypes.LPCWSTR] * 3 + [void, dword, ctypes.POINTER(void)], ctypes.c_long),
            "DeleteAppContainerProfile": (userenv, [wintypes.LPCWSTR], ctypes.c_long),
            "ConvertSidToStringSidW": (security, [void, ctypes.POINTER(wintypes.LPWSTR)], wintypes.BOOL),
            "FreeSid": (security, [void], void),
            "OpenProcessToken": (security, [handle, dword, ctypes.POINTER(handle)], wintypes.BOOL),
            "GetTokenInformation": (security, [handle, ctypes.c_int, void, dword, ctypes.POINTER(dword)], wintypes.BOOL),
            "LocalFree": (kernel, [void], void),
            "InitializeProcThreadAttributeList": (kernel, [void, dword, dword, ctypes.POINTER(size)], wintypes.BOOL),
            "UpdateProcThreadAttribute": (kernel, [void, dword, size, void, size, void, void], wintypes.BOOL),
            "DeleteProcThreadAttributeList": (kernel, [void], None),
            "CreateProcessW": (kernel, [wintypes.LPCWSTR, wintypes.LPWSTR, void, void, wintypes.BOOL,
                                          dword, void, wintypes.LPCWSTR, ctypes.POINTER(_StartupEx),
                                          ctypes.POINTER(_Process)], wintypes.BOOL),
            "ResumeThread": (kernel, [handle], dword),
            "WaitForSingleObject": (kernel, [handle, dword], dword),
            "GetExitCodeProcess": (kernel, [handle, ctypes.POINTER(dword)], wintypes.BOOL),
            "TerminateProcess": (kernel, [handle, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": (kernel, [handle], wintypes.BOOL),
        }
        for name, (dll, arguments, result) in signatures.items():
            function = getattr(dll, name)
            function.argtypes, function.restype = arguments, result
            setattr(self, name, function)


def _checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def token_evidence(api, process):
    token = wintypes.HANDLE()
    _checked(api.OpenProcessToken(process, 0x0008, ctypes.byref(token)))
    try:
        result = {}
        # TOKEN_GROUPS starts with its count; reserve enough space for any groups.
        for name, kind in (("appcontainer", 29), ("capability_count", 30), ("elevated", 20)):
            length = wintypes.DWORD()
            api.GetTokenInformation(token, kind, None, 0, ctypes.byref(length))
            buffer = ctypes.create_string_buffer(length.value)
            _checked(api.GetTokenInformation(token, kind, buffer, length, ctypes.byref(length)))
            value = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD))[0]
            result[name] = value if name == "capability_count" else bool(value)
        return result
    finally:
        api.CloseHandle(token)


class AppContainer:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.api = _Api()
        self.name = "harness.probe." + uuid.uuid4().hex
        self.sid = ctypes.c_void_p()
        self.created = False
        self.record = {"name": self.name, "capabilities": [], "grants": []}
        self.traversed = set()

    def __enter__(self):
        code = self.api.CreateAppContainerProfile(self.name, self.name,
                                                  "Disposable harness permission probe", None, 0,
                                                  ctypes.byref(self.sid))
        self.record["create_hresult"] = code
        if code != 0:
            raise HarnessError(f"AppContainer profile creation failed (0x{code & 0xffffffff:08x}); no fallback executed.")
        self.created = True
        text = wintypes.LPWSTR()
        try:
            _checked(self.api.ConvertSidToStringSidW(self.sid, ctypes.byref(text)))
            self.sid_string = text.value
            self.record["sid"] = self.sid_string
        except BaseException:
            self.__exit__(None, None, None)
            raise
        finally:
            if text:
                self.api.LocalFree(text)
        return self

    def owned(self, path):
        path = Path(path).absolute()
        if not path.is_relative_to(self.root) or path == self.root:
            raise HarnessError("AppContainer probe access must stay inside its disposable tree.")
        for part in (path, *path.parents):
            if part == self.root:
                break
            if part.is_symlink() or part.is_junction():
                raise HarnessError("Linked paths are not supported in AppContainer probes.")
        if not path.resolve().is_relative_to(self.root):
            raise HarnessError("AppContainer probe path resolves outside its disposable tree.")
        return path

    def grant(self, path, *, write=False):
        path = self.owned(path)
        for parent in path.parents:
            if not parent.is_relative_to(self.root):
                break
            if parent not in self.traversed:
                # Read/list this directory only, with NO inheritance to files or
                # children. Windows Python stats ancestors when resolving inputs.
                # Never grant anything on ancestors outside this disposable root.
                self._grant(parent, "RX")
                self.traversed.add(parent)
        rights = ("(OI)(CI)" if path.is_dir() else "") + ("M" if write else "RX")
        self._grant(path, rights)

    def _grant(self, path, rights):
        # Numeric SID, explicit argv, and only this new profile's disposable copies.
        result = subprocess.run([str(Path(os.environ["SystemRoot"]) / "System32/icacls.exe"),
                                 str(path), "/grant", "*" + self.sid_string + ":" + rights],
                                capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise HarnessError("Cannot grant access to a disposable AppContainer probe path.")
        self.record["grants"].append({"path": str(path), "rights": rights})

    def run(self, argv, cwd, output, *, timeout=25, scratch=None, launched=lambda _: None):
        """Create suspended inside a kill-on-close job, verify token, then start."""
        if type(timeout) not in {int, float} or not math.isfinite(timeout) or not 0 < timeout <= 3600:
            raise HarnessError("AppContainer timeout must be between 0 and 3600 seconds.")
        cwd, output = self.owned(cwd), self.owned(output)
        scratch = self.owned(scratch) if scratch is not None else cwd / "tmp"
        self.owned(argv[0])  # No system/installed executable ACL changes.
        output.mkdir(exist_ok=False)
        api, process, attributes, job = self.api, _Process(), None, None
        started = time.time()
        try:
            job = Job()
            length = ctypes.c_size_t()
            api.InitializeProcThreadAttributeList(None, 3, 0, ctypes.byref(length))
            attributes = ctypes.create_string_buffer(length.value)
            _checked(api.InitializeProcThreadAttributeList(attributes, 3, 0, ctypes.byref(length)))
            # Assign during creation so controller death cannot strand a suspended
            # process between CreateProcessW and AssignProcessToJobObject.
            jobs = (wintypes.HANDLE * 1)(job.handle)
            _checked(api.UpdateProcThreadAttribute(attributes, 0, 0x2000D, jobs,
                                                   ctypes.sizeof(jobs), None, None))
            capabilities = _Capabilities(self.sid, None, 0, 0)
            _checked(api.UpdateProcThreadAttribute(attributes, 0, 0x20009, ctypes.byref(capabilities),
                                                   ctypes.sizeof(capabilities), None, None))
            with open(os.devnull, "rb") as source, (output / "stdout.log").open("xb") as out, (output / "stderr.log").open("xb") as err:
                handles = [msvcrt.get_osfhandle(f.fileno()) for f in (source, out, err)]
                inherited = (wintypes.HANDLE * len(handles))(*handles)
                _checked(api.UpdateProcThreadAttribute(attributes, 0, 0x20002, inherited,
                                                       ctypes.sizeof(inherited), None, None))
                startup = _StartupEx()
                startup.info.cb, startup.info.flags = ctypes.sizeof(startup), 0x100
                startup.attributes = ctypes.cast(attributes, ctypes.c_void_p)
                startup.info.stdin, startup.info.stdout, startup.info.stderr = handles
                # Windows 10 AppContainer setup requires the user/profile path variables.
                allowed = {"SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}
                env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
                env.update(TEMP=str(scratch), TMP=str(scratch))
                environment = ctypes.create_unicode_buffer("\0".join(f"{k}={v}" for k, v in sorted(env.items())) + "\0\0")
                command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
                try:
                    for handle in handles:
                        os.set_handle_inheritable(handle, True)
                    # EXTENDED_STARTUPINFO_PRESENT | UNICODE_ENVIRONMENT | NO_WINDOW | SUSPENDED
                    _checked(api.CreateProcessW(str(argv[0]), command, None, None, True, 0x80000 | 0x400 | 0x8000000 | 0x4,
                                               environment, str(cwd), ctypes.byref(startup), ctypes.byref(process)))
                finally:
                    for handle in handles:
                        os.set_handle_inheritable(handle, False)
                token = token_evidence(api, process.process)
                if token != {"appcontainer": True, "capability_count": 0, "elevated": False}:
                    raise HarnessError("Unexpected AppContainer token; process was not started.")
                launched({"process": identity(process.pid), "containment": dict(job.record),
                          "token": token, "outcome": "running"})
                if api.ResumeThread(process.thread) == 0xffffffff:
                    raise ctypes.WinError(ctypes.get_last_error())
                deadline = time.monotonic() + timeout
                while True:
                    state = api.WaitForSingleObject(process.process, max(1, min(200, int((deadline - time.monotonic()) * 1000))))
                    if state != 258 or time.monotonic() >= deadline:
                        break
                if state not in (0, 258):
                    raise HarnessError("Cannot determine AppContainer process completion.")
                if state == 258:
                    job.close()
                    if api.WaitForSingleObject(process.process, 5000) != 0:
                        raise HarnessError("AppContainer process did not stop after its deadline.")
                code = wintypes.DWORD()
                _checked(api.GetExitCodeProcess(process.process, ctypes.byref(code)))
                job.close()  # Also stop children left behind by a finished parent.
            result = {"outcome": "finished" if state == 0 else "interrupted", "exit_code": code.value,
                      "pid": process.pid, "containment": dict(job.record), "token": token,
                      "duration": time.time() - started if state == 0 else None}
            for name in ("stdout", "stderr"):
                with (output / (name + ".log")).open("rb") as stream:
                    raw = stream.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise HarnessError("AppContainer probe output exceeded the investigation limit.")
                result[name] = raw.decode("utf-8", errors="replace")
            return result
        finally:
            if job:
                job.close()
            if process.process:
                # Cover setup errors while the process is still suspended/unassigned.
                if api.WaitForSingleObject(process.process, 0) != 0:
                    api.TerminateProcess(process.process, 1)
                    api.WaitForSingleObject(process.process, 5000)
                api.CloseHandle(process.process)
            if process.thread:
                api.CloseHandle(process.thread)
            if attributes is not None:
                api.DeleteProcThreadAttributeList(attributes)

    def __exit__(self, *_):
        try:
            if self.created:
                self.record["delete_hresult"] = self.api.DeleteAppContainerProfile(self.name)
                self.created = False
                if self.record["delete_hresult"] != 0:
                    raise HarnessError("Cannot remove the disposable AppContainer profile: " + self.name)
        finally:
            if self.sid:
                self.api.FreeSid(self.sid)
                self.sid = ctypes.c_void_p()


# Preserve the earlier synthetic diagnostic's import/API.
ProbeContainer = AppContainer
