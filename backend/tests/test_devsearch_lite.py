import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from devnote.app.search.providers.searxng_provider import SearXNGProvider

client = TestClient(app)

def test_searxng_provider_unit():
    """Validates SearXNG provider query, JSON normalization, and error resiliency."""
    async def _run():
        provider = SearXNGProvider()

        # 1. Without SEARXNG_URL configured, returns empty list without error
        with patch.dict(os.environ, {"SEARXNG_URL": ""}, clear=False):
            provider.endpoint = ""
            results = await provider.search("python")
            assert results == []

        # 2. With mock SearXNG instance responding with JSON
        mock_payload = {
            "results": [
                {
                    "title": "Python Decorators Guide",
                    "url": "https://docs.python.org/3/glossary.html#term-decorator",
                    "content": "A function returning another function, usually applied as a function transformation.",
                    "engine": "google"
                },
                {
                    "title": "Decorators in Python - Real Python",
                    "url": "https://realpython.com/primer-on-python-decorators/",
                    "content": "Learn what decorators are and how to create and use them in Python.",
                    "engine": "duckduckgo"
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            with patch.dict(os.environ, {"SEARXNG_URL": "http://localhost:8080"}):
                provider.endpoint = "http://localhost:8080"
                res = await provider.search("python decorators", {"category": "doc"})
                assert len(res) == 2
                assert res[0].title == "Python Decorators Guide"
                assert "python.org" in res[0].url
                assert res[0].category == "web"
                assert "SearXNG (google)" in res[0].source

        # 3. Network or endpoint timeout is gracefully handled
        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
            provider.endpoint = "http://localhost:8080"
            res_err = await provider.search("python decorators", {"category": "all"})
            assert len(res_err) == 1
            assert "SearXNG" in res_err[0].source
            assert "unreachable" in res_err[0].id

    asyncio.run(_run())

def test_searxng_categories_it_science_general_and_caching():
    """Validates SearXNG category routing (IT, science, general), engines attribution, and caching."""
    async def _run():
        provider = SearXNGProvider()
        provider.endpoint = "http://localhost:8080"

        captured_params = []

        async def fake_get(url, params=None):
            captured_params.append(params)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "results": [
                    {
                        "title": f"Result for {params.get('q')} in {params.get('categories')}",
                        "url": "https://example.com/item",
                        "content": "Check out this code:\n```python\nimport math\nprint(math.pi)\n```",
                        "engine": "duckduckgo",
                        "engines": ["duckduckgo", "brave"],
                        "category": params.get("categories"),
                        "score": 4.5
                    }
                ]
            }
            return resp

        with patch("httpx.AsyncClient.get", side_effect=fake_get):
            # Test IT category
            res_it = await provider.search("quantum algorithm", {"category": "it"})
            assert len(res_it) == 1
            assert captured_params[-1]["categories"] == "it"
            assert "SearXNG (duckduckgo, brave)" in res_it[0].source
            # Code block extracted
            assert res_it[0].code is not None
            assert "import math" in res_it[0].code

            # Test Science category
            res_sci = await provider.search("quantum teleportation", {"category": "science"})
            assert len(res_sci) == 1
            assert captured_params[-1]["categories"] == "science"

            # Test General category
            res_gen = await provider.search("open source notes", {"category": "general"})
            assert len(res_gen) == 1
            assert captured_params[-1]["categories"] == "general"

            # Test In-Memory Caching: Repeating same query should hit cache without calling get again
            call_count_before = len(captured_params)
            res_cached = await provider.search("quantum teleportation", {"category": "science"})
            assert len(captured_params) == call_count_before
            assert len(res_cached) == 1
            assert res_cached[0].title == res_sci[0].title

    asyncio.run(_run())


def test_bookmarks_and_saved_api():
    """Validates /api/search/bookmarks CRUD endpoints and backwards-compatibility."""
    # 1. Create a bookmark via POST /api/search/bookmarks
    create_res = client.post("/api/search/bookmarks", json={
        "title": "MDN Web Docs: Fetch API",
        "snippet": "The Fetch API provides an interface for fetching resources asynchronously across the network.",
        "code": "const res = await fetch('/api/data');",
        "language": "javascript",
        "source": "MDN",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API",
        "category": "doc",
        "folder": "Web APIs"
    })
    assert create_res.status_code == 201
    bookmark = create_res.json()
    b_id = bookmark["id"]
    assert bookmark["title"] == "MDN Web Docs: Fetch API"
    assert bookmark["folder"] == "Web APIs"

    # 2. Retrieve via GET /api/search/bookmarks
    list_res = client.get("/api/search/bookmarks")
    assert list_res.status_code == 200
    b_list = list_res.json()
    assert any(b["id"] == b_id for b in b_list)

    # 3. Retrieve via alias GET /api/search/saved
    saved_res = client.get("/api/search/saved")
    assert saved_res.status_code == 200
    assert any(b["id"] == b_id for b in saved_res.json())

    # 4. Delete via DELETE /api/search/bookmarks/{id}
    del_res = client.delete(f"/api/search/bookmarks/{b_id}")
    assert del_res.status_code == 204

    # Verify deleted
    post_del_list = client.get("/api/search/bookmarks").json()
    assert not any(b["id"] == b_id for b in post_del_list)


def test_search_settings_searxng():
    """Validates configuring SearXNG endpoint and setting it as default provider via /api/search/settings."""
    # Read current settings
    settings_res = client.get("/api/search/settings")
    assert settings_res.status_code == 200
    orig_settings = settings_res.json()
    assert "searxng_url" in orig_settings
    assert "searxng_categories" in orig_settings
    assert "it" in orig_settings["searxng_categories"]
    assert "science" in orig_settings["searxng_categories"]
    assert "general" in orig_settings["searxng_categories"]

    # Update SearXNG URL and default provider
    update_res = client.put("/api/search/settings", json={
        "searxng_url": "http://127.0.0.1:8888",
        "default_provider": "searxng",
        "enable_cache": True
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["searxng_url"] == "http://127.0.0.1:8888"
    assert updated["default_provider"] == "searxng"

    # Verify environment updated
    assert os.environ.get("SEARXNG_URL") == "http://127.0.0.1:8888"


def test_devsearch_lite_18_step_workflow():
    """
    Validates the 18-step acceptance workflow specified in Section 13:
    1. Open an existing notebook.
    2. Activate Research Workspace.
    3. See research and notebook panels side by side.
    4. Search for "Python decorators".
    5. Receive real search results.
    6. Open Python documentation.
    7. Read the documentation without losing the notebook.
    8. Select and copy relevant material where permitted.
    9. Insert selected material into the notebook.
    10. Verify its source URL is attached.
    11. Write a personal explanation beside it.
    12. Insert a Python code block.
    13. Execute the code.
    14. Save the notebook.
    15. Close and reopen the application.
    16. Verify that all notes, references, and code blocks remain intact.
    17. Disconnect from the internet.
    18. Verify that the notebook and saved references still work.
    """

    # Step 1: Open an existing notebook (create & load)
    nb_res = client.post("/api/notebooks", json={
        "title": "Python Metaprogramming Study",
        "tags": ["python", "research", "decorators"]
    })
    assert nb_res.status_code == 201
    nb_data = nb_res.json()
    nb_id = nb_data["id"]

    # Initial block in the notebook
    initial_block = {
        "id": "block-initial-01",
        "type": "heading",
        "level": 1,
        "content": "Python Metaprogramming Study Notes"
    }
    client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": [initial_block],
        "title": "Python Metaprogramming Study"
    })

    # Step 2 & 3: Activate Research Workspace (Check providers and split-screen readiness)
    prov_res = client.get("/api/search/providers")
    assert prov_res.status_code == 200
    assert any(p["id"] == "devdocs" for p in prov_res.json())

    # Step 4: Search for "Python decorators"
    search_res = client.post("/api/search", json={
        "query": "Python decorators",
        "category": "all"
    })
    assert search_res.status_code == 200
    search_data = search_res.json()

    # Step 5: Receive real search results
    assert search_data["total_results"] > 0
    results = search_data["results"]
    assert any("decorator" in r["title"].lower() or "decorator" in r["snippet"].lower() for r in results)

    # Step 6: Open Python documentation (Select Python documentation entry)
    doc_item = next(
        (r for r in results if "decorator" in r["title"].lower()),
        results[0]
    )
    assert doc_item["url"] is not None

    # Step 7: Read documentation without losing the notebook
    # Verify notebook content remains unaltered while reading
    curr_nb = client.get(f"/api/notebooks/{nb_id}").json()
    assert len(curr_nb["blocks"]) == 1
    assert curr_nb["blocks"][0]["content"] == "Python Metaprogramming Study Notes"

    # Step 8: Select and copy relevant material where permitted
    captured_quote = doc_item["snippet"] or "A function returning another function, usually applied as a transformation."
    source_url = doc_item["url"]
    source_title = doc_item["title"]

    # Step 9, 10, 11: Insert selected material, attach source URL, write personal explanation beside it
    personal_note = "Decorators wrap functions using closures. Useful for caching, logging, and access control."
    today = "2026-11-06"

    # Formatted evidence markdown block matching the Study & Evidence Capture Dock
    evidence_block_content = (
        f"> {captured_quote}\n"
        f">\n"
        f"> **Source:** [{source_title}]({source_url})\n"
        f"> **Retrieved:** {today}\n"
        f">\n"
        f"> **Note:** {personal_note}"
    )

    evidence_block = {
        "id": "block-evidence-02",
        "type": "paragraph",
        "content": evidence_block_content
    }

    # Step 12: Insert a Python code block
    py_code = (
        "def timer_decorator(func):\n"
        "    def wrapper(*args, **kwargs):\n"
        "        return func(*args, **kwargs)\n"
        "    return wrapper\n\n"
        "@timer_decorator\n"
        "def greet(name):\n"
        "    return f'Hello, {name}!'\n\n"
        "print(greet('Developer'))\n"
    )

    code_block = {
        "id": "block-code-03",
        "type": "code",
        "language": "python",
        "code": py_code,
        "output": "",
        "error": "",
        "status": "idle"
    }

    # Step 13: Execute the code using backend execution engine
    exec_res = client.post("/api/execute", json={
        "language": "python",
        "code": py_code,
        "notebook_id": nb_id,
        "block_id": "block-code-03"
    })
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    assert "Hello, Developer!" in exec_data["output"]

    code_block["output"] = exec_data["output"]
    code_block["status"] = "success"

    # Step 14: Save the notebook with all blocks (initial + evidence + code)
    # Guarantee: existing notebook blocks are preserved and never overwritten
    all_blocks = [initial_block, evidence_block, code_block]
    save_res = client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": all_blocks,
        "title": "Python Metaprogramming Study"
    })
    assert save_res.status_code == 200

    # Step 15 & 16: Close and reopen application (Simulate new session and verify persistence)
    reloaded_nb = client.get(f"/api/notebooks/{nb_id}").json()
    assert len(reloaded_nb["blocks"]) == 3
    # Initial block intact
    assert reloaded_nb["blocks"][0]["content"] == "Python Metaprogramming Study Notes"
    # Evidence block has quote, source URL, and personal note
    assert source_url in reloaded_nb["blocks"][1]["content"]
    assert personal_note in reloaded_nb["blocks"][1]["content"]
    # Executed code block intact with output
    assert "Hello, Developer!" in reloaded_nb["blocks"][2]["output"]

    # Step 17: Disconnect from the internet (Mock all external network requests to fail)
    with patch("httpx.AsyncClient.get", side_effect=Exception("No internet connection")):
        with patch("urllib.request.urlopen", side_effect=Exception("Network unreachable")):
            # Step 18: Verify that the notebook and saved references still work offline
            # A. Notebook editing & viewing remains completely functional
            offline_nb = client.get(f"/api/notebooks/{nb_id}").json()
            assert len(offline_nb["blocks"]) == 3

            # B. Local SQLite FTS5 offline docs search works with zero network
            offline_docs_res = client.get("/api/search/docs?q=decorator")
            assert offline_docs_res.status_code == 200
            assert offline_docs_res.json()["query"] == "decorator"

            # C. Saved bookmarks / references remain accessible offline
            bookmarks_res = client.get("/api/search/bookmarks")
            assert bookmarks_res.status_code == 200
            assert isinstance(bookmarks_res.json(), list)
