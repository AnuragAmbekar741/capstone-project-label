from uuid import UUID
from datetime import datetime, timezone
from app.models.gmail_account import GmailAccount
from app.enums.gmail import GmailAccountStatus

class GmailAccountRepository:

    @staticmethod
    async def create_gmail_account(
        user_id: UUID,
        email_address: str,
        meta: dict,
        token_expiry: datetime
    ) -> GmailAccount:
        """Create a new Gmail account connection"""
        return await GmailAccount.create(
            user_id=user_id,
            email_address=email_address,
            meta=meta,
            token_expiry=token_expiry,
            status=GmailAccountStatus.ACTIVE
        )

    @staticmethod
    async def get_user_gmail_accounts(user_id: UUID) -> list[GmailAccount]:
        """Get all active Gmail accounts for a user"""
        return await GmailAccount.filter(
            user_id=user_id,
            status=GmailAccountStatus.ACTIVE
        ).all()

    @staticmethod
    async def get_gmail_account_by_id(account_id: UUID) -> GmailAccount | None:
        """Get Gmail account by ID"""
        return await GmailAccount.get_or_none(id=account_id)
    
    @staticmethod
    async def get_gmail_account_by_email(email_address: str) -> GmailAccount | None:
        """Get Gmail account by email address"""
        return await GmailAccount.get_or_none(email_address=email_address)

    @staticmethod
    async def update_tokens(
        account: GmailAccount,
        new_meta: dict,
        token_expiry: datetime
    ) -> GmailAccount:
        """Update access token after refresh"""
        account.meta = new_meta
        account.token_expiry = token_expiry
        account.status = GmailAccountStatus.ACTIVE
        await account.save()
        return account

    @staticmethod
    async def mark_as_error(
        account: GmailAccount,
    ) -> GmailAccount:
        """Mark account as error (needs reconnection)"""
        account.status = GmailAccountStatus.ERROR
        await account.save()
        return account
    
    @staticmethod
    async def disconnect_gmail_account(account: GmailAccount) -> None:
        """Disconnect (delete) a Gmail account"""
        await account.delete()
    
    @staticmethod
    async def get_expiring_accounts(minutes: int = 15) -> list[GmailAccount]:
        """Get accounts expiring within N minutes (for Celery Beat)"""
        from datetime import timedelta
        threshold = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        return await GmailAccount.filter(
            token_expiry__lt=threshold,
            status=GmailAccountStatus.ACTIVE
        ).all()