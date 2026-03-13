from app.db.connection import transaction
from app.db.repositories.video_repository import (
    assign_next_pending_video_atomically,
    flag_video_atomically,
    get_assigned_in_review_video_for_moderator,
    get_queue_stats,
    get_video_by_id,
    get_video_logs,
    insert_video,
    insert_video_log,
)
from app.schemas.video import (
    AddVideoRequest,
    FlagVideoRequest,
    FlagVideoResponse,
    ModerationDecision,
    StatsResponse,
    VideoLogEntryResponse,
    VideoResponse,
    VideoStatus,
)
from app.services.auth import decode_moderator_name
from app.services.errors import (
    InvalidAuthorizationHeaderError,
    MissingAuthorizationHeaderError,
    NoVideoAvailableError,
    VideoAlreadyExistsError,
    VideoAssignedToAnotherModeratorError,
    VideoNotFlaggableError,
    VideoNotFoundError,
)
from sqlalchemy.exc import IntegrityError


def _is_unique_violation(error: IntegrityError) -> bool:
    original_error = getattr(error, "orig", None)

    sqlstate = getattr(original_error, "sqlstate", None)
    if sqlstate == "23505":
        return True

    diag = getattr(original_error, "diag", None)
    if diag is not None and getattr(diag, "sqlstate", None) == "23505":
        return True

    return False


def add_video(payload: AddVideoRequest) -> VideoResponse:
    try:
        with transaction() as connection:
            inserted_video = insert_video(
                connection=connection,
                video_id=payload.video_id,
                status=VideoStatus.pending.value,
                assigned_to=None,
            )

            insert_video_log(
                connection=connection,
                video_id=payload.video_id,
                event_type=VideoStatus.pending.value,
                moderator_name=None,
                details="Video added to moderation queue",
            )

    except IntegrityError as error:
        if _is_unique_violation(error):
            raise VideoAlreadyExistsError from error
        raise

    return VideoResponse(
        video_id=inserted_video["video_id"],
        status=VideoStatus(inserted_video["status"]),
        assigned_to=inserted_video["assigned_to"],
    )

def get_video_for_moderator(authorization_header: str | None) -> VideoResponse:
    moderator_name = decode_moderator_name(authorization_header)

    with transaction() as connection:
        assigned_video = get_assigned_in_review_video_for_moderator(
            connection=connection,
            moderator_name=moderator_name,
        )
        if assigned_video is not None:
            return VideoResponse(
                video_id=assigned_video["video_id"],
                status=VideoStatus(assigned_video["status"]),
                assigned_to=assigned_video["assigned_to"],
            )

        next_video = assign_next_pending_video_atomically(
            connection=connection,
            moderator_name=moderator_name,
        )
        if next_video is None:
            raise NoVideoAvailableError

        insert_video_log(
            connection=connection,
            video_id=next_video["video_id"],
            event_type=VideoStatus.in_review.value,
            moderator_name=moderator_name,
            details="Video assigned to moderator",
        )

    return VideoResponse(
        video_id=next_video["video_id"],
        status=VideoStatus(next_video["status"]),
        assigned_to=next_video["assigned_to"],
    )

def _map_decision_to_db_status(decision: ModerationDecision) -> str:
    if decision == ModerationDecision.spam:
        return VideoStatus.spam.value
    return VideoStatus.not_spam.value


def flag_video_for_moderator(
    authorization_header: str | None,
    payload: FlagVideoRequest,
) -> FlagVideoResponse:
    moderator_name = decode_moderator_name(authorization_header)
    target_db_status = _map_decision_to_db_status(payload.status)

    with transaction() as connection:
        current_video = get_video_by_id(
            connection=connection,
            video_id=payload.video_id,
        )

        if current_video is None:
            raise VideoNotFoundError

        if current_video["status"] != VideoStatus.in_review.value:
            raise VideoNotFlaggableError

        if current_video["assigned_to"] != moderator_name:
            raise VideoAssignedToAnotherModeratorError

        flagged_video = flag_video_atomically(
            connection=connection,
            video_id=payload.video_id,
            moderator_name=moderator_name,
            target_status=target_db_status,
        )

        if flagged_video is None:
            raise VideoNotFlaggableError

        insert_video_log(
            connection=connection,
            video_id=payload.video_id,
            event_type=target_db_status,
            moderator_name=moderator_name,
            details="Video flagged by moderator",
        )

    return FlagVideoResponse(
        video_id=flagged_video["video_id"],
        status=payload.status,
    )

def get_stats() -> StatsResponse:
    with transaction() as connection:
        stats = get_queue_stats(connection=connection)

    return StatsResponse(
        total_pending_videos=stats["total_pending_videos"],
        total_spam_videos=stats["total_spam_videos"],
        total_not_spam_videos=stats["total_not_spam_videos"],
    )

def _map_log_event_type_to_api_status(event_type: str) -> str:
    if event_type == "not_spam":
        return "not spam"
    return event_type


def get_video_log(video_id: str) -> list[VideoLogEntryResponse]:
    with transaction() as connection:
        video = get_video_by_id(connection=connection, video_id=video_id)
        if video is None:
            raise VideoNotFoundError

        logs = get_video_logs(connection=connection, video_id=video_id)

    return [
        VideoLogEntryResponse(
            date=log["created_at"],
            status=_map_log_event_type_to_api_status(log["event_type"]),
            moderator=log["moderator_name"],
        )
        for log in logs
    ]
