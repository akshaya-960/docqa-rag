"""Database engine/session setup and one-time schema bootstrap.

Uses a plain SQLAlchemy engine (no Alembic) since this project's schema is
small and stable. A real production service would use migrations instead of
create_all().
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    """Create the pgvector extension and any missing tables.

    Safe to call on every startup: CREATE EXTENSION IF NOT EXISTS and
    Base.metadata.create_all() are both idempotent.
    """
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Import models here so they're registered on Base before create_all runs.
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
