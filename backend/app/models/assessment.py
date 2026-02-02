from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), nullable=True)  # FK exists in DB; keep nullable for safety
    question_text = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # beginner/intermediate/advanced
    is_entry = Column(Boolean, default=False)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, default=0)
    level = Column(String, nullable=True)  # beginner/intermediate/advanced


class UserResponse(Base):
    __tablename__ = "user_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=False)
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime, default=datetime.utcnow)
