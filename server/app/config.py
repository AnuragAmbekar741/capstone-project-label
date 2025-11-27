import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()
class Settings(BaseModel):
    APP_NAME: str = "Capstone Project Label API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173","http://localhost:5174", "http://localhost:8080"]

    #Database Configuration
    DATABASE_URL:str = os.environ.get("DATABASE_URL","sqlite://db.sqlite3")

    # Redis Configuration
    REDIS_URL: str = os.environ.get("REDIS_URL")
    REDIS_CACHE_URL: str = os.environ.get("REDIS_CACHE_URL")


    #LangChain Configuration
    # Model provider: "gemini" or "openai"
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "gemini")
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TEMPERATURE: float = float(os.environ.get("GEMINI_TEMPERATURE", "0.7"))
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # or "gpt-3.5-turbo" for cheaper
    OPENAI_TEMPERATURE: float = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))

    #Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET")

    GMAIL_REDIRECT_URI: str = os.environ.get("GMAIL_REDIRECT_URI")
    GMAIL_SCOPES: List[str] = [
        "https://mail.google.com/",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]

    # JWT Configuration
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 60
    # Tortoise ORM Configuration

settings = Settings()

TORTOISE_ORM:dict = {
        "connections":{
            "default":settings.DATABASE_URL
        },
        "apps":{
            "models": {
                "models": ["app.models.user", "app.models.gmail_account", "aerich.models"],
                "default_connection": "default",
            }
        }
    }
