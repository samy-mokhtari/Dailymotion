import pytest
from app.cache.redis_client import get_redis_client
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_proxy_cache() -> None:
    redis_client = get_redis_client()

    for key in redis_client.scan_iter(match="video_info:*"):
        redis_client.delete(key)
