import pytest
from app.db.connection import transaction
from app.db.repositories.video_repository import flag_video_atomically, get_video_by_id
from app.schemas.video import (
    AddVideoRequest,
    FlagVideoRequest,
    ModerationDecision,
    VideoStatus,
)
from pydantic import ValidationError
from tests.test_video_repository import _seed_video


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

def test_flag_video_request_accepts_spam_status() -> None:
    payload = FlagVideoRequest(
        video_id="abc123",
        status=ModerationDecision.spam,
    )

    assert payload.video_id == "abc123"
    assert payload.status == ModerationDecision.spam


def test_flag_video_request_accepts_not_spam_status() -> None:
    payload = FlagVideoRequest(
        video_id="abc123",
        status=ModerationDecision.not_spam,
    )

    assert payload.video_id == "abc123"
    assert payload.status == ModerationDecision.not_spam


def test_flag_video_request_accepts_string_spam_status_via_model_validate() -> None:
    payload = FlagVideoRequest.model_validate(
        {"video_id": "abc123", "status": "spam"}
    )

    assert payload.status == ModerationDecision.spam


def test_flag_video_request_accepts_string_not_spam_status_via_model_validate() -> None:
    payload = FlagVideoRequest.model_validate(
        {"video_id": "abc123", "status": "not spam"}
    )

    assert payload.status == ModerationDecision.not_spam


def test_flag_video_request_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        FlagVideoRequest.model_validate({"video_id": "abc123", "status": "maybe"})


def test_flag_video_request_rejects_blank_video_id() -> None:
    with pytest.raises(ValidationError):
        FlagVideoRequest.model_validate({"video_id": "   ", "status": "spam"})

def test_get_video_by_id_returns_video_when_it_exists() -> None:
    _seed_video(
        video_id="video-flag-001",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
    )

    with transaction() as connection:
        result = get_video_by_id(connection=connection, video_id="video-flag-001")

    assert result == {
        "video_id": "video-flag-001",
        "status": "in_review",
        "assigned_to": "john.doe",
    }


def test_get_video_by_id_returns_none_when_video_does_not_exist() -> None:
    with transaction() as connection:
        result = get_video_by_id(connection=connection, video_id="missing-video")

    assert result is None


def test_flag_video_atomically_updates_video_for_assigned_moderator() -> None:
    _seed_video(
        video_id="video-flag-010",
        status=VideoStatus.in_review,
        assigned_to="john.doe",
    )

    with transaction() as connection:
        result = flag_video_atomically(
            connection=connection,
            video_id="video-flag-010",
            moderator_name="john.doe",
            target_status="spam",
        )

    assert result == {
        "video_id": "video-flag-010",
        "status": "spam",
        "assigned_to": "john.doe",
    }


def test_flag_video_atomically_returns_none_when_video_is_not_in_review() -> None:
    _seed_video(
        video_id="video-flag-020",
        status=VideoStatus.pending,
        assigned_to=None,
    )

    with transaction() as connection:
        result = flag_video_atomically(
            connection=connection,
            video_id="video-flag-020",
            moderator_name="john.doe",
            target_status="spam",
        )

    assert result is None


def test_flag_video_atomically_returns_none_when_video_is_assigned_to_other_moderator() -> None:
    _seed_video(
        video_id="video-flag-030",
        status=VideoStatus.in_review,
        assigned_to="jane.doe",
    )

    with transaction() as connection:
        result = flag_video_atomically(
            connection=connection,
            video_id="video-flag-030",
            moderator_name="john.doe",
            target_status="spam",
        )

    assert result is None
