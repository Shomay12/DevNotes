import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.search.query_classifier import QueryClassifier
from backend.app.search.ranking_engine import RankingEngine
from backend.app.search.deduplication import ResultDeduplicator
from backend.app.search.cache import SearchCache
from backend.app.schemas.search import SearchResultItem

client = TestClient(app)

# ==========================================
# 1. Query Classifier & Intelligence Tests
# ==========================================

def test_query_classifier_concept():
    res = QueryClassifier.classify("Python decorators")
    assert res.intent in ("concept", "api")
    assert res.language == "python"
    assert "devdocs" in res.recommended_providers

def test_query_classifier_error():
    res = QueryClassifier.classify("ModuleNotFoundError: No module named torch")
    assert res.intent == "error"
    assert "stackoverflow" in res.recommended_providers
    assert res.framework == "pytorch" or res.language == "python"

def test_query_classifier_code_implementation():
    res = QueryClassifier.classify("FastAPI authentication example")
    assert res.intent in ("code", "api")
    assert res.framework == "fastapi"
    assert res.language == "python"
    assert "github" in res.recommended_providers or "devdocs" in res.recommended_providers

def test_query_classifier_javascript():
    res = QueryClassifier.classify("TypeError: Cannot read properties of undefined in React")
    assert res.intent == "error"
    assert res.framework == "react"
    assert res.language == "javascript"

# ==========================================
# 2. Ranking & Deduplication Tests
# ==========================================

def test_result_deduplicator():
    items = [
        SearchResultItem(
            id="1",
            title="FastAPI Routing Guide",
            category="doc",
            snippet="Routing guide",
            url="https://fastapi.tiangolo.com/tutorial/routing/?utm_source=devnote"
        ),
        SearchResultItem(
            id="2",
            title="FastAPI Routing Guide",
            category="doc",
            snippet="Routing guide duplicate",
            url="https://fastapi.tiangolo.com/tutorial/routing/"
        ),
        SearchResultItem(
            id="3",
            title="Different Title",
            category="doc",
            snippet="Different",
            url="https://fastapi.tiangolo.com/tutorial/different/"
        )
    ]
    deduped = ResultDeduplicator.deduplicate(items)
    assert len(deduped) == 2
    assert deduped[0].id == "1"
    assert deduped[1].id == "3"

def test_ranking_engine_error_boost():
    classification = QueryClassifier.classify("TypeError: NoneType")
    items = [
        SearchResultItem(
            id="1",
            title="Python Functions Overview",
            category="doc",
            snippet="Functions in python",
            url="https://docs.python.org"
        ),
        SearchResultItem(
            id="2",
            title="TypeError: 'NoneType' object is not subscriptable",
            category="stackoverflow",
            snippet="How to fix NoneType subscriptable error",
            url="https://stackoverflow.com/questions/123"
        )
    ]
    ranked = RankingEngine.rank(items, classification)
    assert ranked[0].id == "2"  # Error intent boosts StackOverflow and exact error title match

# ==========================================
# 3. Search Cache Tests
# ==========================================

def test_search_cache():
    cache = SearchCache(default_ttl_seconds=10, max_entries=5)
    key = SearchCache.make_key("test query", "all", "python")
    cache.set(key, [{"title": "Cached Result"}])
    cached = cache.get(key)
    assert cached is not None
    assert cached[0]["title"] == "Cached Result"

    # Test cache key variation
    other_key = SearchCache.make_key("other query", "all", "python")
    assert cache.get(other_key) is None

# ==========================================
# 4. Unified Search API Endpoints Tests
# ==========================================

def test_api_unified_search_post():
    res = client.post("/api/search", json={
        "query": "Python decorators",
        "category": "all"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    assert any("decorator" in item["title"].lower() or "decorator" in item["snippet"].lower() for item in data["results"])

def test_api_search_providers_list():
    res = client.get("/api/search/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 5
    provider_ids = [p["id"] for p in providers]
    assert "devdocs" in provider_ids
    assert "stackoverflow" in provider_ids
    assert "github" in provider_ids
    assert "local_docs" in provider_ids

def test_api_search_history_lifecycle():
    # Execute a search to populate history
    client.post("/api/search", json={"query": "asyncio event loop", "category": "all"})

    res = client.get("/api/search/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 1
    recent_entry = history[0]
    assert "asyncio" in recent_entry["query"]

    # Delete specific entry
    del_res = client.delete(f"/api/search/history/{recent_entry['id']}")
    assert del_res.status_code == 204

    # Clear all history
    clear_res = client.delete("/api/search/history")
    assert clear_res.status_code == 204

    # Verify empty
    res_after = client.get("/api/search/history")
    assert len(res_after.json()) == 0

# ==========================================
# 5. Offline Documentation (FTS5) Tests
# ==========================================

def test_api_offline_docs_search():
    res = client.get("/api/search/docs?q=decorator")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    assert any("decorator" in item["title"].lower() for item in data["results"])

def test_api_doc_indexes_management():
    # List indexes
    res = client.get("/api/search/docs/indexes")
    assert res.status_code == 200
    indexes = res.json()
    assert len(indexes) >= 3
    idx_ids = [idx["id"] for idx in indexes]
    assert "python-core" in idx_ids

    # Download / re-index pack
    dl_res = client.post("/api/search/docs/download", json={"index_id": "fastapi-docs"})
    assert dl_res.status_code == 200
    dl_data = dl_res.json()
    assert dl_data["status"] == "downloaded"
    assert dl_data["entry_count"] >= 1

# ==========================================
# 6. Saved Resources (Bookmarks) Tests
# ==========================================

def test_api_saved_resources_crud():
    # Create bookmark
    create_res = client.post("/api/search/saved", json={
        "title": "FastAPI Dependency Injection",
        "snippet": "Use Depends() to inject database and authentication",
        "code": "def get_db(): yield session",
        "language": "python",
        "source": "DevDocs",
        "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
        "folder": "FastAPI Architecture",
        "tags": ["fastapi", "di"]
    })
    assert create_res.status_code == 201
    saved = create_res.json()
    saved_id = saved["id"]
    assert saved["title"] == "FastAPI Dependency Injection"
    assert saved["folder"] == "FastAPI Architecture"

    # List bookmarks
    list_res = client.get("/api/search/saved")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(i["id"] == saved_id for i in items)

    # Filter by folder
    folder_res = client.get("/api/search/saved?folder=FastAPI Architecture")
    assert folder_res.status_code == 200
    folder_items = folder_res.json()
    assert len(folder_items) >= 1

    # Delete bookmark
    del_res = client.delete(f"/api/search/saved/{saved_id}")
    assert del_res.status_code == 204

# ==========================================
# 7. Search Settings Tests
# ==========================================

def test_api_search_settings():
    get_res = client.get("/api/search/settings")
    assert get_res.status_code == 200
    settings = get_res.json()
    assert "default_provider" in settings
    assert "has_google_key" in settings

    put_res = client.put("/api/search/settings", json={
        "default_provider": "devdocs",
        "enable_cache": True
    })
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["default_provider"] == "devdocs"
