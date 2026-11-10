import pytest

from routers.routes import today


@pytest.fixture
def author(make_user):
    return make_user("Алиса")


@pytest.fixture
def reviewer(make_user):
    return make_user("Борис")


@pytest.fixture
def route_id(author, make_route):
    return make_route(author)["id"]


def review(client, account, route_id, **overrides):
    return client.post(f"/api/routes/{route_id}/reviews", json={"rating": 4, "text": "Хубаво", **overrides}, headers=account.headers)


def test_add_review_returns_decorated_route(client, reviewer, route_id):
    r = review(client, reviewer, route_id)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == route_id
    assert data["ratingCount"] == 1 and data["rating"] == 4
    v = data["reviews"][0]
    assert v["userId"] == reviewer.id and v["userName"] == "Борис"
    assert v["rating"] == 4 and v["text"] == "Хубаво" and v["createdAt"] == today()
    assert len(v["id"]) == 8


def test_new_review_goes_first_and_updates_average(client, reviewer, route_id, make_user):
    review(client, reviewer, route_id, rating=5)
    data = review(client, make_user("Ана"), route_id, rating=2).json()
    assert [v["userName"] for v in data["reviews"]] == ["Ана", "Борис"]
    assert data["rating"] == 3.5 and data["ratingCount"] == 2


def test_second_review_by_same_user_replaces_first(client, reviewer, route_id):
    first = review(client, reviewer, route_id, rating=5).json()["reviews"][0]
    data = review(client, reviewer, route_id, rating=1, text="Промених мнението си").json()
    assert data["ratingCount"] == 1
    assert data["reviews"][0]["text"] == "Промених мнението си"
    assert data["rating"] == 1
    assert data["reviews"][0]["id"] != first["id"]


def test_cannot_review_own_route(client, author, route_id):
    r = review(client, author, route_id)
    assert r.status_code == 403
    assert r.json() == {"detail": "Не можете да оценявате собствен маршрут."}


def test_review_missing_route(client, reviewer):
    r = review(client, reviewer, "nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}


@pytest.mark.parametrize("text", ["", "   ", "<b></b>"])
def test_review_needs_text(client, reviewer, route_id, text):
    r = review(client, reviewer, route_id, text=text)
    assert r.status_code == 400
    assert r.json() == {"detail": "Напишете няколко думи в отзива."}


def test_review_requires_auth(client, route_id):
    r = client.post(f"/api/routes/{route_id}/reviews", json={"rating": 5, "text": "x"})
    assert r.status_code == 401


def test_review_text_is_sanitized_and_truncated(client, reviewer, route_id):
    v = review(client, reviewer, route_id, text="<img src=x onerror=alert(1)>" + "д" * 1200).json()["reviews"][0]
    assert v["text"] == "д" * 1000


@pytest.mark.parametrize(
    ("rating", "stars"),
    [(5, 5), (1, 1), (9, 5), (-3, 1), (0, 1), (3.4, 3), (3.5, 4), (2.5, 3), ("4", 4)],
)
def test_rating_is_rounded_like_js_and_clamped(client, reviewer, route_id, rating, stars):
    assert review(client, reviewer, route_id, rating=rating).json()["reviews"][0]["rating"] == stars


@pytest.mark.parametrize("rating", ["abc", None])
def test_non_numeric_rating_is_rejected(client, reviewer, route_id, rating):
    assert review(client, reviewer, route_id, rating=rating).status_code == 422


def test_check_order_matches_mock(client, author, route_id):
    # missing route beats everything, own-route check beats empty text
    assert review(client, author, "nope", text="").status_code == 404
    assert review(client, author, route_id, text="").status_code == 403


def test_review_is_visible_in_list(client, reviewer, route_id):
    review(client, reviewer, route_id, rating=5)
    listed = client.get("/api/routes").json()
    assert listed[0]["ratingCount"] == 1 and listed[0]["rating"] == 5
