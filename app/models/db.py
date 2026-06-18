# WHAT DOES THIS FILE DO: Defines database schema, models and session creators for SQLite.

# ================== IMPORTS ==================
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.config import settings
# ================== IMPORTS ==================


# =========== VARIABLES : Database connection engine, session factory and declarative base ===========
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    pass


class AnalysisTask(Base):
    ''' Model representing a single code analysis or generation task '''
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, default="queued")
    prompt = Column(String, nullable=True)
    original_code = Column(String, nullable=True)
    fixed_code = Column(String, nullable=True)
    diff = Column(String, nullable=True)
    repair_attempt = Column(Integer, default=0)
    reliability_report = Column(JSON, nullable=True)
    security_report = Column(JSON, nullable=True)
    confidence_report = Column(JSON, nullable=True)
    output_state = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
# =========== VARIABLES : Database connection engine, session factory and declarative base ===========


# =========== FUNCTION ===========
# ROLE: Initializes the database schema by creating all defined tables
def init_db() -> None:
    ''' Creates tables in database if they do not exist '''

    # FLOW-1: call metadata create_all to build tables
    Base.metadata.create_all(bind=engine)
# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: Provides a database session generator for endpoints and operations
def get_db():
    ''' Yields a database session and closes it after use '''

    # FLOW-1: open new session
    db = SessionLocal()     # USE: main db session

    try:
        yield db
    finally:
        db.close()
# =========== FUNCTION ===========
