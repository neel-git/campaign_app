import pytest
from sqlalchemy import create_engine, event, Integer,BigInteger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from tests.utils.mock_models import (
    TestBase,
    MockPractice,
    MockUser,
    MockPracticeUserAssignment,
)
from tests.utils.mock_service import TestPracticeService
from alembic import command
from alembic.config import Config
from authentication.models import UserRoles


# Enable SQLite foreign key support
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations before running tests"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:", echo=True, connect_args={"check_same_thread": False}
    )

    from authentication.models import Base as AuthBase
    from practices.models import Base as PracticeBase

    # Force SQLite to use INTEGER instead of BigInteger
    if "sqlite" in str(test_engine.url):
        for table in [AuthBase.metadata.tables, PracticeBase.metadata.tables]:
            for column in table.values():
                if isinstance(column.primary_key, BigInteger):
                    column.type = Integer  # Use Integer for SQLite
    
    AuthBase.metadata.create_all(bind=test_engine)
    PracticeBase.metadata.create_all(bind=test_engine)

    yield test_engine

    AuthBase.metadata.drop_all(bind=test_engine)
    PracticeBase.metadata.drop_all(bind=test_engine)

    # TestBase.metadata.create_all(bind=test_engine)

    # yield test_engine

    # TestBase.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def practice_service(db_session):
    return TestPracticeService(db_session)


@pytest.fixture
def sample_practice(db_session):
    practice = MockPractice(
        name="Test Practice", description="Test Description", is_active=True
    )
    db_session.add(practice)
    db_session.commit()
    db_session.refresh(practice)
    return practice


@pytest.fixture
def sample_user(db_session):
    user = MockUser(
        username="testuser",
        email="test@example.com",
        role=UserRoles.PRACTICE_USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_assignment(db_session, sample_practice, sample_user):
    assignment = MockPracticeUserAssignment(
        practice_id=sample_practice.id, user_id=sample_user.id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment
