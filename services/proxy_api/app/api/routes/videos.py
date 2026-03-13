from app.schemas.video import ErrorResponse, VideoInfoResponse
from app.services.errors import VideoNotFoundError
from app.services.proxy_service import get_video_info
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["videos"])


@router.get(
    "/get_video_info/{video_id}",
    response_model=VideoInfoResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "The requested video does not exist.",
        },
    },
)
def get_video_info_endpoint(video_id: str):
    try:
        return get_video_info(video_id)
    except VideoNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "Video not found",
                "error_code": "video_not_found",
            },
        )
