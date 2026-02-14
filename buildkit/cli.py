import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .template import TEMPLATE_FILENAME, write_template


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m buildkit")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="create buildkit-setup.py template")
    subparsers.add_parser("setup", help="create buildkit-setup.py template")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command not in {"init", "setup"}:
        parser.print_help()
        return 1

    target_dir = Path.cwd()
    target_path = target_dir / TEMPLATE_FILENAME
    if target_path.exists():
        print(f"[WARN] {TEMPLATE_FILENAME} already exists: {target_path}")
        return 1

    write_template(target_dir)
    print(f"[OK] Created {target_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
