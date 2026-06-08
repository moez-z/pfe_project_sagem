import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# ── Load .env manually (no extra dependency needed) ───────────────────────────

def _load_dotenv():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

_load_dotenv()


# ── Connection settings ───────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)


# ── SQLAlchemy setup ──────────────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # reconnect silently if connection dropped
    pool_size=5,
    max_overflow=10,
    echo=False,                # set True to log all SQL queries
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# ── DB initialisation ─────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    from db import models as _  # noqa — ensures models are registered
    Base.metadata.create_all(bind=engine)
    print(f"[db] Tables created on {DB_HOST}:{DB_PORT}/{DB_NAME}")


def get_db():
    """Context manager for a DB session. Use with `with get_db() as db:`."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> tuple[bool, str]:
    """Returns (success, message). Used by login dialog to verify DB."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, f"Connected to {DB_HOST}:{DB_PORT}/{DB_NAME}"
    except Exception as e:
        return False, str(e)
