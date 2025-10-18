from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AuthService(ABC):
    """
    Abstract base class for OAuth authentication services
    Defines the contract that all auth providers must implement
    """
    
    @abstractmethod
    async def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify OAuth token and return user information
        
        Args:
            token: OAuth token from provider
            
        Returns:
            Dictionary with user info if valid, None if invalid
            Expected keys: google_id (or provider_id), email, name, email_verified
        """
        pass
    
