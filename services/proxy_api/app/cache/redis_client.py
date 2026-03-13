import json
from typing import Any

from app.core.config import settings
from redis import Redis


def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


def build_video_info_cache_key(video_id: str) -> str:
    return f"video_info:{video_id}"


def get_cached_video_info(video_id: str) -> dict[str, Any] | None:
    client = get_redis_client()
    cache_key = build_video_info_cache_key(video_id)

    cached_value = client.get(cache_key)
    if cached_value is None:
        return None

    if not isinstance(cached_value, str):
        raise TypeError("Expected cached Redis value to be a string.")

    return json.loads(cached_value)


def set_cached_video_info(video_id: str, payload: dict[str, Any]) -> None:
    client = get_redis_client()
    cache_key = build_video_info_cache_key(video_id)

    client.set(
        cache_key,
        json.dumps(payload),
        ex=settings.cache_ttl_seconds,
    )
