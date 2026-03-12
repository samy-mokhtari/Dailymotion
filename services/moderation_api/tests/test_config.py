from app.core.config import get_settings


def test_get_settings_builds_database_url(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "moderation")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "admin")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    settings = get_settings()

    assert settings.postgres_db == "moderation"
    assert settings.postgres_user == "postgres"
    assert settings.postgres_password == "admin"
    assert settings.postgres_host == "postgres"
    assert settings.postgres_port == 5432
    assert settings.log_level == "INFO"
    assert (
        settings.database_url
        == "postgresql+psycopg://postgres:admin@postgres:5432/moderation"
    )

def test_get_settings_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = get_settings()

    assert settings.postgres_db == "moderation"
    assert settings.postgres_user == "postgres"
    assert settings.postgres_password == "admin"
    assert settings.postgres_host == "postgres"
    assert settings.postgres_port == 5432
    assert settings.log_level == "INFO"
