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
