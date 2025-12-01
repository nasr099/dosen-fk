import logging
from app.db.base import Base, engine
from app.db.models import User, Category, Question, QuestionSet, ExamSession, ExamAnswer, PromoBanner, TeamMember

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    logger.info("Creating all tables in database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

if __name__ == "__main__":
    init_db()
