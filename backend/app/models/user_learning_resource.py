from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserLearningResource(Base):
    __tablename__ = "user_learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)

    # True when the user saved this resource for later
    is_bookmarked = Column(Boolean, nullable=False, default=False)

    # True when the user hit "See another" and skipped this resource
    is_skipped = Column(Boolean, nullable=False, default=False)