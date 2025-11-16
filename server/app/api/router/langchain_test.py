# server/app/api/router/test.py
"""
Test endpoints for LangChain integration.
These endpoints help verify that LangChain + Gemini is working correctly.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.default.langchain_service import LangChainService
import logging

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/test", tags=["Testing"])


# Response models
class LangChainTestResponse(BaseModel):
    """Response model for LangChain test endpoint"""
    status: str
    service_type: str
    model: str
    configured: bool
    connection_test: str
    message: str


class LangChainTestErrorResponse(BaseModel):
    """Error response model for LangChain test endpoint"""
    status: str
    error: str
    message: str


@router.get(
    "/langchain",
    response_model=LangChainTestResponse,
    responses={
        500: {"model": LangChainTestErrorResponse}
    },
    summary="Test LangChain + Gemini Integration",
    description="""
    Test endpoint to verify LangChain + Gemini Free Tier integration.
    
    This endpoint:
    1. Creates a LangChainService instance (default implementation)
    2. Checks if the service is configured
    3. Tests the connection to Gemini
    4. Returns the model name and test results
    
    **Requirements:**
    - GOOGLE_API_KEY must be set in .env file
    - Get your free API key at: https://aistudio.google.com/apikey
    """
)
async def test_langchain():
    """
    Test LangChain + Gemini integration.
    
    Returns:
        LangChainTestResponse with test results
    """
    try:
        # Create service instance (uses default implementation)
        service = LangChainService()
        
        # Test 1: Check configuration
        is_configured = service.is_configured()
        model_name = service.get_model_name()
        
        # Test 2: Test connection to Gemini
        connection_test = service.test_connection()
        
        return LangChainTestResponse(
            status="success",
            service_type="LangChainService (Default Implementation)",
            model=model_name,
            configured=is_configured,
            connection_test=connection_test,
            message="✓ LangChain base/default pattern is working!"
        )
        
    except ValueError as e:
        # Configuration error (missing API key, etc.)
        logger.error(f"LangChain configuration error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "message": "Configuration error. Please set GOOGLE_API_KEY in your .env file. "
                          "Get your free API key at: https://aistudio.google.com/apikey"
            }
        )
    except Exception as e:
        # Other errors (API errors, network issues, etc.)
        logger.error(f"LangChain test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "message": "LangChain service failed. Check your configuration and API key."
            }
        )