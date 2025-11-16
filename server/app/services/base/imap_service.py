from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class EmailMessage:
    """Represents an email message"""
    uid: int
    subject: str
    from_address: str
    to_addresses: List[str]
    date: str
    body_text: Optional[str]
    body_html: Optional[str]
    labels: List[str]
    attachments: List[Dict[str, Any]]
    # Thread identification fields
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[str] = None

@dataclass
class FolderInfo:
    """Represents a Gmail folder/label"""
    name: str
    flags: List[str]
    delimiter: str = '/'

class GmailImapServiceBase(ABC):
    """Abstract base class for Gmail IMAP operations"""
    
    @abstractmethod
    async def connect(self, access_token: str, email_address: str) -> bool:
        """Connect to Gmail IMAP server using XOAUTH2"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from IMAP server"""
        pass
    
    @abstractmethod
    async def list_folders(self) -> List[FolderInfo]:
        """List all folders/labels"""
        pass
    
    @abstractmethod
    async def fetch_emails(
        self,
        folder: str = 'INBOX',
        limit: int = 50,
        since_date: Optional[str] = None
    ) -> List[EmailMessage]:
        """Fetch emails from a folder"""
        pass
    
    @abstractmethod
    async def search_emails(
        self,
        query: str,
        folder: str = 'INBOX',
        limit: int = 50
    ) -> List[EmailMessage]:
        """Search emails"""
        pass
    
    @abstractmethod
    async def add_label(self, uid: int, label: str, folder: str = 'INBOX') -> bool:
        """Add label to email"""
        pass
    
    @abstractmethod
    async def remove_label(self, uid: int, label: str, folder: str = 'INBOX') -> bool:
        """Remove label from email"""
        pass
    
    @abstractmethod
    async def delete_email(self, uid: int, folder: str = 'INBOX') -> bool:
        """Delete an email"""
        pass