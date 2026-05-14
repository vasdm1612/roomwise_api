"""Tests for room and equipment CRUD."""

from fastapi.testclient import TestClient

from tests.conftest import admin_headers, auth_headers, register_user


def test_admin_can_create_room_and_equipment(client: TestClient) -> None:
    """Admin can create equipment, a room and attach equipment to it."""

    headers = admin_headers(client)
    equipment = client.post(
        "/equipment",
        json={"name": "Projector", "description": "HDMI projector"},
        headers=headers,
    )
    assert equipment.status_code == 201
    room = client.post(
        "/rooms",
        json={"name": "Blue", "floor": 1, "capacity": 10, "is_active": True},
        headers=headers,
    )
    assert room.status_code == 201
    attach = client.post(
        f"/rooms/{room.json()['id']}/equipment/{equipment.json()['id']}", headers=headers
    )
    assert attach.status_code == 200
    assert attach.json()["equipment"][0]["name"] == "Projector"


def test_regular_user_cannot_create_room(client: TestClient) -> None:
    """Non-admin user cannot access admin-only room creation."""

    register_user(client)
    headers = auth_headers(client)
    response = client.post(
        "/rooms",
        json={"name": "Small", "floor": 1, "capacity": 4, "is_active": True},
        headers=headers,
    )
    assert response.status_code == 403


def test_room_filters_and_update(client: TestClient) -> None:
    """Room list filters and PATCH endpoint work."""

    headers = admin_headers(client)
    client.post(
        "/rooms",
        json={"name": "Small", "floor": 1, "capacity": 4, "is_active": True},
        headers=headers,
    )
    room = client.post(
        "/rooms",
        json={"name": "Large", "floor": 3, "capacity": 20, "is_active": True},
        headers=headers,
    ).json()
    response = client.get("/rooms?min_capacity=10")
    assert response.status_code == 200
    assert len(response.json()) == 1
    patch = client.patch(f"/rooms/{room['id']}", json={"capacity": 25}, headers=headers)
    assert patch.status_code == 200
    assert patch.json()["capacity"] == 25


def test_admin_can_update_detach_and_delete_equipment(client: TestClient) -> None:
    """Admin can maintain equipment records and room-equipment links."""

    headers = admin_headers(client)
    equipment = client.post(
        "/equipment",
        json={"name": "Screen", "description": "Wall screen"},
        headers=headers,
    ).json()
    room = client.post(
        "/rooms",
        json={"name": "Green", "floor": 1, "capacity": 6, "is_active": True},
        headers=headers,
    ).json()
    update = client.patch(
        f"/equipment/{equipment['id']}",
        json={"description": "Portable screen"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["description"] == "Portable screen"
    client.post(f"/rooms/{room['id']}/equipment/{equipment['id']}", headers=headers)
    detach = client.delete(f"/rooms/{room['id']}/equipment/{equipment['id']}", headers=headers)
    assert detach.status_code == 200
    delete = client.delete(f"/equipment/{equipment['id']}", headers=headers)
    assert delete.status_code == 204
