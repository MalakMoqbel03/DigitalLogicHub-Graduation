from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base


class ResourceQuizQuestion(Base):
    __tablename__ = "resource_quiz_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(1), nullable=False)  # 'a', 'b', 'c', or 'd'
    concept_tag = Column(String(255), nullable=True)  # For misconception tracking


class UserResourceQuizAttempt(Base):
    __tablename__ = "user_resource_quiz_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("resource_quiz_questions.id", ondelete="CASCADE"), nullable=False)
    chosen_option = Column(String(1), nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow)
