import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client():
    # Fresh in-memory database per test; the context manager runs startup (tables + seed).
    with TestClient(create_app("sqlite://")) as c:
        yield c
