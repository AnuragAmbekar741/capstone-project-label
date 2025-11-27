from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging
import secrets
import httpx

from app.api.deps import get_current_user
from app.models.user import User
from app.services.default.gmail_oauth_service import gmail_oauth_service
from app.repository.gmail_account_repository import GmailAccountRepository
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["Gmail OAuth"])

class ConnectGmailResponse(BaseModel):
    """Response for initiating Gmail OAuth"""
    authorization_url: str
    state: str

class GmailAccountResponse(BaseModel):
    """Response model for connected Gmail account"""
    id: str
    email_address: str
    status: str
    created_at: str
    updated_at: str

class GmailAccountsResponse(BaseModel):
    """Response for listing user's Gmail accounts"""
    accounts: List[GmailAccountResponse]

async def get_user_email_from_token(access_token: str) -> Optional[str]:
    """
    Get user's email address from Google OAuth access token
    Uses Google's userinfo API
    
    Args:
        access_token: OAuth access token from Google
        
    Returns:
        User's email address or None if failed
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                userinfo = response.json()
                email = userinfo.get("email")
                logger.info(f"Successfully retrieved email from token: {email}")
                return email
            else:
                logger.error(f"Failed to get userinfo: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user email from token: {e}")
        return None


@router.get("/connect", response_model=ConnectGmailResponse)
async def connect_gmail_account(
    current_user: User = Depends(get_current_user)
):
    """
    Initiate Gmail OAuth flow
    
    **Protected endpoint** - User must be authenticated
    
    Returns authorization URL that user should visit to grant access.
    The state parameter contains user_id for security.
    
    Flow:
    1. Frontend calls this endpoint (with JWT token)
    2. Backend generates OAuth URL with user_id in state
    3. Frontend redirects user to authorization_url
    4. User grants permission
    5. Google redirects to /api/gmail/callback
    """
    try:
        state_secret = secrets.token_urlsafe(32)
        state = f"{current_user.id}:{state_secret}"
        
        # Generate authorization URL using OAuth service
        auth_url = gmail_oauth_service.get_auth_url(state=state)
        
        logger.info(f"Generated Gmail OAuth URL for user {current_user.id}")
        
        return ConnectGmailResponse(
            authorization_url=auth_url,
            state=state
        )
        
    except ValueError as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in connect_gmail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/callback")
async def gmail_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter containing user_id"),
    error: Optional[str] = Query(None, description="Error from Google OAuth")
):
    logger.info(f"=== Gmail OAuth Callback Called ===")
    logger.info(f"Code: {code[:20]}... (truncated)")
    logger.info(f"State: {state}")
    logger.info(f"Error: {error}")
    """
    Handle OAuth callback from Google
    
    **Public endpoint** - No auth required (Google redirects here)
    
    This endpoint:
    1. Receives authorization code from Google
    2. Exchanges code for access/refresh tokens
    3. Gets user's email from token
    4. Saves Gmail account to database
    5. Redirects user to frontend with success/error
    
    Flow:
    - Google redirects here after user grants permission
    - Backend processes the OAuth flow
    - Redirects to frontend dashboard
    """
    # Handle OAuth errors from Google
    if error:
        logger.error(f"OAuth error from Google: {error}")
        frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?gmail_error={error}",
            status_code=status.HTTP_302_FOUND
        )
    
    if not code:
        logger.error("Missing authorization code in callback")
        frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?gmail_error=missing_code",
            status_code=status.HTTP_302_FOUND
        )
    
    try:
        # Step 1: Extract user ID from state (format: "{user_id}:{secret}")
        user_id = None
        if state:
            try:
                from uuid import UUID
                user_id_part = state.split(":")[0]
                user_id = UUID(user_id_part)
                logger.info(f"Extracted user_id from state: {user_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid state format: {state} - {e}")
        
        if not user_id:
            logger.error("No user_id in state parameter")
            frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
            return RedirectResponse(
                url=f"{frontend_url}/dashboard?gmail_error=invalid_state",
                status_code=status.HTTP_302_FOUND
            )
        
        # Step 2: Exchange code for tokens using OAuth service
        logger.info("Exchanging authorization code for tokens...")
        token_data = gmail_oauth_service.exchange_tokens(code)
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        if not access_token:
            raise ValueError("No access token received from Google")
        
        if not refresh_token:
            logger.warning("No refresh token received - user may need to re-authenticate")
        
        # Step 3: Get user's email from access token using helper function
        logger.info("Fetching user email from Google userinfo API...")
        email_address = await get_user_email_from_token(access_token)
        
        if not email_address:
            raise ValueError("Failed to get user email from token")
        
        logger.info(f"User email from token: {email_address}")
        
        # Step 4: Calculate token expiry
        expires_in = token_data.get("expires_in", 3600)  # Now always in SECONDS
        token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Step 5: Prepare meta data for database
        meta_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scope": token_data.get("scope", ""),
            "token_type": token_data.get("token_type", "Bearer")
        }
        
        # Step 6: Check if Gmail account already exists for this user and email
        # Since repository method doesn't filter by user_id, we'll check all accounts and filter manually
        existing_account = await GmailAccountRepository.get_gmail_account_by_email(email_address)
        
        # Verify the account belongs to the current user if it exists
        if existing_account and existing_account.user_id == user_id:
            # Update existing account with new tokens
            logger.info(f"Updating existing Gmail account: {email_address}")
            updated_account = await GmailAccountRepository.update_tokens(
                account=existing_account,
                new_meta=meta_data,
                token_expiry=token_expiry
            )
            account_id = str(updated_account.id)
        elif existing_account and existing_account.user_id != user_id:
            # Account exists but belongs to different user - create new entry
            logger.info(f"Email {email_address} exists for different user, creating new account")
            new_account = await GmailAccountRepository.create_gmail_account(
                user_id=user_id,
                email_address=email_address,
                meta=meta_data,
                token_expiry=token_expiry
            )
            account_id = str(new_account.id)
        else:
            # Create new Gmail account
            logger.info(f"Creating new Gmail account: {email_address}")
            new_account = await GmailAccountRepository.create_gmail_account(
                user_id=user_id,
                email_address=email_address,
                meta=meta_data,
                token_expiry=token_expiry
            )
            account_id = str(new_account.id)
        
        logger.info(f"✅ Successfully connected Gmail account: {email_address} (ID: {account_id})")
        
        # Step 7: Redirect to frontend with success
        frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?gmail_connected={account_id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?gmail_error={str(e)}",
            status_code=status.HTTP_302_FOUND
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {e}", exc_info=True)
        frontend_url = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?gmail_error=unexpected_error",
            status_code=status.HTTP_302_FOUND
        )

@router.get("/accounts", response_model=GmailAccountsResponse)
async def get_user_gmail_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    Get all connected Gmail accounts for the current user
    
    **Protected endpoint** - User must be authenticated
    """
    try:
        accounts = await GmailAccountRepository.get_user_gmail_accounts(current_user.id)
        
        account_responses = [
            GmailAccountResponse(
                id=str(account.id),
                email_address=account.email_address,
                status=account.status.value,
                created_at=account.created_at.isoformat(),
                updated_at=account.updated_at.isoformat()
            )
            for account in accounts
        ]
        
        return GmailAccountsResponse(accounts=account_responses)
        
    except Exception as e:
        logger.error(f"Error fetching Gmail accounts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Gmail accounts"
        )