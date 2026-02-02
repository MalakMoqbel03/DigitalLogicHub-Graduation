from sqlalchemy.orm import Session
from backend.app.models.learning_resource import LearningResource

def recommend_by_content(db: Session, topic: str, difficulty: str):
    return db.query(LearningResource).filter(
        LearningResource.topic == topic,
        LearningResource.difficulty == difficulty
    ).all()
