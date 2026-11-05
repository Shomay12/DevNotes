#!/usr/bin/env python3
"""Compatibility shim for backend.cli -> devnote.cli."""
from devnote.cli import main, CLI_VERSION

if __name__ == "__main__":
    main()
