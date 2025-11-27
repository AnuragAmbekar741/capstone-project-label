from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class LangChainServiceBase(ABC):
    """
    Abstract base class for LangChain service.
    Defines the contract for LangChain operations.
    """

    @abstractmethod
    def __init__(self):
        """
        Initialize the LangChain service.
        Must set up the model and configuration.
        """
        pass

    @abstractmethod
    def test_connection(self) -> str:
        """
        Test if the LangChain model connection is working.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the model being used.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the service is properly configured.
        """
        pass

    @abstractmethod
    def label_email(
        self,
        email_subject: str,
        email_body: str,
        existing_labels: List[str]
    ) -> Dict[str, Any]:
        """
        Label an email using AI based on subject, body, and existing labels.
        
        Args:
            email_subject: Email subject line
            email_body: Email body text (plain text preferred)
            existing_labels: List of existing labels from Redis cache
        
        Returns:
            Dictionary with 'label' (suggested label name) and 'confidence' (optional)
        """
        pass

    @abstractmethod
    def label_emails_batch(
        self,
        emails: List[Dict[str, Any]],
        existing_labels: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Label multiple emails in a single batch using AI.
        
        Args:
            emails: List of email dictionaries with keys: 'id', 'subject', 'body'
            existing_labels: List of existing labels from Redis cache
        
        Returns:
            List of dictionaries with 'id', 'label', 'reason' for each email
        """
        pass