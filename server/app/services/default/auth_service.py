from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError
from typing import Optional, Dict, Any
from app.config import settings
from app.services.base.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

class GoogleAuthService(AuthService):
    """
    Google OAuth authentication service implementation
    """
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
    
    async def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google OAuth ID token using official google-auth library.
        
        How it works:
        1. Google signs tokens with their private key
        2. We verify using Google's public keys (fetched automatically)
        3. If signature is valid, token is genuine
        
        Args:
            token: Google ID token from frontend
            
        Returns:
            Dictionary with user info if valid, None if invalid
        """
        try:
            # Verify token signature and claims automatically
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id,
                clock_skew_in_seconds=10
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
                "google_id": idinfo.get("sub"),  # Google user ID
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "email_verified": idinfo.get("email_verified", False),
                "locale": idinfo.get("locale"),
            }
            
        except GoogleAuthError as e:
            logger.error(f"Google auth error: {e}")
            return None
        except ValueError as e:
            logger.error(f"Token validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return None
    
# Singleton instance
google_auth_service = GoogleAuthService()