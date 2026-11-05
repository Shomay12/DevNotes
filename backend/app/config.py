import os
import sys
from pathlib import Path

# Version & Edition info
DEVNOTE_VERSION = "1.1.0"
DEVNOTE_EDITION = os.environ.get("DEVNOTE_EDITION", "local").lower()  # "local" or "hosted"

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Custom data directory support (e.g. ~/.devnote or custom path via DEVNOTE_DATA_DIR)
custom_data_dir = os.environ.get("DEVNOTE_DATA_DIR")
if custom_data_dir:
    STORAGE_DIR = Path(custom_data_dir).resolve()
else:
    STORAGE_DIR = BASE_DIR / "storage"

# Storage subdirectories
NOTEBOOKS_DIR = STORAGE_DIR / "notebooks"
EXPORTS_DIR = STORAGE_DIR / "exports"
UPLOADS_DIR = STORAGE_DIR / "uploads"
DATABASE_PATH = STORAGE_DIR / "devnote.db"

# Ensure storage directories exist
for directory in [STORAGE_DIR, NOTEBOOKS_DIR, EXPORTS_DIR, UPLOADS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Frontend directories
FRONTEND_DIR = BASE_DIR / "frontend"

# Database Configuration (supports custom DATABASE_URL or SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Network & Security Configuration
# When bound beyond localhost (0.0.0.0 or LAN IP), an access token is enforced
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
