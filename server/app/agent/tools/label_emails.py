# server/app/agent/tools/label_emails.py
from langchain_core.tools import tool
from app.services.default.langchain_service import langchain_service
from app.services.workers.redis_label_cache import RedisLabelCache
from typing import List, Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

# Initialize Redis label cache (singleton)
_label_cache = None

def get_label_cache():
    """Get or create Redis label cache instance"""
    global _label_cache
    if _label_cache is None:
        _label_cache = RedisLabelCache()
    return _label_cache


@tool
def label_emails_batch(
    emails: List[Dict[str, str]],
    account_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Label multiple emails using AI. 
    """
    try:
        if not emails:
            logger.warning("No emails provided for labeling")
            return []
        
        # Get LLM from langchain_service and Redis cache
        llm = langchain_service.llm
        label_cache = get_label_cache()
        
        # Get existing labels from Redis cache
        existing_labels = []
        if account_id:
            existing_labels = label_cache.get_labels(account_id)
            logger.info(f"Retrieved {len(existing_labels)} existing labels for account {account_id}")
        
        # Build context from existing labels
        labels_context = ""
        if existing_labels:
            labels_context = f"""
EXISTING LABELS FOR THIS ACCOUNT:
{', '.join(existing_labels)}

IMPORTANT RULES:
1. If an email matches an existing label's purpose, use that EXACT label name (case-sensitive).
2. Only create a NEW label if the email doesn't fit any existing label.
3. Be specific and concise with label names (1-3 words max).
4. Use consistent labels across similar emails.
"""
        else:
            labels_context = """
NOTE: No existing labels found. You can suggest new label names.
Keep label names short and descriptive (1-3 words max).
Be consistent - use the same label for similar emails.
"""
        
        # Format emails for the prompt
        emails_text = ""
        for idx, email in enumerate(emails, 1):
            email_id = email.get("id", f"email_{idx}")
            subject = email.get("subject", "(No subject)")
            body = email.get("body", "")
            
            # Limit body text to avoid token limits
            body_preview = body[:500] + ("..." if len(body) > 500 else "") if body else "(No body)"
            
            emails_text += f"""
Email #{idx}:
  ID: {email_id}
  Subject: {subject}
  Body: {body_preview}
"""
        
        # Create prompt
        prompt = f"""{labels_context}

Analyze these emails and suggest a label for each. Respond with a JSON array in this exact format:

[
  {{
    "email_id": "email_1_id",
    "label": "Work",
    "confidence": 0.9,
    "reasoning": "Email is about work project meeting"
  }},
  {{
    "email_id": "email_2_id",
    "label": "Finance",
    "confidence": 0.85,
    "reasoning": "Email contains invoice information"
  }}
]

Emails to label:
{emails_text}

Respond ONLY with the JSON array, no other text.
"""
        
        # Get response from LLM
        logger.info(f"Labeling {len(emails)} emails in batch...")
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Parse JSON (handle markdown code blocks if present)
        if content.startswith("son"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(content)
            
            # Ensure it's a list
            if isinstance(result, dict) and "labels" in result:
                result = result["labels"]
            elif not isinstance(result, list):
                raise ValueError("Expected JSON array")
            
            # Validate and structure results
            labels_result = []
            for item in result:
                labels_result.append({
                    "email_id": str(item.get("email_id", "")),
                    "label": str(item.get("label", "")).strip(),
                    "confidence": float(item.get("confidence", 0.5)),
                    "reasoning": str(item.get("reasoning", ""))
                })
            
            logger.info(f"Successfully labeled {len(labels_result)} emails")
            return labels_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {content}")
            # Fallback: return error for all emails
            return [
                {
                    "email_id": email.get("id", "unknown"),
                    "label": "",
                    "confidence": 0.0,
                    "reasoning": f"Error parsing response: {str(e)}"
                }
                for email in emails
            ]
        
    except Exception as e:
        logger.error(f"Error in label_emails_batch tool: {e}")
        # Return error results for all emails
        return [
            {
                "email_id": email.get("id", "unknown"),
                "label": "",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
            for email in emails
        ]