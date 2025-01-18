# authentication/models.py
from sqlalchemy import Column, String, BigInteger, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from django.utils import timezone
import enum
import bcrypt
from datetime import timedelta
from .mixins import AuthenticationMixin

Base = declarative_base()


class UserRoleType(enum.Enum):
    __enum_name__ = "user_role_type"
    super_admin = "Practice by Numbers Support"
    admin = "Admin"
    practice_user = "Practice User"


class User(Base, AuthenticationMixin):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleType), nullable=False)
    desired_practice_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, default=True)
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
