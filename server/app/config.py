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

settings = Settings()