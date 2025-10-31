from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional
from app.config import settings
from app.services.base.gmail_oauth_service import GmailOAuthServiceBase
import logging

logger = logging.getLogger(__name__)

class GmailOAuthService(GmailOAuthServiceBase):
    """
    Gmail OAuth service implementation using google-auth-oauthlib
    Handles OAuth flow for Gmail API access
    """
    
    def __init__(self):
        """Initialize with settings from config"""
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GMAIL_REDIRECT_URI
        self.scopes = settings.GMAIL_SCOPES
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Gmail OAuth credentials not fully configured")
    
    def _create_flow(self, state: Optional[str] = None) -> Flow:
        """
        Create OAuth flow instance
        
        Args:
            state: Optional state parameter
            
        Returns:
            Configured Flow instance
        """
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if state:
            flow.state = state
        
        return flow
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            state: Optional state parameter (typically user ID for CSRF protection)
            
        Returns:
            Authorization URL string
        """
        try:
            flow = self._create_flow(state)
            
            # Generate authorization URL with offline access to get refresh token
            authorization_url, _ = flow.authorization_url(
                access_type='offline',  # Required to get refresh_token
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to ensure refresh_token
            )
            
            logger.info(f"Generated Gmail OAuth URL for state: {state}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to generate Gmail OAuth URL: {e}")
            raise ValueError(f"Failed to generate authorization URL: {str(e)}")
    
    def exchange_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with tokens and metadata
        """
        try:
            flow = self._create_flow()
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Extract token information
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,  # May be None if not granted
                'expires_in': int(credentials.expiry.timestamp()) if credentials.expiry else 3600,
                'scope': ' '.join(credentials.scopes) if credentials.scopes else '',
                'token_type': 'Bearer'
            }
            
            logger.info("Successfully exchanged code for Gmail tokens")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            raise ValueError(f"Failed to exchange authorization code: {str(e)}")
    
    def refresh_auth_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token
        
        Args:
            refresh_token: Refresh token from stored credentials
            
        Returns:
            Dictionary with new access token and metadata
        """
        try:
            # Create credentials object with refresh token
            credentials = Credentials(
                token=None,  # Will be populated by refresh
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            # Extract new token information
            token_data = {
                'access_token': credentials.token,
                'expires_in': int(credentials.expiry.timestamp()) if credentials.expiry else 3600,
                'scope': ' '.join(credentials.scopes) if credentials.scopes else '',
                'token_type': 'Bearer'
            }
            
            logger.info("Successfully refreshed Gmail access token")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise ValueError(f"Failed to refresh access token: {str(e)}")

# Singleton instance
gmail_oauth_service = GmailOAuthService()