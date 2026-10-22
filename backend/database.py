import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Use PostgreSQL from docker compose as default for local scripts
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://presentation_user:presentation_password@localhost:5435/presentation_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
