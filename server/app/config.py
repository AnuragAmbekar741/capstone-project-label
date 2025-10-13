import os
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Capstone Project Label API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8080"]

    #Database Configuration
    DATABASE_URL:str = os.environ.get("DATABASE_URL","sqlite://db.sqlite3")

    #Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Tortoise ORM Configuration

settings = Settings()

TORTOISE_ORM:dict = {
        "connections":{
            "default":settings.DATABASE_URL
        },
        "apps":{
            "models": {
                "models": ["app.api.models.user", "aerich.models"],
                "default_connection": "default",
            }
        }
    }
