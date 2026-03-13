from fastapi.testclient import TestClient


def test_log_video_returns_404_when_video_does_not_exist(client: TestClient) -> None:
    response = client.get("/log_video/missing-video")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Video not found",
        "error_code": "video_not_found",
    }


def test_log_video_returns_chronological_history_for_spam_video(client: TestClient) -> None:
    client.post("/add_video", json={"video_id": "log-video-001"})

    client.get(
        "/get_video",
        headers={"Authorization": "am9obi5kb2U="},
    )

    client.post(
        "/flag_video",
        headers={"Authorization": "am9obi5kb2U="},
        json={"video_id": "log-video-001", "status": "spam"},
    )

    response = client.get("/log_video/log-video-001")

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 3

    assert body[0]["status"] == "pending"
    assert body[0]["moderator"] is None

    assert body[1]["status"] == "in_review"
    assert body[1]["moderator"] == "john.doe"

    assert body[2]["status"] == "spam"
    assert body[2]["moderator"] == "john.doe"


def test_log_video_returns_not_spam_label_for_not_spam_video(client: TestClient) -> None:
    client.post("/add_video", json={"video_id": "log-video-002"})

    client.get(
        "/get_video",
        headers={"Authorization": "am9obi5kb2U="},
    )

    client.post(
        "/flag_video",
        headers={"Authorization": "am9obi5kb2U="},
        json={"video_id": "log-video-002", "status": "not spam"},
    )

    response = client.get("/log_video/log-video-002")

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 3

    assert body[2]["status"] == "not spam"
    assert body[2]["moderator"] == "john.doe"
