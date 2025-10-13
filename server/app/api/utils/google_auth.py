from google.auth.transport import requests
from google.oauth2 import id_token
from typing import Optional, Dict, Any
from app.config import settings
import httpx

async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth access token and return user information
    """
    try:
        # Use the access token to get user info from Google API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token}"
            )
            
            if response.status_code != 200:
                return None
                
            user_info = response.json()
            
            # Extract user information
            return {
                "google_id": user_info.get("id"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "email_verified": user_info.get("verified_email", False)
            }
            
    except Exception as e:
        print(f"Google token verification failed: {e}")
        return None