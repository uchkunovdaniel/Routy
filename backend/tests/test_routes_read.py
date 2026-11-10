from sqlmodel import Session

from models import Review, Route


def ids(resp):
    return [r["id"] for r in resp.json()]


def add_route(client, **kw):
    data = {"author_id": "u2", "title": "Нов", "destination": "Пирин", "created_at": "2026-01-01",
            "waypoints": [{"name": "A", "lat": 1, "lng": 1}, {"name": "B", "lat": 2, "lng": 2}], **kw}
    with Session(client.app.state.engine) as s:
        s.add(Route(**data))
        s.commit()


def add_review(client, route_id, user_id, rating):
    with Session(client.app.state.engine) as s:
        s.add(Review(route_id=route_id, user_id=user_id, user_name="x", rating=rating, text="t",
                     created_at="2026-01-01"))
        s.commit()


def test_list_defaults_to_newest_first(client):
    r = client.get("/api/routes")
    assert r.status_code == 200
    assert ids(r) == ["r1", "r2", "r3"]


def test_list_unknown_sort_falls_back_to_newest(client):
    assert ids(client.get("/api/routes", params={"sort": "whatever"})) == ["r1", "r2", "r3"]


def test_list_top_sorts_by_rating_then_count(client):
    # r1: 5.0 (1), r2: 4.0 (1), r3: 0 (0)
    assert ids(client.get("/api/routes", params={"sort": "top"})) == ["r1", "r2", "r3"]
    # Give r3 two 5-star reviews: ties with r1 on rating, wins on count.
    add_review(client, "r3", "u2", 5)
    add_review(client, "r3", "x", 5)
    assert ids(client.get("/api/routes", params={"sort": "top"})) == ["r3", "r1", "r2"]


def test_list_same_date_keeps_newest_inserted_first(client):
    add_route(client, id="aaaaaaa1", created_at="2026-08-14")
    add_route(client, id="aaaaaaa2", created_at="2026-08-14")
    assert ids(client.get("/api/routes"))[:3] == ["aaaaaaa2", "aaaaaaa1", "r1"]


def test_list_search_matches_title_and_destination_case_insensitive(client):
    assert ids(client.get("/api/routes", params={"q": "  ВИТОША "})) == ["r2"]
    assert ids(client.get("/api/routes", params={"q": "езера"})) == ["r1"]
    assert ids(client.get("/api/routes", params={"q": "българия"})) == ["r1", "r2", "r3"]
    assert ids(client.get("/api/routes", params={"q": "алеко витоша"})) == ["r2"]  # "title destination"
    assert client.get("/api/routes", params={"q": "несъществуващо"}).json() == []


def test_list_search_combines_with_sort(client):
    assert ids(client.get("/api/routes", params={"q": "българия", "sort": "top"})) == ["r1", "r2", "r3"]


def test_list_filters_by_author(client):
    assert ids(client.get("/api/routes", params={"author": "u1"})) == ["r1", "r3"]
    assert ids(client.get("/api/routes", params={"author": "u2"})) == ["r2"]
    assert client.get("/api/routes", params={"author": "nobody"}).json() == []


def test_list_items_have_the_full_decorated_shape(client):
    item = client.get("/api/routes").json()[0]
    assert set(item) == {
        "id", "authorId", "author", "title", "destination", "createdAt", "impressions", "tips",
        "waypoints", "photos", "reviews", "rating", "ratingCount",
    }


def test_get_route(client):
    r = client.get("/api/routes/r2")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Черни връх по билото от Алеко"
    assert data["author"] == "Георги"
    assert data["rating"] == 4 and data["ratingCount"] == 1
    assert data["waypoints"][0] == {"name": "Алеко", "lat": 42.5631, "lng": 23.2897}
    assert data["photos"] == []


def test_get_missing_route_is_404(client):
    r = client.get("/api/routes/nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}
