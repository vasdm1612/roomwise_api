"""Tests for slot recommendation business logic."""

from fastapi.testclient import TestClient

from tests.conftest import admin_headers, auth_headers, create_room, register_user


def test_recommendation_returns_best_available_slot(client: TestClient) -> None:
    """Recommendation endpoint returns slots sorted by score."""

    admin = admin_headers(client)
    equipment = client.post(
        "/equipment",
        json={"name": "Whiteboard", "description": "Large board"},
        headers=admin,
    ).json()
    small = create_room(client, admin, capacity=5)
    large = create_room(client, admin, capacity=20)
    client.post(f"/rooms/{small['id']}/equipment/{equipment['id']}", headers=admin)
    client.post(f"/rooms/{large['id']}/equipment/{equipment['id']}", headers=admin)
    register_user(client)
    user = auth_headers(client)
    response = client.post(
        "/recommendations/slots",
        json={
            "window_start": "2026-06-03T09:00:00",
            "window_end": "2026-06-03T12:00:00",
            "duration_minutes": 60,
            "participants_count": 4,
            "required_equipment_ids": [equipment["id"]],
            "preferred_start": "2026-06-03T10:00:00",
        },
        headers=user,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data
    assert data[0]["room_id"] == small["id"]
    assert "score_reason" in data[0]
