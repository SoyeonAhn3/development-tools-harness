"""Trusted synthetic observations inside the disposable AppContainer."""

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def token():
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    security.OpenProcessToken.restype = wintypes.BOOL
    security.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    security.GetTokenInformation.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = wintypes.HANDLE()
    if not security.OpenProcessToken(wintypes.HANDLE(-1), 8, ctypes.byref(handle)):
        raise ctypes.WinError(ctypes.get_last_error())
    result = {}
    try:
        for name, kind in (("appcontainer", 29), ("capability_count", 30), ("elevated", 20)):
            size = wintypes.DWORD()
            security.GetTokenInformation(handle, kind, None, 0, ctypes.byref(size))
            buffer = ctypes.create_string_buffer(size.value)
            if not security.GetTokenInformation(handle, kind, buffer, size, ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            value = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD))[0]
            result[name] = value if name == "capability_count" else bool(value)
    finally:
        kernel.CloseHandle(handle)
    return result


def observe(spec, generation):
    label = spec["role"] + ":" + generation
    result = {"pid": os.getpid(), "token": token(), "reads": {}, "writes": {}, "networks": {}}
    for name, path in spec["paths"].items():
        try:
            Path(path).read_bytes()
            result["reads"][name] = "read"
        except PermissionError:
            result["reads"][name] = "denied"
        except OSError as exc:
            result["reads"][name] = "error: " + str(exc)
        try:
            Path(path).write_text(label + "\n", encoding="utf-8")
            result["writes"][name] = {"outcome": "written"}
        except PermissionError:
            result["writes"][name] = {"outcome": "denied"}
        except OSError as exc:
            result["writes"][name] = {"outcome": "error", "error": str(exc)}
    for name, endpoint in spec["endpoints"].items():
        family = socket.AF_INET6 if name.endswith("6") else socket.AF_INET
        kind = socket.SOCK_DGRAM if name.startswith("udp") else socket.SOCK_STREAM
        try:
            with socket.socket(family, kind) as connection:
                connection.settimeout(0.75)
                connection.connect(tuple(endpoint))
                connection.send((label + ":" + name).encode("ascii"))
                response = connection.recv(16)
            result["networks"][name] = {"outcome": "connected" if response == b"ack" else "error"}
        except (PermissionError, TimeoutError) as exc:
            result["networks"][name] = {"outcome": "denied", "error": str(exc),
                                         "winerror": getattr(exc, "winerror", None)}
        except OSError as exc:
            result["networks"][name] = {"outcome": "error", "error": str(exc),
                                         "winerror": getattr(exc, "winerror", None)}
    # Existing file/process evaluator uses one network result; the host additionally
    # checks every protocol, token and read observation.
    result["network"] = result["networks"]["tcp4"]
    return result


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "--child" in sys.argv[2:]:
        print(json.dumps(observe(spec, "child")))
        return
    parent = observe(spec, "parent")
    child = subprocess.run([sys.executable, "-I", "-B", __file__, sys.argv[1], "--child"],
                           capture_output=True, text=True, encoding="utf-8", timeout=12,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        child_result = json.loads(child.stdout)
    except ValueError:
        child_result = {"error": "Child did not return observations", "stderr": child.stderr}
    print(json.dumps({"parent": parent, "child": child_result, "child_exit_code": child.returncode}))


if __name__ == "__main__":
    main()
