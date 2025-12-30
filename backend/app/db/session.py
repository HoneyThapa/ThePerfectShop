from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite for easy testing, PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../theperfectshop.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = sessionmaker(bind=engine)
