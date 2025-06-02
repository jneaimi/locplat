from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.health import router as health_router
from app.api.translation import router as translation_router
from app.api.cache import router as cache_router
from app.api.field_mapping import router as field_mapping_router
from app.api.webhooks import router as webhooks_router
from app.services.ai_response_cache import close_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(f"🚀 LocPlat starting on {settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    # Initialize database tables
    await initialize_database()
    
    print("💾 Redis cache initialized")
    yield
    # Shutdown
    print("💾 Closing Redis cache connections...")
    await close_cache()
    print("👋 LocPlat shutting down...")

async def initialize_database():
    """Initialize database tables on startup with retry logic."""
    import asyncio
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
    from app.models.field_config import create_tables
    
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"🗄️  Initializing database tables (attempt {attempt + 1}/{max_retries})...")
            engine = create_engine(settings.DATABASE_URL)
            
            # Test connection first
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create tables
            create_tables(engine)
            print("✅ Database tables initialized successfully")
            return True
            
        except OperationalError as e:
            if "could not connect" in str(e).lower() or "connection refused" in str(e).lower():
                print(f"⏳ Database not ready, waiting {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                continue
            else:
                print(f"❌ Database error: {e}")
                break
        except Exception as e:
            print(f"❌ Failed to initialize database tables: {e}")
            break
    
    print("⚠️  Application will continue but field mapping may not work properly")
    return False

# Create FastAPI app with modern lifespan pattern
app = FastAPI(
    title="LocPlat - AI Translation Service",
    description="Simple AI-powered translation service for Directus CMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)

# Include routers
app.include_router(health_router, prefix="", tags=["Health"])
app.include_router(translation_router, prefix="/api/v1", tags=["Translation"])
app.include_router(cache_router, prefix="/api/v1", tags=["Cache"])
app.include_router(field_mapping_router, tags=["Field Mapping"])
app.include_router(webhooks_router, prefix="/api/v1", tags=["Webhooks"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )