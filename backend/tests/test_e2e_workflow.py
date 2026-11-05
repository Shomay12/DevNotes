import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_devnote_acceptance_workflow():
    """
    Validates the complete 16-step user workflow from Section 15:
    1. Open app
    2. Create notebook
    3. Write text
    4. Insert Python code block
    5. Execute code
    6. Verify output
    7. Search developer workspace
    8. Search programming concept
    9. Insert search result into notebook
    10. Add handwritten drawing block
    11. Autosave document
    12. Export notebook as PDF
    13. Reopen application / list notebooks
    14. Open same notebook without duplicate
    15. Upload exported PDF and continue editing
    16. Export updated notebook again
    """

    # Step 1: Open application / Health check
    res_index = client.get("/")
    assert res_index.status_code == 200

    # Step 2: Create a notebook
    create_res = client.post("/api/notebooks", json={
        "title": "Machine Learning Fundamentals",
        "tags": ["ml", "python", "ai"]
    })
    assert create_res.status_code == 201
    notebook = create_res.json()
    nb_id = notebook["id"]
    assert notebook["title"] == "Machine Learning Fundamentals"

    # Step 3 & 4: Write text and insert Python code block between two paragraphs
    blocks = [
        {
            "id": "block-p1",
            "type": "paragraph",
            "content": "Gradient descent is an optimization algorithm used to minimize the loss function."
        },
        {
            "id": "block-code-1",
            "type": "code",
            "language": "python",
            "code": "learning_rate = 0.01\ngradient = 3.5\nweight = 10.0\nnew_weight = weight - learning_rate * gradient\nprint(f'Updated Weight: {new_weight:.4f}')",
            "output": "",
            "error": "",
            "status": "idle"
        },
        {
            "id": "block-p2",
            "type": "paragraph",
            "content": "Notice how the parameter step reduces the loss proportionally to the gradient."
        }
    ]

    # Save initial blocks
    save_res = client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": blocks,
        "title": "Machine Learning Fundamentals"
    })
    assert save_res.status_code == 200

    # Step 5 & 6: Execute the code block and verify output
    exec_res = client.post("/api/execute", json={
        "language": "python",
        "code": blocks[1]["code"],
        "notebook_id": nb_id,
        "block_id": "block-code-1"
    })
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    assert "Updated Weight: 9.9650" in exec_data["output"]

    # Verify block output was recorded in notebook
    nb_check = client.get(f"/api/notebooks/{nb_id}").json()
    assert "Updated Weight: 9.9650" in nb_check["blocks"][1]["output"]

    # Step 7 & 8: Search developer search workspace for programming concepts
    search_res = client.get("/api/search/notebooks?q=decorators")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_results"] >= 1
    decorator_item = next(item for item in search_data["results"] if "Decorator" in item["title"])

    # Step 9: Insert relevant search result into notebook (adds heading, snippet, code without overwriting)
    updated_blocks = list(nb_check["blocks"])
    updated_blocks.append({
        "id": "block-search-h2",
        "type": "heading",
        "level": 2,
        "content": decorator_item["title"]
    })
    updated_blocks.append({
        "id": "block-search-p",
        "type": "paragraph",
        "content": decorator_item["snippet"]
    })
    if decorator_item.get("code"):
        updated_blocks.append({
            "id": "block-search-code",
            "type": "code",
            "language": decorator_item.get("language", "python"),
            "code": decorator_item["code"],
            "output": "",
            "status": "idle"
        })

    # Step 10: Use stylus/mouse to draw handwritten notes (Handwriting block)
    # Generate 1x1 base64 transparent PNG for test canvas
    dummy_png_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    updated_blocks.append({
        "id": "block-draw-loss-curve",
        "type": "drawing",
        "caption": "Loss Curve Graph",
        "strokes": [
            {
                "tool": "pen",
                "color": "#2563eb",
                "width": 3.0,
                "points": [{"x": 10, "y": 10, "pressure": 0.5}, {"x": 50, "y": 80, "pressure": 0.8}]
            }
        ],
        "image_data": dummy_png_data
    })

    # Step 11: Automatically save the document
    autosave_res = client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": updated_blocks,
        "title": "Machine Learning Fundamentals",
        "tags": ["ml", "python", "ai", "optimization"]
    })
    assert autosave_res.status_code == 200
    saved_nb = autosave_res.json()
    assert len(saved_nb["blocks"]) >= 6

    # Step 12: Export the notebook as PDF
    export_res = client.post(f"/api/notebooks/{nb_id}/export")
    assert export_res.status_code == 200
    export_info = export_res.json()
    assert export_info["notebook_id"] == nb_id
    assert export_info["page_count"] >= 1
    assert export_info["file_size_bytes"] > 0

    # Download exported PDF
    download_res = client.get(f"/api/notebooks/{nb_id}/pdf")
    assert download_res.status_code == 200
    pdf_content = download_res.content
    assert len(pdf_content) > 0

    # Step 13 & 14: Close and reopen application / list notebooks -> same notebook without duplicates!
    initial_count = len(client.get("/api/notebooks").json())
    reopened_nb = client.get(f"/api/notebooks/{nb_id}").json()
    assert reopened_nb["id"] == nb_id
    assert reopened_nb["title"] == "Machine Learning Fundamentals"
    assert len(client.get("/api/notebooks").json()) == initial_count

    # Step 15: Upload exported notebook PDF and continue editing it
    pdf_file = io.BytesIO(pdf_content)
    import_res = client.post("/api/notebooks/import", files={
        "file": ("ml_exported.pdf", pdf_file, "application/pdf")
    })
    assert import_res.status_code == 200
    import_info = import_res.json()
    assert import_info["notebook_id"] == nb_id # Reconstructs same canonical document without duplicates!

    # Continue editing: add another paragraph
    continuation_blocks = list(reopened_nb["blocks"])
    continuation_blocks.append({
        "id": "block-continue-1",
        "type": "paragraph",
        "content": "Continued editing after round-trip PDF import!"
    })

    cont_res = client.patch(f"/api/notebooks/{nb_id}/content", json={
        "blocks": continuation_blocks
    })
    assert cont_res.status_code == 200
    assert len(cont_res.json()["blocks"]) == len(continuation_blocks)

    # Step 16: Export the updated notebook again
    export_v2_res = client.post(f"/api/notebooks/{nb_id}/export")
    assert export_v2_res.status_code == 200
    export_v2_info = export_v2_res.json()
    assert export_v2_info["notebook_id"] == nb_id
    assert export_v2_info["file_size_bytes"] > 0

    # Final check: total notebook count has not increased by duplicate imports
    final_count = len(client.get("/api/notebooks").json())
    assert final_count == initial_count
