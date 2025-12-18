from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from configparser import ConfigParser
import os

Base = declarative_base()

# Global session factory
SessionLocal = None
engine = None


def init_database():
    """Initialize database connection from config"""
    global SessionLocal, engine
    
    config = ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.ini')
    config.read(config_path)
    
    db_type = config.get('database', 'db_type', fallback='sqlite')
    # Normalise and allow for inline comments like "postgresql  # or 'sqlite'"
    db_type = db_type.split('#', 1)[0].strip().lower()
    
    if db_type == 'postgresql':
        host = config.get('database', 'host')
        port = config.get('database', 'port')
        database = config.get('database', 'database')
        username = config.get('database', 'username')
        password = config.get('database', 'password')
        
        database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    else:  # sqlite
        sqlite_path = config.get('database', 'sqlite_path', fallback='data/te_measurements.db')
        # Ensure directory exists
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        database_url = f"sqlite:///{sqlite_path}"
    
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if db_type == 'sqlite' else {},
        echo=False  # Set to True for SQL debugging
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal


def get_db():
    """Get database session"""
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    if engine is None:
        init_database()
    Base.metadata.create_all(bind=engine)

