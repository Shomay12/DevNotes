#!/usr/bin/env python3
"""Compatibility shim for backend.cli -> devnote.cli."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from devnote.cli import main, CLI_VERSION

if __name__ == "__main__":
    main()
