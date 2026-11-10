from datetime import UTC, datetime, timedelta

import jwt
import pytest

from security import _secret, create_token

REG_INVALID = "Попълнете име, валиден имейл и парола от поне 6 символа."


def register(client, **overrides):
    body = {"name": "Иван", "email": "ivan@example.com", "password": "secret1", **overrides}
    return client.post("/api/auth/register", json=body)


def test_register_returns_user_and_token(client):
    r = register(client)
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["name"] == "Иван"
    assert data["user"]["email"] == "ivan@example.com"
    assert len(data["user"]["id"]) == 8
    assert set(data["user"]) == {"id", "name", "email"}
    assert data["token"]


def test_register_sanitizes_name_and_lowercases_email(client):
    r = register(client, name="  <b>Иван</b>  ", email="  IVAN@Example.COM ")
    assert r.json()["user"]["name"] == "Иван"
    assert r.json()["user"]["email"] == "ivan@example.com"


def test_register_truncates_name_to_40(client):
    r = register(client, name="я" * 60)
    assert r.json()["user"]["name"] == "я" * 40


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "<i></i>"},
        {"email": "not-an-email"},
        {"email": "a@b"},
        {"email": "a b@c.d"},
        {"password": "12345"},
        {"password": ""},
    ],
)
def test_register_validation(client, overrides):
    r = register(client, **overrides)
    assert r.status_code == 400
    assert r.json() == {"detail": REG_INVALID}


def test_register_missing_fields_uses_same_message(client):
    r = client.post("/api/auth/register", json={})
    assert r.status_code == 400
    assert r.json() == {"detail": REG_INVALID}


def test_register_duplicate_email(client):
    r = register(client, email="Maria@Example.com")
    assert r.status_code == 409
    assert r.json() == {"detail": "Вече има акаунт с този имейл."}


def test_password_is_not_stored_in_plain_text(client):
    register(client)
    from sqlmodel import Session, select

    from models import User

    with Session(client.app.state.engine) as s:
        u = s.exec(select(User).where(User.email == "ivan@example.com")).one()
    assert u.password_hash != "secret1"


def test_login_seed_user(client):
    r = client.post("/api/auth/login", json={"email": " MARIA@example.com ", "password": "demo1234"})
    assert r.status_code == 200
    assert r.json()["user"] == {"id": "u1", "name": "Мария", "email": "maria@example.com"}
    assert r.json()["token"]


def test_login_after_register(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "ivan@example.com", "password": "secret1"})
    assert r.status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {"email": "maria@example.com", "password": "wrong-pass"},
        {"email": "nobody@example.com", "password": "demo1234"},
        {},
    ],
)
def test_login_failure(client, body):
    r = client.post("/api/auth/login", json=body)
    assert r.status_code == 401
    assert r.json() == {"detail": "Грешен имейл или парола."}


def test_me_with_token(client):
    token = register(client).json()["token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ivan@example.com"


def _expired_token():
    past = datetime.now(UTC) - timedelta(days=1)
    return jwt.encode({"sub": "u1", "exp": past}, _secret(), algorithm="HS256")


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer garbage"},
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": f"Bearer {jwt.encode({'sub': 'u1', 'exp': 9999999999}, 'wrong-secret-wrong-secret-wrong-secret', algorithm='HS256')}"},
        {"Authorization": f"Bearer {create_token('ghost-user')}"},
    ],
)
def test_me_rejects_missing_or_invalid_token(client, headers):
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 401
    assert r.json() == {"detail": "Моля, влезте в профила си."}


def test_me_rejects_expired_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {_expired_token()}"})
    assert r.status_code == 401
