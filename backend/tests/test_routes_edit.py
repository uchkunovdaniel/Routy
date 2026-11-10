import pytest

IMG = "data:image/png;base64,iVBOR"
POINTS = [{"name": "Старт", "lat": 42.1, "lng": 23.1}, {"name": "Край", "lat": 42.2, "lng": 23.2}]
BODY = {"title": "Ново заглавие", "destination": "Пирин", "impressions": "Нови", "tips": "Съвети",
        "waypoints": POINTS, "photos": [IMG]}


def login(client, email):
    token = client.post("/api/auth/login", json={"email": email, "password": "demo1234"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def maria(client):
    return login(client, "maria@example.com")  # author of r1, r3


@pytest.fixture
def georgi(client):
    return login(client, "georgi@example.com")


def put(client, auth, route_id="r1", **overrides):
    return client.put(f"/api/routes/{route_id}", json={**BODY, **overrides}, headers=auth)


def test_edit_replaces_fields_and_keeps_metadata(client, maria):
    r = put(client, maria)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "r1"
    assert data["title"] == "Ново заглавие" and data["destination"] == "Пирин"
    assert data["impressions"] == "Нови" and data["tips"] == "Съвети"
    assert data["waypoints"] == POINTS and data["photos"] == [IMG]
    # unchanged
    assert data["authorId"] == "u1" and data["author"] == "Мария"
    assert data["createdAt"] == "2026-08-14"
    assert [v["id"] for v in data["reviews"]] == ["v1"] and data["rating"] == 5


def test_edit_is_persisted(client, maria):
    put(client, maria)
    assert client.get("/api/routes/r1").json()["title"] == "Ново заглавие"
    assert client.get("/api/routes", params={"q": "пирин"}).json()[0]["id"] == "r1"


def test_edit_applies_same_sanitization_as_create(client, maria):
    data = put(client, maria, title="<b>Х</b>" + "т" * 200, photos=["javascript:x", IMG],
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
def test_edit_validation(client, maria, overrides, detail):
    r = put(client, maria, **overrides)
    assert r.status_code == 400
    assert r.json() == {"detail": detail}
    assert client.get("/api/routes/r1").json()["title"] == "Седемте рилски езера за един ден"


def test_only_author_can_edit(client, georgi):
    r = put(client, georgi, "r1")
    assert r.status_code == 403
    assert r.json() == {"detail": "Можете да променяте само собствените си маршрути."}
    assert client.get("/api/routes/r1").json()["title"] == "Седемте рилски езера за един ден"


def test_edit_requires_auth(client):
    assert client.put("/api/routes/r1", json=BODY).status_code == 401


def test_edit_missing_route(client, maria):
    r = put(client, maria, "nope")
    assert r.status_code == 404
    assert r.json() == {"detail": "Маршрутът не съществува."}
