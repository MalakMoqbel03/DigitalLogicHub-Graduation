from sqlalchemy import Column, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class UserResourceFeedback(Base):
    __tablename__ = "user_resource_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=True)
    liked = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'learning_resource_id', name='uq_user_resource_feedback_user_resource'),
    )