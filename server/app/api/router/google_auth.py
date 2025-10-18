from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
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