"""Tests for administrative analytical reports."""

from fastapi.testclient import TestClient

from tests.conftest import admin_headers, auth_headers, create_room, register_user


def test_room_utilization_report_requires_admin(client: TestClient) -> None:
    """Regular users cannot read administrative utilization reports."""

    register_user(client)
    headers = auth_headers(client)
    response = client.get(
        "/reports/room-utilization",
        params={
            "period_start": "2026-06-01T09:00:00",
            "period_end": "2026-06-01T12:00:00",
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_room_utilization_report_counts_booked_minutes(client: TestClient) -> None:
    """Report calculates booked and available minutes for every room."""

    admin = admin_headers(client)
    room = create_room(client, admin, capacity=8)
    register_user(client)
    user = auth_headers(client)
    client.post(
        "/bookings",
        json={
            "room_id": room["id"],
            "title": "Daily meeting",
            "start_at": "2026-06-01T10:00:00",
            "end_at": "2026-06-01T11:00:00",
            "participants_count": 4,
        },
        headers=user,
    )
    response = client.get(
        "/reports/room-utilization",
        params={
            "period_start": "2026-06-01T09:00:00",
            "period_end": "2026-06-01T12:00:00",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["rooms"][0]["booked_minutes"] == 60
    assert report["rooms"][0]["available_minutes"] == 120
    assert report["rooms"][0]["utilization_percent"] == 33.33
