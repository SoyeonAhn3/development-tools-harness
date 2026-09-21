"""Starting CLI for the Phase 3 external workflow example."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description="Double an integer.")
    parser.add_argument("value", type=int)
    args = parser.parse_args(argv)
    print(args.value * 2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
