def test_root_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cors_allows_vite_dev_server(client):
    r = client.options(
        "/api/routes",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_other_origins(client):
    r = client.get("/api/routes", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_openapi_lists_every_endpoint(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths["/api/auth/register"]) == {"post"}
    assert set(paths["/api/auth/login"]) == {"post"}
    assert set(paths["/api/auth/me"]) == {"get"}
    assert set(paths["/api/routes"]) == {"get", "post"}
    assert set(paths["/api/routes/{route_id}"]) == {"get", "put"}
    assert set(paths["/api/routes/{route_id}/reviews"]) == {"post"}
