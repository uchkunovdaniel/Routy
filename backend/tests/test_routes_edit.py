import pytest

from conftest import POINTS
from routers.routes import today

IMG = "data:image/png;base64,iVBOR"
BODY = {"title": "Ново заглавие", "destination": "Пирин", "impressions": "Нови", "tips": "Съвети",
        "waypoints": POINTS, "photos": [IMG]}


@pytest.fixture
def author(make_user):
    return make_user("Алиса")


@pytest.fixture
def route(author, make_user, make_route, add_review):
    r = make_route(author, title="Старо заглавие")
    add_review(make_user("Борис"), r["id"], 5)
    return r


def put(client, account, route_id, **overrides):
    return client.put(f"/api/routes/{route_id}", json={**BODY, **overrides}, headers=account.headers)


def test_edit_replaces_fields_and_keeps_metadata(client, author, route):
    r = put(client, author, route["id"])
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == route["id"]
    assert data["title"] == "Ново заглавие" and data["destination"] == "Пирин"
    assert data["impressions"] == "Нови" and data["tips"] == "Съвети"
    assert data["waypoints"] == POINTS and data["photos"] == [IMG]
    # unchanged
    assert data["authorId"] == author.id and data["author"] == "Алиса"
    assert data["createdAt"] == today()
    assert data["ratingCount"] == 1 and data["rating"] == 5


def test_edit_is_persisted(client, author, route):
    put(client, author, route["id"])
    assert client.get(f"/api/routes/{route['id']}").json()["title"] == "Ново заглавие"
    assert client.get("/api/routes", params={"q": "ново"}).json()[0]["id"] == route["id"]


def test_edit_applies_same_sanitization_as_create(client, author, route):
    data = put(client, author, route["id"], title="<b>Х</b>" + "т" * 200, photos=["javascript:x", IMG],
               waypoints=[{"lat": 1, "lng": 1}, {"lat": 999, "lng": 0}, {"name": "Б", "lat": 2, "lng": 2}]).json()
    assert data["title"] == ("Х" + "т" * 200)[:120]
    assert data["photos"] == [IMG]
    assert data["waypoints"] == [{"name": "Точка 1", "lat": 1, "lng": 1}, {"name": "Б", "lat": 2, "lng": 2}]


@pytest.mark.parametrize(
    ("overrides", "detail"),
    [
        ({"waypoints": [POINTS[0]]}, "Добавете поне две точки от маршрута на картата."),
        ({"title": ""}, "Заглавието и дестинацията са задължителни."),
    ],
)
def test_edit_validation(client, author, route, overrides, detail):
    r = put(client, author, route["id"], **overrides)
    assert r.status_code == 400
    assert r.json() == {"detail": detail}
    assert client.get(f"/api/routes/{route['id']}").json()["title"] == "Старо заглавие"


def test_only_author_can_edit(client, route, make_user):
    r = put(client, make_user(), route["id"])
    assert r.status_code == 403
    assert r.json() == {"detail": "Можете да променяте само собствените си маршрути."}
    assert client.get(f"/api/routes/{route['id']}").json()["title"] == "Старо заглавие"


def test_edit_requires_auth(client, route):
    assert client.put(f"/api/routes/{route['id']}", json=BODY).status_code == 401


def test_edit_missing_route(client, author):
    r = put(client, author, "nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}
