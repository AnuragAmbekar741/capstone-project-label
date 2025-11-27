from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.api.deps import get_current_user
from app.models.user import User
from app.models.gmail_account import GmailAccount
from app.repository.gmail_account_repository import GmailAccountRepository
from app.services.default.langchain_service import langchain_service
from app.services.workers.redis_label_cache import RedisLabelCache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["Label Suggestions"])

# Request/Response Models
class SuggestLabelRequest(BaseModel):
    """Request model for single email label suggestion"""
    email_id: str
    subject: str
    body: str

class SuggestLabelResponse(BaseModel):
    """Response model for label suggestion"""
    id: str
    label: str
    reason: str

# Helper function (copy from imap.py if you don't want to import)
async def get_valid_gmail_account(
    account_id: UUID,
    current_user: User
) -> GmailAccount:
    """Get Gmail account and refresh token if expired"""
    from app.services.default.gmail_oauth_service import gmail_oauth_service
    from datetime import datetime, timedelta, timezone
    
    account = await GmailAccountRepository.get_gmail_account_by_id(account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Gmail account not found")
    
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if token needs refresh
    if account.is_expired or account.needs_refresh:
        refresh_token = account.get_refresh_token
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Token expired and no refresh token available"
            )
        
        # Refresh token
        try:
            token_data = gmail_oauth_service.refresh_auth_access_token(refresh_token)
            expires_in = token_data.get('expires_in', 3600)
            token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            account.meta['access_token'] = token_data['access_token']
            account.token_expiry = token_expiry
            await account.save()
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh token")
    
    return account

@router.post("/accounts/{account_id}/emails/suggest-label", response_model=SuggestLabelResponse)
async def suggest_label_for_email(
    account_id: UUID = Path(..., description="Gmail account ID"),
    request: SuggestLabelRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """
    Suggest a label for a single email using AI (LangChain + OpenAI/Gemini).
    Uses langchain_service.label_email() for single email processing.
    Only returns suggestions - does not create or apply labels.
    """
    account = await get_valid_gmail_account(account_id, current_user)
    
    redis_cache = RedisLabelCache()
    
    try:
        # Validate email body
        if not request.body or not request.body.strip():
            raise HTTPException(
                status_code=400,
                detail="Email has no body content to analyze"
            )
        
        # Get existing labels from Redis cache for AI context
        existing_labels = redis_cache.get_labels(str(account_id))
        logger.info(f"Retrieved {len(existing_labels)} existing labels from cache for label suggestion")
        
        # Get label suggestion from AI using single email method
        label_result = langchain_service.label_email(
            email_subject=request.subject or "",
            email_body=request.body.strip()[:2000],  # Limit body length
            existing_labels=existing_labels
        )
        
        suggested_label = label_result.get("label", "").strip()
        reason = label_result.get("reason", "")
        
        if not suggested_label:
            raise HTTPException(
                status_code=400,
                detail="No label suggested by AI"
            )
        
        logger.info(f"✅ Suggested label '{suggested_label}' for email {request.email_id}")
        
        return SuggestLabelResponse(
            id=request.email_id,
            label=suggested_label,
            reason=reason
        )
        
    except ValueError as e:
        logger.error(f"Error in label suggestion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error suggesting label: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest label: {str(e)}")
