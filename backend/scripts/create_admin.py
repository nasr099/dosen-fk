import os
import sys
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.base import engine, SessionLocal, Base
from app.db.models import User
from app.core.security import get_password_hash

# Ensure tables exist (for safety if running without migrations)
Base.metadata.create_all(bind=engine)

def create_admin(email: str, full_name: str, password: str):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if not user.is_admin:
                user.is_admin = True
                db.commit()
                print(f"User {email} promoted to admin.")
            else:
                print(f"Admin {email} already exists.")
            return
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin {email} created.")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', required=True)
    parser.add_argument('--full_name', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    create_admin(args.email, args.full_name, args.password)
