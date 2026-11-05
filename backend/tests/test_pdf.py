import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_pdf_export_and_roundtrip_import():
    # 1. Create a notebook with multiple rich blocks: heading, paragraph, code with output, drawing
    create_res = client.post("/api/notebooks", json={
        "title": "Quantum Computing Notes",
        "description": "Exploration of qubits and superposition",
        "tags": ["quantum", "physics", "python"],
        "blocks": [
            {
                "id": "b-h1",
                "type": "heading",
                "level": 1,
                "content": "Qubit Representation"
            },
            {
                "id": "b-p1",
                "type": "paragraph",
                "content": "A qubit can exist in a superposition of |0> and |1> basis states."
            },
            {
                "id": "b-code1",
                "type": "code",
                "language": "python",
                "code": "import math\nprob_0 = 1 / math.sqrt(2)\nprint(f'Amplitude: {prob_0:.4f}')",
                "output": "Amplitude: 0.7071\n",
                "error": "",
                "execution_time_ms": 12.5,
                "status": "success"
            },
            {
                "id": "b-draw1",
                "type": "drawing",
                "caption": "Bloch Sphere sketch",
                "image_data": None
            }
        ]
    })
    assert create_res.status_code == 201
    nb = create_res.json()
    nb_id = nb["id"]

    # 2. Export to PDF
    export_res = client.post(f"/api/notebooks/{nb_id}/export")
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["notebook_id"] == nb_id
    assert export_data["page_count"] >= 1
    assert export_data["file_size_bytes"] > 0

    # 3. Download the PDF bytes
    download_res = client.get(f"/api/notebooks/{nb_id}/pdf")
    assert download_res.status_code == 200
    pdf_bytes = download_res.content
    assert len(pdf_bytes) > 0

    # 4. Import the PDF back
    # Test importing without target ID (reconstructs canonical notebook and updates it)
    files = {"file": ("exported_quantum.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    import_res = client.post("/api/notebooks/import", files=files)
    assert import_res.status_code == 200
    imported = import_res.json()
    assert imported["reconstructed_from"] == "embedded_metadata"
    assert imported["notebook_id"] == nb_id  # Reopened exact canonical notebook!
    assert imported["block_count"] == 4

    # 5. Verify the notebook in DB has the exact restored state
    get_res = client.get(f"/api/notebooks/{nb_id}")
    restored_nb = get_res.json()
    assert restored_nb["title"] == "Quantum Computing Notes"
    assert len(restored_nb["blocks"]) == 4
    assert restored_nb["blocks"][2]["output"] == "Amplitude: 0.7071\n"
