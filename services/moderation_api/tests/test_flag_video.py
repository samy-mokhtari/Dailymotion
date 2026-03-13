import base64
from datetime import datetime, timezone

from app.db.connection import get_connection, transaction
from app.schemas.video import VideoStatus
from fastapi.testclient import TestClient
from sqlalchemy import text


def _authorization_header(moderator_name: str) -> dict[str, str]:
    encoded_value = base64.b64encode(moderator_name.encode("utf-8")).decode("utf-8")
    return {"Authorization": encoded_value}


def _seed_video_with_timestamps(
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


def test_flag_video_returns_200_and_updates_video_to_spam(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-001",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-001", "status": "spam"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "video-flag-001",
        "status": "spam",
    }

    with get_connection() as connection:
        video_row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to, created_at, updated_at
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "video-flag-001"},
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
                "video_id": "video-flag-001",
                "event_type": "spam",
            },
        ).mappings().one()

    assert dict(video_row)["video_id"] == "video-flag-001"
    assert dict(video_row)["status"] == "spam"
    assert dict(video_row)["assigned_to"] == "john.doe"
    assert dict(video_row)["updated_at"] > dict(video_row)["created_at"]

    assert dict(log_row) == {
        "video_id": "video-flag-001",
        "event_type": "spam",
        "moderator_name": "john.doe",
        "details": "Video flagged by moderator",
    }


def test_flag_video_returns_200_and_updates_video_to_not_spam(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-002",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-002", "status": "not spam"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "video-flag-002",
        "status": "not spam",
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
            {"video_id": "video-flag-002"},
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
                "video_id": "video-flag-002",
                "event_type": "not_spam",
            },
        ).mappings().one()

    assert dict(video_row) == {
        "video_id": "video-flag-002",
        "status": "not_spam",
        "assigned_to": "john.doe",
    }
    assert dict(log_row) == {
        "video_id": "video-flag-002",
        "event_type": "not_spam",
        "moderator_name": "john.doe",
        "details": "Video flagged by moderator",
    }


def test_flag_video_returns_422_for_invalid_status(client: TestClient) -> None:
    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-003", "status": "maybe"},
    )

    assert response.status_code == 422


def test_flag_video_returns_404_when_video_does_not_exist(client: TestClient) -> None:
    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "missing-video", "status": "spam"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Video not found",
        "error_code": "video_not_found",
    }


def test_flag_video_returns_409_when_video_is_already_finalized(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-004",
        status=VideoStatus.spam,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-004", "status": "spam"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Video cannot be flagged in its current state",
        "error_code": "video_not_flaggable",
    }


def test_flag_video_returns_403_when_video_is_assigned_to_another_moderator(
    client: TestClient,
) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-005",
        status=VideoStatus.in_review,
        assigned_to="jane.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-005", "status": "spam"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Video is assigned to another moderator",
        "error_code": "video_assigned_to_another_moderator",
    }


def test_flag_video_returns_401_when_authorization_header_is_missing(
    client: TestClient,
) -> None:
    response = client.post(
        "/flag_video",
        json={"video_id": "video-flag-006", "status": "spam"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Missing Authorization header",
        "error_code": "missing_authorization_header",
    }


def test_flag_video_returns_400_when_authorization_header_is_invalid(
    client: TestClient,
) -> None:
    response = client.post(
        "/flag_video",
        headers={"Authorization": "not-base64"},
        json={"video_id": "video-flag-007", "status": "spam"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid Authorization header",
        "error_code": "invalid_authorization_header",
    }


def test_flag_video_returns_409_when_video_is_pending(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-008",
        status=VideoStatus.pending,
        assigned_to=None,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-008", "status": "spam"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Video cannot be flagged in its current state",
        "error_code": "video_not_flaggable",
    }

def test_flag_video_keeps_assigned_to_after_flagging(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-009",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-009", "status": "spam"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        video_row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "video-flag-009"},
        ).mappings().one()

    assert dict(video_row) == {
        "video_id": "video-flag-009",
        "status": "spam",
        "assigned_to": "john.doe",
    }

def test_flag_video_keeps_assigned_to_after_not_spam_flagging(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="video-flag-010",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    response = client.post(
        "/flag_video",
        headers=_authorization_header("john.doe"),
        json={"video_id": "video-flag-010", "status": "not spam"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        video_row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "video-flag-010"},
        ).mappings().one()

    assert dict(video_row) == {
        "video_id": "video-flag-010",
        "status": "not_spam",
        "assigned_to": "john.doe",
    }
