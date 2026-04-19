from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)

    is_verified = Column(Boolean, default=True)
    verification_code = Column(String, nullable=True)

    learning_style = Column(String, nullable=True)
    level = Column(String, nullable=True)

    cluster_id = Column(Integer, nullable=True)