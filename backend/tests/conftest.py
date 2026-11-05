import os
import tempfile
import pytest

# Ensure isolated temporary storage during tests
_test_dir = tempfile.mkdtemp(prefix="devnote_test_")
os.environ.setdefault("DEVNOTE_DATA_DIR", _test_dir)

from backend.app.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
