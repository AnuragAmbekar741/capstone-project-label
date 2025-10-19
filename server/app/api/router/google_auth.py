from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.models.user import User
from app.services import google_auth_service 
from app.api.utils.jwt import create_token, TokenType
from app.repository.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class GoogleLoginRequest(BaseModel):
    """Request body for Google login"""
    id_token: str

class AuthResponse(BaseModel):
    """Response after successful authentication"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class UserProfileResponse(BaseModel):
    """User profile response"""
    id: int
    email: str
    name: str
    google_id: str
    created_at: str
    updated_at: str

class RefreshTokenRequest(BaseModel):
    """Request body for token refresh"""
    refresh_token: str

@router.post("/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_login(request_data: GoogleLoginRequest):
    """Google OAuth login/signup endpoint"""
    
    logger.info("=" * 50)
    logger.info("Starting Google login process")
    
    try:
        # Step 1: Verify Google token using service
        logger.info("Step 1: Verifying Google token...")
        google_user = await google_auth_service.verify_google_token(request_data.id_token)
        
        if not google_user:
            logger.warning("❌ Google token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to authenticate with Google. Please try again."
            )
        
        logger.info(f"✅ Google token verified for: {google_user.get('email')}")
        
        # Step 2: Check if user exists in database
        logger.info("Step 2: Checking if user exists in database...")
        user = await UserRepository.get_user_by_google_id(google_user["google_id"])
        
        is_new_user = False
        
        # Step 3: Create user if new
        if not user:
            logger.info("Step 3: User not found, creating new user...")
            user = await UserRepository.create_user(
                google_id=google_user["google_id"],
                email=google_user["email"],
                name=google_user["name"]
            )
            is_new_user = True
            logger.info(f"✅ New user created: ID={user.id}, Email={user.email}")
        else:
            logger.info(f"✅ Existing user found: ID={user.id}, Email={user.email}")
        
        # Step 4: Create tokens
        logger.info("Step 4: Creating JWT tokens...")
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "google_id": user.google_id,
            "name": user.name
        }
        
        access_token = create_token(token_data, token_type=TokenType.ACCESS)
        refresh_token = create_token(token_data, token_type=TokenType.REFRESH)
        
        logger.info("✅ Tokens created successfully")
        
        # Step 5: Return response
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
        
        logger.info("✅ Login successful!")
        logger.info("=" * 50)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during authentication: {str(e)}"
        )

@router.post("/refresh", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(request_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    This endpoint allows clients to get a new access token when the current one expires,
    using a valid refresh token.
    """
    logger.info("=" * 50)
    logger.info("Starting token refresh process")
    
    try:
        # Step 1: Verify refresh token
        logger.info("Step 1: Verifying refresh token...")
        from app.api.utils.jwt import verify_token
        
        payload = verify_token(request_data.refresh_token)
        
        if not payload:
            logger.warning("❌ Refresh token verification failed - Invalid or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Step 2: Verify it's a refresh token (not an access token)
        token_type = payload.get("type")
        if token_type != TokenType.REFRESH.value:
            logger.warning(f"❌ Invalid token type: {token_type}, expected: refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Please provide a refresh token."
            )
        
        logger.info("✅ Refresh token verified successfully")
        
        # Step 3: Extract user info from token
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("❌ Token payload missing user ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Step 4: Verify user still exists in database
        logger.info(f"Step 2: Verifying user exists (ID: {user_id})...")
        user = await UserRepository.get_user_by_id(int(user_id))
        
        if not user:
            logger.warning(f"❌ User not found: ID={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        logger.info(f"✅ User verified: {user.email}")
        
        # Step 5: Create new tokens
        logger.info("Step 3: Creating new JWT tokens...")
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "google_id": user.google_id,
            "name": user.name
        }
        
        # Generate new access token
        new_access_token = create_token(token_data, token_type=TokenType.ACCESS)
        
        # Optionally generate a new refresh token (rotation strategy)
        new_refresh_token = create_token(token_data, token_type=TokenType.REFRESH)
        
        logger.info("✅ New tokens created successfully")
        
        # Step 6: Return new tokens
        response_data = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
        }
        
        logger.info("✅ Token refresh successful!")
        logger.info("=" * 50)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during token refresh: {str(e)}"
        )

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile
    Requires: Bearer token in Authorization header
    """
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        google_id=current_user.google_id,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat(),
    )