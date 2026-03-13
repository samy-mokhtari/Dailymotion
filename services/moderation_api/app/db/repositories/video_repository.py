from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


def insert_video(
    connection: Connection,
    video_id: str,
    status: str,
    assigned_to: str | None = None,
) -> Mapping[str, Any]:
    query = text(
        """
        INSERT INTO videos (video_id, status, assigned_to, updated_at)
        VALUES (:video_id, :status, :assigned_to, CURRENT_TIMESTAMP)
        RETURNING video_id, status, assigned_to
        """
    )

    result = connection.execute(
        query,
        {
            "video_id": video_id,
            "status": status,
            "assigned_to": assigned_to,
        },
    )

    return dict(result.mappings().one())


def insert_video_log(
    connection: Connection,
    video_id: str,
    event_type: str,
    moderator_name: str | None = None,
    details: str | None = None,
) -> None:
    query = text(
        """
        INSERT INTO video_logs (video_id, event_type, moderator_name, details)
        VALUES (:video_id, :event_type, :moderator_name, :details)
        """
    )

    connection.execute(
        query,
        {
            "video_id": video_id,
            "event_type": event_type,
            "moderator_name": moderator_name,
            "details": details,
        },
    )

def get_assigned_in_review_video_for_moderator(
    connection: Connection,
    moderator_name: str,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT video_id, status, assigned_to
        FROM videos
        WHERE status = :status
            AND assigned_to = :moderator_name
        ORDER BY created_at ASC
        LIMIT 1
        """
    )

    result = connection.execute(
        query,
        {
            "status": "in_review",
            "moderator_name": moderator_name,
        },
    ).mappings().first()

    if result is None:
        return None

    return dict(result)

def assign_next_pending_video_atomically(
    connection: Connection,
    moderator_name: str,
) -> dict[str, Any] | None:
    query = text(
        """
        WITH next_video AS (
            SELECT id
            FROM videos
            WHERE status = :pending_status
                AND assigned_to IS NULL
            ORDER BY created_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        UPDATE videos
        SET status = :in_review_status,
            assigned_to = :moderator_name,
            updated_at = CURRENT_TIMESTAMP
        WHERE id IN (SELECT id FROM next_video)
        RETURNING video_id, status, assigned_to
        """
    )

    result = connection.execute(
        query,
        {
            "pending_status": "pending",
            "in_review_status": "in_review",
            "moderator_name": moderator_name,
        },
    ).mappings().first()

    if result is None:
        return None

    return dict(result)

def get_video_by_id(
    connection: Connection,
    video_id: str,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT video_id, status, assigned_to
        FROM videos
        WHERE video_id = :video_id
        """
    )

    result = connection.execute(
        query,
        {"video_id": video_id},
    ).mappings().first()

    if result is None:
        return None

    return dict(result)


def flag_video_atomically(
    connection: Connection,
    video_id: str,
    moderator_name: str,
    target_status: str,
) -> dict[str, Any] | None:
    query = text(
        """
        UPDATE videos
        SET status = :target_status,
            updated_at = CURRENT_TIMESTAMP
        WHERE video_id = :video_id
            AND status = :in_review_status
            AND assigned_to = :moderator_name
        RETURNING video_id, status, assigned_to
        """
    )

    result = connection.execute(
        query,
        {
            "video_id": video_id,
            "moderator_name": moderator_name,
            "target_status": target_status,
            "in_review_status": "in_review",
        },
    ).mappings().first()

    if result is None:
        return None

    return dict(result)

def get_queue_stats(connection: Connection) -> dict[str, int]:
    query = text(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') AS total_pending_videos,
            COUNT(*) FILTER (WHERE status = 'spam') AS total_spam_videos,
            COUNT(*) FILTER (WHERE status = 'not_spam') AS total_not_spam_videos
        FROM videos
        """
    )

    result = connection.execute(query).mappings().one()

    return {
        "total_pending_videos": int(result["total_pending_videos"]),
        "total_spam_videos": int(result["total_spam_videos"]),
        "total_not_spam_videos": int(result["total_not_spam_videos"]),
    }
