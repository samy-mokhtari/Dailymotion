from app.cache.redis_client import get_cached_video_info, set_cached_video_info
from app.schemas.video import VideoInfoResponse
from app.services.errors import VideoNotFoundError


def _build_mock_video_info(video_id: str) -> VideoInfoResponse | None:
    if video_id.endswith("404"):
        return None

    return VideoInfoResponse(
        title="Dailymotion Spirit Movie",
        channel="creation",
        owner="Dailymotion",
        filmstrip_60_url=f"https://www.dailymotion.com/thumbnail/video/{video_id}",
        embed_url=f"https://www.dailymotion.com/embed/video/{video_id}",
    )


def get_video_info(video_id: str) -> VideoInfoResponse:
    cached_payload = get_cached_video_info(video_id)
    if cached_payload is not None:
        return VideoInfoResponse.model_validate(cached_payload)

    video_info = _build_mock_video_info(video_id)
    if video_info is None:
        raise VideoNotFoundError

    set_cached_video_info(video_id, video_info.model_dump())

    return video_info
