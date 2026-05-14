"""Tests for booking logic."""

from fastapi.testclient import TestClient

from tests.conftest import admin_headers, auth_headers, create_room, register_user


def test_booking_creation_and_conflict(client: TestClient) -> None:
    """A room cannot be double-booked for overlapping time intervals."""

    admin = admin_headers(client)
    room = create_room(client, admin, capacity=8)
    register_user(client)
    user = auth_headers(client)
    payload = {
        "room_id": room["id"],
        "title": "Planning",
        "start_at": "2026-06-01T10:00:00",
        "end_at": "2026-06-01T11:00:00",
        "participants_count": 5,
    }
    created = client.post("/bookings", json=payload, headers=user)
    assert created.status_code == 201
    conflict = client.post(
        "/bookings",
        json={**payload, "title": "Overlapping", "start_at": "2026-06-01T10:30:00"},
        headers=user,
    )
    assert conflict.status_code == 409


def test_capacity_validation(client: TestClient) -> None:
    """Booking participants must fit room capacity."""

    admin = admin_headers(client)
    room = create_room(client, admin, capacity=4)
    register_user(client)
    user = auth_headers(client)
    response = client.post(
        "/bookings",
        json={
            "room_id": room["id"],
            "title": "Too many people",
            "start_at": "2026-06-01T12:00:00",
            "end_at": "2026-06-01T13:00:00",
            "participants_count": 8,
        },
        headers=user,
    )
    assert response.status_code == 409


def test_user_cannot_read_other_user_booking(client: TestClient) -> None:
    """Users can access only their own bookings."""

    admin = admin_headers(client)
    room = create_room(client, admin, capacity=8)
    register_user(client, email="one@example.com")
    one = auth_headers(client, email="one@example.com")
    booking = client.post(
        "/bookings",
        json={
            "room_id": room["id"],
            "title": "Private",
            "start_at": "2026-06-02T10:00:00",
            "end_at": "2026-06-02T11:00:00",
            "participants_count": 3,
        },
        headers=one,
    ).json()
    register_user(client, email="two@example.com")
    two = auth_headers(client, email="two@example.com")
    response = client.get(f"/bookings/{booking['id']}", headers=two)
    assert response.status_code == 403


def test_user_can_update_cancel_and_delete_own_booking(client: TestClient) -> None:
    """Users can update, cancel and delete their own bookings."""

    admin = admin_headers(client)
    room = create_room(client, admin, capacity=10)
    register_user(client)
    user = auth_headers(client)
    booking = client.post(
        "/bookings",
        json={
            "room_id": room["id"],
            "title": "Initial meeting",
            "start_at": "2026-06-05T10:00:00",
            "end_at": "2026-06-05T11:00:00",
            "participants_count": 4,
        },
        headers=user,
    ).json()
    patch = client.patch(
        f"/bookings/{booking['id']}",
        json={"title": "Updated meeting", "status": "cancelled"},
        headers=user,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["status"] == "cancelled"
    delete = client.delete(f"/bookings/{booking['id']}", headers=user)
    assert delete.status_code == 204
    missing = client.get(f"/bookings/{booking['id']}", headers=user)
    assert missing.status_code == 404
