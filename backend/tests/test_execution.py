import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_execute_python_success():
    res = client.post("/api/execute", json={
        "language": "python",
        "code": "a = 21\nb = 21\nprint('Total:', a + b)"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Total: 42" in data["output"]
    assert data["execution_time_ms"] > 0

def test_execute_javascript_success():
    res = client.post("/api/execute", json={
        "language": "javascript",
        "code": "const x = 50; const y = 50; console.log(`JS Sum: ${x + y}`);"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "JS Sum: 100" in data["output"]

def test_execute_python_error():
    res = client.post("/api/execute", json={
        "language": "python",
        "code": "1 / 0"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "error"
    assert "ZeroDivisionError" in data["error"]

def test_execute_timeout():
    res = client.post("/api/execute", json={
        "language": "python",
        "code": "import time\nwhile True:\n    time.sleep(0.05)",
        "timeout": 1.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "timeout"
    assert "Execution Timeout" in data["error"]

def test_execute_updates_notebook_block():
    # Create notebook with code block
    nb_res = client.post("/api/notebooks", json={
        "title": "Execution Block Test",
        "blocks": [
            {
                "id": "block-code-test-1",
                "type": "code",
                "language": "python",
                "code": "print('Attached block execution')",
                "output": "",
                "status": "idle"
            }
        ]
    })
    nb_id = nb_res.json()["id"]

    # Run execution with block_id
    exec_res = client.post("/api/execute", json={
        "language": "python",
        "code": "print('Attached block execution')",
        "notebook_id": nb_id,
        "block_id": "block-code-test-1"
    })
    assert exec_res.status_code == 200

    # Fetch notebook and verify block has output and history
    get_res = client.get(f"/api/notebooks/{nb_id}")
    block = get_res.json()["blocks"][0]
    assert "Attached block execution" in block["output"]
    assert block["status"] == "success"
    assert len(block.get("history", [])) >= 1
