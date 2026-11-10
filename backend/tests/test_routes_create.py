import pytest

from routers.routes import today

IMG = "data:image/jpeg;base64,/9j/AAAA"
POINTS = [{"name": "Старт", "lat": 42.1, "lng": 23.1}, {"name": "Край", "lat": 42.2, "lng": 23.2}]


@pytest.fixture
def auth(client):
    token = client.post("/api/auth/login", json={"email": "georgi@example.com", "password": "demo1234"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def create(client, auth, **overrides):
    body = {"title": "Мусала", "destination": "Рила", "impressions": "Супер", "tips": "Вода",
            "waypoints": POINTS, "photos": [], **overrides}
    return client.post("/api/routes", json=body, headers=auth)


def test_create_route(client, auth):
    r = create(client, auth)
    assert r.status_code == 201
    data = r.json()
    assert data["authorId"] == "u2" and data["author"] == "Георги"
    assert data["title"] == "Мусала" and data["destination"] == "Рила"
    assert data["impressions"] == "Супер" and data["tips"] == "Вода"
    assert data["waypoints"] == POINTS
    assert data["createdAt"] == today()
    assert data["reviews"] == [] and data["rating"] == 0 and data["ratingCount"] == 0
    assert len(data["id"]) == 8


def test_created_route_is_listed_first_and_fetchable(client, auth):
    rid = create(client, auth).json()["id"]
    assert client.get("/api/routes").json()[0]["id"] == rid
    assert client.get(f"/api/routes/{rid}").json()["title"] == "Мусала"
    assert rid in [r["id"] for r in client.get("/api/routes", params={"author": "u2"}).json()]


def test_create_requires_auth(client):
    r = client.post("/api/routes", json={"title": "x"})
    assert r.status_code == 401
    assert r.json() == {"detail": "Моля, влезте в профила си."}


def test_create_sanitizes_text_fields(client, auth):
    data = create(
        client, auth,
        title="  <script>x</script>Мусала  ", destination="<b>Рила</b>",
        impressions="a" * 5000, tips="b" * 3000,
    ).json()
    assert data["title"] == "xМусала"
    assert data["destination"] == "Рила"
    assert len(data["impressions"]) == 4000
    assert len(data["tips"]) == 2000


def test_create_truncates_title_and_destination(client, auth):
    data = create(client, auth, title="т" * 200, destination="д" * 200).json()
    assert len(data["title"]) == 120 and len(data["destination"]) == 120


def test_create_drops_invalid_waypoints_and_numbers_unnamed_ones(client, auth):
    waypoints = [
        {"lat": 200, "lng": 0},                       # out of range
        {"name": "Низ", "lat": "42", "lng": 23},      # string, not a number
        {"lat": 42.0, "lng": 23.0},                   # unnamed -> "Точка 1" (index after filtering)
        "garbage",
        {"name": "<i></i>", "lat": 42.5, "lng": 23.5},  # name empty after cleaning -> "Точка 2"
        {"name": "н" * 100, "lat": -90, "lng": 180},  # name truncated to 80
    ]
    data = create(client, auth, waypoints=waypoints).json()
    assert data["waypoints"] == [
        {"name": "Точка 1", "lat": 42.0, "lng": 23.0},
        {"name": "Точка 2", "lat": 42.5, "lng": 23.5},
        {"name": "н" * 80, "lat": -90, "lng": 180},
    ]


@pytest.mark.parametrize(
    "waypoints",
    [[], [POINTS[0]], [POINTS[0], {"lat": 999, "lng": 0}]],
)
def test_create_needs_two_valid_waypoints(client, auth, waypoints):
    r = create(client, auth, waypoints=waypoints)
    assert r.status_code == 400
    assert r.json() == {"detail": "Добавете поне две точки от маршрута на картата."}


def test_waypoint_check_runs_before_title_check(client, auth):
    r = create(client, auth, title="", waypoints=[])
    assert r.json()["detail"] == "Добавете поне две точки от маршрута на картата."


@pytest.mark.parametrize("overrides", [{"title": ""}, {"destination": "   "}, {"title": "<br>"}])
def test_create_requires_title_and_destination(client, auth, overrides):
    r = create(client, auth, **overrides)
    assert r.status_code == 400
    assert r.json() == {"detail": "Заглавието и дестинацията са задължителни."}


def test_create_keeps_only_safe_photos_max_six(client, auth):
    photos = ["javascript:alert(1)", "https://evil.example/x.png", 42] + [IMG + str(i) for i in range(8)]
    data = create(client, auth, photos=photos).json()
    assert data["photos"] == [IMG + str(i) for i in range(6)]


def test_create_optional_fields_default_to_empty(client, auth):
    r = client.post("/api/routes", json={"title": "T", "destination": "D", "waypoints": POINTS}, headers=auth)
    assert r.status_code == 201
    assert r.json()["impressions"] == "" and r.json()["tips"] == "" and r.json()["photos"] == []
