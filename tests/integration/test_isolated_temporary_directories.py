"""Real pytest/tempfile use inside AppContainer, including child interpreters."""

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

import pytest

from development_harness.appcontainer_probe import tree_hash
from development_harness.isolated_validation import IsolatedValidator
from test_workflow_permissions import CHECK, validation_environment


TEMP_TESTS = r'''
import json, os, subprocess, sys, tempfile
from pathlib import Path
import pytest
from _harness_appcontainer_temp import require, SCRATCH_ENV

def exercise(path):
    assert path.resolve(strict=True) == path.absolute()
    file = path / 'value.txt'
    file.write_text('temporary data')
    assert file.read_text() == 'temporary data'
    file.unlink()
    assert not file.exists()
    with pytest.raises(FileNotFoundError):
        file.resolve(strict=True)

def test_pytest_temporary_fixtures(tmp_path, tmp_path_factory, tmpdir, tmpdir_factory):
    for path in (tmp_path, tmp_path_factory.mktemp('factory'), Path(str(tmpdir)),
                 Path(str(tmpdir_factory.mktemp('legacy')))):
        exercise(path)

def test_standard_temporary_directory():
    with tempfile.TemporaryDirectory(prefix='space 한글 ') as name:
        path = Path(name)
        exercise(path)
    assert not path.exists()

def test_private_directory_errors_and_acl_evidence():
    scratch = Path(os.environ['TEMP'])
    info = require(scratch)
    path = scratch / 'private 한글'
    path.mkdir(mode=0o700)
    exercise(path)
    with pytest.raises(FileExistsError):
        path.mkdir(mode=0o700)
    with pytest.raises(FileNotFoundError):
        (scratch / 'missing' / 'leaf').mkdir(mode=0o700)
    with pytest.raises(TypeError):
        (scratch / 'float-mode').mkdir(mode=448.0)
    encoded = os.fsencode(scratch / 'bytes-directory')
    os.mkdir(encoded, 0o700)
    exercise(Path(os.fsdecode(encoded)))
    previous = Path.cwd()
    try:
        os.chdir(scratch)
        Path('relative-directory').mkdir(mode=0o700)
        exercise(Path('relative-directory'))
    finally:
        os.chdir(previous)
    info['private_directory'] = str(path)
    (scratch / 'temp-proof.json').write_text(json.dumps(info))

@pytest.mark.parametrize('isolated', [False, True])
def test_child_python_and_grandchild(isolated):
    child = r"""
import os, pathlib, subprocess, sys, tempfile
from _harness_appcontainer_temp import require
require(os.environ['TEMP'])
with tempfile.TemporaryDirectory() as name:
    p = pathlib.Path(name) / 'child.txt'
    p.write_text('child')
    assert p.read_text() == 'child'
    assert p.resolve(strict=True) == p.absolute()
code = 'import tempfile,pathlib; t=tempfile.TemporaryDirectory(); p=pathlib.Path(t.name)/"grandchild"; p.write_text("ok"); assert p.read_text()=="ok"; t.cleanup()'
result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', '-c', code], capture_output=True, text=True)
assert result.returncode == 0, result.stderr
"""
    args = [sys.executable, '-B', '-X', 'utf8', *(['-I'] if isolated else []), '-c', child]
    result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr

def test_protected_paths_and_forged_child_marker_stay_denied():
    scratch = Path(os.environ['TEMP'])
    protected = [Path.cwd(), Path(sys.prefix), scratch.parent, Path('protected.json')]
    for parent in protected[:-1]:
        with pytest.raises(PermissionError):
            (parent / 'forbidden-private-directory').mkdir(mode=0o700)
    with pytest.raises(PermissionError):
        protected[-1].write_text('changed')
    # The new WRITE_DAC grant belongs to scratch only. Attempts to remove a
    # protected copied source/runtime DACL must still be rejected by Windows.
    import ctypes
    from ctypes import wintypes
    change_acl = ctypes.WinDLL('advapi32', use_last_error=True).SetNamedSecurityInfoW
    change_acl.argtypes = [wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD,
                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    change_acl.restype = wintypes.DWORD
    for path in (Path.cwd() / 'protected.json',
                 Path(sys.prefix) / 'Lib/site-packages/_harness_appcontainer_temp.py'):
        assert change_acl(str(path), 1, 4, None, None, None, None) == 5
    child = 'import os,pathlib; pathlib.Path("forged-private-directory").mkdir(mode=0o700)'
    result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', '-c', child],
                            env=os.environ | {SCRATCH_ENV: str(Path.cwd())}, capture_output=True, text=True)
    assert result.returncode != 0 and 'PermissionError' in result.stderr
    assert not Path('forged-private-directory').exists()
    # A denied DOS volume lookup may be translated only inside scratch.
    with pytest.raises(PermissionError):
        scratch.parent.resolve(strict=True)

def test_audit_hook_can_veto_creation():
    path = Path(os.environ['TEMP']) / 'audit-veto'
    def veto(event, args):
        if event == 'os.mkdir' and str(args[0]) == str(path):
            raise PermissionError('audit veto')
    sys.addaudithook(veto)
    with pytest.raises(PermissionError, match='audit veto'):
        path.mkdir(mode=0o700)
    assert not path.exists()
'''


