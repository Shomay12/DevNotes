import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_create_and_get_notebook():
    payload = {
        "title": "Test Algorithm Notebook",
        "description": "Testing algorithms and data structures",
        "tags": ["algorithms", "python"],
        "blocks": [
            {
                "id": "b-test-1",
                "type": "heading",
                "level": 1,
                "content": "Algorithm Analysis"
            },
            {
                "id": "b-test-2",
                "type": "paragraph",
                "content": "Here is an implementation of a binary search tree."
            }
        ]
    }
    create_res = client.post("/api/notebooks", json=payload)
    assert create_res.status_code == 201
    nb = create_res.json()
    assert nb["id"] is not None
    assert nb["title"] == "Test Algorithm Notebook"
    assert len(nb["blocks"]) == 2

    nb_id = nb["id"]

    # Get by ID
    get_res = client.get(f"/api/notebooks/{nb_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == nb_id

    # List notebooks
    list_res = client.get("/api/notebooks")
    assert list_res.status_code == 200
    ids = [item["id"] for item in list_res.json()]
    assert nb_id in ids

def test_autosave_content():
    # Create notebook first
    res = client.post("/api/notebooks", json={"title": "Autosave Notebook"})
    nb_id = res.json()["id"]

    # Autosave patch
    patch_payload = {
        "blocks": [
            {"id": "b-auto-1", "type": "paragraph", "content": "Updated content from autosave."},
            {"id": "b-auto-2", "type": "code", "language": "python", "code": "print('autosaved')"}
        ],
        "title": "Autosaved Notebook Title"
    }
    patch_res = client.patch(f"/api/notebooks/{nb_id}/content", json=patch_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["title"] == "Autosaved Notebook Title"
    assert len(updated["blocks"]) == 2
    assert updated["blocks"][1]["code"] == "print('autosaved')"

def test_update_notebook_metadata():
    res = client.post("/api/notebooks", json={"title": "Original Title"})
    nb_id = res.json()["id"]

    update_res = client.put(f"/api/notebooks/{nb_id}", json={
        "title": "New Title",
        "description": "Updated description",
        "is_pinned": True
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "New Title"
    assert data["is_pinned"] is True

def test_delete_notebook():
    res = client.post("/api/notebooks", json={"title": "To Delete"})
    nb_id = res.json()["id"]

    del_res = client.delete(f"/api/notebooks/{nb_id}")
    assert del_res.status_code == 200

    # Ensure not found
    get_res = client.get(f"/api/notebooks/{nb_id}")
    assert get_res.status_code == 404
