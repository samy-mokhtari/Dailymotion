from typing import Annotated

from app.schemas.video import (
    AddVideoRequest,
    ErrorResponse,
    FlagVideoRequest,
    FlagVideoResponse,
    StatsResponse,
    VideoLogEntryResponse,
    VideoResponse,
)
from app.services.errors import (
    InvalidAuthorizationHeaderError,
    MissingAuthorizationHeaderError,
    NoVideoAvailableError,
    VideoAlreadyExistsError,
    VideoAssignedToAnotherModeratorError,
    VideoNotFlaggableError,
    VideoNotFoundError,
)
from app.services.video_service import (
    add_video,
    flag_video_for_moderator,
    get_stats,
    get_video_for_moderator,
    get_video_log,
)
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["videos"])


@router.post(
    "/add_video",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "The video already exists in the moderation queue.",
        }
    },
)
def add_video_endpoint(payload: AddVideoRequest) -> VideoResponse | JSONResponse:
    try:
        return add_video(payload)
    except VideoAlreadyExistsError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Video already exists",
                "error_code": "video_already_exists",
            },
        )

@router.get(
    "/get_video",
    response_model=VideoResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The Authorization header is invalid.",
        },
        401: {
            "model": ErrorResponse,
            "description": "The Authorization header is missing.",
        },
        404: {
            "model": ErrorResponse,
            "description": "No video is currently available for moderation.",
        },
    },
)
def get_video_endpoint(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> VideoResponse | JSONResponse:
    try:
        return get_video_for_moderator(authorization)
    except MissingAuthorizationHeaderError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Missing Authorization header",
                "error_code": "missing_authorization_header",
            },
        )
    except InvalidAuthorizationHeaderError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid Authorization header",
                "error_code": "invalid_authorization_header",
            },
        )
    except NoVideoAvailableError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "No video available",
                "error_code": "no_video_available",
            },
        )

@router.post(
    "/flag_video",
    response_model=FlagVideoResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The Authorization header is invalid.",
        },
        401: {
            "model": ErrorResponse,
            "description": "The Authorization header is missing.",
        },
        403: {
            "model": ErrorResponse,
            "description": "The video is assigned to another moderator.",
        },
        404: {
            "model": ErrorResponse,
            "description": "The requested video does not exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": "The video cannot be flagged in its current state.",
        },
    },
)
def flag_video_endpoint(
    payload: FlagVideoRequest,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> FlagVideoResponse | JSONResponse:
    try:
        return flag_video_for_moderator(authorization, payload)
    except MissingAuthorizationHeaderError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Missing Authorization header",
                "error_code": "missing_authorization_header",
            },
        )
    except InvalidAuthorizationHeaderError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid Authorization header",
                "error_code": "invalid_authorization_header",
            },
        )
    except VideoAssignedToAnotherModeratorError:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Video is assigned to another moderator",
                "error_code": "video_assigned_to_another_moderator",
            },
        )
    except VideoNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "Video not found",
                "error_code": "video_not_found",
            },
        )
    except VideoNotFlaggableError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Video cannot be flagged in its current state",
                "error_code": "video_not_flaggable",
            },
        )

@router.get("/stats")
def get_stats_endpoint() -> StatsResponse:
    return get_stats()

@router.get(
    "/log_video/{video_id}",
    response_model=list[VideoLogEntryResponse],
    responses={
        404: {
            "model": ErrorResponse,
            "description": "The requested video does not exist.",
        },
    },
)
def get_video_log_endpoint(video_id: str) -> list[VideoLogEntryResponse] | JSONResponse:
    try:
        return get_video_log(video_id)
    except VideoNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "Video not found",
                "error_code": "video_not_found",
            },
        )