def _dacl(path):
    """Inspect the actual private directory ACL independently from the hook."""
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security.GetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD,
                                              ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                              ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    security.GetNamedSecurityInfoW.restype = wintypes.DWORD
    security.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [ctypes.c_void_p, wintypes.DWORD,
        wintypes.DWORD, ctypes.POINTER(wintypes.LPWSTR), ctypes.c_void_p]
    security.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = wintypes.BOOL
    kernel.LocalFree.argtypes, kernel.LocalFree.restype = [ctypes.c_void_p], ctypes.c_void_p
    descriptor, text = ctypes.c_void_p(), wintypes.LPWSTR()
    error = security.GetNamedSecurityInfoW(str(path), 1, 4, None, None, None, None, ctypes.byref(descriptor))
    if error:
        raise ctypes.WinError(error)
    try:
        if not security.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, 1, 4, ctypes.byref(text), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return text.value
    finally:
        if text:
            kernel.LocalFree(text)
        kernel.LocalFree(descriptor)


@pytest.mark.parametrize("private_parent", [False, True])
def test_actual_temporary_directories_children_and_private_acl(validation_environment, private_parent):
    root, validator = validation_environment
    if private_parent:
        root = root / ("private-" + uuid.uuid4().hex[:8])
        root.mkdir(mode=0o700)
        validator = IsolatedValidator(root / "validator")
        validator.verify()
    project = root / ("temp-" + uuid.uuid4().hex[:8])
    project.mkdir()
    (project / "test_temporary.py").write_text(TEMP_TESTS, encoding="utf-8")
    (project / "protected.json").write_text("original")
    before = tree_hash(project)
    result = validator.run(CHECK | {"timeout": 60}, project)
    assert result["outcome"] == "passed" and result["tests"] == 7, result
    assert tree_hash(project) == before
    proof = json.loads((Path(result["copied_project"]).parent / "tmp/temp-proof.json").read_text())
    sddl = _dacl(proof["private_directory"])
    assert sddl.startswith("D:P"), sddl
    assert set(re.findall(r"\(A;OICI;FA;;;([^;)]+)\)", sddl)) == {"SY", "BA", "OW", proof["appcontainer_sid"]}, sddl
    assert len(re.findall(r"\(", sddl)) == 4, sddl


def test_hook_is_inert_in_host_python_even_with_marker(validation_environment):
    _, validator = validation_environment
    code = "import os; from _harness_appcontainer_temp import _installation; assert _installation is None; print('host unchanged')"
    result = subprocess.run([str(validator.runtime / "python.exe"), "-I", "-B", "-c", code],
                            env=os.environ | {"DEVELOPMENT_HARNESS_TEST_SCRATCH": str(validator.directory)},
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0 and result.stdout.strip() == "host unchanged", result.stderr
