from app.db.connection import get_connection
from fastapi.testclient import TestClient
from sqlalchemy import text


def test_add_video_returns_201_and_expected_payload(client: TestClient) -> None:
    response = client.post("/add_video", json={"video_id": "abc123"})

    assert response.status_code == 201
    assert response.json() == {
        "video_id": "abc123",
        "status": "pending",
        "assigned_to": None,
    }


def test_add_video_persists_video_and_audit_log(client: TestClient) -> None:
    response = client.post("/add_video", json={"video_id": "abc123"})

    assert response.status_code == 201

    with get_connection() as connection:
        video_row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "abc123"},
        ).mappings().one()

        log_row = connection.execute(
            text(
                """
                SELECT video_id, event_type, moderator_name, details
                FROM video_logs
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "abc123"},
        ).mappings().one()

    assert dict(video_row) == {
        "video_id": "abc123",
        "status": "pending",
        "assigned_to": None,
    }
    assert dict(log_row) == {
        "video_id": "abc123",
        "event_type": "pending",
        "moderator_name": None,
        "details": "Video added to moderation queue",
    }


def test_add_video_returns_409_when_video_already_exists(client: TestClient) -> None:
    first_response = client.post("/add_video", json={"video_id": "abc123"})
    second_response = client.post("/add_video", json={"video_id": "abc123"})

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Video already exists",
        "error_code": "video_already_exists",
    }


def test_add_video_returns_422_for_blank_video_id(client: TestClient) -> None:
    response = client.post("/add_video", json={"video_id": "   "})

    assert response.status_code == 422
