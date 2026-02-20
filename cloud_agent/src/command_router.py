"""
Command Router - WhatsApp/CLI Natural Language → Vault Draft

Parses natural language commands from admin (WhatsApp or CLI) into structured
intent dicts, then creates vault/Pending_Approval/ draft files.

Supported actions:
  - create_draft_invoice  → vault/Pending_Approval/Odoo/INVOICE_DRAFT_*.md
  - create_draft_expense  → vault/Pending_Approval/Odoo/INVOICE_DRAFT_*.md
  - send_email            → vault/Pending_Approval/Email/EMAIL_DRAFT_*.md
  - send_message          → vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_*.md
  - create_contact        → vault/Pending_Approval/Odoo/CONTACT_DRAFT_*.md
  - register_payment      → vault/Pending_Approval/Odoo/PAYMENT_DRAFT_*.md
  - create_purchase_bill  → vault/Pending_Approval/Odoo/BILL_DRAFT_*.md
  - create_post           → vault/Pending_Approval/LinkedIn/LINKEDIN_POST_*.md

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-20
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# ── Admin detection ───────────────────────────────────────────────────────────
ADMIN_NAME = os.getenv("WHATSAPP_ADMIN_NAME", "")
COMMAND_PREFIXES = ("!", "/", "!cmd", "/cmd")


def is_admin_command(sender_name: str, message: str) -> bool:
    """
    Return True if this message should be treated as an admin command.

    Conditions (any one is sufficient):
    1. sender_name matches WHATSAPP_ADMIN_NAME env var (case-insensitive partial match)
    2. message starts with "!" or "/"
    3. sender_name is empty but message starts with a command prefix
    """
    msg = message.strip()

    # Prefix check (works for anyone if they know the prefix)
    if any(msg.startswith(p) for p in COMMAND_PREFIXES):
        return True

    # Admin sender check
    if ADMIN_NAME and sender_name:
        if ADMIN_NAME.lower() in sender_name.lower() or sender_name.lower() in ADMIN_NAME.lower():
            return True

    return False


# ── Few-shot examples for Claude ─────────────────────────────────────────────
COMMAND_EXAMPLES = """
INPUT: "Create invoice for Ali for 5000 Rs web design"
OUTPUT: {"action": "create_draft_invoice", "customer": "Ali", "amount": 5000, "currency": "PKR", "description": "Web design services"}

INPUT: "Send invoice to Muhammad Khan 15000 Rs website development"
OUTPUT: {"action": "create_draft_invoice", "customer": "Muhammad Khan", "amount": 15000, "currency": "PKR", "description": "Website development"}

INPUT: "Invoice Ahmad 200 USD consulting"
OUTPUT: {"action": "create_draft_invoice", "customer": "Ahmad", "amount": 200, "currency": "USD", "description": "Consulting services"}

INPUT: "Create expense for office rent 30000 Rs"
OUTPUT: {"action": "create_draft_expense", "customer": "Office Rent", "amount": 30000, "currency": "PKR", "description": "Office rent payment"}

INPUT: "Add contact John Smith john@company.com +923001234567"
OUTPUT: {"action": "create_contact", "customer": "John Smith", "email": "john@company.com", "phone": "+923001234567"}

INPUT: "Register payment for invoice INV/2026/00003"
OUTPUT: {"action": "register_payment", "invoice_number": "INV/2026/00003"}

INPUT: "Create purchase bill from Ali Traders 25000 Rs office supplies"
OUTPUT: {"action": "create_purchase_bill", "customer": "Ali Traders", "amount": 25000, "currency": "PKR", "description": "Office supplies"}

INPUT: "Send email to john@gmail.com about project update tomorrow's meeting"
OUTPUT: {"action": "send_email", "to": "john@gmail.com", "subject": "Project Update - Tomorrow's Meeting", "body": "Hi, wanted to confirm our meeting tomorrow. Please let me know if the time works for you."}

INPUT: "WhatsApp Ali about invoice ready"
OUTPUT: {"action": "send_message", "chat_id": "Ali", "body": "Hi Ali, your invoice is ready. Please let me know if you have any questions."}

INPUT: "Post linkedin: We just shipped AI-powered invoicing!"
OUTPUT: {"action": "create_post", "post_content": "We just shipped AI-powered invoicing! Our Personal AI Employee can now create invoices directly from WhatsApp commands. #AI #Automation #ProductivityHack"}

INPUT: "!invoice Ali 5000"
OUTPUT: {"action": "create_draft_invoice", "customer": "Ali", "amount": 5000, "currency": "PKR", "description": "Services"}

INPUT: "!email john@test.com Meeting tomorrow at 10am"
OUTPUT: {"action": "send_email", "to": "john@test.com", "subject": "Meeting Tomorrow", "body": "Hi, just a reminder about our meeting tomorrow at 10am."}
""".strip()


# ── Claude intent parser ──────────────────────────────────────────────────────
def parse_command_with_claude(message: str) -> Dict[str, Any]:
    """
    Use Claude API to extract structured intent from a natural language command.

    Returns dict with keys depending on action:
      - action: str (required)
      - customer, amount, currency, description (for invoice/expense/bill)
      - to, subject, body (for email)
      - chat_id, body (for WhatsApp message)
      - post_content (for LinkedIn)
      - email, phone (for contact)
      - invoice_number (for payment)

    Falls back to {"action": "unknown", "raw": message} on failure.
    """
    import json

    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = f"""You are an intent extractor for a Personal AI Employee system.
