import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_search_concepts():
    res = client.get("/api/search/notebooks?q=decorator")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    titles = [item["title"] for item in data["results"]]
    assert any("Decorator" in t for t in titles)

def test_search_error_messages():
    res = client.get("/api/search/notebooks?q=TypeError")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    categories = [item["category"] for item in data["results"]]
    assert "error" in categories

def test_search_notebooks_content():
    # Create notebook with unique keyword
    client.post("/api/notebooks", json={
        "title": "Machine Learning Notebook",
        "description": "Gradient descent notes",
        "blocks": [
            {"id": "b-ml-1", "type": "paragraph", "content": "Backpropagation computes the gradient of loss."}
        ]
    })

    res = client.get("/api/search/notebooks?q=Backpropagation")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    assert any("Backpropagation" in item["snippet"] for item in data["results"])

def test_web_search_endpoint():
    res = client.post("/api/search/web", json={"query": "python async"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) >= 1
