import base64
from datetime import datetime, timezone

from app.db.connection import get_connection, transaction
from app.schemas.video import VideoStatus
from fastapi.testclient import TestClient
from sqlalchemy import text


def _authorization_header(moderator_name: str) -> dict[str, str]:
    encoded_value = base64.b64encode(moderator_name.encode("utf-8")).decode("utf-8")
    return {"Authorization": encoded_value}


def _seed_video_with_created_at(
    *,
    video_id: str,
    status: VideoStatus,
    created_at: datetime,
    assigned_to: str | None = None,
) -> None:
    with transaction() as connection:
        connection.execute(
            text(
                """
                INSERT INTO videos (
                    video_id,
                    status,
                    assigned_to,
                    created_at,
                    updated_at
                )
                VALUES (
                    :video_id,
                    :status,
                    :assigned_to,
                    :created_at,
                    :created_at
                )
                """
            ),
            {
                "video_id": video_id,
                "status": status.value,
                "assigned_to": assigned_to,
                "created_at": created_at,
            },
        )


def test_get_video_returns_same_video_for_same_moderator(client: TestClient) -> None:
    _seed_video_with_created_at(
        video_id="video-001",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    headers = _authorization_header("john.doe")

    first_response = client.get("/get_video", headers=headers)
    second_response = client.get("/get_video", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == {
        "video_id": "video-001",
        "status": "in_review",
        "assigned_to": "john.doe",
    }
    assert second_response.json() == {
        "video_id": "video-001",
        "status": "in_review",
        "assigned_to": "john.doe",
    }

    with get_connection() as connection:
        log_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM video_logs
                WHERE video_id = :video_id
                    AND event_type = :event_type
                    AND moderator_name = :moderator_name
                """
            ),
            {
                "video_id": "video-001",
                "event_type": "in_review",
                "moderator_name": "john.doe",
            },
        ).scalar_one()

    assert log_count == 1


def test_get_video_returns_different_videos_for_different_moderators(client: TestClient) -> None:
    _seed_video_with_created_at(
        video_id="video-100",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_created_at(
        video_id="video-200",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )

    first_response = client.get("/get_video", headers=_authorization_header("john.doe"))
    second_response = client.get("/get_video", headers=_authorization_header("jane.doe"))

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == {
        "video_id": "video-100",
        "status": "in_review",
        "assigned_to": "john.doe",
    }
    assert second_response.json() == {
        "video_id": "video-200",
        "status": "in_review",
        "assigned_to": "jane.doe",
    }


def test_get_video_respects_fifo_order(client: TestClient) -> None:
    _seed_video_with_created_at(
        video_id="video-oldest",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_created_at(
        video_id="video-newest",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get("/get_video", headers=_authorization_header("john.doe"))

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "video-oldest",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_get_video_returns_401_when_authorization_header_is_missing(client: TestClient) -> None:
    response = client.get("/get_video")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Missing Authorization header",
        "error_code": "missing_authorization_header",
    }


def test_get_video_returns_400_when_authorization_header_is_invalid(client: TestClient) -> None:
    response = client.get("/get_video", headers={"Authorization": "not-base64"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid Authorization header",
        "error_code": "invalid_authorization_header",
    }


def test_get_video_returns_400_when_decoded_moderator_name_is_blank(client: TestClient) -> None:
    response = client.get("/get_video", headers=_authorization_header("   "))

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid Authorization header",
        "error_code": "invalid_authorization_header",
    }


def test_get_video_returns_404_when_no_video_is_available(client: TestClient) -> None:
    response = client.get("/get_video", headers=_authorization_header("john.doe"))

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No video available",
        "error_code": "no_video_available",
    }


def test_get_video_updates_database_and_creates_assignment_log(client: TestClient) -> None:
    _seed_video_with_created_at(
        video_id="video-500",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get("/get_video", headers=_authorization_header("john.doe"))

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "video-500",
        "status": "in_review",
        "assigned_to": "john.doe",
    }

    with get_connection() as connection:
        video_row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "video-500"},
        ).mappings().one()

        log_row = connection.execute(
            text(
                """
                SELECT video_id, event_type, moderator_name, details
                FROM video_logs
                WHERE video_id = :video_id
                    AND event_type = :event_type
                """
            ),
            {
                "video_id": "video-500",
                "event_type": "in_review",
            },
        ).mappings().one()

    assert dict(video_row) == {
        "video_id": "video-500",
        "status": "in_review",
        "assigned_to": "john.doe",
    }
    assert dict(log_row) == {
        "video_id": "video-500",
        "event_type": "in_review",
        "moderator_name": "john.doe",
        "details": "Video assigned to moderator",
    }
