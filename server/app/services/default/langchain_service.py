from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.services.base.langchain_service import LangChainServiceBase
from app.config import settings
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)


class LangChainService(LangChainServiceBase):    
    def __init__(self):
        self.llm = None
        self._model_name = ""
        self._is_configured = False
        self._provider = settings.LLM_PROVIDER.lower()
        
        # Initialize based on provider
        if self._provider == "openai":
            self._init_openai()
        elif self._provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}. Use 'gemini' or 'openai'")
    
    def _init_openai(self):
        """Initialize OpenAI model"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")
        
        try:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                openai_api_key=settings.OPENAI_API_KEY,
            )
            
            self._model_name = settings.OPENAI_MODEL
            self._is_configured = True
            
            logger.info(
                f"LangChain service initialized with OpenAI model: {self._model_name}"
            )
            
        except Exception as e:
            self._is_configured = False
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise
    
    def _init_gemini(self):
        """Initialize Gemini model"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=settings.GEMINI_TEMPERATURE,
                google_api_key=settings.GEMINI_API_KEY,
            )
            
            self._model_name = settings.GEMINI_MODEL
            self._is_configured = True
            
            logger.info(
                f"LangChain service initialized with Gemini model: {self._model_name}"
            )
            
        except Exception as e:
            self._is_configured = False
            logger.error(f"Failed to initialize Gemini service: {e}")
            raise
    
    def test_connection(self) -> str:
        try:
            # Simple test - ask model to confirm it's working
            response = self.llm.invoke(
                f"Say 'Hello, LangChain with {self._provider.upper()} is working!' in one sentence."
            )
            return response.content
        except Exception as e:
            logger.error(f"{self._provider.upper()} connection test failed: {e}")
            raise
    
    def get_model_name(self) -> str:
        return self._model_name
    
    def is_configured(self) -> bool:
        return self._is_configured

    def label_email(
        self,
        email_subject: str,
        email_body: str,
        existing_labels: List[str]
    ) -> Dict[str, Any]:
        """
        Label an email using AI based on subject, body, and existing labels.
        Works with both OpenAI and Gemini models.
        """
        try:
            # Clean and sanitize inputs
            email_subject = (email_subject or "").strip()
            email_body = (email_body or "").strip()
            
            # Build prompt with context
            labels_context = ""
            if existing_labels:
                labels_context = f"""
Existing labels in your account:
{', '.join(existing_labels)}

Please suggest a label from the existing labels above, or suggest a new appropriate label name if none match.
"""
            else:
                labels_context = """
You don't have any existing labels yet. Please suggest an appropriate label name for this email.
"""

            # Limit body to 2000 chars to avoid token limits
            email_body_limited = email_body[:2000] if email_body else ""

            prompt = f"""You are an email organization assistant. Analyze the following email and suggest the most appropriate label.

{labels_context}

Email Subject: {email_subject}

Email Body:
{email_body_limited}

Instructions:
1. If an existing label matches the email content, return that exact label name
2. If no existing label matches, suggest a new concise label name (2-4 words max)
3. Return your response as a JSON object with this exact format:
{{
    "label": "label_name_here",
    "reason": "brief explanation why this label fits"
}}

Only return the JSON object, no additional text."""

            # Invoke LLM
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Try to parse JSON from response
            # Sometimes LLM adds markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                result = json.loads(response_text)
                label_name = result.get("label", "").strip()
                reason = result.get("reason", "")
                
                if not label_name:
                    raise ValueError("Empty label name in response")
                
                logger.info(f"AI suggested label: {label_name} (reason: {reason})")
                
                return {
                    "label": label_name,
                    "reason": reason,
                    "confidence": "high"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {response_text}")
                # Fallback: try to extract label from text
                lines = response_text.split("\n")
                for line in lines:
                    if "label" in line.lower() and ":" in line:
                        label_name = line.split(":")[-1].strip().strip('"').strip("'")
                        if label_name:
                            return {
                                "label": label_name,
                                "reason": "AI suggested label",
                                "confidence": "medium"
                            }
                raise ValueError(f"Could not parse label from response: {response_text}")
                
        except Exception as e:
            logger.error(f"Error labeling email with AI: {e}")
            raise ValueError(f"Failed to label email: {str(e)}")

    def label_emails_batch(
        self,
        emails: List[Dict[str, Any]],
        existing_labels: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Label multiple emails in a single batch using AI.
        Works with both OpenAI and Gemini models.
        """
        try:
            if not emails:
                return []
            
            # Build prompt with context
            labels_context = ""
            if existing_labels:
                labels_context = f"""
Existing labels in your account:
{', '.join(existing_labels)}

For each email, suggest a label from the existing labels above, or suggest a new appropriate label name if none match.
"""
            else:
                labels_context = """
You don't have any existing labels yet. For each email, suggest an appropriate label name.
"""

            # Format emails for prompt
            emails_text = ""
            for idx, email in enumerate(emails, 1):
                subject = (email.get('subject') or '').strip()
                body = (email.get('body') or '').strip()[:1000]  # Limit body to 1000 chars per email
                
                emails_text += f"""
Email {idx}:
ID: {email.get('id')}
Subject: {subject}
Body: {body}
---
"""

            prompt = f"""You are an email organization assistant. Analyze the following emails and suggest the most appropriate label for each one.

{labels_context}

Emails to label:
{emails_text}

Instructions:
1. For each email, if an existing label matches the email content, return that exact label name
2. If no existing label matches, suggest a new concise label name (2-4 words max)
3. Return your response as a JSON array with this exact format:
[
  {{
    "id": "email_id_1",
    "label": "label_name_here",
    "reason": "brief explanation why this label fits"
  }},
  {{
    "id": "email_id_2",
    "label": "label_name_here",
    "reason": "brief explanation why this label fits"
  }}
]

Only return the JSON array, no additional text. Make sure to include all {len(emails)} emails."""

            # Invoke LLM
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Try to parse JSON from response
            # Sometimes LLM adds markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                results = json.loads(response_text)
                
                # Validate it's a list
                if not isinstance(results, list):
                    raise ValueError("Response is not a list")
                
                # Validate all emails have results
                if len(results) != len(emails):
                    logger.warning(f"Expected {len(emails)} labels, got {len(results)}")
                
                # Process results
                labeled_emails = []
                for result in results:
                    email_id = result.get("id")
                    label_name = result.get("label", "").strip()
                    reason = result.get("reason", "")
                    
                    if not email_id or not label_name:
                        logger.warning(f"Invalid result: {result}")
                        continue
                    
                    labeled_emails.append({
                        "id": email_id,
                        "label": label_name,
                        "reason": reason
                    })
                
                logger.info(f"✅ Successfully labeled {len(labeled_emails)}/{len(emails)} emails in batch")
                return labeled_emails
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {response_text}")
                raise ValueError(f"Could not parse batch label response: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error batch labeling emails: {e}")
            raise ValueError(f"Failed to batch label emails: {str(e)}")

langchain_service = LangChainService()