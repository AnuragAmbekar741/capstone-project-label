import os
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Capstone Project Label API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    #Database Configuration
    DATABASE_URL:str = os.environ.get("DATABASE_URL","")

    # Tortoise ORM Configuration
    TORTOISE_ORM:dict = {
        "connections":{
            "default":DATABASE_URL
        },
        "apps":{
            "models": {
                "models": ["app.api.models", "aerich.models"],
                "default_connection": "default",
            }
        }
    }

settings = Settings()