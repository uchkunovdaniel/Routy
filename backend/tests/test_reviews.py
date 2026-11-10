import pytest

from routers.routes import today


def login(client, email):
    token = client.post("/api/auth/login", json={"email": email, "password": "demo1234"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def maria(client):
    return login(client, "maria@example.com")  # author of r1, r3


@pytest.fixture
def georgi(client):
    return login(client, "georgi@example.com")  # author of r2


def review(client, auth, route_id="r3", **overrides):
    return client.post(f"/api/routes/{route_id}/reviews", json={"rating": 4, "text": "Хубаво", **overrides}, headers=auth)


def test_add_review_returns_decorated_route(client, georgi):
    r = review(client, georgi)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "r3"
    assert data["ratingCount"] == 1 and data["rating"] == 4
    v = data["reviews"][0]
    assert v["userId"] == "u2" and v["userName"] == "Георги"
    assert v["rating"] == 4 and v["text"] == "Хубаво" and v["createdAt"] == today()
    assert len(v["id"]) == 8


def test_new_review_goes_first_and_updates_average(client, maria, georgi):
    # r1 already has Георги's 5; register a third user to add another.
    token = client.post("/api/auth/register", json={"name": "Ана", "email": "ana@example.com", "password": "secret1"}).json()["token"]
    data = review(client, {"Authorization": f"Bearer {token}"}, "r1", rating=2).json()
    assert [v["userName"] for v in data["reviews"]] == ["Ана", "Георги"]
    assert data["rating"] == 3.5 and data["ratingCount"] == 2


def test_second_review_by_same_user_replaces_first(client, georgi):
    data = review(client, georgi, "r1", rating=1, text="Промених мнението си").json()
    assert data["ratingCount"] == 1
    assert data["reviews"][0]["text"] == "Промених мнението си"
    assert data["rating"] == 1
    assert data["reviews"][0]["id"] != "v1"


def test_cannot_review_own_route(client, maria):
    r = review(client, maria, "r1")
    assert r.status_code == 403
    assert r.json() == {"detail": "Не можете да оценявате собствен маршрут."}


def test_review_missing_route(client, georgi):
    r = review(client, georgi, "nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}


@pytest.mark.parametrize("text", ["", "   ", "<b></b>"])
def test_review_needs_text(client, georgi, text):
    r = review(client, georgi, text=text)
    assert r.status_code == 400
    assert r.json() == {"detail": "Напишете няколко думи в отзива."}


def test_review_requires_auth(client):
    r = client.post("/api/routes/r3/reviews", json={"rating": 5, "text": "x"})
    assert r.status_code == 401


def test_review_text_is_sanitized_and_truncated(client, georgi):
    v = review(client, georgi, text="<img src=x onerror=alert(1)>" + "д" * 1200).json()["reviews"][0]
    assert v["text"] == "д" * 1000


@pytest.mark.parametrize(
    ("rating", "stars"),
    [(5, 5), (1, 1), (9, 5), (-3, 1), (0, 1), (3.4, 3), (3.5, 4), (2.5, 3), ("4", 4)],
)
def test_rating_is_rounded_like_js_and_clamped(client, georgi, rating, stars):
    assert review(client, georgi, rating=rating).json()["reviews"][0]["rating"] == stars


@pytest.mark.parametrize("rating", ["abc", None])
def test_non_numeric_rating_is_rejected(client, georgi, rating):
    assert review(client, georgi, rating=rating).status_code == 422


def test_check_order_matches_mock(client, maria, georgi):
    # missing route beats everything, own-route check beats empty text
    assert review(client, maria, "nope", text="").status_code == 404
    assert review(client, maria, "r1", text="").status_code == 403


def test_review_is_visible_in_list_and_top_sort(client, georgi):
    review(client, georgi, "r3", rating=5)
    listed = {r["id"]: r for r in client.get("/api/routes").json()}
    assert listed["r3"]["ratingCount"] == 1
    # r3 now 5.0 with 1 review, tied with r1 (5.0, 1): r3 was inserted earlier in the
    # mock's array order, so r1 stays first.
    assert [r["id"] for r in client.get("/api/routes", params={"sort": "top"}).json()] == ["r1", "r3", "r2"]
