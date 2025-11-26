from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.base.langchain_service import LangChainServiceBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LangChainService(LangChainServiceBase):    
    def __init__(self):
        # Validate configuration
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found."
            )

        try:
            # Initialize Gemini model (free tier: gemini-1.5-flash)
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,  # Default: "gemini-1.5-flash"
                temperature=settings.GEMINI_TEMPERATURE,
                google_api_key=settings.GEMINI_API_KEY,
            )
            
            self._model_name = settings.GEMINI_MODEL
            self._is_configured = True
            
            logger.info(
                f"LangChain service initialized with model: {self._model_name}"
            )
            
        except Exception as e:
            self._is_configured = False
            logger.error(f"Failed to initialize LangChain service: {e}")
            raise
    
    def test_connection(self) -> str:
        try:
            # Simple test - ask Gemini to confirm it's working
            response = self.llm.invoke(
                "Say 'Hello, LangChain with Gemini is working!' in one sentence."
            )
            return response.content
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            raise
    
    def get_model_name(self) -> str:
        return self._model_name
    
    def is_configured(self) -> bool:
        return self._is_configured

langchain_service = LangChainService()