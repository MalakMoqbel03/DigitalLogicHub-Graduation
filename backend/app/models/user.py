from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)

    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)

    learning_style = Column(String, nullable=True)
    level = Column(String, nullable=True)

    cluster_id = Column(Integer, nullable=True)

    verification_code_sent_at = Column(DateTime, nullable=True)

    # Task 10: context multiplier support
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Extended profile for clustering
    university_name = Column(String(255), nullable=True)
    major = Column(String(255), nullable=True)
    study_year = Column(String(50), nullable=True)