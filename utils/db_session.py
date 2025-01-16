from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from contextlib import contextmanager
from django.conf import settings

# SQLAlchemy engine
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
db_session = scoped_session(SessionLocal)


@contextmanager
def get_db_session():
    """provide a transactional scope for SQLAlchemy session"""
    session = db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
