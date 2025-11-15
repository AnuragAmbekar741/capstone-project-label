from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_current_user
from app.models.user import User
from app.models.gmail_account import GmailAccount
from app.repository.gmail_account_repository import GmailAccountRepository
from app.services.default.imap_service import GmailImapService
from app.services.default.gmail_oauth_service import gmail_oauth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["Gmail IMAP"])

# Response models
class FolderResponse(BaseModel):
    name: str
    flags: List[str]

class EmailResponse(BaseModel):
    uid: int
    subject: str
    from_address: str
    to_addresses: List[str]
    date: str
    body_text: Optional[str]
    body_html: Optional[str]
    labels: List[str]
    attachments: List[dict]
    # Thread identification fields
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[str] = None
    is_thread: bool = False  # Computed field indicating if email is part of a thread

# Add these response models after EmailResponse
class CreateLabelRequest(BaseModel):
    name: str
    label_list_visibility: str = "labelShow"  # labelShow or labelHide
    message_list_visibility: str = "show"  # show or hide

class LabelResponse(BaseModel):
    id: str
    name: str
    label_list_visibility: str
    message_list_visibility: str
    type: str

# Helper function to get account and refresh token if needed
async def get_valid_gmail_account(
    account_id: UUID,
    current_user: User
) -> GmailAccount:
    """Get Gmail account and refresh token if expired"""
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
            # Update account with new token
            from datetime import datetime, timedelta
            expires_in = token_data.get('expires_in', 3600)
            token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            account.meta['access_token'] = token_data['access_token']
            account.token_expiry = token_expiry
            await account.save()
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh token")
    
    return account

@router.get("/accounts/{account_id}/folders", response_model=List[FolderResponse])
async def list_folders(
    account_id: UUID = Path(..., description="Gmail account ID"),
    current_user: User = Depends(get_current_user)
):
    """List all folders/labels for a Gmail account"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token available")
        
        await imap_service.connect(access_token, account.email_address)
        folders = await imap_service.list_folders()
        
        return [FolderResponse(name=f.name, flags=f.flags) for f in folders]
        
    except Exception as e:
        logger.error(f"Failed to list folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()

@router.post("/accounts/{account_id}/labels", response_model=LabelResponse)
async def create_label(
    account_id: UUID = Path(..., description="Gmail account ID"),
    request: CreateLabelRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """Create a new label in Gmail"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    gmail_api_service = GmailApiService()
    try:
        access_token = account.get_access_token
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token available")
        
        label_data = await gmail_api_service.create_label(
            access_token=access_token,
            label_name=request.name,
            label_list_visibility=request.label_list_visibility,
            message_list_visibility=request.message_list_visibility
        )
        
        return LabelResponse(
            id=label_data.get("id", ""),
            name=label_data.get("name", ""),
            label_list_visibility=label_data.get("labelListVisibility", ""),
            message_list_visibility=label_data.get("messageListVisibility", ""),
            type=label_data.get("type", "user")
        )
        
    except ValueError as e:
        logger.error(f"Failed to create label: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create label: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/emails", response_model=List[EmailResponse])
async def get_emails(
    account_id: UUID = Path(..., description="Gmail account ID"),
    folder: str = Query('INBOX', description="Folder to fetch from"),
    limit: int = Query(50, ge=1, le=200, description="Number of emails to fetch"),
    offset: int = Query(0, ge=0, description="Number of emails to skip"),
    since_date: Optional[str] = Query(None, description="Fetch emails since date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user)
):
    """Fetch emails from a Gmail account"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token available")
        
        fetch_limit = limit + offset
        await imap_service.connect(access_token, account.email_address)
        emails = await imap_service.fetch_emails(folder, fetch_limit, since_date)

        # Apply offset
        emails = emails[offset:offset+limit]
        
        return [
            EmailResponse(
                uid=e.uid,
                subject=e.subject,
                from_address=e.from_address,
                to_addresses=e.to_addresses,
                date=e.date,
                body_text=e.body_text,
                body_html=e.body_html,
                labels=e.labels,
                attachments=e.attachments,
                message_id=e.message_id,
                in_reply_to=e.in_reply_to,
                references=e.references,
                is_thread=bool(e.in_reply_to or e.references),  # True if part of thread
            )
            for e in emails
        ]
        
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()

@router.get("/accounts/{account_id}/search", response_model=List[EmailResponse])
async def search_emails(
    account_id: UUID = Path(..., description="Gmail account ID"),
    query: str = Query(..., description="Gmail search query"),
    folder: str = Query('INBOX', description="Folder to search in"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Search emails using Gmail search syntax"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token available")
        
        await imap_service.connect(access_token, account.email_address)
        emails = await imap_service.search_emails(query, folder, limit)
        
        return [
            EmailResponse(
                uid=e.uid,
                subject=e.subject,
                from_address=e.from_address,
                to_addresses=e.to_addresses,
                date=e.date,
                body_text=e.body_text,
                body_html=e.body_html,
                labels=e.labels,
                attachments=e.attachments,
                message_id=e.message_id,
                in_reply_to=e.in_reply_to,
                references=e.references,
                is_thread=bool(e.in_reply_to or e.references),  # True if part of thread
            )
            for e in emails
        ]
        
    except Exception as e:
        logger.error(f"Failed to search emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()

@router.post("/accounts/{account_id}/emails/{uid}/labels/{label}")
async def add_label_to_email(
    account_id: UUID = Path(...),
    uid: int = Path(...),
    label: str = Path(...),
    folder: str = Query('INBOX'),
    current_user: User = Depends(get_current_user)
):
    """Add label to an email"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        await imap_service.connect(access_token, account.email_address)
        success = await imap_service.add_label(uid, label, folder)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add label")
        
        return {"message": "Label added successfully"}
        
    except Exception as e:
        logger.error(f"Failed to add label: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()

@router.delete("/accounts/{account_id}/emails/{uid}/labels/{label}")
async def remove_label_from_email(
    account_id: UUID = Path(...),
    uid: int = Path(...),
    label: str = Path(...),
    folder: str = Query('INBOX'),
    current_user: User = Depends(get_current_user)
):
    """Remove label from an email"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        await imap_service.connect(access_token, account.email_address)
        success = await imap_service.remove_label(uid, label, folder)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove label")
        
        return {"message": "Label removed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to remove label: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()

@router.delete("/accounts/{account_id}/emails/{uid}")
async def delete_email(
    account_id: UUID = Path(...),
    uid: int = Path(...),
    folder: str = Query('INBOX'),
    current_user: User = Depends(get_current_user)
):
    """Delete an email"""
    account = await get_valid_gmail_account(account_id, current_user)
    
    imap_service = GmailImapService()
    try:
        access_token = account.get_access_token
        await imap_service.connect(access_token, account.email_address)
        success = await imap_service.delete_email(uid, folder)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete email")
        
        return {"message": "Email deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await imap_service.disconnect()