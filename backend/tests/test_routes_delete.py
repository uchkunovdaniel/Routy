from sqlmodel import Session, select

from models import Review


def login(client, email):
    token = client.post("/api/auth/login", json={"email": email, "password": "demo1234"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_author_can_delete_route(client):
    r = client.delete("/api/routes/r1", headers=login(client, "maria@example.com"))
    assert r.status_code == 204
    assert r.content == b""
    assert client.get("/api/routes/r1").status_code == 404
    assert [x["id"] for x in client.get("/api/routes").json()] == ["r2", "r3"]


def test_delete_removes_the_routes_reviews(client):
    client.delete("/api/routes/r1", headers=login(client, "maria@example.com"))
    with Session(client.app.state.engine) as s:
        assert s.exec(select(Review).where(Review.route_id == "r1")).all() == []
        assert len(s.exec(select(Review)).all()) == 1  # r2's review is untouched


def test_only_author_can_delete(client):
    r = client.delete("/api/routes/r1", headers=login(client, "georgi@example.com"))
    assert r.status_code == 403
    assert r.json() == {"detail": "Можете да променяте само собствените си маршрути."}
    assert client.get("/api/routes/r1").status_code == 200


def test_delete_requires_auth(client):
    assert client.delete("/api/routes/r1").status_code == 401
    assert client.get("/api/routes/r1").status_code == 200


def test_delete_missing_route(client):
    r = client.delete("/api/routes/nope", headers=login(client, "maria@example.com"))
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}


def test_delete_twice_is_404(client):
    auth = login(client, "maria@example.com")
    assert client.delete("/api/routes/r3", headers=auth).status_code == 204
    assert client.delete("/api/routes/r3", headers=auth).status_code == 404
