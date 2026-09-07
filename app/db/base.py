from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import (
    SQLALCHEMY_DATABASE_URL,
    SQLALCHEMY_MAX_OVERFLOW,
    SQLALCHEMY_POOL_SIZE,
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Register cross-model transaction guards after Base exists. The guard imports
# concrete models lazily inside Session events to avoid circular imports here.
from . import owner_transfer_guard as _owner_transfer_guard  # noqa: E402,F401
