from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from authentication.models import Base, User

# Create your models here.


class Practice(Base):
    __tablename__ = "practices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(500),nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PracticeUserAssignment(Base):
    __tablename__ = "practice_user_assignments"
    
    id = Column(BigInteger, primary_key=True)
    practice_id = Column(BigInteger, ForeignKey('practices.id'))
    user_id = Column(BigInteger, ForeignKey('users.id'))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
