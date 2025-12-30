from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite for easy testing
DATABASE_URL = "sqlite:///./theperfectshop.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)