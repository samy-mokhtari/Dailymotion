from dataclasses import asdict
from datetime import datetime, timezone

from app.db.connection import get_connection, transaction
from app.db.repositories.video_repository import (
    assign_next_pending_video_atomically,
    get_assigned_in_review_video_for_moderator,
    insert_video,
)
from app.schemas.video import VideoStatus
from sqlalchemy import text
from sqlalchemy.engine import RowMapping


def _seed_video(
    *,
    video_id: str,
    status: VideoStatus,
    assigned_to: str | None = None,
) -> None:
    with transaction() as connection:
        insert_video(
            connection=connection,
            video_id=video_id,
            status=status.value,
            assigned_to=assigned_to,
        )

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

def test_get_assigned_in_review_video_for_moderator_returns_matching_video() -> None:
    _seed_video(
        video_id="video-001",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
    )

    with transaction() as connection:
        result = get_assigned_in_review_video_for_moderator(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is not None
    assert asdict(result) == {
        "video_id": "video-001",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_get_assigned_in_review_video_for_moderator_returns_none_when_no_match() -> None:
    with transaction() as connection:
        result = get_assigned_in_review_video_for_moderator(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is None


def test_get_assigned_in_review_video_for_moderator_ignores_pending_videos() -> None:
    _seed_video(
        video_id="video-002",
        status=VideoStatus.pending,
        assigned_to=None,
    )

    with transaction() as connection:
        result = get_assigned_in_review_video_for_moderator(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is None


def test_get_assigned_in_review_video_for_moderator_ignores_other_moderator_video() -> None:
    _seed_video(
        video_id="video-003",
        status=VideoStatus.in_review,
        assigned_to="jane.doe",
    )

    with transaction() as connection:
        result = get_assigned_in_review_video_for_moderator(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is None

def test_assign_next_pending_video_atomically_returns_oldest_pending_video() -> None:
    _seed_video_with_created_at(
        video_id="video-oldest",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_created_at(
        video_id="video-newest",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )

    with transaction() as connection:
        result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is not None
    assert asdict(result) == {
        "video_id": "video-oldest",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_assign_next_pending_video_atomically_updates_video_state_in_database() -> None:
    _seed_video(
        video_id="video-010",
        status=VideoStatus.pending,
    )

    with transaction() as connection:
        result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is not None
    assert asdict(result) == {
        "video_id": "video-010",
        "status": "in_review",
        "assigned_to": "john.doe",
    }

    with get_connection() as connection:
        row = connection.execute(
            text(
                """
                SELECT video_id, status, assigned_to
                FROM videos
                WHERE video_id = :video_id
                """
            ),
            {"video_id": "video-010"},
        ).mappings().one()

    assert dict(row) == {
        "video_id": "video-010",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_assign_next_pending_video_atomically_returns_none_when_no_pending_video_exists() -> None:
    with transaction() as connection:
        result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is None


def test_assign_next_pending_video_atomically_ignores_already_in_review_videos() -> None:
    _seed_video_with_created_at(
        video_id="video-in-review",
        status=VideoStatus.in_review,
        assigned_to="jane.doe",
        created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    _seed_video_with_created_at(
        video_id="video-pending",
        status=VideoStatus.pending,
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )

    with transaction() as connection:
        result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="john.doe",
        )

    assert result is not None
    assert asdict(result) == {
        "video_id": "video-pending",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_assign_next_pending_video_atomically_does_not_reassign_same_video_on_second_call() -> None:
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

    with transaction() as connection:
        first_result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="john.doe",
        )

    with transaction() as connection:
        second_result = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name="jane.doe",
        )

    assert first_result is not None
    assert asdict(first_result) == {
        "video_id": "video-100",
        "status": "in_review",
        "assigned_to": "john.doe",
    }

    assert second_result is not None
    assert asdict(second_result) == {
        "video_id": "video-200",
        "status": "in_review",
        "assigned_to": "jane.doe",
    }