Extract the action and parameters from the user command and return ONLY valid JSON.

Supported actions:
- create_draft_invoice: create sales invoice in Odoo
- create_draft_expense: create expense entry in Odoo
- create_contact: add new customer/vendor to Odoo
- register_payment: register payment against an invoice
- create_purchase_bill: create vendor bill in Odoo
- send_email: compose and send an email
- send_message: send a WhatsApp message
- create_post: create a LinkedIn post

Rules:
1. Return ONLY a JSON object, no markdown, no explanation
2. Default currency to PKR unless USD/EUR/GBP/AED explicitly mentioned
3. If amount has "k" suffix, multiply by 1000 (e.g. "5k" = 5000)
4. Clean the action prefix (!, /) from the message before extracting
5. For missing fields, use sensible defaults or empty string ""

Examples:
{COMMAND_EXAMPLES}
"""

        resp = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001") or "claude-haiku-4-5-20251001",
            max_tokens=400,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Extract intent from: {message}"
            }]
        )

        raw = resp.content[0].text.strip()

        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        intent = json.loads(raw)
        intent.setdefault("raw_command", message)
        return intent

    except Exception as e:
        logger.warning(f"Claude parse failed ({e}) — returning unknown intent")
        return {"action": "unknown", "raw": message, "error": str(e)}


# ── Vault draft creator ───────────────────────────────────────────────────────
def create_vault_draft(intent: Dict[str, Any], vault_path: Optional[str] = None) -> str:
    """
    Write a vault draft file based on parsed intent.

    Args:
        intent:     Dict from parse_command_with_claude()
        vault_path: Override vault root (defaults to VAULT_PATH env var)

    Returns:
        Absolute path to the created draft file.

    Raises:
        ValueError: if action is unknown or unhandled
    """
    vault = Path(vault_path or os.getenv("VAULT_PATH", "vault"))
    action = intent.get("action", "unknown")
    ts = int(datetime.now().timestamp() * 1000)
    now_iso = datetime.now().isoformat()

    if action == "unknown":
        raise ValueError(f"Cannot create draft for unknown action: {intent.get('raw', '')}")

    # ── Odoo: Invoice ─────────────────────────────────────────────────────────
    if action == "create_draft_invoice":
        customer = intent.get("customer", "Unknown")
        amount   = intent.get("amount", 0)
        currency = intent.get("currency", "PKR")
        desc     = intent.get("description", "Services")
        email    = intent.get("email", "")
        safe_name = customer.replace(" ", "_")
        filename  = f"INVOICE_DRAFT_MANUAL_{safe_name}_{ts}.md"
        folder    = vault / "Pending_Approval" / "Odoo"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: create_draft_invoice
customer: "{customer}"
customer_email: "{email}"
amount: {amount}
currency: {currency}
description: "{desc}"
status: pending_approval
created: {now_iso}
source: command_router
mcp_server: odoo-mcp
---

## Invoice Draft

**Customer:** {customer}
**Amount:** {currency} {amount:,}
**Description:** {desc}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to post this invoice draft to Odoo.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created invoice draft: {path}")
        return str(path)

    # ── Odoo: Expense ─────────────────────────────────────────────────────────
    elif action == "create_draft_expense":
        customer = intent.get("customer", "Expense")
        amount   = intent.get("amount", 0)
        currency = intent.get("currency", "PKR")
        desc     = intent.get("description", "Expense")
        safe_name = customer.replace(" ", "_")
        filename  = f"INVOICE_DRAFT_MANUAL_{safe_name}_{ts}.md"
        folder    = vault / "Pending_Approval" / "Odoo"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: create_draft_expense
customer: "{customer}"
amount: {amount}
currency: {currency}
description: "{desc}"
status: pending_approval
created: {now_iso}
source: command_router
mcp_server: odoo-mcp
---

## Expense Draft

**Vendor/Category:** {customer}
**Amount:** {currency} {amount:,}
**Description:** {desc}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to create this expense draft in Odoo.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created expense draft: {path}")
        return str(path)

    # ── Odoo: Contact ─────────────────────────────────────────────────────────
    elif action == "create_contact":
        name   = intent.get("customer", intent.get("name", "Unknown"))
        email  = intent.get("email", "")
        phone  = intent.get("phone", "")
        safe_name = name.replace(" ", "_")
        filename  = f"CONTACT_DRAFT_{safe_name}_{ts}.md"
        folder    = vault / "Pending_Approval" / "Odoo"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: create_contact
name: "{name}"
email: "{email}"
phone: "{phone}"
status: pending_approval
created: {now_iso}
source: command_router
mcp_server: odoo-mcp
---

## Contact Draft

**Name:** {name}
**Email:** {email}
**Phone:** {phone}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to add this contact to Odoo.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created contact draft: {path}")
        return str(path)

    # ── Odoo: Payment ─────────────────────────────────────────────────────────
    elif action == "register_payment":
        invoice_num = intent.get("invoice_number", "")
        amount      = intent.get("amount", 0)
        filename    = f"PAYMENT_DRAFT_{invoice_num.replace('/', '_')}_{ts}.md"
        folder      = vault / "Pending_Approval" / "Odoo"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: register_payment
invoice_number: "{invoice_num}"
amount: {amount}
status: pending_approval
created: {now_iso}
source: command_router
mcp_server: odoo-mcp
---

## Payment Draft

**Invoice:** {invoice_num}
**Amount:** {amount if amount else "As per invoice"}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to register this payment in Odoo.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created payment draft: {path}")
        return str(path)

    # ── Odoo: Purchase Bill ───────────────────────────────────────────────────
    elif action == "create_purchase_bill":
        vendor   = intent.get("customer", intent.get("vendor", "Unknown"))
        amount   = intent.get("amount", 0)
        currency = intent.get("currency", "PKR")
        desc     = intent.get("description", "Purchase")
        safe_name = vendor.replace(" ", "_")
        filename  = f"BILL_DRAFT_{safe_name}_{ts}.md"
        folder    = vault / "Pending_Approval" / "Odoo"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: create_purchase_bill
vendor: "{vendor}"
amount: {amount}
currency: {currency}
description: "{desc}"
status: pending_approval
created: {now_iso}
source: command_router
mcp_server: odoo-mcp
---

## Purchase Bill Draft

**Vendor:** {vendor}
**Amount:** {currency} {amount:,}
**Description:** {desc}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to create this vendor bill in Odoo.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created purchase bill draft: {path}")
        return str(path)

    # ── Email ─────────────────────────────────────────────────────────────────
    elif action == "send_email":
        to      = intent.get("to", "")
        subject = intent.get("subject", "Message from Qasim")
        body    = intent.get("body", "")
        safe_to = to.replace("@", "_at_").replace(".", "_")
        filename = f"EMAIL_DRAFT_CMD_{safe_to}_{ts}.md"
        folder   = vault / "Pending_Approval" / "Email"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: send_email
to: "{to}"
subject: "{subject}"
draft_body: "{body}"
status: pending_approval
generated_at: {now_iso}
source: command_router
mcp_server: email-mcp
---

## Email Draft

**To:** {to}
**Subject:** {subject}

{body}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to send this email.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created email draft: {path}")
        return str(path)

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    elif action == "send_message":
        chat_id = intent.get("chat_id", intent.get("to", ""))
        body    = intent.get("body", "")
        safe_chat = chat_id.replace(" ", "_")
        filename  = f"WHATSAPP_DRAFT_CMD_{safe_chat}_{ts}.md"
        folder    = vault / "Pending_Approval" / "WhatsApp"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: send_message
chat_id: "{chat_id}"
to: "{chat_id}"
draft_body: "{body}"
status: pending_approval
generated_at: {now_iso}
source: command_router
mcp_server: whatsapp-mcp
---

## WhatsApp Draft

**To:** {chat_id}

{body}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to send this WhatsApp message.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created WhatsApp draft: {path}")
        return str(path)

    # ── LinkedIn ──────────────────────────────────────────────────────────────
    elif action == "create_post":
        post_content = intent.get("post_content", "")
        char_count   = len(post_content)
        filename     = f"LINKEDIN_POST_CMD_{ts}.md"
        folder       = vault / "Pending_Approval" / "LinkedIn"
        folder.mkdir(parents=True, exist_ok=True)

        content = f"""---
