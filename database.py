from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from datetime import datetime
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./grievance_system.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Complaint(Base):
    __tablename__ = "complaints"
    
    complaint_id = Column(String, primary_key=True, default=lambda: f"GRV-{uuid.uuid4().hex[:8].upper()}")
    name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False, index=True)
    complaint_text = Column(Text, nullable=False)
    category = Column(String, default="general")
    priority = Column(String, default="medium")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_database():
    """Initialize the database and create tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Test database connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        # Test connection with proper SQLAlchemy text()
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Initialize database on import
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}") 