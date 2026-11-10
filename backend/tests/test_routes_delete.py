import pytest
from sqlmodel import Session, select

from models import Review


@pytest.fixture
def author(make_user):
    return make_user("Алиса")


@pytest.fixture
def reviewer(make_user):
    return make_user("Борис")


@pytest.fixture
def route_id(author, reviewer, make_route, add_review):
    rid = make_route(author)["id"]
    add_review(reviewer, rid, 5)
    return rid


def test_author_can_delete_route(client, author, route_id, make_route):
    other = make_route(author, title="Друг")["id"]
    r = client.delete(f"/api/routes/{route_id}", headers=author.headers)
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/api/routes/{route_id}").status_code == 404
    assert [x["id"] for x in client.get("/api/routes").json()] == [other]


def test_delete_removes_only_that_routes_reviews(client, author, reviewer, route_id, make_route, add_review):
    other = make_route(author)["id"]
    add_review(reviewer, other, 3)
    client.delete(f"/api/routes/{route_id}", headers=author.headers)
    with Session(client.app.state.engine) as s:
        assert s.exec(select(Review).where(Review.route_id == route_id)).all() == []
        assert len(s.exec(select(Review)).all()) == 1


def test_only_author_can_delete(client, reviewer, route_id):
    r = client.delete(f"/api/routes/{route_id}", headers=reviewer.headers)
    assert r.status_code == 403
    assert r.json() == {"detail": "Можете да променяте само собствените си маршрути."}
    assert client.get(f"/api/routes/{route_id}").status_code == 200


def test_delete_requires_auth(client, route_id):
    assert client.delete(f"/api/routes/{route_id}").status_code == 401
    assert client.get(f"/api/routes/{route_id}").status_code == 200


def test_delete_missing_route(client, author):
    r = client.delete("/api/routes/nope", headers=author.headers)
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}


def test_delete_twice_is_404(client, author, route_id):
    assert client.delete(f"/api/routes/{route_id}", headers=author.headers).status_code == 204
    assert client.delete(f"/api/routes/{route_id}", headers=author.headers).status_code == 404