draft_id: {filename[:-3]}
action: create_post
post_content: "{post_content}"
character_count: {char_count}
scheduled_date: "{datetime.now().strftime('%Y-%m-%d')}"
business_goal_reference: "command_router"
status: pending_approval
generated_at: {now_iso}
source: command_router
mcp_server: linkedin-mcp
---

## LinkedIn Post Draft

{post_content}

> Created from command: `{intent.get('raw_command', '')}`
> Approve to publish this post on LinkedIn.
"""
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"📄 Created LinkedIn draft: {path}")
        return str(path)

    else:
        raise ValueError(f"Unhandled action type: {action}")


# ── Convenience: parse + create in one call ───────────────────────────────────
def route_command(message: str, vault_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Full pipeline: parse message → create vault draft → return result dict.

    Returns:
        {
          "success": bool,
          "action": str,
          "draft_path": str | None,
          "intent": dict,
          "error": str | None
        }
    """
    intent = parse_command_with_claude(message)

    if intent.get("action") == "unknown":
        return {
            "success": False,
            "action": "unknown",
            "draft_path": None,
            "intent": intent,
            "error": f"Could not parse command: {message}",
        }

    try:
        draft_path = create_vault_draft(intent, vault_path)
        return {
            "success": True,
            "action": intent["action"],
            "draft_path": draft_path,
            "intent": intent,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Failed to create vault draft: {e}")
        return {
            "success": False,
            "action": intent.get("action", "unknown"),
            "draft_path": None,
            "intent": intent,
            "error": str(e),
        }
