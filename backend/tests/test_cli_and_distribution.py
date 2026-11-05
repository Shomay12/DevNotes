import os
import json
import subprocess
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.storage_provider import get_storage_provider, LocalStorageProvider
from backend.app.services.execution_provider import get_execution_provider, LocalSubprocessExecutionProvider

client = TestClient(app)

def test_api_config_endpoint():
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "edition" in data
    assert "auth_required" in data

def test_json_export_and_import_endpoints():
    # 1. Create a notebook
    create_res = client.post("/api/notebooks", json={
        "title": "Cross-Platform Export Test",
        "description": "Testing JSON export & import round-trip",
        "tags": ["cross-platform", "cli"],
        "blocks": [
            {
                "id": "block-json-1",
                "type": "heading",
                "level": 1,
                "content": "Distributed Notebook"
            },
            {
                "id": "block-json-2",
                "type": "code",
                "language": "python",
                "code": "print('Shared JSON format across macOS, Linux, Windows, and iPad')",
                "output": "Shared JSON format across macOS, Linux, Windows, and iPad\n",
                "status": "success"
            },
            {
                "id": "block-json-3",
                "type": "drawing",
                "caption": "Pencil Annotation",
                "strokes": [{"tool": "pen", "color": "#2563eb", "width": 2.5, "points": [{"x": 1, "y": 1, "pressure": 0.5}]}]
            }
        ]
    })
    assert create_res.status_code == 201
    nb = create_res.json()
    nb_id = nb["id"]

    # 2. Export via JSON endpoint
    export_res = client.get(f"/api/notebooks/{nb_id}/export-json")
    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("application/json")
    json_bytes = export_res.content

    data = json.loads(json_bytes.decode("utf-8"))
    assert data["notebook_id"] == nb_id
    assert data["title"] == "Cross-Platform Export Test"
    assert len(data["blocks"]) == 3
    assert data["blocks"][2]["type"] == "drawing"

    # 3. Import JSON payload back
    import_res = client.post("/api/notebooks/import-json", data={"raw_json": json_bytes.decode("utf-8")})
    assert import_res.status_code == 200
    imported_nb = import_res.json()
    # Canonical guarantee: Stable ID preserved, no duplicate notebook created!
    assert imported_nb["id"] == nb_id
    assert imported_nb["title"] == "Cross-Platform Export Test"
    assert len(imported_nb["blocks"]) == 3

def test_storage_provider_abstraction():
    storage = get_storage_provider()
    assert isinstance(storage, LocalStorageProvider)

    test_data = {
        "id": "test-uuid-12345",
        "title": "Storage Abstraction Test",
        "tags": ["test"],
        "blocks": [{"id": "b1", "type": "paragraph", "content": "Storage decoupled"}]
    }

    serialized = storage.export_notebook_json(test_data)
    parsed = storage.parse_notebook_json(serialized)
    assert parsed["notebook_id"] == "test-uuid-12345"
    assert parsed["title"] == "Storage Abstraction Test"
    assert len(parsed["blocks"]) == 1

def test_execution_provider_abstraction():
    provider = get_execution_provider()
    assert isinstance(provider, LocalSubprocessExecutionProvider)

    res = provider.execute("a = 15; b = 25; print(a * b)", "python")
    assert res.status == "success"
    assert "375" in res.output.strip()

def test_network_security_middleware():
    from backend.app import main as app_module
    original_token = app_module.DEVNOTE_AUTH_TOKEN

    try:
        # Simulate active security token
        app_module.DEVNOTE_AUTH_TOKEN = "supersecret_lan_token"

        # 1. Public endpoints should still be accessible
        res_health = client.get("/api/health")
        assert res_health.status_code == 200
        res_config = client.get("/api/config")
        assert res_config.status_code == 200
        assert res_config.json()["auth_required"] is True

        # 2. Protected API without token should be 401
        res_unauth = client.get("/api/notebooks")
        assert res_unauth.status_code == 401
        assert "Unauthorized" in res_unauth.json()["detail"]

        # 3. Protected API with Authorization header should succeed
        res_auth_header = client.get("/api/notebooks", headers={"Authorization": "Bearer supersecret_lan_token"})
        assert res_auth_header.status_code == 200

        # 4. Protected API with query token param should succeed (convenient for iPad Safari bookmarks/links)
        res_auth_query = client.get("/api/notebooks?token=supersecret_lan_token")
        assert res_auth_query.status_code == 200

    finally:
        app_module.DEVNOTE_AUTH_TOKEN = original_token

def test_cli_execution_commands():
    cli_path = Path(__file__).resolve().parent.parent / "cli.py"

    # Test version
    ver_proc = subprocess.run([sys.executable, str(cli_path), "version"], capture_output=True, text=True)
    assert ver_proc.returncode == 0
    assert "DevNote version" in ver_proc.stdout

    # Test doctor
    doc_proc = subprocess.run([sys.executable, str(cli_path), "doctor"], capture_output=True, text=True)
    assert doc_proc.returncode == 0
    assert "Doctor" in doc_proc.stdout

    # Test list
    list_proc = subprocess.run([sys.executable, str(cli_path), "list"], capture_output=True, text=True)
    assert list_proc.returncode == 0
    assert "TITLE" in list_proc.stdout
