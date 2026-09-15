from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )

    DATABASE_URL: str = "postgresql+psycopg2://postgres:leebpostgred@localhost:5432/scapegis"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # SMTP Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Optional - will use console print if empty
    SMTP_PASS: str = ""  # Optional - will use console print if empty
    SMTP_FROM_NAME: str = "Scapegis"
    SMTP_FROM_EMAIL: str = "noreply@scapegis.com"
    
    # Token expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30


settings = Settings()

