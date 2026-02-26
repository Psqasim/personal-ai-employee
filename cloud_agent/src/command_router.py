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


def _yaml_safe(value: str) -> str:
    """Escape a string for safe inclusion in YAML double-quoted values.

    Replaces internal double-quotes with escaped quotes and wraps in double
    quotes so that values like:  "Indeed, with hardship comes ease."
    don't produce invalid YAML:  draft_body: ""Indeed..."  (broken)
    Instead produces:            draft_body: "\"Indeed..."  (valid)
    Also collapses multi-line text into a single line.
    """
    v = value.replace("\n", "\\n").replace('"', '\\"')
    return f'"{v}"'

# ── Admin detection ───────────────────────────────────────────────────────────
# Phone numbers that can issue admin commands (comma-separated in env var)
# e.g. WHATSAPP_ADMIN_PHONES=+923010832227,+923460326429
_ADMIN_PHONES_RAW = os.getenv("WHATSAPP_ADMIN_PHONES", "")

# Normalize: strip everything except digits, compare last 10 digits
def _normalize_phone(raw: str) -> str:
    digits = "".join(c for c in raw if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

ADMIN_PHONES: set = {
    _normalize_phone(p.strip())
    for p in _ADMIN_PHONES_RAW.split(",")
    if p.strip()
}


def is_admin_command(sender: str, message: str) -> bool:
    """
    Return True if this message should be treated as an admin command.

    Auth is PHONE NUMBER based only.
    The last 10 digits of sender are matched against WHATSAPP_ADMIN_PHONES.

    IMPORTANT: For phone matching to work, the admin numbers must NOT be saved
    as contacts in the WhatsApp account the bot uses. If saved, WhatsApp shows
    the contact name (e.g. "Muhammad Qasim") instead of the number — matching fails.
    Solution: delete admin contacts from the bot's phone contact list.
    """
    if not ADMIN_PHONES:
        return False  # No admin phones configured → all commands blocked

    sender_norm = _normalize_phone(sender)
    return bool(sender_norm and sender_norm in ADMIN_PHONES)


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

INPUT: "Send emails to ali@gmail.com, bob@gmail.com, carol@gmail.com say you are invited to Iftar party Friday 6pm"
OUTPUT: {"action": "send_email", "recipients": ["ali@gmail.com", "bob@gmail.com", "carol@gmail.com"], "subject": "You're Invited - Iftar Party Friday 6PM", "body": "Assalamu Alaikum! You are warmly invited to join us for an Iftar party this Friday at 6:00 PM. Looking forward to seeing you!"}

INPUT: "Send WhatsApp message say Good morning to\n1.923011496677\n2.923451754772\n3.923112759356\n4.923491136194"
OUTPUT: {"action": "send_message", "recipients": ["923011496677", "923451754772", "923112759356", "923491136194"], "body": "Good morning! 🌅 Have a wonderful day!"}

INPUT: "Send message to (923112759356) (923451754772) say Iftar is at 6pm today"
OUTPUT: {"action": "send_message", "recipients": ["923112759356", "923451754772"], "body": "Assalamu Alaikum! Just a reminder that Iftar is at 6pm today."}
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
6. If MULTIPLE email addresses mentioned, use "recipients": ["a@b.com", "c@d.com"] (not "to")
7. If MULTIPLE phone numbers mentioned (numbered list "1.923... 2.923...", parentheses, or comma-separated), use "recipients": ["923...", "923..."] — digits only, no spaces or + signs
8. Single recipient still uses "to" or "chat_id" as before

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
customer: {_yaml_safe(customer)}
customer_email: {_yaml_safe(email)}
amount: {amount}
currency: {currency}
description: {_yaml_safe(desc)}
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
customer: {_yaml_safe(customer)}
amount: {amount}
currency: {currency}
description: {_yaml_safe(desc)}
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
name: {_yaml_safe(name)}
email: {_yaml_safe(email)}
phone: {_yaml_safe(phone)}
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
invoice_number: {_yaml_safe(invoice_num)}
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
vendor: {_yaml_safe(vendor)}
amount: {amount}
currency: {currency}
description: {_yaml_safe(desc)}
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
        # Support single (to) and multi-recipient (recipients list)
        recipients: list = intent.get("recipients") or []
        if not recipients:
            single = intent.get("to", "")
            recipients = [r.strip() for r in single.split(",") if r.strip()] if single else [""]
        subject = intent.get("subject", "Message from Qasim")
        body    = intent.get("body", "")
        folder  = vault / "Pending_Approval" / "Email"
        folder.mkdir(parents=True, exist_ok=True)

        first_path = None
        for i, to in enumerate(recipients):
            to = str(to).strip()
            safe_to  = to.replace("@", "_at_").replace(".", "_").replace(",", "_").replace(" ", "_")
            filename = f"EMAIL_DRAFT_CMD_{safe_to}_{ts + i}.md"
            content  = f"""---
draft_id: {filename[:-3]}
action: send_email
to: "{to}"
subject: {_yaml_safe(subject)}
draft_body: {_yaml_safe(body)}
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
            if first_path is None:
                first_path = str(path)

        # Store recipients back for confirmation message
        intent["_recipient_count"] = len(recipients)
        return first_path or ""

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    # Admin commands skip Pending_Approval and go directly to Approved/
    # so the watcher sends immediately without dashboard review.
    elif action == "send_message":
        # Support single (chat_id/to) and multi-recipient (recipients list)
        recipients: list = intent.get("recipients") or []
        if not recipients:
            single = intent.get("chat_id", intent.get("to", ""))
            recipients = [single] if single else []

        body   = intent.get("body", "")
        folder = vault / "Approved" / "WhatsApp"
        folder.mkdir(parents=True, exist_ok=True)

        first_path = None
        for i, chat_id in enumerate(recipients):
            chat_id   = str(chat_id).strip().lstrip("+")
            safe_chat = chat_id.replace(" ", "_").replace("+", "")
            filename  = f"WHATSAPP_DRAFT_CMD_{safe_chat}_{ts + i}.md"
            content   = f"""---
draft_id: {filename[:-3]}
action: send_message
chat_id: "{chat_id}"
to: "{chat_id}"
draft_body: {_yaml_safe(body)}
status: approved
generated_at: {now_iso}
source: command_router
mcp_server: whatsapp-mcp
---

## WhatsApp Message

**To:** {chat_id}

{body}

> Auto-approved admin command: `{intent.get('raw_command', '')}`
"""
            path = folder / filename
            path.write_text(content, encoding="utf-8")
            logger.info(f"📤 Created auto-approved WhatsApp send to {chat_id}: {path}")
            if first_path is None:
                first_path = str(path)

        intent["_recipient_count"] = len(recipients)
        intent["chat_id"] = recipients[0] if recipients else ""
        return first_path or ""

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
post_content: {_yaml_safe(post_content)}
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
