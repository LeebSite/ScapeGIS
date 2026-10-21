from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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

    # Spatial AI Provider Selection
    SPATIAL_AI_PROVIDER: str = "gemini"

    # Gemini / Spatial AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: int = 30
    SPATIAL_AI_MAX_TOOL_CALLS: int = 8
    SPATIAL_AI_MAX_HISTORY_MESSAGES: int = 10

    # Groq Configuration (Alternative Provider)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: int = 30
    GROQ_REASONING_EFFORT: str = "medium"
    GROQ_MAX_COMPLETION_TOKENS: int = 2048

    @field_validator("SPATIAL_AI_PROVIDER")
    @classmethod
    def validate_spatial_ai_provider(cls, v: str) -> str:
        provider = (v or "").lower().strip()
        if provider not in ("gemini", "groq"):
            from app.spatial_ai.exceptions import ProviderConfigurationError
            raise ProviderConfigurationError(
                f"Unsupported SPATIAL_AI_PROVIDER '{v}'. Must be 'gemini' or 'groq'."
            )
        return provider

    @field_validator("GROQ_REASONING_EFFORT")
    @classmethod
    def validate_groq_reasoning_effort(cls, v: str) -> str:
        effort = (v or "").lower().strip()
        if effort not in ("low", "medium", "high"):
            raise ValueError(
                f"Invalid GROQ_REASONING_EFFORT '{v}'. Must be 'low', 'medium', or 'high'."
            )
        return effort

    @field_validator("GROQ_MAX_COMPLETION_TOKENS")
    @classmethod
    def validate_groq_max_completion_tokens(cls, v: int) -> int:
        if v < 256 or v > 8192:
            raise ValueError(
                f"GROQ_MAX_COMPLETION_TOKENS must be between 256 and 8192, got {v}."
            )
        return v


settings = Settings()
