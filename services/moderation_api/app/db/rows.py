from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VideoRow:
    video_id: str
    status: str
    assigned_to: str | None


@dataclass(frozen=True)
class VideoLogRow:
    created_at: datetime
    event_type: str
    moderator_name: str | None


@dataclass(frozen=True)
class QueueStatsRow:
    total_pending_videos: int
    total_spam_videos: int
    total_not_spam_videos: int
