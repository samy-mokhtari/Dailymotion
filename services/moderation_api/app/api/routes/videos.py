from app.schemas.video import AddVideoRequest, ErrorResponse, VideoResponse
from app.services.video_service import VideoAlreadyExistsError, add_video
from fastapi import APIRouter, status
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
