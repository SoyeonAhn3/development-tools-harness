"""Read-only bootstrap invoked by the controller inside AppContainer only."""

import json
import os
from pathlib import Path
import sys


def main():
    configuration = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    # Import the pinned pytest installation before adding project imports.
    import pytest
    project = Path(configuration["project"])
    os.chdir(project)
    sys.dont_write_bytecode = True
    # Windows rewrites TEMP/TMP when creating an AppContainer; choose the
    # controller's explicitly granted scratch directory after process startup.
    os.environ.update(TEMP=configuration["scratch"], TMP=configuration["scratch"], PYTHONUTF8="1",
                      PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="", PYTHONDONTWRITEBYTECODE="1")
    os.environ.pop("PYTEST_PLUGINS", None)
    sys.path.insert(0, str(project))
    if (project / "src").is_dir():
        sys.path.insert(0, str(project / "src"))
    return pytest.main(configuration["args"])


if __name__ == "__main__":
    raise SystemExit(main())
