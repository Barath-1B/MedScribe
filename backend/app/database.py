"""SQLAlchemy database configuration (SQLite)."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = Path(__file__).parent.parent / "ocr_clinical.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    from app.models import Document, GroundTruthNote, Experiment, StageResult  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
