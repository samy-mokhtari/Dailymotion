from app.db.connection import transaction
from app.db.repositories.video_repository import insert_video, insert_video_log
from app.schemas.video import AddVideoRequest, VideoResponse, VideoStatus
from app.services.errors import VideoAlreadyExistsError
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
