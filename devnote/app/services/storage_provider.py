import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from devnote.app.config import (
    DEVNOTE_EDITION,
    STORAGE_DIR,
    EXPORTS_DIR,
    UPLOADS_DIR,
    NOTEBOOKS_DIR
)

class BaseStorageProvider(ABC):
    """Abstract storage provider interface decoupling storage from execution/routers."""

    @abstractmethod
    def save_export_file(self, filename: str, content: bytes) -> str:
        """Save an exported file (e.g. PDF or JSON) and return its storage path/URI."""
        pass

    @abstractmethod
    def get_export_file(self, filename: str) -> Optional[bytes]:
        """Retrieve the bytes of an exported file."""
        pass

    @abstractmethod
    def save_upload_file(self, filename: str, content: bytes) -> str:
        """Save an uploaded file and return its storage path/URI."""
        pass

    @abstractmethod
    def export_notebook_json(self, notebook_data: Dict[str, Any]) -> bytes:
        """Serializes a notebook into canonical DevNote JSON format."""
        pass

    @abstractmethod
    def parse_notebook_json(self, json_bytes: bytes) -> Dict[str, Any]:
        """Parses and validates a canonical DevNote JSON payload."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider for Local Developer Edition."""

    def __init__(self, exports_dir: Path = EXPORTS_DIR, uploads_dir: Path = UPLOADS_DIR):
        self.exports_dir = exports_dir
        self.uploads_dir = uploads_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def save_export_file(self, filename: str, content: bytes) -> str:
        target_path = self.exports_dir / filename
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def get_export_file(self, filename: str) -> Optional[bytes]:
        target_path = self.exports_dir / filename
        if target_path.exists():
            with open(target_path, "rb") as f:
                return f.read()
        return None

    def save_upload_file(self, filename: str, content: bytes) -> str:
        target_path = self.uploads_dir / filename
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def export_notebook_json(self, notebook_data: Dict[str, Any]) -> bytes:
        # Standard canonical DevNote schema
        canonical = {
            "devnote_version": "1.0",
            "notebook_id": notebook_data.get("id"),
            "title": notebook_data.get("title", "Untitled Notebook"),
            "description": notebook_data.get("description", ""),
            "tags": notebook_data.get("tags", []),
            "blocks": notebook_data.get("blocks", []),
            "version": notebook_data.get("version", 1),
            "created_at": notebook_data.get("created_at"),
            "updated_at": notebook_data.get("updated_at"),
            "last_edited_at": notebook_data.get("last_edited_at"),
        }
        return json.dumps(canonical, indent=2, ensure_ascii=False).encode("utf-8")

    def parse_notebook_json(self, json_bytes: bytes) -> Dict[str, Any]:
        data = json.loads(json_bytes.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid notebook JSON: root must be an object.")
        if "blocks" not in data:
            raise ValueError("Invalid notebook JSON: missing 'blocks' array.")
        return data


class HostedStorageProvider(LocalStorageProvider):
    """
    Hosted cloud storage provider for Hosted Edition.
    Extends local storage with optional cloud object storage routing,
    falling back to robust local persistent volumes if object storage credentials are not provided.
    """
    def __init__(self):
        super().__init__()
        self.s3_bucket = os.environ.get("DEVNOTE_S3_BUCKET", "")
        # Can connect to boto3 / cloud bucket when credentials exist


def get_storage_provider() -> BaseStorageProvider:
    """Factory returning the appropriate storage provider according to edition."""
    if DEVNOTE_EDITION == "hosted":
        return HostedStorageProvider()
    return LocalStorageProvider()
