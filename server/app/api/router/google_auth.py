# server/app/api/router/google_auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.utils.google_auth import verify_google_token
from app.api.repository.user_repository import UserRepository
from app.api.utils.jwt import create_token

router = APIRouter(prefix="/auth", tags=["authentication"])

class GoogleAuthRequest(BaseModel):
    access_token: str

class AuthResponse(BaseModel):
    jwt_token: str
    user: dict

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """
    Authenticate user with Google OAuth access token
    """
    try:
        # Verify Google access token
        google_user_info = await verify_google_token(request.access_token)
        
        if not google_user_info:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        # Check if email is verified
        if not google_user_info.get("email_verified", False):
            raise HTTPException(status_code=400, detail="Email not verified")
        
        # Create or get user from database
        user = await UserRepository.create_user(
            google_id=google_user_info["google_id"],
            email=google_user_info["email"],
            name=google_user_info["name"]
        )
        
        # Create JWT token
        jwt_token = create_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Return response
        return AuthResponse(
            jwt_token=jwt_token,
            user={
                "id": user.id,
                "google_id": user.google_id,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")