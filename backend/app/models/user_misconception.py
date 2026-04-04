from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base


class UserMisconception(Base):
    """
    Tracks per-user misconceptions detected from wrong quiz/assessment answers.
    One row per (user, concept_tag) pair — updated in place when the user
    answers the same concept wrong again (count increments).
    """
    __tablename__ = "user_misconceptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # The concept/topic tag this misconception belongs to
    # e.g. "boolean_algebra", "karnaugh_map", "flip_flop"
    concept_tag = Column(String(255), nullable=False)

    # How many times this misconception has been triggered
    count = Column(Integer, default=1, nullable=False)

    # When it was first and last seen
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)