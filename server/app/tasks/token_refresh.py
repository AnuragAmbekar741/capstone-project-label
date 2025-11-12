# app/tasks/token_refresh.py
from app.celery_app import celery_app
from app.repository.gmail_account_repository import GmailAccountRepository
from app.services.default.gmail_oauth_service import gmail_oauth_service
from app.enums.gmail import GmailAccountStatus
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.token_refresh.refresh_expiring_gmail_tokens")
def refresh_expiring_gmail_tokens():
    """
    Celery task to refresh Gmail access tokens before they expire.
    
    This task:
    1. Finds all Gmail accounts with tokens expiring within 15 minutes
    2. Refreshes their access tokens using the refresh_token from meta
    3. Updates the account with new token and expiry
    4. Marks accounts as ERROR if refresh fails
    """
    logger.info("🔄 Starting scheduled Gmail token refresh task")
    
    try:
        # Import Tortoise to ensure DB connection
        from tortoise import Tortoise
        import asyncio
        
        # Initialize Tortoise if not already initialized
        async def refresh_tokens_async():
            # Check if Tortoise is already initialized
            try:
                await Tortoise.get_connection("default")
            except Exception:
                # Initialize Tortoise for this task
                from app.config import TORTOISE_ORM
                await Tortoise.init(config=TORTOISE_ORM)
            
            try:
                # Get accounts expiring within 15 minutes
                expiring_accounts = await GmailAccountRepository.get_expiring_accounts(minutes=15)
                
                if not expiring_accounts:
                    logger.info("✅ No Gmail accounts need token refresh")
                    return {"refreshed": 0, "failed": 0, "skipped": 0}
                
                logger.info(f"📧 Found {len(expiring_accounts)} Gmail account(s) needing token refresh")
                
                refreshed_count = 0
                failed_count = 0
                skipped_count = 0
                
                for account in expiring_accounts:
                    try:
                        # Get refresh token from meta
                        refresh_token = account.get_refresh_token
                        
                        if not refresh_token:
                            logger.warning(
                                f"⚠️  Account {account.email_address} (ID: {account.id}) "
                                "has no refresh token - skipping"
                            )
                            skipped_count += 1
                            # Mark as error since we can't refresh
                            await GmailAccountRepository.mark_as_error(account)
                            continue
                        
                        logger.info(
                            f"🔄 Refreshing token for account: {account.email_address} "
                            f"(expires: {account.token_expiry})"
                        )
                        
                        # Refresh the access token
                        token_data = gmail_oauth_service.refresh_auth_access_token(refresh_token)
                        
                        # Calculate new expiry
                        expires_in = token_data.get('expires_in', 3600)
                        # Handle both timestamp and seconds format
                        if isinstance(expires_in, (int, float)) and expires_in > 1000000000:
                            # It's a timestamp
                            new_token_expiry = datetime.fromtimestamp(expires_in)
                        else:
                            # It's seconds from now
                            new_token_expiry = datetime.now() + timedelta(seconds=expires_in)
                        
                        # Update meta with new access token (keep refresh_token)
                        new_meta = account.meta.copy()
                        new_meta['access_token'] = token_data['access_token']
                        new_meta['scope'] = token_data.get('scope', new_meta.get('scope', ''))
                        new_meta['token_type'] = token_data.get('token_type', 'Bearer')
                        
                        # Update account
                        await GmailAccountRepository.update_tokens(
                            account=account,
                            new_meta=new_meta,
                            token_expiry=new_token_expiry
                        )
                        
                        refreshed_count += 1
                        logger.info(
                            f"✅ Successfully refreshed token for {account.email_address} "
                            f"(new expiry: {new_token_expiry})"
                        )
                        
                    except Exception as e:
                        logger.error(
                            f"❌ Failed to refresh token for account {account.email_address} "
                            f"(ID: {account.id}): {e}",
                            exc_info=True
                        )
                        failed_count += 1
                        # Mark account as error
                        try:
                            await GmailAccountRepository.mark_as_error(account)
                        except Exception as mark_error:
                            logger.error(f"Failed to mark account as error: {mark_error}")
                
                result = {
                    "refreshed": refreshed_count,
                    "failed": failed_count,
                    "skipped": skipped_count,
                    "total": len(expiring_accounts)
                }
                
                logger.info(
                    f"✅ Token refresh task completed: "
                    f"{refreshed_count} refreshed, {failed_count} failed, "
                    f"{skipped_count} skipped"
                )
                
                return result
                
            finally:
                # Close Tortoise connections
                await Tortoise.close_connections()
        
        return asyncio.run(refresh_tokens_async())
            
    except Exception as e:
        logger.error(f"❌ Token refresh task failed with error: {e}", exc_info=True)
        raise