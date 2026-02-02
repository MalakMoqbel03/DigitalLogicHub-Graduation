from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.app.database import Base

class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    topic = Column(String)
    difficulty = Column(String)
