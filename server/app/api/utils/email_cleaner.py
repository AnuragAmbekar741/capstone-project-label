import re
import html
from typing import Optional, List
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class EmailCleaner:
    """Utility class for cleaning and sanitizing email data"""
    
    @staticmethod
    def clean_subject(subject: str) -> str:
        """Clean email subject"""
        if not subject:
            return "(No subject)"
        
        # Decode HTML entities
        subject = html.unescape(subject)
        
        # Remove extra whitespace
        subject = ' '.join(subject.split())
        
        # Remove common email prefixes like "Re:", "Fwd:", etc. (optional - you may want to keep them)
        # subject = re.sub(r'^(Re:|Fwd:|FW:|RE:|fwd:)\s*', '', subject, flags=re.IGNORECASE)
        
        return subject.strip()
    
    @staticmethod
    def extract_email_address(address: str) -> str:
        """Extract clean email address from 'Name <email@domain.com>' format"""
        if not address:
            return ""
        
        # Parse address to get email part
        name, email = parseaddr(address)
        
        # If no email found, try to extract from the string
        if not email:
            # Try to find email pattern
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', address)
            if email_match:
                email = email_match.group(0)
            else:
                return address.strip()
        
        return email.strip().lower()
    
    @staticmethod
    def extract_name_from_address(address: str) -> str:
        """Extract name from 'Name <email@domain.com>' format"""
        if not address:
            return ""
        
        name, email = parseaddr(address)
        
        # If name is empty, use email username part
        if not name:
            if email:
                return email.split('@')[0]
            return address.strip()
        
        # Clean the name
        name = html.unescape(name)
        name = name.strip().strip('"').strip("'")
        
        return name
    
    @staticmethod
    def clean_body_text(body_text: Optional[str]) -> Optional[str]:
        """Clean plain text email body"""
        if not body_text:
            return None
        
        # Decode HTML entities
        body_text = html.unescape(body_text)
        
        # Remove HTML tags if present (sometimes text/plain contains HTML)
        body_text = re.sub(r'<[^>]+>', '', body_text)
        
        # Normalize whitespace (replace multiple spaces/newlines with single)
        body_text = re.sub(r'\s+', ' ', body_text)
        
        # Remove common email signatures/separators
        body_text = re.sub(r'-{3,}.*$', '', body_text, flags=re.MULTILINE | re.DOTALL)
        body_text = re.sub(r'_{3,}.*$', '', body_text, flags=re.MULTILINE | re.DOTALL)
        
        return body_text.strip()
    
    @staticmethod
    def clean_body_html(body_html: Optional[str]) -> Optional[str]:
        """Clean HTML email body - basic sanitization"""
        if not body_html:
            return None
        
        # Decode HTML entities
        body_html = html.unescape(body_html)
        
        # Remove dangerous scripts and event handlers
        # Remove script tags
        body_html = re.sub(r'<script[^>]*>.*?</script>', '', body_html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers (onclick, onerror, etc.)
        body_html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', body_html, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        body_html = re.sub(r'javascript:', '', body_html, flags=re.IGNORECASE)
        
        # Remove data: URLs that could be dangerous
        body_html = re.sub(r'data:image/[^;]+;base64[^"\'>\s]+', '', body_html, flags=re.IGNORECASE)
        
        # Normalize whitespace in HTML
        body_html = re.sub(r'\s+', ' ', body_html)
        
        return body_html.strip()
    
    @staticmethod
    def clean_date(date_str: str) -> str:
        """Clean and format email date"""
        if not date_str:
            return ""
        
        try:
            # Parse email date string
            date_obj = parsedate_to_datetime(date_str)
            # Return ISO format string
            return date_obj.isoformat()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return date_str
    
    @staticmethod
    def normalize_datetime_to_utc(dt: datetime) -> datetime:
        """
        Normalize a datetime to timezone-aware UTC.
        
        If the datetime is naive (no timezone), assumes it's UTC and adds timezone info.
        If the datetime is timezone-aware, converts it to UTC.
        
        Args:
            dt: datetime object (can be naive or timezone-aware)
            
        Returns:
            timezone-aware datetime in UTC
        """
        if dt.tzinfo is None:
            # Naive datetime - assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Timezone-aware datetime - convert to UTC
            return dt.astimezone(timezone.utc)
    
    @staticmethod
    def parse_email_date_to_utc(date_str: str) -> datetime:
        """
        Parse an email date string and return a timezone-aware UTC datetime.
        
        Tries multiple parsing strategies:
        1. ISO format with timezone
        2. ISO format without timezone (assumes UTC)
        3. Standard email date format (parsedate_to_datetime)
        4. Direct ISO parsing
        
        Args:
            date_str: Email date string in various formats
            
        Returns:
            timezone-aware datetime in UTC, or datetime.min (UTC) if parsing fails
        """
        try:
            # Try ISO format parsing (e.g., "2025-11-10T14:57:09+05:30")
            if 'T' in date_str:
                # Handle ISO format with timezone
                if '+' in date_str or date_str.endswith('Z'):
                    try:
                        # Handle Z suffix (UTC)
                        if date_str.endswith('Z'):
                            date_str = date_str.replace('Z', '+00:00')
                        # Parse ISO format - already timezone-aware
                        parsed = datetime.fromisoformat(date_str)
                        return EmailCleaner.normalize_datetime_to_utc(parsed)
                    except ValueError:
                        pass
                else:
                    # ISO format without timezone - parse and normalize to UTC
                    parsed = datetime.fromisoformat(date_str)
                    return EmailCleaner.normalize_datetime_to_utc(parsed)
            
            # Try standard email date format
            parsed_date = parsedate_to_datetime(date_str)
            if parsed_date:
                return EmailCleaner.normalize_datetime_to_utc(parsed_date)
            
            # Try direct datetime parsing
            parsed = datetime.fromisoformat(date_str)
            return EmailCleaner.normalize_datetime_to_utc(parsed)
            
        except (ValueError, TypeError, AttributeError) as e:
            # If date parsing fails, return datetime.min in UTC
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return datetime.min.replace(tzinfo=timezone.utc)
    
    @staticmethod
    def filter_system_labels(labels: List[str]) -> List[str]:
        """Filter out system IMAP flags/labels"""
        if not labels:
            return []
        
        # System flags to exclude
        system_flags = {
            '\\Seen', '\\Unseen', '\\Answered', '\\Flagged', '\\Deleted',
            '\\Draft', '\\Recent', 'SEEN', 'UNSEEN', 'ANSWERED', 'FLAGGED',
            'DELETED', 'DRAFT', 'RECENT'
        }
        
        # Filter out system flags and empty strings
        filtered = [
            label for label in labels
            if label and label not in system_flags and not label.startswith('\\')
        ]
        
        return filtered
    
    @staticmethod
    def clean_attachment_filename(filename: Optional[str]) -> str:
        """Clean attachment filename"""
        if not filename:
            return "attachment"
        
        # Decode HTML entities
        filename = html.unescape(filename)
        
        # Remove path components (security)
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        return filename.strip()
    
    @staticmethod
    def clean_email_preview(body_text: Optional[str], body_html: Optional[str], max_length: int = 200) -> str:
        """Create a clean preview text from email body"""
        preview = None
        
        # Prefer text over HTML
        if body_text:
            preview = EmailCleaner.clean_body_text(body_text)
        elif body_html:
            # Strip HTML tags for preview
            preview = re.sub(r'<[^>]+>', '', body_html)
            preview = html.unescape(preview)
            preview = re.sub(r'\s+', ' ', preview).strip()
        
        if not preview:
            return "(No content)"
        
        # Truncate to max_length
        if len(preview) > max_length:
            preview = preview[:max_length].rsplit(' ', 1)[0] + '...'
        
        return preview
