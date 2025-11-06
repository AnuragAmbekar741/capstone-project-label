# llm_api/prompts.py
"""
EmailSum-aligned prompts using the same linearization you trained with:
- Body is produced by preprocess.thread_to_source(thread)  (messages joined by " ||| ")
- Subject is included on a separate line (optional, low-risk addition)
- Task prefixes: emailsum_summarize / emailsum_categorize / emailsum_suggest
- Length control tokens for summary: <SHORT> / <LONG>
- Outputs remain compatible with existing parsers
"""

from .models import Thread
from .preprocess import thread_to_source


def _emailsum_block(thread: Thread) -> str:
    """Minimal-risk linearization: subject on its own line, then EmailSum-style body."""
    subj = (thread.subject or "").strip()
    body = thread_to_source(thread)  # uses " ||| " between messages
    if subj:
        return f"Subject: {subj}\nThread:\n{body}"
    return f"Thread:\n{body}"


# -------------------------
# SUMMARIZE (keeps short/long)
# -------------------------

def summarize_prompt(thread: Thread) -> str:
    """
    EmailSum-style summarization with length control.
    Output format (plain text) remains:
      Summary:
      Key Points:
      Actions:
      Dates:
      Entities:
    """
    mode = (thread.mode or "short").lower()
    length_tok = "<LONG>" if mode == "long" else "<SHORT>"
    block = _emailsum_block(thread)

    return (
        f"emailsum_summarize: {length_tok}\n\n"
        "You will summarize the following email thread. Preserve concrete facts (names, amounts, dates, refs),\n"
        "the original intent/tone, and actionable details. After the summary paragraph, list bullets.\n"
        "Do not invent information. Plain text only.\n\n"
        "Return format:\n"
        "Summary: <one paragraph>\n"
        "Key Points:\n"
        "- <point 1>\n"
        "- <point 2>\n"
        "Actions:\n"
        "- <action 1>\n"
        "Dates:\n"
        "- <date or deadline 1>\n"
        "Entities:\n"
        "- <person/org/product/account id 1>\n\n"
        f"{block}"
    )


# -------------------------
# CATEGORIZE (free-form labels, JSON)
# -------------------------

def categorize_prompt(thread: Thread) -> str:
    """
    Lets the model infer categories directly from text (no fixed label set).
    Returns strict JSON with labels + rationale for your downstream parser.
    """
    block = _emailsum_block(thread)
    return (
        "emailsum_categorize:\n\n"
        "Analyze the email content and infer meaningful, free-form categories that describe:\n"
        "- domain/topic (e.g., banking, billing, travel, support, hiring, security_alert, newsletter),\n"
        "- intent (e.g., statement, receipt, action_required, request_info, fyi),\n"
        "- tone/sentiment, and any salient tags (e.g., password, otp, invoice, shipment, meeting).\n\n"
        "Rules:\n"
        "- Do NOT restrict to a predefined list.\n"
        "- Prefer 1-3 concise labels; use lowercase snake_case where natural.\n"
        "- Return JSON ONLY with exactly these fields: labels (array of strings), rationale (short text).\n\n"
        "Return JSON:\n"
        "{\n"
        '  "labels": ["<label1>", "<label2>", "..."],\n'
        '  "rationale": "<one or two sentences>"\n'
        "}\n\n"
        f"{block}"
    )


# -------------------------
# SUGGEST (recipient-centric actions/replies)
# -------------------------

def suggest_prompt(thread: Thread) -> str:
    """
    Generates recipient-centric suggestions: 2–3 short one-liners + 1 longer draft reply.
    Plain text output to match existing parser.
    """
    block = _emailsum_block(thread)
    return (
        "emailsum_suggest:\n\n"
        "You are assisting the recipient of this email. Based on the thread, propose what the recipient should:\n"
        "- do next (actions),\n"
        "- ask/clarify,\n"
        "- or reply with (polite, concise).\n\n"
        "Produce:\n"
        "- 2–3 short, actionable suggestions (one line each, imperative, recipient-centric).\n"
        "- One longer, well-phrased draft reply (3–6 sentences) that can be sent as-is.\n\n"
        "Output format (plain text, no JSON):\n"
        "Suggestions:\n"
        "- <short suggestion 1>\n"
        "- <short suggestion 2>\n"
        "- <short suggestion 3>\n\n"
        "Draft:\n"
        "<long, polished reply paragraph(s) here>\n\n"
        f"{block}"
    )
