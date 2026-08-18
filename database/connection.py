"""
database/connection.py
Manages PostgreSQL and Redis connections for the Travel AI Agent.
Uses connection pooling for PostgreSQL and a singleton pattern for Redis.
All configuration is read from config.py — no credentials here.
"""

import logging
from contextlib import contextmanager
from typing import Generator

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config import settings

logger = logging.getLogger(__name__)

# ─── PostgreSQL ───────────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """Returns a database session for dependency injection in FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_postgres_connection() -> bool:
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False


# ─── Redis ────────────────────────────────────────────────────────────────────

_redis_client = None


def get_redis_client() -> redis.Redis:
    """Returns a Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


def check_redis_connection() -> bool:
    try:
        get_redis_client().ping()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


# ─── Health Check ─────────────────────────────────────────────────────────────

def check_all_connections() -> dict:
    return {
        "postgresql": check_postgres_connection(),
        "redis": check_redis_connection(),
    }
