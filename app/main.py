from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.health import router as health_router

# Create FastAPI app
app = FastAPI(
    title="LocPlat - AI Translation Service",
    description="Simple AI-powered translation service for Directus CMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="", tags=["Health"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"🚀 LocPlat starting on {settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API Documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 LocPlat shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )