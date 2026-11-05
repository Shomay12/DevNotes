"""
DevNote Cross-Platform Path & Storage Resolution.
Provides standard, reliable filesystem locations across macOS, Linux, and Windows.
Never assumes current terminal directory is the installation directory.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional


def get_user_data_dir() -> Path:
    """
    Returns platform-specific user application data directory.
    - macOS: ~/Library/Application Support/DevNote
    - Linux: ~/.local/share/devnote (or $XDG_DATA_HOME/devnote)
    - Windows: %LOCALAPPDATA%\\DevNote (or ~/AppData/Local/DevNote)
    Can be overridden via DEVNOTE_DATA_DIR environment variable.
    """
    custom = os.environ.get("DEVNOTE_DATA_DIR")
    if custom and custom.strip():
        return Path(custom.strip()).resolve()

    if sys.platform == "darwin":
        primary = Path.home() / "Library" / "Application Support" / "DevNote"
    elif sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA")
        base = Path(local_app) if local_app else Path.home() / "AppData" / "Local"
        primary = base / "DevNote"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
        primary = base / "devnote"

    return primary


def get_user_config_dir() -> Path:
    """
    Returns platform-specific user configuration directory.
    - macOS: ~/Library/Application Support/DevNote
    - Linux: ~/.config/devnote (or $XDG_CONFIG_HOME/devnote)
    - Windows: %LOCALAPPDATA%\\DevNote
    Can be overridden via DEVNOTE_CONFIG_DIR or DEVNOTE_DATA_DIR.
    """
    custom = os.environ.get("DEVNOTE_CONFIG_DIR")
    if custom and custom.strip():
        return Path(custom.strip()).resolve()

    # If custom data dir was specified, store config there unless DEVNOTE_CONFIG_DIR was set
    if os.environ.get("DEVNOTE_DATA_DIR"):
        return get_user_data_dir()

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "DevNote"
    elif sys.platform == "win32":
        return get_user_data_dir()
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg_config) if xdg_config else Path.home() / ".config"
        return base / "devnote"


def get_frontend_dir() -> Path:
    """
    Resolves the packaged frontend assets directory using importlib.resources.
    Falls back to development repository paths when running from source checkout.
    """
    # 1. Package resources resolution (standard for installed wheel / site-packages)
    try:
        if sys.version_info >= (3, 10):
            from importlib.resources import files
            pkg_traversable = files("devnote").joinpath("frontend")
            pkg_path = Path(str(pkg_traversable))
            if pkg_path.exists() and (pkg_path / "index.html").exists():
                return pkg_path
    except Exception:
        pass

    # 2. Package relative path
    pkg_relative = Path(__file__).resolve().parent / "frontend"
    if pkg_relative.exists() and (pkg_relative / "index.html").exists():
        return pkg_relative

    # 3. Development root relative path
    dev_relative = Path(__file__).resolve().parent.parent / "frontend"
    if dev_relative.exists() and (dev_relative / "index.html").exists():
        return dev_relative

    return pkg_relative


def ensure_storage_dirs(data_dir: Optional[Path] = None) -> dict[str, Path]:
    """
    Ensures data directory and all subdirectories exist.
    If permissions are restricted on the primary path, falls back gracefully.
    """
    if data_dir:
        base = data_dir
    else:
        # Check workspace storage first if running inside source tree
        dev_storage = Path(__file__).resolve().parent.parent / "storage"
        if dev_storage.exists():
            base = dev_storage
        else:
            base = get_user_data_dir()

    try:
        base.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fallback to local workspace storage or tmp
        dev_storage = Path(__file__).resolve().parent.parent / "storage"
        try:
            dev_storage.mkdir(parents=True, exist_ok=True)
            base = dev_storage
        except (PermissionError, OSError):
            base = Path(tempfile.gettempdir()) / "devnote_storage"
            base.mkdir(parents=True, exist_ok=True)

    dirs = {
        "storage": base,
        "notebooks": base / "notebooks",
        "exports": base / "exports",
        "uploads": base / "uploads",
    }
    for p in dirs.values():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            pass
    return dirs


def get_pid_file(data_dir: Optional[Path] = None) -> Path:
    """Returns PID file path."""
    base = data_dir or get_user_data_dir()
    return base / "devnote.pid"


def get_config_file(config_dir: Optional[Path] = None) -> Path:
    """Returns configuration file path."""
    base = config_dir or get_user_config_dir()
    return base / "config.json"


def get_log_file(data_dir: Optional[Path] = None) -> Path:
    """Returns log file path."""
    base = data_dir or get_user_data_dir()
    return base / "devnote.log"
