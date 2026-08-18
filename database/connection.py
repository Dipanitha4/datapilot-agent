"""
database/connection.py
Manages PostgreSQL and Redis connections for the Travel AI Agent.
Uses connection pooling for PostgreSQL and a singleton pattern for Redis.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── PostgreSQL Configuration ─────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:travelai2026@localhost:5432/travel_ai"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # number of connections to keep open
    max_overflow=20,        # extra connections allowed beyond pool_size
    pool_pre_ping=True,     # verify connection is alive before using it
    pool_recycle=3600,      # recycle connections after 1 hour
    echo=False,             # set True to log all SQL queries (debug only)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically commits on success and rolls back on error.
    
    Usage:
        with get_db() as db:
            result = db.execute(text("SELECT 1"))
    """
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
    """
    Returns a database session for dependency injection in FastAPI.
    
    Usage in FastAPI:
        @app.get("/")
        def route(db: Session = Depends(get_db_session)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_postgres_connection() -> bool:
    """Verify PostgreSQL connection is working."""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False


# ─── Redis Configuration ──────────────────────────────────────────────────────

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis_client = None


def get_redis_client() -> redis.Redis:
    """
    Returns a Redis client singleton.
    Creates the connection on first call, reuses on subsequent calls.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,      # return strings instead of bytes
            socket_connect_timeout=5,   # fail fast if Redis is down
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


def check_redis_connection() -> bool:
    """Verify Redis connection is working."""
    try:
        client = get_redis_client()
        client.ping()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


# ─── Health Check ─────────────────────────────────────────────────────────────

def check_all_connections() -> dict:
    """
    Check all database connections and return status.
    Used by the API health endpoint.
    """
    return {
        "postgresql": check_postgres_connection(),
        "redis": check_redis_connection(),
    }


# ─── Run directly to test connections ─────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing database connections...")
    status = check_all_connections()
    print(f"PostgreSQL: {'✅ Connected' if status['postgresql'] else '❌ Failed'}")
    print(f"Redis:      {'✅ Connected' if status['redis'] else '❌ Failed'}")
