
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./lyftr.db"
)

# SQLite connection settings
connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# Database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()


# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
