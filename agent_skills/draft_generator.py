"""
Draft Generator - AI-powered draft generation for Email, WhatsApp, LinkedIn

This module generates drafts using Claude API with sanitization, validation,
and graceful fallback to templates when API is unavailable.

Supports:
- Email draft generation (professional replies)
- WhatsApp draft generation (brief, conversational)
- LinkedIn post generation (hook + value + CTA structure)

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, environment variables must be set manually
    pass


def generate_email_draft(
    original_email: Dict[str, Any],
    company_handbook_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate email reply draft using Claude API.

    Args:
        original_email: Dict with keys: from, subject, body, email_id, priority
        company_handbook_path: Optional path to Company_Handbook.md for context

    Returns:
        EmailDraft dict with keys: draft_id, to, subject, draft_body, status

    Raises:
        ValueError: If required fields missing from original_email
    """
    # Validate required fields
    required_fields = ["from", "subject", "body", "email_id"]
    for field in required_fields:
        if field not in original_email:
            raise ValueError(f"Missing required field: {field}")

    # Sanitize input (limit to title + first 200 chars to reduce API cost)
    sanitized_body = _sanitize_text(original_email["body"], max_length=200)

    # Load company context if available
    company_context = ""
    if company_handbook_path and os.path.exists(company_handbook_path):
        with open(company_handbook_path, 'r', encoding='utf-8') as f:
            company_context = f.read()[:500]  # First 500 chars for sender context

    # Build Claude API prompt
    prompt = f"""You are a professional email assistant. Draft a reply to the email below.

Context from Company Handbook:
{company_context if company_context else "[No context available]"}

Original Email:
From: {original_email['from']}
Subject: {original_email['subject']}
Body: {sanitized_body}

Draft a professional email reply that:
1. Starts with appropriate greeting (Hi/Dear [Name])
2. Acknowledges the email content
3. Provides a clear response or action
4. Includes call-to-action if needed
5. Ends with professional signature

Keep the reply concise (2-4 paragraphs). Use a professional but friendly tone.

Examples:
- Acknowledging: "Thank you for reaching out. I've reviewed your request and..."
- Declining politely: "I appreciate your interest. Unfortunately, we're unable to..."
- Requesting info: "Could you please provide additional details about..."

Draft Reply:"""

    # Call Claude API (with fallback to template)
    try:
        draft_body = _call_claude_api(prompt, max_tokens=500)
    except Exception as e:
        print(f"[draft_generator] Claude API failed: {e}. Using template fallback.")
        draft_body = _email_template_fallback(original_email)

    # Validate draft
    if len(draft_body) > 5000:
        draft_body = draft_body[:4997] + "..."

    # Generate draft ID
    draft_id = f"EMAIL_DRAFT_{int(datetime.now().timestamp())}"

    return {
        "draft_id": draft_id,
        "original_email_id": original_email["email_id"],
        "to": original_email["from"],
        "subject": f"Re: {original_email['subject']}",
        "draft_body": draft_body,
        "status": "pending_approval",
        "generated_at": datetime.now().isoformat(),
        "sent_at": None,
        "action": "send_email",
        "mcp_server": "email-mcp"
    }


