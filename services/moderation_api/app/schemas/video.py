from enum import Enum

from pydantic import BaseModel, Field, field_validator


class VideoStatus(str, Enum):
    pending = "pending"
    in_review = "in_review"
    spam = "spam"
    not_spam = "not_spam"

class ModerationDecision(str, Enum):
    spam = "spam"
    not_spam = "not spam"


class AddVideoRequest(BaseModel):
    video_id: str = Field(..., min_length=1, max_length=255)

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("video_id must not be blank")
        return cleaned_value

class FlagVideoRequest(BaseModel):
    video_id: str = Field(..., min_length=1, max_length=255)
    status: ModerationDecision

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("video_id must not be blank")
        return cleaned_value

class VideoResponse(BaseModel):
    video_id: str
    status: VideoStatus
    assigned_to: str | None = None

class FlagVideoResponse(BaseModel):
    video_id: str
    status: ModerationDecision

class StatsResponse(BaseModel):
    total_pending_videos: int
    total_spam_videos: int
    total_not_spam_videos: int

class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
