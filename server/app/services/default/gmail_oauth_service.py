from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from typing import Dict, Any, Optional
from app.config import settings
from app.services.base.gmail_oauth_service import GmailOAuthServiceBase
import logging
from datetime import datetime, timezone

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
    
    def _create_flow(self) -> Flow:
        """
        Create OAuth flow instance
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

        return flow
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL
        """
        try:
            flow = self._create_flow()
            
            # Generate authorization URL with offline access to get refresh token
            authorization_url,returned_state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )

            if state:
                from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
                parsed = urlparse(authorization_url)
                query_params = parse_qs(parsed.query)
                query_params['state'] = [state]
                new_query = urlencode(query_params, doseq=True)
                authorization_url = urlunparse(
                    (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
                )
            return authorization_url

        except Exception as e:
            logger.error(f"Failed to generate Gmail OAuth URL: {e}")
            raise ValueError(f"Failed to generate authorization URL: {str(e)}")

    def exchange_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        """
        try:
            flow = self._create_flow()
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Extract token information
            # Handle timezone-aware/naive datetime for expiry
            expires_in_seconds = 3600  # default
            if credentials.expiry:
                # credentials.expiry might be naive (no timezone), make it UTC-aware
                expiry = credentials.expiry
                if expiry.tzinfo is None:
                    # Naive datetime - assume UTC
                    expiry = expiry.replace(tzinfo=timezone.utc)
                expires_in_seconds = int((expiry - datetime.now(timezone.utc)).total_seconds())
            
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_in': expires_in_seconds,
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
            
            # Handle timezone-aware/naive datetime for expiry
            expires_in_seconds = 3600  # default
            if credentials.expiry:
                # credentials.expiry might be naive (no timezone), make it UTC-aware
                expiry = credentials.expiry
                if expiry.tzinfo is None:
                    # Naive datetime - assume UTC
                    expiry = expiry.replace(tzinfo=timezone.utc)
                expires_in_seconds = int((expiry - datetime.now(timezone.utc)).total_seconds())
            
            token_data = {
                'access_token': credentials.token,
                'expires_in': expires_in_seconds,
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