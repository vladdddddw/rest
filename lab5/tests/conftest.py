import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app
from models.book import library_store


@pytest.fixture(scope="session")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_store():
    library_store.clear()
    yield
    library_store.clear()
