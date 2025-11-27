from imapclient import IMAPClient
from typing import List, Dict, Optional, Any
import logging
import email
import base64
from email.header import decode_header
from app.services.base.imap_service import (
    GmailImapServiceBase,
    EmailMessage,
    FolderInfo
)
from app.api.utils.email_cleaner import EmailCleaner
from datetime import datetime, timezone
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

class GmailImapService(GmailImapServiceBase):
    """
    Gmail IMAP service implementation using imapclient
    Uses XOAUTH2 authentication with OAuth access tokens
    """
    
    def __init__(self):
        self.client: Optional[IMAPClient] = None
        self.access_token: Optional[str] = None
        self.email_address: Optional[str] = None
    
    def _create_oauth2_string(self, email: str, access_token: str) -> str:
        """
        Create XOAUTH2 authentication string
        Format: user=email\1auth=Bearer token\1\1
        Then base64 encode it
        """
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        auth_string_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        return auth_string_b64
    
    async def connect(self, access_token: str, email_address: str) -> bool:
        """
        Connect to Gmail IMAP server using XOAUTH2
        
        Args:
            access_token: OAuth access token
            email_address: User's email address
            
        Returns:
            True if connected successfully
        """
        try:
            self.access_token = access_token
            self.email_address = email_address
            
            logger.info(f"Connecting to Gmail IMAP for {email_address}")
            
            # Validate inputs
            if not access_token:
                raise ValueError("Access token is empty")
            if not email_address:
                raise ValueError("Email address is empty")
            
            host = 'imap.gmail.com'
            port = 993
            
            # Connect to IMAP server
            logger.info(f"Connecting to {host}:{port}")
            self.client = IMAPClient(host, port=port, use_uid=True, ssl=True)
            logger.info("IMAP TCP connection established")
            
            # Check capabilities
            try:
                caps = self.client.capabilities()
                logger.debug(f"📋 Server capabilities: {caps}")
                if b'AUTH=XOAUTH2' not in caps:
                    logger.warning("Server may not support XOAUTH2")
            except Exception as e:
                logger.warning(f"Could not check capabilities: {e}")
            
            # Try oauth2_login first if it exists
            if hasattr(self.client, 'oauth2_login'):
                logger.info("�� Attempting oauth2_login() method...")
                try:
                    self.client.oauth2_login(email_address, access_token)
                    logger.info(f"✅ Successfully authenticated using oauth2_login()")
                    return True
                except AttributeError:
                    logger.warning("oauth2_login() not available, using manual XOAUTH2")
                except Exception as e:
                    logger.error(f"oauth2_login() failed: {e}")
                    logger.info("Falling back to manual XOAUTH2...")
            
            auth_string = f"user={email_address}\x01auth=Bearer {access_token}\x01\x01"

            def oauth2_auth_handler(challenge):
                return auth_string
            
            self.client._imap.authenticate('XOAUTH2', oauth2_auth_handler)
            logger.info(f"Successfully authenticated to Gmail IMAP for {email_address}")
            return True
            
        except AttributeError as e:
            logger.error(f"Attribute error - method not found: {e}")
            if self.client:
                logger.error(f"Available methods: {[m for m in dir(self.client) if not m.startswith('_')]}")
            self.client = None
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {type(e).__name__}: {e}")
            logger.error(f"Full error traceback:", exc_info=True)
            self.client = None
            return False
    
    async def disconnect(self):
        """Disconnect from IMAP server"""
        if self.client:
            try:
                self.client.logout()
                self.client = None
                logger.info("Disconnected from Gmail IMAP")
            except Exception as e:
                logger.error(f"Error disconnecting from IMAP: {e}")
    
    async def list_folders(self) -> List[FolderInfo]:
        """List all folders/labels"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            folders = self.client.list_folders()
            folder_info_list = []
            
            for flags, delimiter, name in folders:
                folder_info = FolderInfo(
                    name=name.decode('utf-8') if isinstance(name, bytes) else name,
                    flags=[f.decode('utf-8') if isinstance(f, bytes) else f for f in flags],
                    delimiter=delimiter.decode('utf-8') if isinstance(delimiter, bytes) else delimiter
                )
                folder_info_list.append(folder_info)
            
            return folder_info_list
            
        except Exception as e:
            logger.error(f"Failed to list folders: {e}")
            raise
    
    async def fetch_emails(
        self,
        folder: str = 'INBOX',
        limit: int = 50,
        since_date: Optional[str] = None
    ) -> List[EmailMessage]:
        """Fetch emails from a folder"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            # Select folder
            self.client.select_folder(folder)
            
            # Build search criteria
            if since_date:
                try:
                    # Validate the date format is DD-MMM-YYYY
                    # datetime is already imported at the top of the file
                    datetime.strptime(since_date, '%d-%b-%Y')
                    # Use the date directly - no conversion needed
                    search_criteria = ['SINCE', since_date]
                except ValueError as e:
                    logger.warning(f"Invalid date format '{since_date}': {e}. Using ALL instead.")
                    search_criteria = ['ALL']
            else:
                search_criteria = ['ALL']
            
            # Search for emails
            search_results = self.client.search(search_criteria)
            
            # Convert SearchIds to list if needed
            if hasattr(search_results, '__iter__') and not isinstance(search_results, (str, bytes)):
                uids = list(search_results)
            else:
                uids = search_results if isinstance(search_results, list) else []
            
            # If no UIDs found, return empty list
            if not uids:
                logger.info(f"No emails found in folder {folder}")
                return []
            
            # Reverse to get most recent first (IMAP returns UIDs in ascending order)
            uids = list(reversed(uids))
            
            # Limit results to most recent emails
            if len(uids) > limit:
                uids = uids[:limit]
            
            # Fetch emails
            messages = self.client.fetch(uids, ['RFC822', 'FLAGS', 'ENVELOPE'])
            
            email_list = []
            for uid, data in messages.items():
                try:
                    email_msg = self._parse_email(uid, data)
                    email_list.append(email_msg)
                except Exception as e:
                    logger.error(f"Failed to parse email {uid}: {e}")
                    continue
            
            # Sort by date (most recent first) to ensure correct order
            def get_date_sort_key(email: EmailMessage) -> datetime:
                """Get timezone-aware UTC datetime for sorting"""
                return EmailCleaner.parse_email_date_to_utc(email.date)
            
            # Sort by date (most recent first - reverse=True)
            email_list.sort(key=get_date_sort_key, reverse=True)
            
            # Ensure we only return the top limit most recent
            return email_list[:limit]
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise
    
    async def search_emails(
        self,
        query: str,
        folder: str = 'INBOX',
        limit: int = 50
    ) -> List[EmailMessage]:
        """Search emails using Gmail search syntax"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            # Select folder
            self.client.select_folder(folder)
            
            # Gmail supports X-GM-RAW for advanced search
            # Format: X-GM-RAW "search query"
            search_criteria = ['X-GM-RAW', f'"{query}"']
            
            # Search
            uids = self.client.search(search_criteria)
            
            # Limit results
            if len(uids) > limit:
                uids = uids[-limit:]
            
            # Fetch emails
            messages = self.client.fetch(uids, ['RFC822', 'FLAGS', 'ENVELOPE'])
            
            email_list = []
            for uid, data in messages.items():
                try:
                    email_msg = self._parse_email(uid, data)
                    email_list.append(email_msg)
                except Exception as e:
                    logger.error(f"Failed to parse email {uid}: {e}")
                    continue
            
            return email_list
            
        except Exception as e:
            logger.error(f"Failed to search emails: {e}")
            raise
    
    async def add_label(self, uid: int, label: str, folder: str = 'INBOX') -> bool:
        """Add label to email"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            self.client.select_folder(folder)
            self.client.add_gmail_labels(uid, label)
            return True
        except Exception as e:
            logger.error(f"Failed to add label {label} to email {uid}: {e}")
            return False
    
    async def remove_label(self, uid: int, label: str, folder: str = 'INBOX') -> bool:
        """Remove label from email"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            self.client.select_folder(folder)
            self.client.remove_gmail_labels(uid, label)
            return True
        except Exception as e:
            logger.error(f"Failed to remove label {label} from email {uid}: {e}")
            return False
    
    async def delete_email(self, uid: int, folder: str = 'INBOX') -> bool:
        """Delete an email"""
        if not self.client:
            raise ValueError("Not connected to IMAP server")
        
        try:
            self.client.select_folder(folder)
            # Add Deleted flag and expunge
            self.client.set_flags(uid, [b'\\Deleted'])
            self.client.expunge()
            return True
        except Exception as e:
            logger.error(f"Failed to delete email {uid}: {e}")
            return False
    
    async def create_label(
        self,
        access_token: str,
        label_name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show"
    ) -> Dict[str, Any]:
        """
        Create a new label in Gmail using REST API
        Note: IMAP doesn't support creating labels, so we use Gmail REST API
        """
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": label_name,
            "labelListVisibility": label_list_visibility,
            "messageListVisibility": message_list_visibility
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                label_data = response.json()
                
                logger.info(f"Successfully created label: {label_name} (ID: {label_data.get('id')})")
                return label_data
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            
            logger.error(f"Failed to create label '{label_name}': {error_detail}")
            raise ValueError(f"Failed to create label: {error_detail}")
        except Exception as e:
            logger.error(f"Unexpected error creating label '{label_name}': {e}")
            raise ValueError(f"Failed to create label: {str(e)}")
    
    def _parse_email(self, uid: int, data: Dict) -> EmailMessage:
        """Parse IMAP email data into EmailMessage with cleaning"""
        try:
            # Parse RFC822 message
            msg_data = data[b'RFC822']
            msg = email.message_from_bytes(msg_data)
            
            # Decode and clean headers
            raw_subject = self._decode_header(msg.get('Subject', ''))
            subject = EmailCleaner.clean_subject(raw_subject)
            
            raw_from = self._decode_header(msg.get('From', ''))
            from_addr = EmailCleaner.extract_email_address(raw_from)
            
            raw_to = [self._decode_header(addr) for addr in msg.get_all('To', [])]
            to_addrs = [EmailCleaner.extract_email_address(addr) for addr in raw_to]
            
            raw_date = msg.get('Date', '')
            date_str = EmailCleaner.clean_date(raw_date)
            
            # Extract thread identification headers
            message_id = msg.get('Message-ID', '').strip() or None
            in_reply_to = msg.get('In-Reply-To', '').strip() or None
            references = msg.get('References', '').strip() or None
            
            # Extract body
            body_text = None
            body_html = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain' and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode('utf-8', errors='ignore')
                            body_text = EmailCleaner.clean_body_text(body_text)
                    elif content_type == 'text/html' and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode('utf-8', errors='ignore')
                            body_html = EmailCleaner.clean_body_html(body_html)
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode('utf-8', errors='ignore')
                    if content_type == 'text/html':
                        body_html = EmailCleaner.clean_body_html(decoded)
                    else:
                        body_text = EmailCleaner.clean_body_text(decoded)
            
            # Extract and filter labels/flags
            flags = data.get(b'FLAGS', [])
            raw_labels = [f.decode('utf-8') for f in flags if isinstance(f, bytes)]
            labels = EmailCleaner.filter_system_labels(raw_labels)
            
            # Extract and clean attachments
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        cleaned_filename = EmailCleaner.clean_attachment_filename(filename)
                        attachments.append({
                            'filename': cleaned_filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b'')
                        })
            
            return EmailMessage(
                uid=uid,
                subject=subject,
                from_address=from_addr,
                to_addresses=to_addrs,
                date=date_str,
                body_text=body_text,
                body_html=body_html,
                labels=labels,
                attachments=attachments,
                message_id=message_id,
                in_reply_to=in_reply_to,
                references=references,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse email: {e}")
            raise
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ''
        
        try:
            decoded_parts = decode_header(header)
            decoded_str = ''
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_str += part
            return decoded_str
        except Exception:
            return str(header)