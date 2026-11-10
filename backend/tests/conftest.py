import itertools

import pytest
from fastapi.testclient import TestClient

from main import create_app

PASSWORD = "secret1"
POINTS = [{"name": "Старт", "lat": 42.1, "lng": 23.1}, {"name": "Край", "lat": 42.2, "lng": 23.2}]


@pytest.fixture
def client():
    # Fresh, empty in-memory database per test.
    with TestClient(create_app("sqlite://")) as c:
        yield c


class Account:
    def __init__(self, user: dict, token: str):
        self.user = user
        self.id = user["id"]
        self.name = user["name"]
        self.headers = {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(client):
    """Register a user through the API. Returns an Account with .id, .name and auth .headers."""
    counter = itertools.count(1)

    def make(name: str | None = None, email: str | None = None) -> Account:
        n = next(counter)
        body = {"name": name or f"Потребител {n}", "email": email or f"user{n}@example.com", "password": PASSWORD}
        r = client.post("/api/auth/register", json=body)
        assert r.status_code == 201, r.text
        return Account(r.json()["user"], r.json()["token"])

    return make


@pytest.fixture
def make_route(client):
    """Create a route through the API as `account`. Returns the created route JSON."""

    def make(account: Account, **overrides) -> dict:
        body = {"title": "Маршрут", "destination": "Пирин", "impressions": "", "tips": "",
                "waypoints": POINTS, "photos": [], **overrides}
        r = client.post("/api/routes", json=body, headers=account.headers)
        assert r.status_code == 201, r.text
        return r.json()

    return make


@pytest.fixture
def add_review(client):
    def add(account: Account, route_id: str, rating: int = 5, text: str = "Хубаво") -> dict:
        r = client.post(f"/api/routes/{route_id}/reviews", json={"rating": rating, "text": text}, headers=account.headers)
        assert r.status_code == 200, r.text
        return r.json()

    return add
