from app.cache.redis_client import build_video_info_cache_key, get_redis_client
from app.services import proxy_service
from fastapi.testclient import TestClient


def test_get_video_info_returns_200_with_expected_payload(client: TestClient) -> None:
    response = client.get("/get_video_info/123456")

    assert response.status_code == 200
    assert response.json() == {
        "title": "Dailymotion Spirit Movie",
        "channel": "creation",
        "owner": "Dailymotion",
        "filmstrip_60_url": "https://www.dailymotion.com/thumbnail/video/123456",
        "embed_url": "https://www.dailymotion.com/embed/video/123456",
    }


def test_get_video_info_returns_404_for_video_ids_ending_with_404(
    client: TestClient,
) -> None:
    response = client.get("/get_video_info/1404")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Video not found",
        "error_code": "video_not_found",
    }


def test_get_video_info_stores_payload_in_cache_on_first_call(
    client: TestClient,
) -> None:
    redis_client = get_redis_client()
    cache_key = build_video_info_cache_key("123456")

    assert redis_client.get(cache_key) is None

    response = client.get("/get_video_info/123456")

    assert response.status_code == 200
    assert redis_client.get(cache_key) is not None


def test_get_video_info_uses_cache_on_second_call(
    client: TestClient,
    monkeypatch,
) -> None:
    call_count = 0

    def fake_build_mock_video_info(video_id: str) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {
            "title": "Dailymotion Spirit Movie",
            "channel": "creation",
            "owner": "Dailymotion",
            "filmstrip_60_url": f"https://www.dailymotion.com/thumbnail/video/{video_id}",
            "embed_url": f"https://www.dailymotion.com/embed/video/{video_id}",
        }

    monkeypatch.setattr(
        proxy_service,
        "_build_mock_video_info",
        fake_build_mock_video_info,
    )

    first_response = client.get("/get_video_info/123456")
    second_response = client.get("/get_video_info/123456")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()
    assert call_count == 1


def test_get_video_info_does_not_cache_not_found_videos(client: TestClient) -> None:
    redis_client = get_redis_client()
    cache_key = build_video_info_cache_key("10404")

    response = client.get("/get_video_info/10404")

    assert response.status_code == 404
    assert redis_client.get(cache_key) is None
