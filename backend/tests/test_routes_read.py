import pytest
from sqlmodel import Session, select

from models import Route
from services import decorate


def ids(resp):
    return [r["id"] for r in resp.json()]


def set_date(client, route_id, date):
    """Routes get today's date on creation; backdate them to test date ordering."""
    with Session(client.app.state.engine) as s:
        route = s.exec(select(Route).where(Route.id == route_id)).one()
        route.created_at = date
        s.add(route)
        s.commit()


@pytest.fixture
def three(client, make_user, make_route, add_review):
    """alice: a (Рила, 2026-08-14, 5★) and c (Родопи, 2026-06-21, no reviews); bob: b (Витоша, 2026-07-03, 4★)."""
    alice, bob = make_user("Алиса"), make_user("Борис")
    a = make_route(alice, title="Седемте рилски езера", destination="Рила, България")
    b = make_route(bob, title="Черни връх от Алеко", destination="Витоша, България")
    c = make_route(alice, title="Триград", destination="Родопи, България")
    for rid, date in ((a["id"], "2026-08-14"), (b["id"], "2026-07-03"), (c["id"], "2026-06-21")):
        set_date(client, rid, date)
    add_review(bob, a["id"], 5)
    add_review(alice, b["id"], 4)
    return {"alice": alice, "bob": bob, "a": a["id"], "b": b["id"], "c": c["id"]}


def test_list_is_empty_on_a_fresh_database(client):
    r = client.get("/api/routes")
    assert r.status_code == 200
    assert r.json() == []


def test_list_defaults_to_newest_first(client, three):
    assert ids(client.get("/api/routes")) == [three["a"], three["b"], three["c"]]


def test_list_unknown_sort_falls_back_to_newest(client, three):
    assert ids(client.get("/api/routes", params={"sort": "whatever"})) == [three["a"], three["b"], three["c"]]


def test_list_top_sorts_by_rating_then_count(client, three, make_user, add_review):
    # a: 5.0 (1), b: 4.0 (1), c: 0 (0)
    assert ids(client.get("/api/routes", params={"sort": "top"})) == [three["a"], three["b"], three["c"]]
    # Two 5-star reviews for c: ties with a on rating, wins on count.
    add_review(three["bob"], three["c"], 5)
    add_review(make_user(), three["c"], 5)
    assert ids(client.get("/api/routes", params={"sort": "top"})) == [three["c"], three["a"], three["b"]]


def test_list_same_date_keeps_newest_created_first(client, make_user, make_route):
    u = make_user()
    first, second = make_route(u)["id"], make_route(u)["id"]
    assert ids(client.get("/api/routes")) == [second, first]


def test_list_search_matches_title_and_destination_case_insensitive(client, three):
    assert ids(client.get("/api/routes", params={"q": "  ВИТОША "})) == [three["b"]]
    assert ids(client.get("/api/routes", params={"q": "езера"})) == [three["a"]]
    assert ids(client.get("/api/routes", params={"q": "българия"})) == [three["a"], three["b"], three["c"]]
    assert ids(client.get("/api/routes", params={"q": "алеко витоша"})) == [three["b"]]  # "title destination"
    assert client.get("/api/routes", params={"q": "несъществуващо"}).json() == []


def test_list_search_combines_with_sort(client, three):
    assert ids(client.get("/api/routes", params={"q": "българия", "sort": "top"})) == [three["a"], three["b"], three["c"]]


def test_list_filters_by_author(client, three):
    assert ids(client.get("/api/routes", params={"author": three["alice"].id})) == [three["a"], three["c"]]
    assert ids(client.get("/api/routes", params={"author": three["bob"].id})) == [three["b"]]
    assert client.get("/api/routes", params={"author": "nobody"}).json() == []


def test_list_items_have_the_full_decorated_shape(client, three):
    item = client.get("/api/routes").json()[0]
    assert set(item) == {
        "id", "authorId", "author", "title", "destination", "createdAt", "impressions", "tips",
        "waypoints", "photos", "reviews", "rating", "ratingCount",
    }


def test_get_route(client, three):
    r = client.get(f"/api/routes/{three['b']}")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Черни връх от Алеко"
    assert data["author"] == "Борис" and data["authorId"] == three["bob"].id
    assert data["rating"] == 4 and data["ratingCount"] == 1
    assert data["reviews"][0]["userName"] == "Алиса"
    assert data["photos"] == []


def test_get_missing_route_is_404(client):
    r = client.get("/api/routes/nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}


def test_decorate_falls_back_to_unknown_author(client):
    with Session(client.app.state.engine) as s:
        route = Route(author_id="ghost", title="t", destination="d", created_at="2026-01-01")
        assert decorate(s, route).author == "Непознат"
