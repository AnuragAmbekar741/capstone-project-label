from enum import Enum

class GmailAccountStatus(str, Enum):
    """Gmail account connection status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    ERROR = "error"
    DISCONNECTED = "disconnected"


