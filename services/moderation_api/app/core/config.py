import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    log_level: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def get_settings() -> Settings:
    return Settings(
        postgres_db=os.getenv("POSTGRES_DB", "moderation"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "admin"),
        postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = get_settings()
