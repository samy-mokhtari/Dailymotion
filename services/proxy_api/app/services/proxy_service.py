from app.cache.redis_client import get_cached_video_info, set_cached_video_info
from app.schemas.video import VideoInfoResponse
from app.services.errors import VideoNotFoundError


def _is_video_not_found(video_id: str) -> bool:
    return video_id.endswith("404")


def _build_mock_video_info(video_id: str) -> dict[str, str]:
    return {
        "title": "Dailymotion Spirit Movie",
        "channel": "creation",
        "owner": "Dailymotion",
        "filmstrip_60_url": f"https://www.dailymotion.com/thumbnail/video/{video_id}",
        "embed_url": f"https://www.dailymotion.com/embed/video/{video_id}",
    }


def get_video_info(video_id: str) -> VideoInfoResponse:
    if _is_video_not_found(video_id):
        raise VideoNotFoundError

    cached_payload = get_cached_video_info(video_id)
    if cached_payload is not None:
        return VideoInfoResponse.model_validate(cached_payload)

    payload = _build_mock_video_info(video_id)
    set_cached_video_info(video_id, payload)

    return VideoInfoResponse.model_validate(payload)
