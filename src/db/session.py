"""
Database session management
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from .engine import SessionLocal

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Create a database session with automatic cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session() -> Session:
    """Get a new database session"""
    return SessionLocal()