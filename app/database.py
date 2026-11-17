"""SQLAlchemy database engine, session factory, and initialization helpers."""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _ensure_sqlite_directory(database_url: str) -> None:
    """Create parent directory for file-based SQLite databases if needed."""
    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:///:memory:"):
        db_path = Path(database_url.replace("sqlite:///", "", 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(database_url: str = settings.database_url):
    """Create a SQLAlchemy engine configured for SQLite or PostgreSQL."""
    _ensure_sqlite_directory(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def init_db(target_engine=engine) -> None:
    """Create all database tables if they do not exist."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=target_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it safely."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
