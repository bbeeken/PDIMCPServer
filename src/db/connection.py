"""Database helpers using SQLAlchemy sessions."""

import logging
from contextlib import contextmanager
from typing import Optional, Any, List, Dict, Union

from sqlalchemy import text

from .engine import SessionLocal

logger = logging.getLogger(__name__)


@contextmanager
def get_session() -> Any:
    """Yield a SQLAlchemy session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - propagate errors
        session.rollback()
        raise
    finally:
        session.close()


def execute_query(sql: str, params: Optional[Union[Dict[str, Any], List[Any]]] = None) -> list:
    """Execute a SQL statement and return rows as dicts."""
    bound = params or {}
    with get_session() as session:
        result = session.execute(text(sql), bound)
        columns = result.keys()
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def test_connection() -> bool:
    """Validate basic connectivity to the database."""
    try:
        with get_session() as session:
            result = session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            return value == 1
    except Exception as e:  # pragma: no cover - depends on DB state
        logger.error("Connection test failed: %s", e)
        return False
