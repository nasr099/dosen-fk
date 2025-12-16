from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Explicit connection pool configuration so the app behaves well under
# higher traffic and on limited-connections environments (e.g. Railway).
#
# - pool_size: base number of persistent connections
# - max_overflow: how many extra connections beyond pool_size
# - pool_timeout: seconds to wait for a connection before raising
# - pool_pre_ping: validate connections and drop stale ones
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_timeout=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
