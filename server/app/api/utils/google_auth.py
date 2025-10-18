from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError
from typing import Optional, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth ID token using official google-auth library.
    
    Best Practices:
    1. Uses Google's official library (most secure)
    2. Automatic audience validation
    3. Local signature verification (efficient)
    4. Proper error handling and logging
    
    Args:
        token: Google ID token from frontend
        
    Returns:
        User information if valid, None if invalid
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10  # Allow 10 seconds clock skew
        )
        
        # Additional security validations
        if not idinfo.get("email_verified"):
            logger.warning(f"Email not verified for: {idinfo.get('email')}")
            return None
        
        # Check token issuer (defense in depth)
        valid_issuers = ["accounts.google.com", "https://accounts.google.com"]
        if idinfo.get("iss") not in valid_issuers:
            logger.error(f"Invalid issuer: {idinfo.get('iss')}")
            return None
        
        # Return validated user information
        return {
            "google_id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            # "picture": idinfo.get("picture"),
            "email_verified": idinfo.get("email_verified", False),
            "locale": idinfo.get("locale"),
        }
        
    except GoogleAuthError as e:
        logger.error(f"Google auth error: {e}")
        return None
    except ValueError as e:
        # Token is invalid or expired
        logger.error(f"Token validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None