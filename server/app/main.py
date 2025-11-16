# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import uvicorn
from app.api.router import google_auth
from app.api.router import gmail_oauth
from app.api.router import imap
from app.api.router import langchain_test
from app.config import settings, TORTOISE_ORM

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Label - Email Organization API with Google OAuth",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
# Allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# PUBLIC ROUTES (No authentication required)
# ============================================================================

# Authentication routes - /auth/google (public), /auth/me (protected)
app.include_router(google_auth.router)

app.include_router(langchain_test.router)


# ============================================================================
# PROTECTED ROUTES (Authentication required)
# ============================================================================
app.include_router(gmail_oauth.router)
app.include_router(imap.router)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Register Tortoise ORM with database
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,  # Auto-create tables
    add_exception_handlers=True,
)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy"}


@app.get("/health/db", tags=["Health"])
async def db_health_check():
    """Database connection health check"""
    from tortoise import Tortoise
    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Use string format for better reload
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )