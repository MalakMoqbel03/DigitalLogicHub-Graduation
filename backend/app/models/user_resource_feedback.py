from sqlalchemy import Column, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class UserResourceFeedback(Base):
    __tablename__ = "user_resource_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)
    rating = Column(Integer, nullable=True)
    liked = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)