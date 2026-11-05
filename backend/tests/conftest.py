import pytest
from backend.app.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
