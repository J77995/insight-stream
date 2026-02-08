"""
Configuration settings management using Pydantic BaseSettings.
Centralizes all environment variables and application settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_TITLE: str = "Insight Stream API"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    FRONTEND_URL: str = "http://localhost:8080"

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """List of allowed origins for CORS."""
        return [
            self.FRONTEND_URL,
            "http://localhost:8080",
            "http://localhost:5173",
            # Vercel deployments
            "https://insightfind-alpha.vercel.app",
            "https://insightfind-git-main-jklb739s-projects.vercel.app",
            "https://insightfind-jjtpe70hb-jklb739s-projects.vercel.app"
        ]

    # AI Provider Selection
    AI_PROVIDER: str = "gemini"  # Options: "gemini" or "openai"

    # Gemini AI
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_TOP_P: float = 0.9
    GEMINI_MAX_TOKENS_OVERVIEW: int = 500
    GEMINI_MAX_TOKENS_DETAIL: int = 6000

    # OpenAI
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS_OVERVIEW: int = 500
    OPENAI_MAX_TOKENS_DETAIL: int = 6000

    # Transcript Processing
    TRANSCRIPT_LIMIT_OVERVIEW: int = 8000
    TRANSCRIPT_LIMIT_DETAIL: int = 50000

    # YouTube API (optional for anti-blocking)
    YOUTUBE_COOKIES: str = ""  # Optional: YouTube cookies for better access

    # Translation Models (cost-optimized)
    GEMINI_TRANSLATION_MODEL: str = "gemini-1.5-flash"
    OPENAI_TRANSLATION_MODEL: str = "gpt-4o-mini"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
