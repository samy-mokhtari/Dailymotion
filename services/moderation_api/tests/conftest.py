import pytest
from app.db.connection import transaction
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_database() -> None:
    with transaction() as connection:
        connection.execute(text("DELETE FROM video_logs"))
        connection.execute(text("DELETE FROM videos"))