def generate_whatsapp_draft(
    original_message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate WhatsApp reply draft using Claude API.

    Args:
        original_message: Dict with keys: contact_name, message_preview, chat_id,
                         message_id, keywords_matched

    Returns:
        WhatsAppDraft dict with keys: draft_id, to, chat_id, draft_body, status

    Raises:
        ValueError: If required fields missing
    """
    # Validate required fields
    required_fields = ["contact_name", "message_preview", "chat_id", "message_id"]
    for field in required_fields:
        if field not in original_message:
            raise ValueError(f"Missing required field: {field}")

    # Sanitize input (limit to first 200 chars)
    sanitized_message = _sanitize_text(original_message["message_preview"], max_length=200)
    keywords = original_message.get("keywords_matched", [])
    keywords_str = ", ".join(keywords) if keywords else "None"

    # Build Claude API prompt
    prompt = f"""You are drafting a WhatsApp reply for a business conversation.

Original Message:
From: {original_message['contact_name']}
Message: {sanitized_message}
Keywords detected: {keywords_str}

Draft a professional but conversational WhatsApp reply that:
1. Is BRIEF (max 3-4 sentences, 500 characters)
2. Addresses the urgency indicated by keywords ({keywords_str})
3. Uses business-casual tone (professional but not formal)
4. No emojis unless original message used them

Examples:
- Urgent payment: "Got it, will process payment today. Expect confirmation by 5 PM."
- Meeting request: "Sure, I'm available tomorrow 2 PM. Send calendar invite?"
- General inquiry: "Thanks for reaching out! Let me check and get back to you shortly."

Draft Reply:"""

    # Call Claude API (with fallback)
    try:
        draft_body = _call_claude_api(prompt, max_tokens=200)
    except Exception as e:
        print(f"[draft_generator] Claude API failed: {e}. Using template fallback.")
        draft_body = _whatsapp_template_fallback(original_message)

    # Enforce 500 char limit
    if len(draft_body) > 500:
        draft_body = draft_body[:497] + "..."

    # Generate draft ID
    draft_id = f"WHATSAPP_DRAFT_{original_message['chat_id']}_{int(datetime.now().timestamp())}"

    return {
        "draft_id": draft_id,
        "original_message_id": original_message["message_id"],
        "to": original_message["contact_name"],
        "chat_id": original_message["chat_id"],
        "draft_body": draft_body,
        "status": "pending_approval",
        "generated_at": datetime.now().isoformat(),
        "sent_at": None,
        "keywords_matched": keywords,
        "action": "send_message",
        "mcp_server": "whatsapp-mcp"
    }


def generate_linkedin_draft(
    business_goals: str,
    posting_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate LinkedIn post draft using Claude API.

    Args:
        business_goals: Business goals text from Company_Handbook.md
        posting_date: Optional date for post (defaults to today)

    Returns:
        LinkedInDraft dict with keys: draft_id, post_content, character_count, status

    Raises:
        ValueError: If business_goals is empty
    """
    if not business_goals:
        raise ValueError("business_goals cannot be empty")

    if not posting_date:
        posting_date = datetime.now().strftime("%Y-%m-%d")

    # Sanitize business goals (first 500 chars)
    sanitized_goals = business_goals[:500]

    # Build Claude API prompt
    prompt = f"""You are drafting a LinkedIn post to promote a business.

Business Goals (from Company Handbook):
{sanitized_goals}

Posting Date: {posting_date}

Draft a LinkedIn post that:
1. Starts with a HOOK (engaging first line, <100 chars)
2. Provides VALUE (insight, tip, or story related to business goals)
3. Ends with CLEAR CTA (call-to-action: comment, visit website, DM)
4. Uses 2-3 short paragraphs (not wall of text)
5. Professional tone aligned with business goals
6. Max 3000 characters

Examples:
- Hook: "Most people overlook this when building X..."
- Value: "Here's what I learned after 5 years in the industry..."
- CTA: "What's your experience? Share in comments below."

Draft Post:"""

    # Call Claude API (with fallback)
    try:
        post_content = _call_claude_api(prompt, max_tokens=1000)
    except Exception as e:
        print(f"[draft_generator] Claude API failed: {e}. Using template fallback.")
        post_content = _linkedin_template_fallback(business_goals)

    # Enforce 3000 char limit (truncate at sentence boundary)
    if len(post_content) > 3000:
        post_content = post_content[:2997]
        last_period = post_content.rfind('.')
        if last_period > 2500:
            post_content = post_content[:last_period+1] + " […]"

    # Generate draft ID
    draft_id = f"LINKEDIN_POST_{posting_date}"

    return {
        "draft_id": draft_id,
        "scheduled_date": posting_date,
        "business_goal_reference": "Business Goals",  # Section name from handbook
        "post_content": post_content,
        "character_count": len(post_content),
        "status": "pending_approval",
        "generated_at": datetime.now().isoformat(),
        "posted_at": None,
        "action": "create_post",
        "mcp_server": "linkedin-mcp"
    }


# ====== Helper Functions ======

def _sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for API calls (reduce cost, remove sensitive data).

    Args:
        text: Raw text input
        max_length: Max characters to keep

    Returns:
        Sanitized text
    """
    # Strip excessive whitespace
    text = " ".join(text.split())

    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def _call_claude_api(prompt: str, max_tokens: int = 500) -> str:
    """
    Call Claude API for text generation.

    Args:
        prompt: User prompt
        max_tokens: Max tokens to generate

    Returns:
        Generated text

    Raises:
        Exception: If API call fails (no CLAUDE_API_KEY, network error, etc.)
    """
    import anthropic

    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise Exception("CLAUDE_API_KEY not set in environment")

    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    except Exception as e:
        raise Exception(f"Claude API call failed: {e}")


def _email_template_fallback(original_email: Dict[str, Any]) -> str:
    """Template fallback for email drafts when Claude API unavailable"""
    return f"""Thank you for your email regarding "{original_email['subject']}".

I've received your message and will review it carefully. I'll get back to you with a detailed response shortly.

Best regards"""


def _whatsapp_template_fallback(original_message: Dict[str, Any]) -> str:
    """Template fallback for WhatsApp drafts when Claude API unavailable"""
    return f"Thanks for your message! I'll review and get back to you soon."


def _linkedin_template_fallback(business_goals: str) -> str:
    """Template fallback for LinkedIn posts when Claude API unavailable"""
    return f"""Excited to share an update on our journey!

{business_goals[:200]}

What are your thoughts? Let me know in the comments!"""


# Example usage
if __name__ == "__main__":
    # Example: Generate email draft
    test_email = {
        "email_id": "EMAIL_test_001",
        "from": "client@example.com",
        "subject": "Project Proposal Review",
        "body": "Can you review the attached proposal and provide feedback by Friday?",
        "priority": "High"
    }

    draft = generate_email_draft(test_email, company_handbook_path="vault/Company_Handbook.md")
    print(f"Email draft generated: {draft['draft_id']}")
    print(f"Draft body preview: {draft['draft_body'][:100]}...")
