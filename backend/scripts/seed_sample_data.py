import os
import sys
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.base import engine, SessionLocal, Base
from app.db.models import Category, Question, PromoBanner, QuestionSet

# Ensure tables exist (for safety if running without migrations)
Base.metadata.create_all(bind=engine)

CATEGORIES = [
    {"name": "Anatomy", "description": "Human anatomy fundamentals"},
    {"name": "Physiology", "description": "Body function and mechanisms"},
    {"name": "Pharmacology", "description": "Drugs and their actions"},
]

# Predefined sets per category
SETS = {
    "Anatomy": [
        {"title": "Latihan Anatomi 2025 #1", "description": "100 item", "time_limit_minutes": 105},
        {"title": "Latihan Anatomi 2025 #2", "description": "100 item", "time_limit_minutes": 105},
    ],
    "Physiology": [
        {"title": "Latihan Fisiologi 2025 #1", "description": "100 item", "time_limit_minutes": 105},
    ],
    "Pharmacology": [
        {"title": "Latihan Farmakologi 2025 #1", "description": "100 item", "time_limit_minutes": 105},
    ],
}

QUESTIONS = [
    {
        "category": "Anatomy",
        "set_title": "Latihan Anatomi 2025 #1",
        "question_text": "Which bone is part of the axial skeleton?",
        "option_a": "Femur",
        "option_b": "Humerus",
        "option_c": "Sternum",
        "option_d": "Clavicle",
        "option_e": "Scapula",
        "correct_answer": "C",
        "explanation": "The sternum is part of the axial skeleton (along with skull, vertebral column, and rib cage).",
        "difficulty_level": "easy",
        "is_featured": True,
    },
    {
        "category": "Physiology",
        "set_title": "Latihan Fisiologi 2025 #1",
        "question_text": "Which ion is primarily responsible for the depolarization phase of a neuron action potential?",
        "option_a": "Na+",
        "option_b": "K+",
        "option_c": "Ca2+",
        "option_d": "Cl-",
        "option_e": "Mg2+",
        "correct_answer": "A",
        "explanation": "Rapid Na+ influx through voltage-gated Na+ channels causes depolarization.",
        "difficulty_level": "medium",
        "is_featured": True,
    },
    {
        "category": "Pharmacology",
        "set_title": "Latihan Farmakologi 2025 #1",
        "question_text": "Which receptor type do beta-blockers primarily antagonize?",
        "option_a": "Alpha-1 adrenergic",
        "option_b": "Muscarinic",
        "option_c": "Beta-adrenergic",
        "option_d": "Nicotinic",
        "option_e": "Histamine H1",
        "correct_answer": "C",
        "explanation": "Beta-blockers antagonize beta-adrenergic receptors, reducing heart rate and contractility.",
        "difficulty_level": "easy",
        "is_featured": False,
    },
]

PROMO = {
    "title": "Welcome to MedExam!",
    "description": "Try our featured questions and track your progress.",
    "image_url": "https://picsum.photos/seed/medexam/600/300",
    "link_url": "https://example.com/promo",
    "display_order": 0,
    "is_active": True,
}

def seed():
    db: Session = SessionLocal()
    try:
        # Seed categories
        name_to_id = {}
        for c in CATEGORIES:
            existing = db.query(Category).filter(Category.name == c["name"]).first()
            if not existing:
                cat = Category(**c)
                db.add(cat)
                db.commit()
                db.refresh(cat)
                name_to_id[c["name"]] = cat.id
            else:
                name_to_id[c["name"]] = existing.id

        # Seed sets per category
        set_lookup = {}  # (category, title) -> id
        for cat_name, sets in SETS.items():
            for s in sets:
                existing = db.query(QuestionSet).filter(
                    QuestionSet.category_id == name_to_id[cat_name],
                    QuestionSet.title == s["title"],
                ).first()
                if not existing:
                    qs = QuestionSet(category_id=name_to_id[cat_name], **s)
                    db.add(qs)
                    db.commit()
                    db.refresh(qs)
                    set_lookup[(cat_name, s["title"])] = qs.id
                else:
                    set_lookup[(cat_name, s["title"])] = existing.id

        # Seed questions
        for q in QUESTIONS:
            category = q.pop("category")
            set_title = q.pop("set_title")
            category_id = name_to_id[category]
            set_id = set_lookup.get((category, set_title))
            exists = db.query(Question).filter(
                Question.category_id == category_id,
                Question.question_text == q["question_text"],
            ).first()
            if not exists:
                db.add(Question(category_id=category_id, question_set_id=set_id, **q))
                db.commit()

        # Seed promo banner
        existing_promo = db.query(PromoBanner).filter(PromoBanner.title == PROMO["title"]).first()
        if not existing_promo:
            db.add(PromoBanner(**PROMO))
            db.commit()

        print("Seed completed.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
