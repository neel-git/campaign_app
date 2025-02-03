# campaigns/models.py
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from authentication.models import Base, User
from practices.models import Practice


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(String(20), nullable=False)  # 'DEFAULT' or 'CUSTOM'
    delivery_type = Column(String(20), nullable=False)  # 'IMMEDIATE' or 'SCHEDULED'
    status = Column(String(20), default="DRAFT")
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    target_roles = Column(JSON, nullable=False)  # List of role strings

    # For copied campaigns
    copied_from = Column(BigInteger, ForeignKey("campaigns.id"), nullable=True)

    # Relationships
    creator = relationship(
        "User",
        backref="created_campaigns",
        foreign_keys=[created_by],
        overlaps="campaigns",
    )
    practice_associations = relationship(
        "CampaignPracticeAssociation",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    schedules = relationship(
        "CampaignSchedule", back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignSchedule(Base):
    """Handles scheduled campaigns execution"""

    __tablename__ = "campaign_schedules"

    id = Column(BigInteger, primary_key=True)
    campaign_id = Column(BigInteger, ForeignKey("campaigns.id", ondelete="CASCADE"))
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="PENDING")  # 'PENDING', 'PROCESSED', 'FAILED'
    execution_time = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="schedules")


class CampaignHistory(Base):
    """Tracks all campaign actions"""

    __tablename__ = "campaign_history"

    id = Column(BigInteger, primary_key=True)
    campaign_id = Column(BigInteger, ForeignKey("campaigns.id", ondelete="CASCADE"))
    action = Column(String(50))  # 'CREATED', 'UPDATED', 'SENT', 'SCHEDULED'
    details = Column(Text, nullable=True)
    performed_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    performer = relationship(
        "User",
        foreign_keys=[performed_by],
        backref="campaign_history_entries"
    )

class CampaignPracticeAssociation(Base):
    """Associates campaigns with target practices"""

    __tablename__ = "campaign_practice_associations"

    id = Column(BigInteger, primary_key=True)
    campaign_id = Column(BigInteger, ForeignKey("campaigns.id", ondelete="CASCADE"))
    practice_id = Column(BigInteger, ForeignKey("practices.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="practice_associations")
    practice = relationship("Practice")
