from __future__ import annotations
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.common.config import load_config
from app.common.utils import ensure_dir

cfg = load_config()
db_url = cfg["cloud"]["database_url"]

if db_url.startswith("sqlite:///"):
    db_file = db_url.replace("sqlite:///", "")
    ensure_dir(Path(db_file).parent)

engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()