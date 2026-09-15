"""Internal validation worker: do nothing until containment and journaling finish."""

import json
from pathlib import Path
import subprocess
import sys


def main():
    line = sys.stdin.buffer.readline()
    if not line:  # Parent died before authorizing launch.
        return 125
    request = json.loads(line)
    try:
        completed = subprocess.run(request["argv"], stdin=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        result = {"exit_code": completed.returncode}
    except OSError as exc:
        result = {"exit_code": None, "error": str(exc)}
    Path(sys.argv[1]).write_text(json.dumps(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
