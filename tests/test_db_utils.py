import pytest
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Table for testing
metadata = MetaData()
test_table = Table(
    "test_table",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("description", String),
)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new session for each test"""
    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(test_table.delete())
    session.commit()

    yield session

    # Clean up after the test
    session.rollback()
    session.execute(test_table.delete())
    session.commit()
    session.close()


def test_session_basic_operations(session):

    session.execute(
        test_table.insert().values(name="Test 1", description="Description 1")
    )
    session.commit()

    result = session.execute(
        test_table.select().where(test_table.c.name == "Test 1")
    ).first()
    assert result is not None
    assert result.name == "Test 1"
    assert result.description == "Description 1"


def test_session_rollback(session):

    session.execute(
        test_table.insert().values(name="Test 2", description="Description 2")
    )
    session.commit()

    # Verify initial state
    initial_count = len(session.execute(test_table.select()).fetchall())
    assert initial_count == 1, "Should have exactly one record to start"

    try:
        session.execute(
            test_table.insert().values(
                name="Test 2",
                description="Another Description",
            )
        )
        session.commit()
        pytest.fail("Should have raised a unique constraint error")
    except SQLAlchemyError:
        session.rollback()

    result = session.execute(test_table.select()).fetchall()
    assert len(result) == 1, "Should still have exactly one record after rollback"
    assert result[0].name == "Test 2", "Original record should still exist"
    assert (
        result[0].description == "Description 2"
    ), "Original record should be unchanged"

    session.execute(
        test_table.insert().values(name="Test 3", description="Description 3")
    )
    session.commit()

    # Final verification
    final_result = session.execute(test_table.select()).fetchall()
    assert len(final_result) == 2, "Should now have two records after successful insert"


def test_session_multiple_operations(session):

    initial_count = len(session.execute(test_table.select()).fetchall())
    assert initial_count == 0, "Table should be empty at start of test"

    data = [
        {"name": "Multi 1", "description": "First"},
        {"name": "Multi 2", "description": "Second"},
        {"name": "Multi 3", "description": "Third"},
    ]
    session.execute(test_table.insert(), data)
    session.commit()

    after_insert = session.execute(test_table.select()).fetchall()
    assert len(after_insert) == 3, "Should have exactly three records after insert"

    session.execute(
        test_table.update()
        .where(test_table.c.name == "Multi 2")
        .values(description="Updated")
    )
    session.commit()

    results = session.execute(
        test_table.select().order_by(test_table.c.name)
    ).fetchall()

    assert len(results) == 3, "Should still have exactly three records"

    updated_record = next(r for r in results if r.name == "Multi 2")
    assert updated_record.description == "Updated", "Record should have been updated"

    original_records = [r for r in results if r.name != "Multi 2"]
    assert len(original_records) == 2, "Should have two unchanged records"
    assert any(r.description == "First" for r in original_records)
    assert any(r.description == "Third" for r in original_records)


def test_session_delete(session):
    session.execute(
        test_table.insert().values(name="ToDelete", description="Will be deleted")
    )
    session.commit()

    session.execute(test_table.delete().where(test_table.c.name == "ToDelete"))
    session.commit()

    result = session.execute(
        test_table.select().where(test_table.c.name == "ToDelete")
    ).first()
    assert result is None


def test_session_isolation(engine):

    Session = sessionmaker(bind=engine)
    session1 = Session()
    session2 = Session()

    session1.execute(test_table.insert().values(name="Isolation", description="Test"))
    session1.commit()

    result = session2.execute(
        test_table.select().where(test_table.c.name == "Isolation")
    ).first()
    assert result is not None

    # Clean up
    session1.close()
    session2.close()
