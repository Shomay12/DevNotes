import pytest
from fastapi.testclient import TestClient
from devnote.app.main import app

client = TestClient(app)


def test_hackernews_feed_endpoint():
    res = client.get("/api/news/hackernews", params={"feed": "top", "limit": 5})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    story = data[0]
    assert "title" in story
    assert "url" in story
    assert "points" in story
    assert "hn_url" in story


def test_hackernews_filter_query():
    res = client.get("/api/news/hackernews", params={"query": "numpy", "limit": 5})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any("numpy" in s["title"].lower() for s in data)


def test_general_search_returns_raw_text_not_dummy_url():
    # Verify searching raw text returns substantive content, not just a dummy google link
    payload = {
        "query": "numpy array",
        "category": "general",
        "limit": 5
    }
    res = client.post("/api/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    first = data["results"][0]
    assert "numpy" in first["title"].lower()
    assert len(first["snippet"]) > 20
    # Must NOT be a dummy Google search link
    assert "google.com/search?q=" not in first["url"]


def test_wikipedia_search_provider():
    payload = {
        "query": "Fast Fourier Transform",
        "category": "wikipedia",
        "limit": 3
    }
    res = client.post("/api/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    item = data["results"][0]
    assert "fourier" in item["title"].lower() or "fft" in item["title"].lower()
    assert item["source"] == "Wikipedia"


def test_llm_config_endpoint():
    res = client.get("/api/llm/config")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    provider_ids = [p["id"] for p in data["providers"]]
    assert "ollama" in provider_ids
    assert "openai" in provider_ids
    assert "gemini" in provider_ids


def test_llm_chat_heuristic_fallback():
    # Test chat with default built-in assistant
    req = {
        "prompt": "How do I print a NumPy array without truncation?",
        "provider": "ollama"
    }
    res = client.post("/api/llm/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert "threshold" in data["text"].lower() or "set_printoptions" in data["text"].lower()


def test_llm_test_connection_endpoint():
    res = client.post("/api/llm/test", json={"provider": "ollama", "endpoint": "http://localhost:11434"})
    assert res.status_code == 200
    data = res.json()
    assert "ok" in data
    assert "message" in data
