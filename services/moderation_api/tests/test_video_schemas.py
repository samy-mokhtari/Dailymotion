import pytest
from app.schemas.video import AddVideoRequest, VideoStatus
from pydantic import ValidationError


def test_add_video_request_accepts_valid_video_id() -> None:
    payload = AddVideoRequest(video_id="abc123")

    assert payload.video_id == "abc123"


def test_add_video_request_strips_video_id() -> None:
    payload = AddVideoRequest(video_id="  abc123  ")

    assert payload.video_id == "abc123"


def test_add_video_request_rejects_blank_video_id() -> None:
    with pytest.raises(ValidationError):
        AddVideoRequest(video_id="   ")


def test_video_status_pending_value() -> None:
    assert VideoStatus.pending.value == "pending"
