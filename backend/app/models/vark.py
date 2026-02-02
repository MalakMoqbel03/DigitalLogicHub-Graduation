from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# =========================
# VARK QUESTIONS
# =========================
class VarkQuestion(Base):
    __tablename__ = "vark_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)


# =========================
# VARK OPTIONS
# =========================
class VarkOption(Base):
    __tablename__ = "vark_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("vark_questions.id"), nullable=False)
    option_text = Column(String, nullable=False)
    vark_type = Column(String, nullable=False)  
    # visual | auditory | reading | kinesthetic


# =========================
# USER VARK RESPONSES
# =========================
class UserVarkResponse(Base):
    __tablename__ = "user_vark_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vark_option_id = Column(Integer, ForeignKey("vark_options.id"), nullable=False)
