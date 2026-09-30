"""Build a fresh fixed runner A from this checkout using installed pinned dependencies."""

import argparse
import json
from pathlib import Path
import sys

from development_harness.fixed_runner import build_runner
from development_harness.model import HarnessError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="New directory outside the repository and OneDrive")
    parser.add_argument("--codex-path", help="Reviewed Codex .exe to copy; no authentication files are copied")
    args = parser.parse_args()
    try:
        print(json.dumps(build_runner(Path(__file__).resolve().parents[1], args.destination,
                                      codex_path=args.codex_path), ensure_ascii=True, indent=2))
        return 0
    except (HarnessError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
