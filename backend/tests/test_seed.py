from sqlmodel import Session, select

from models import Route, User
from security import verify_password
from seed import seed_if_empty
from services import decorate


def _session(client):
    return Session(client.app.state.engine)


def test_seed_creates_demo_users_with_hashed_passwords(client):
    with _session(client) as s:
        users = {u.id: u for u in s.exec(select(User)).all()}
    assert set(users) == {"u1", "u2"}
    assert users["u1"].email == "maria@example.com"
    assert users["u1"].password_hash != "demo1234"
    assert verify_password("demo1234", users["u1"].password_hash)


def test_seed_creates_demo_routes_decorated_like_the_mock(client):
    with _session(client) as s:
        routes = {r.id: decorate(s, r) for r in s.exec(select(Route)).all()}
    assert set(routes) == {"r1", "r2", "r3"}

    r1 = routes["r1"].model_dump(by_alias=True)
    assert r1["author"] == "Мария"
    assert r1["authorId"] == "u1"
    assert r1["createdAt"] == "2026-08-14"
    assert [w["name"] for w in r1["waypoints"]] == ["Хижа Рилски езера", "Окото", "Бъбрека", "Езерен връх"]
    assert r1["rating"] == 5 and r1["ratingCount"] == 1
    assert r1["reviews"][0] == {
        "id": "v1", "userId": "u2", "userName": "Георги", "rating": 5,
        "text": "Точно както е описано. Благодаря за съветите!", "createdAt": "2026-09-02",
    }
    assert routes["r3"].rating == 0 and routes["r3"].rating_count == 0


def test_seed_is_idempotent(client):
    seed_if_empty(client.app.state.engine)
    with _session(client) as s:
        assert len(s.exec(select(User)).all()) == 2
        assert len(s.exec(select(Route)).all()) == 3


def test_decorate_falls_back_to_unknown_author(client):
    with _session(client) as s:
        route = Route(author_id="ghost", title="t", destination="d", created_at="2026-01-01")
        assert decorate(s, route).author == "Непознат"
