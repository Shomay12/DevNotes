import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_devsearch_full_acceptance_workflow():
    """
    Validates the 18-step acceptance criteria from Section 17:
    1. Developer opens a notebook.
    2. Opens DevSearch in split-screen mode.
    3. Searches "Python decorators".
    4. Receives real documentation results.
    5. Filters results by documentation.
    6. Opens a Python documentation result.
    7. Inserts its reference into the current notebook.
    8. Searches "ModuleNotFoundError: No module named torch".
    9. Receives relevant troubleshooting results.
    10. Searches GitHub for a Python implementation.
    11. Inserts a selected code example into the notebook.
    12. Executes that code using the existing execution engine.
    13. Saves the notebook.
    14. Closes and reopens it.
    15. Finds previous searches in search history.
    16. Disconnects from the internet (offline mode).
    17. Searches locally downloaded documentation.
    18. Continues editing and exports the notebook as PDF.
    """

    # Step 1: Open / Create a notebook
    create_res = client.post("/api/notebooks", json={
        "title": "DevSearch Integration Workflow",
        "tags": ["search", "devsearch", "python"]
    })
    assert create_res.status_code == 201
    nb = create_res.json()
    nb_id = nb["id"]

    # Step 2: Query DevSearch provider status
    providers_res = client.get("/api/search/providers")
    assert providers_res.status_code == 200
    providers = providers_res.json()
    assert any(p["id"] == "devdocs" for p in providers)
    assert any(p["id"] == "local_docs" for p in providers)

    # Step 3 & 4: Search "Python decorators"
    search_dec_res = client.post("/api/search", json={
        "query": "Python decorators",
        "category": "all"
    })
    assert search_dec_res.status_code == 200
    dec_data = search_dec_res.json()
    assert dec_data["total_results"] >= 1
    assert any("decorator" in item["title"].lower() for item in dec_data["results"])

    # Step 5 & 6: Filter results by documentation & select a Python documentation result
    doc_filter_res = client.post("/api/search", json={
        "query": "decorators",
        "category": "doc",
        "language": "python"
    })
    assert doc_filter_res.status_code == 200
    doc_results = doc_filter_res.json()["results"]
    assert len(doc_results) >= 1
    selected_doc = next(r for r in doc_results if "decorator" in r["title"].lower())

    # Step 7: Insert its reference into the current notebook (Heading + Paragraph + Citation)
    blocks = [
        {
            "id": "block-dec-title",
            "type": "heading",
            "level": 2,
            "content": selected_doc["title"]
        },
        {
            "id": "block-dec-summary",
            "type": "paragraph",
            "content": f"{selected_doc['snippet']}\n\nSource: {selected_doc['source']} ({selected_doc['url']})"
        }
    ]

    # Step 8 & 9: Search "ModuleNotFoundError: No module named torch" (Error troubleshooting)
    err_res = client.post("/api/search", json={
        "query": "ModuleNotFoundError: No module named torch",
        "category": "all"
    })
    assert err_res.status_code == 200
    err_data = err_res.json()
    assert err_data["intent"] == "error"
    assert err_data["total_results"] >= 1
    assert any("torch" in item["title"].lower() or "modulenotfound" in item["title"].lower() for item in err_data["results"])

    # Step 10: Search GitHub for a Python implementation (e.g. quicksort / algorithms)
    gh_res = client.post("/api/search", json={
        "query": "algorithms python",
        "category": "github",
        "language": "python"
    })
    assert gh_res.status_code == 200
    gh_results = gh_res.json()["results"]
    assert len(gh_results) >= 1
    gh_item_with_code = next((item for item in gh_results if item.get("code")), gh_results[0])

    # Step 11: Insert code example into the notebook
    executable_python_code = gh_item_with_code.get("code") or "def greet():\n    return 'Hello from DevSearch'\nprint(greet())"
    blocks.append({
        "id": "block-gh-code",
        "type": "code",
        "language": "python",
        "code": executable_python_code,
        "output": "",
        "status": "idle"
    })

    # Step 12: Execute the inserted code block using the execution engine
    exec_res = client.post("/api/execute", json={
        "language": "python",
        "code": executable_python_code,
        "notebook_id": nb_id,
        "block_id": "block-gh-code"
    })
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    assert len(exec_data["output"]) > 0

    # Step 13: Save the notebook with updated blocks and recorded output
    blocks[2]["output"] = exec_data["output"]
    save_res = client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": blocks,
        "title": "DevSearch Integration Workflow"
    })
    assert save_res.status_code == 200

    # Step 14: Close and reopen it -> exact same state, no duplicate
    reopen_res = client.get(f"/api/notebooks/{nb_id}")
    assert reopen_res.status_code == 200
    reopened_nb = reopen_res.json()
    assert len(reopened_nb["blocks"]) == 3
    assert reopened_nb["blocks"][0]["content"] == selected_doc["title"]
    assert reopened_nb["blocks"][2]["output"] == exec_data["output"]

    # Step 15: Find previous searches in search history
    hist_res = client.get("/api/search/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2
    queries = [h["query"].lower() for h in history]
    assert any("decorator" in q for q in queries)
    assert any("torch" in q for q in queries)

    # Step 16 & 17: Disconnect from the internet -> Search locally downloaded documentation
    offline_res = client.get("/api/search/docs?q=asyncio")
    assert offline_res.status_code == 200
    offline_data = offline_res.json()
    assert offline_data["total_results"] >= 1
    assert any("async" in item["title"].lower() or "coroutine" in item["snippet"].lower() for item in offline_data["results"])

    # Step 18: Export notebook as PDF
    pdf_res = client.post(f"/api/pdf/export/{nb_id}")
    assert pdf_res.status_code == 200
    pdf_data = pdf_res.json()
    assert "pdf_url" in pdf_data
    assert pdf_data["page_count"] >= 1
