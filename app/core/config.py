from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "TE Measurements"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./te_measurements.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Server
    HOST: str = "127.0.0.1"  # localhost only for school network
    PORT: int = 8080  # Use 8080 instead of 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

