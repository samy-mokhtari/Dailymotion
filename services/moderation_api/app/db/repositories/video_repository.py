from collections.abc import Mapping
from typing import Any

from app.db.rows import QueueStatsRow, VideoLogRow, VideoRow
from sqlalchemy import text
from sqlalchemy.engine import Connection, RowMapping


def _to_video_row(row: RowMapping) -> VideoRow:
    return VideoRow(
        video_id=str(row["video_id"]),
        status=str(row["status"]),
        assigned_to=row["assigned_to"],
    )


def _to_video_log_row(row: RowMapping) -> VideoLogRow:
    return VideoLogRow(
        created_at=row["created_at"],
        event_type=str(row["event_type"]),
        moderator_name=row["moderator_name"],
    )


def _to_queue_stats_row(row: RowMapping) -> QueueStatsRow:
    return QueueStatsRow(
        total_pending_videos=int(row["total_pending_videos"]),
        total_spam_videos=int(row["total_spam_videos"]),
        total_not_spam_videos=int(row["total_not_spam_videos"]),
    )

def insert_video(
    connection: Connection,
    video_id: str,
    status: str,
    assigned_to: str | None = None,
) -> VideoRow:
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
    ).mappings().one()

    return _to_video_row(result)


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
) -> VideoRow | None:
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

    return _to_video_row(result)

def assign_next_pending_video_atomically(
    connection: Connection,
    moderator_name: str,
) -> VideoRow | None:
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

    return _to_video_row(result)

def get_video_by_id(
    connection: Connection,
    video_id: str,
) -> VideoRow | None:
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

    return _to_video_row(result)


def flag_video_atomically(
    connection: Connection,
    video_id: str,
    moderator_name: str,
    target_status: str,
) -> VideoRow | None:
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

    return _to_video_row(result)

def get_queue_stats(connection: Connection) -> QueueStatsRow:
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

    return _to_queue_stats_row(result)

def get_video_logs(
    connection: Connection,
    video_id: str,
) -> list[VideoLogRow]:
    query = text(
        """
        SELECT created_at, event_type, moderator_name
        FROM video_logs
        WHERE video_id = :video_id
        ORDER BY created_at ASC, id ASC
        """
    )

    results = connection.execute(
        query,
        {"video_id": video_id},
    ).mappings().all()

    return [_to_video_log_row(row) for row in results]
