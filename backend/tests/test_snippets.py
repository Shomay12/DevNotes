import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_snippet_crud():
    # 1. Create Snippet
    create_res = client.post("/api/snippets", json={
        "title": "Memoization Decorator",
        "language": "python",
        "code": "from functools import lru_cache\n@lru_cache(maxsize=None)\ndef fib(n):\n    return n if n < 2 else fib(n-1) + fib(n-2)",
        "description": "Fast fibonacci using LRU Cache",
        "tags": ["cache", "decorator"]
    })
    assert create_res.status_code == 201
    snip = create_res.json()
    snip_id = snip["id"]
    assert snip["title"] == "Memoization Decorator"

    # 2. List Snippets
    list_res = client.get("/api/snippets?language=python")
    assert list_res.status_code == 200
    ids = [s["id"] for s in list_res.json()]
    assert snip_id in ids

    # 3. Get Snippet
    get_res = client.get(f"/api/snippets/{snip_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Memoization Decorator"

    # 4. Update Snippet
    update_res = client.put(f"/api/snippets/{snip_id}", json={
        "title": "Updated Memoization Decorator"
    })
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Memoization Decorator"

    # 5. Delete Snippet
    del_res = client.delete(f"/api/snippets/{snip_id}")
    assert del_res.status_code == 200

    # Ensure deleted
    get_after = client.get(f"/api/snippets/{snip_id}")
    assert get_after.status_code == 404
