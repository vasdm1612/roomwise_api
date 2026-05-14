"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_register_login_and_me(client: TestClient) -> None:
    """User can register, login and read own profile."""

    created = register_user(client)
    assert created["email"] == "user@example.com"
    headers = auth_headers(client)
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_reject_invalid_login(client: TestClient) -> None:
    """Invalid credentials are rejected."""

    register_user(client)
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "wrongpass123"}
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient) -> None:
    """Protected profile route cannot be called without a token."""

    response = client.get("/auth/me")
    assert response.status_code == 401
