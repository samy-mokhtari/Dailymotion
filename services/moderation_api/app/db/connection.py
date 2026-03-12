from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import settings
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection


def create_db_engine() -> Engine:
    """
    Create the SQLAlchemy Core engine used by the moderation service.

    Notes:
    - pool_pre_ping helps recover from stale DB connections.
    - future=True enables SQLAlchemy 2.x style behavior.
    """
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )

engine = create_db_engine()

@contextmanager
def get_connection() -> Iterator[Connection]:
    """
    Provide a database connection for read-only or explicit SQL operations.

    The caller is responsible for executing SQL statements.
    The connection is always closed when leaving the context.
    """
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

@contextmanager
def transaction() -> Iterator[Connection]:
    """
    Provide a transactional database connection.

    All statements executed within this context are committed if successful.
    If an exception is raised, the transaction is rolled back automatically.
    """
    with engine.begin() as connection:
        yield connection
