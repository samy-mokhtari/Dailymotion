from datetime import datetime, timezone

from app.db.connection import transaction
from app.schemas.video import VideoStatus
from fastapi.testclient import TestClient
from sqlalchemy import text


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


def test_stats_returns_zeroes_when_no_video_exists(client: TestClient) -> None:
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_pending_videos": 0,
        "total_spam_videos": 0,
        "total_not_spam_videos": 0,
    }


def test_stats_returns_expected_counts(client: TestClient) -> None:
    _seed_video_with_timestamps(
        video_id="stats-001",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_timestamps(
        video_id="stats-002",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_timestamps(
        video_id="stats-003",
        status=VideoStatus.spam,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_timestamps(
        video_id="stats-004",
        status=VideoStatus.not_spam,
        assigned_to="john.doe",
        created_at=datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_timestamps(
        video_id="stats-005",
        status=VideoStatus.in_review,
        assigned_to="jane.doe",
        created_at=datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
    )

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_pending_videos": 2,
        "total_spam_videos": 1,
        "total_not_spam_videos": 1,
    }
