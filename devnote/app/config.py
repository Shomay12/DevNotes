import os
import sys
from pathlib import Path
from devnote.paths import get_user_data_dir, get_frontend_dir, ensure_storage_dirs

# Version & Edition info
DEVNOTE_VERSION = "0.1.0"
DEVNOTE_EDITION = os.environ.get("DEVNOTE_EDITION", "local").lower()  # "local" or "hosted"

# Base package directory
PACKAGE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PACKAGE_DIR

# Storage directories (platform-specific user data directory with graceful fallback)
_storage_dirs = ensure_storage_dirs(get_user_data_dir())
STORAGE_DIR = _storage_dirs["storage"]
NOTEBOOKS_DIR = _storage_dirs["notebooks"]
EXPORTS_DIR = _storage_dirs["exports"]
UPLOADS_DIR = _storage_dirs["uploads"]
DATABASE_PATH = STORAGE_DIR / "devnote.db"

# Packaged frontend assets directory
FRONTEND_DIR = get_frontend_dir()

# Database Configuration (supports custom DATABASE_URL or SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Network & Security Configuration
DEVNOTE_HOST = os.environ.get("DEVNOTE_HOST", "127.0.0.1")
DEVNOTE_PORT = int(os.environ.get("DEVNOTE_PORT", "8000"))
DEVNOTE_AUTH_TOKEN = os.environ.get("DEVNOTE_AUTH_TOKEN", "").strip()

# Sandbox Configuration
DEFAULT_EXECUTION_TIMEOUT = 10.0  # seconds
MAX_EXECUTION_TIMEOUT = 30.0
DEFAULT_MEMORY_LIMIT_MB = 256
MAX_OUTPUT_LENGTH = 100_000  # max characters to prevent crashing on infinite print

PYTHON_BIN = sys.executable
NODE_BIN = os.environ.get("NODE_BIN", "node")

# Supported execution languages
SUPPORTED_LANGUAGES = ["python", "javascript"]

# Cloud/Hosted Execution Worker URL (optional, for hosted edition)
DEVNOTE_CLOUD_EXECUTION_URL = os.environ.get("DEVNOTE_CLOUD_EXECUTION_URL", "")
