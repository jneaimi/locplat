from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
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
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()