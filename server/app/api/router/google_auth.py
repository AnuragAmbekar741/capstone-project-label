from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.api.utils.google_auth import verify_google_token
from app.api.utils.jwt import create_token
from app.api.repository.user_repository import UserRepository
import logging
import traceback

# Configure logging to show more details
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleLoginRequest(BaseModel):
    """Request body for Google login"""
    id_token: str


class AuthResponse(BaseModel):
    """Response after successful authentication"""
    access_token: str
    token_type: str = "Bearer"
    user: dict


@router.post("/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_login(request_data: GoogleLoginRequest):
    """
    Google OAuth login/signup endpoint.
    
    - Verifies Google ID token
    - Creates new user if first time login (signup)
    - Returns JWT access token for your app
    """
    
    logger.info("=" * 50)
    logger.info("Starting Google login process")
    
    try:
        # Step 1: Verify Google token
        logger.info("Step 1: Verifying Google token...")
        google_user = await verify_google_token(request_data.id_token)
        
        if not google_user:
            logger.warning("❌ Google token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to authenticate with Google. Please try again."
            )
        
        logger.info(f"✅ Google token verified for: {google_user.get('email')}")
        logger.info(f"   Google ID: {google_user.get('google_id')}")
        logger.info(f"   Name: {google_user.get('name')}")
        
        # Step 2: Check if user exists in database
        logger.info("Step 2: Checking if user exists in database...")
        user = await UserRepository.get_user_by_google_id(google_user["google_id"])
        
        is_new_user = False
        
        # Step 3: Create or retrieve user
        if not user:
            logger.info("Step 3: User not found, creating new user...")
            try:
                user = await UserRepository.create_user(
                    google_id=google_user["google_id"],
                    email=google_user["email"],
                    name=google_user["name"]
                )
                is_new_user = True
                logger.info(f"✅ New user created: ID={user.id}, Email={user.email}")
            except Exception as create_error:
                logger.error(f"❌ Failed to create user: {create_error}")
                logger.error(traceback.format_exc())
                raise
        else:
            logger.info(f"✅ Existing user found: ID={user.id}, Email={user.email}")
        
        # Step 4: Create JWT access token
        logger.info("Step 4: Creating JWT access token...")
        try:
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "google_id": user.google_id,
                "name": user.name
            }
            access_token = create_token(token_data)
        except Exception as jwt_error:
            logger.error(f"❌ Failed to create JWT: {jwt_error}")
            logger.error(traceback.format_exc())
            raise
        
        # Step 5: Return token and user information
        logger.info("Step 5: Preparing response...")
        response_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "google_id": user.google_id,
                "is_new_user": is_new_user
            }
        }
        logger.info("✅ Login successful!")
        logger.info("=" * 50)
        return response_data
        
    except HTTPException:
        logger.error("HTTPException raised, re-raising...")
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during authentication: {str(e)}"
        )
