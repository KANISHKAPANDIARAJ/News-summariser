"""Database session management and schema initialization."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_config
from app.models.base import Base
# Import all models to ensure registered on metadata
import app.models  # noqa: F401

config = get_config()

# SQLite needs check_same_thread=False for multithreading
connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes database tables."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for obtaining a transactional database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # noqa: BLE001
        session.rollback()
        raise
    finally:
        session.close()
