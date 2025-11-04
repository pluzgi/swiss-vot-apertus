"""
Database connection and session management
PostgreSQL connection with SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

from config import settings, get_database_url
from models import Base

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    get_database_url(),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables
    Run this once during setup
    """
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def drop_db():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    if not settings.is_development():
        raise ValueError("Cannot drop database in production!")

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ Database tables dropped")


@contextmanager
def get_db_session() -> Session:
    """
    Context manager for database sessions
    Automatically handles commit/rollback and session cleanup

    Usage:
        with get_db_session() as session:
            session.query(Initiative).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db():
    """
    Dependency for FastAPI endpoints
    Yields a database session

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Initiative).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


# Convenience functions for common queries

def get_initiative_by_vote_id(session: Session, vote_id: str):
    """Get initiative by vote_id"""
    from models import Initiative
    return session.query(Initiative).filter(Initiative.vote_id == vote_id).first()


def get_all_initiatives(session: Session, limit: int = 100):
    """Get all initiatives with optional limit"""
    from models import Initiative
    return session.query(Initiative).limit(limit).all()


def search_initiatives_by_keyword(session: Session, keyword: str, limit: int = 10):
    """Search initiatives by keyword in title or policy area"""
    from models import Initiative
    search_term = f"%{keyword}%"
    return (
        session.query(Initiative)
        .filter(
            (Initiative.offizieller_titel.ilike(search_term))
            | (Initiative.schlagwort.ilike(search_term))
            | (Initiative.politikbereich.ilike(search_term))
        )
        .limit(limit)
        .all()
    )
