from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Development frontend
        "http://localhost:8080",  # Alternative dev port
        "http://127.0.0.1:3000",  # Local development
        "http://127.0.0.1:8080",  # Alternative local port
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS: List[str] = [
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent"
    ]

    # Database Configuration
    DATABASE_URL: str = "postgresql://locplat:locplat123@localhost:5432/locplat"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour

    # AI Provider Configuration (Optional - Keys provided per request)
    OPENAI_API_KEY: Optional[str] = None
    # Note: Deep Translator (fallback) doesn't require API keys

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()