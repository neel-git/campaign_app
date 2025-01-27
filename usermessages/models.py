from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from authentication.models import Base, User

# Create your models here.


class UserMessage(Base):
    """Individual message copies for each user"""

    __tablename__ = "user_messages"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    campaign_id = Column(BigInteger, ForeignKey("campaigns.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)  # Copy of campaign content
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="messages")
    campaign = relationship("Campaign")
