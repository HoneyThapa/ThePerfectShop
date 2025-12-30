from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ThePerfectShop"

# Create engine with connection timeout settings for faster failure when DB is unavailable
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    connect_args={
        "connect_timeout": 2,  # 2 second connection timeout
        "application_name": "expiryshield_backend"
    }
)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
