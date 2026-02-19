"""
Odoo Draft Generator (Cloud Agent)

Detects emails containing invoice/bill/payment keywords, uses Claude to
extract structured accounting data, and saves a draft to
vault/Pending_Approval/Odoo/INVOICE_DRAFT_*.md for human approval.

Human approves → Local Agent → Odoo MCP → Draft invoice created in Odoo.
NEVER auto-creates Odoo records without approval.
"""
import os
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Keywords that indicate an email contains an invoice/billing request
INVOICE_KEYWORDS = [
    "invoice", "bill", "billing", "payment", "charge", "receipt",
    "quote", "quotation", "estimate", "fee", "due", "amount due",
    "please pay", "attached invoice", "proforma",
]


def _contains_invoice_keywords(subject: str, body: str) -> bool:
    """Return True if the email likely relates to an invoice/payment."""
    text = (subject + " " + body).lower()
    return any(kw in text for kw in INVOICE_KEYWORDS)


def _extract_odoo_data_with_claude(subject: str, body: str, sender: str) -> Optional[Dict[str, Any]]:
    """
    Use Claude API to extract structured invoice data from email text.

    Returns dict with: customer, amount, currency, description, action
    or None if extraction fails.
    """
    import anthropic

    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("No Claude API key — using fallback extraction")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Extract invoice/billing information from this email. Return ONLY valid JSON.

Email From: {sender}
Subject: {subject}
Body:
{body[:1500]}

Extract and return JSON with exactly these fields:
{{
  "customer": "Full name of customer/client (string)",
  "amount": 0.00,
  "currency": "USD",
  "description": "Brief description of service/product (max 100 chars)",
  "action": "create_draft_invoice"
}}

Rules:
- customer: Extract the name from the email or sender. Use "Unknown" if unclear.
- amount: Extract numeric amount. Use 0 if not found.
- currency: USD unless another currency is mentioned.
- description: What the invoice is for (consulting, service, product name etc).
- action: Always "create_draft_invoice" for customer invoices.

Return ONLY the JSON object, nothing else."""

    try:
        msg = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        # Strip markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        data = json.loads(text)
        return data
    except Exception as e:
        logger.warning(f"Claude extraction failed: {e}")
        return None


def _fallback_extraction(subject: str, body: str, sender: str) -> Dict[str, Any]:
    """Simple regex-based extraction when Claude is unavailable."""
    # Try to find amount (e.g. $500, 500.00, USD 500)
    amount = 0.0
    amount_match = re.search(
        r'(?:USD|GBP|EUR|\$|£|€)?\s*(\d{1,6}(?:[,\s]\d{3})*(?:\.\d{1,2})?)',
        subject + " " + body
    )
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", "").replace(" ", ""))
        except ValueError:
            pass

    # Try to get name from sender "Name <email>"
    name_match = re.match(r'^([^<]+)<', sender)
    customer = name_match.group(1).strip() if name_match else sender.split("@")[0].replace(".", " ").title()

    return {
        "customer": customer or "Unknown",
        "amount": amount,
        "currency": "USD",
        "description": (subject[:80] if subject else "Invoice request"),
        "action": "create_draft_invoice",
    }


class OdooDraftGenerator:
    """
    Generates Odoo invoice draft files for Cloud Agent.

    Detects invoice-related emails → extracts data with Claude →
    saves vault/Pending_Approval/Odoo/INVOICE_DRAFT_*.md
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pending_dir = self.vault_path / "Pending_Approval" / "Odoo"
        self.log_dir = self.vault_path / "Logs" / "Odoo"
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def should_generate(self, email_data: Dict[str, Any]) -> bool:
        """Return True if this email should generate an Odoo draft."""
        if os.getenv("ENABLE_ODOO", "false").lower() != "true":
            return False
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        return _contains_invoice_keywords(subject, body)

    def generate_and_save(self, email_data: Dict[str, Any]) -> Optional[Path]:
        """
        Extract invoice data from email and save draft file.

        Args:
            email_data: Dict with email_id, from, subject, body, priority

        Returns:
            Path to saved draft file, or None if failed/not applicable
        """
        if not self.should_generate(email_data):
            return None

        email_id = email_data.get("email_id", f"EMAIL_{int(datetime.now().timestamp())}")
        draft_id = f"ODOO_{email_id}"
        draft_path = self.pending_dir / f"INVOICE_DRAFT_{draft_id}.md"

        # Idempotent — skip if already exists
        if draft_path.exists():
            logger.debug(f"Odoo draft already exists: {draft_path.name}")
            return draft_path

        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        sender = email_data.get("from", "")

        logger.info(f"🧾 Generating Odoo draft for: {subject[:60]}")

        # Extract structured data
        odoo_data = _extract_odoo_data_with_claude(subject, body, sender)
        if not odoo_data:
            odoo_data = _fallback_extraction(subject, body, sender)

        # Validate
        customer = odoo_data.get("customer", "Unknown")
        amount = float(odoo_data.get("amount", 0))
        currency = odoo_data.get("currency", "USD")
        description = odoo_data.get("description", subject[:80])
        action = odoo_data.get("action", "create_draft_invoice")

        now = datetime.now().isoformat()

        content = f"""---
type: odoo_invoice
draft_id: {draft_id}
action: {action}
status: pending
customer: {customer}
amount: {amount:.2f}
currency: {currency}
description: {description}
source_email_id: {email_id}
source_email_subject: {subject[:100]}
source_email_from: {sender}
created: {now}
mcp_server: odoo-mcp
---

## Odoo Invoice Draft

**Customer:** {customer}
**Amount:** {currency} {amount:.2f}
**Description:** {description}

---

### Source Email

**From:** {sender}
**Subject:** {subject}

{body[:800]}
"""

        try:
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(content)

            self._log(f"Draft created: {draft_path.name} | Customer: {customer} | Amount: {currency} {amount:.2f}")
            logger.info(f"✅ Odoo draft saved: {draft_path.name}")
            return draft_path

        except Exception as e:
            logger.error(f"Failed to save Odoo draft: {e}")
            return None

    def _log(self, message: str):
        """Append to daily Odoo log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"odoo-{today}.md"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"- {datetime.now().strftime('%H:%M:%S')} {message}\n")
        except Exception:
            pass
