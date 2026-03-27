from sqlalchemy import Column, String, Integer, Boolean, Text
from app.database import Base

class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    resource_type = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=True)
    vark_style = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    is_short = Column(Boolean, nullable=True)
    source = Column(String(255), nullable=True)
    external_url = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)