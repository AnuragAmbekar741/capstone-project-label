from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class GmailOAuthServiceBase(ABC):
    """
    Abstract base class for Gmail OAuth service
    Defines the contract for Gmail OAuth operations
    """

    @abstractmethod
    def get_auth_url(self,state:Optional[str]=None)->str:
        pass

    @abstractmethod
    def exchange_tokens(self,code:str)->Dict[str,Any]:
        pass

    @abstractmethod
    def refresh_auth_access_token(self,refresh_token:str) ->Dict[str,Any]:
        pass
