from typing import Annotated

from app.schemas.video import AddVideoRequest, ErrorResponse, VideoResponse
from app.services.errors import (
    InvalidAuthorizationHeaderError,
    MissingAuthorizationHeaderError,
    NoVideoAvailableError,
    VideoAlreadyExistsError,
)
from app.services.video_service import add_video, get_video_for_moderator
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
