from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Create base class for mocks
TestBase = declarative_base()


class MockPractice(TestBase):
    """Mock practice model for testing"""

    __tablename__ = "test_practices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MockUser(TestBase):
    """Mock user model for testing"""

    __tablename__ = "test_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)


class MockPracticeUserAssignment(TestBase):
    """Mock practice-user assignment model for testing"""

    __tablename__ = "test_practice_user_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practice_id = Column(Integer, ForeignKey("test_practices.id"))
    user_id = Column(Integer, ForeignKey("test_users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
