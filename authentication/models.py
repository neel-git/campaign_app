# authentication/models.py
from sqlalchemy import Column, String, BigInteger, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from django.utils import timezone
import enum
import bcrypt
from datetime import timedelta
from .mixins import AuthenticationMixin

Base = declarative_base()


class UserRoles:
    SUPER_ADMIN = "Practice by Numbers Support"
    ADMIN = "Admin"
    PRACTICE_USER = "Practice User"


class User(Base, AuthenticationMixin):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    session_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def set_password(self, raw_password):
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        self.password = hashed.decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password.encode("utf-8")
        )

    def update_session_expiry(self):
        """Update session expiry time to 24 hours from now"""
        self.session_expires_at = timezone.now() + timedelta(hours=24)

    def is_session_valid(self):
        """Check if user session is still valid"""
        if not self.is_active:
            return False
        if not self.session_expires_at:
            return False
        return timezone.now() <= self.session_expires_at


class UserRegistrationRequest(Base):
    __tablename__ = "user_registration_requests"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    desired_practice_id = Column(BigInteger, ForeignKey("practices.id"), nullable=False)
    requested_role = Column(String(50), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    reviewed_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add relationships for easier data access
    user = relationship("User", foreign_keys=[user_id], backref="registration_request")
    reviewer = relationship(
        "User", foreign_keys=[reviewed_by], backref="reviewed_requests"
    )
    practice = relationship("Practice", backref="registration_requests")


class RoleChangeRequest(Base):
    __tablename__ = "role_change_requests"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    practice_id = Column(BigInteger, ForeignKey("practices.id"))
    current_role = Column(String(50), nullable=False)
    requested_role = Column(String(50), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    practice = relationship("Practice")
