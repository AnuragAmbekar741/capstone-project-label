# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import uvicorn
from app.api.router import google_auth
from app.config import settings, TORTOISE_ORM

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Simple FastAPI application"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(google_auth.router)

# Register Tortoise ORM with database
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Database health check
@app.get("/health/db")
async def db_health_check():
    from tortoise import Tortoise
    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Simple test endpoint
@app.get("/test")
async def test():
    return {"message": "Test endpoint working!"}

# @app.post("/auth/google")
# async def google_auth(request: dict):
#     return {"message": "Google auth endpoint - not implemented yet"}

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )