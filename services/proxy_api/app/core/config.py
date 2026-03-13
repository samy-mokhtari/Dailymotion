import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    redis_url: str
    cache_ttl_seconds: int
    log_level: str


def get_settings() -> Settings:
    return Settings(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = get_settings()
