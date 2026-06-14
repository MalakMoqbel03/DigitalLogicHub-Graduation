from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a .env with DATABASE_URL.")

try:
    engine = create_engine(
        DATABASE_URL,
        # ── Connection pool settings ──────────────────────────────────────
        # Neon (and most hosted Postgres) closes idle SSL connections after
        # ~5 minutes. Without these settings, SQLAlchemy keeps handing out
        # stale connections from the pool that were silently closed by Neon,
        # causing "SSL connection has been closed unexpectedly" on the next
        # request that hits that connection.
        #
        # pool_pre_ping=True:
        #   Before handing a connection from the pool to a request, SQLAlchemy
        #   sends a cheap "SELECT 1" ping. If the connection is dead, it is
        #   discarded and a fresh one is opened. This adds ~1ms per request
        #   but eliminates the SSL error entirely.
        pool_pre_ping=True,
        #
        # pool_recycle=300 (5 minutes):
        #   Connections are forcibly recycled after 300 seconds regardless of
        #   whether they are still alive. This prevents the pool from holding
        #   connections longer than Neon's idle timeout.
        pool_recycle=300,
        #
        # pool_size / max_overflow:
        #   Keeps the pool small to stay within Neon free-tier connection limits.
        #   pool_size=5 persistent connections + max_overflow=10 burst connections.
        pool_size=5,
        max_overflow=10,
        #
        # pool_timeout:
        #   Raise an error after 30s if no connection is available, instead of
        #   waiting forever.
        pool_timeout=30,
    )
except Exception as e:
    print("Failed to create SQLAlchemy engine:", e)
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()