from datetime import datetime, timedelta, timezone
from tortoise.models import Model
from tortoise import fields
import uuid
from app.enums.gmail import GmailAccountStatus


class GmailAccount(Model):
    """ 
    Stores the Gmail account information for the user
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    # Foreign key to User (UUID)
    user = fields.ForeignKeyField(
        'models.User',
        related_name='gmail_accounts',
        on_delete=fields.CASCADE
    )
    email_address = fields.CharField(max_length=255, index=True)
    # Contains: {access_token, refresh_token, expiry_date, scope, token_type}
    meta = fields.JSONField(default=dict)
    token_expiry = fields.DatetimeField(index=True)
    status = fields.CharEnumField(
        GmailAccountStatus,
        default=GmailAccountStatus.ACTIVE,
        max_length=20
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "gmail_accounts"
        unique_together = (("user", "email_address"),)
        indexes = (
            ("user_id", "email_address"),
            ("token_expiry", "status"),
        )

    # Helper properties
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (within 2 minutes of expiry)"""
        now = datetime.now(timezone.utc)
        return self.token_expiry < now + timedelta(minutes=2)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is already expired"""
        now = datetime.now(timezone.utc)
        return self.token_expiry < now
    
    @property
    def get_refresh_token(self) -> str | None:
        """Safely get refresh token from meta"""
        return self.meta.get('refresh_token') if self.meta else None
    
    @property
    def get_access_token(self) -> str | None:
        """Safely get access token from meta"""
        return self.meta.get('access_token') if self.meta else None
    
    def __str__(self):
        return f"GmailAccount({self.email_address})"