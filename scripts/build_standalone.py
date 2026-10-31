"""Compatibility entry point for the canonical, AST-checked build generator.

Both documented generator paths must produce byte-identical standalone releases.
Do not independently implement a second assembly algorithm here.
"""
from __future__ import annotations
from pathlib import Path
import runpy

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'build_standalone.py'


def main() -> int:
    return runpy.run_path(str(TOOL), run_name='standalone_generator')['main']()


if __name__ == '__main__':
    raise SystemExit(main())
