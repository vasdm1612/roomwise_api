"""Pytest fixtures for RoomWise API tests."""

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path("/tmp/roomwise_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key-with-more-than-thirty-two-bytes"

from app.core.config import get_settings  # noqa: E402
from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> None:
    """Create a clean database before each test."""

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    get_settings.cache_clear()
    init_db()
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI TestClient."""

    with TestClient(app) as test_client:
        yield test_client


def register_user(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "strongpass123",
    role: str = "user",
) -> dict[str, Any]:
    """Register a user and return the JSON response."""

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "strongpass123",
) -> dict[str, str]:
    """Login and return Authorization headers."""

    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def admin_headers(client: TestClient) -> dict[str, str]:
    """Create an admin user and return Authorization headers."""

    register_user(client, email="admin@example.com", role="admin")
    return auth_headers(client, email="admin@example.com")


def create_room(client: TestClient, headers: dict[str, str], capacity: int = 8) -> dict[str, Any]:
    """Create a room for tests."""

    response = client.post(
        "/rooms",
        json={"name": f"Room {capacity}", "floor": 2, "capacity": capacity, "is_active": True},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
