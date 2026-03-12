from app.db.connection import get_connection
from sqlalchemy import text


def test_database_connection() -> None:
    with get_connection() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
