from typing import Optional
from tortoise.exceptions import DoesNotExist
from app.models import User

class UserRepository:
    """Simple repository for User model operations"""

    # Create user
    @staticmethod
    async def create_user(
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None
    ) -> User:
        """Create a new user"""
        user = await User.create(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture
        )
        return user

    # Get user by Google ID
    @staticmethod
    async def get_user_by_google_id(google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        try:
            return await User.get(google_id=google_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            return await User.get(id=user_id)
        except DoesNotExist:
            return None