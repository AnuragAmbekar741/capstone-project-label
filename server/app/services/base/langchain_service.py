from abc import ABC, abstractmethod
from typing import Optional


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