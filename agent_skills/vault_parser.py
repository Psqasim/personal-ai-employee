"""
Vault Parser - Obsidian Markdown + YAML Frontmatter Parsing

This module provides parsing utilities for Obsidian vault files with YAML frontmatter.
Supports all Bronze/Silver/Gold tier entity types:
- Task files (EMAIL_*.md, WHATSAPP_*.md, etc.)
- Draft files (EmailDraft, WhatsAppDraft, LinkedInDraft)
- Plan files (Plan.md with steps)
- Execution state files (state.md in In_Progress/)

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import yaml


# ====== Data Classes for Parsed Entities ======

@dataclass
class EmailDraft:
    """Parsed EmailDraft entity from vault/Pending_Approval/Email/"""
    draft_id: str
    original_email_id: str
    to: str
    subject: str
    draft_body: str
    status: str
    generated_at: datetime
    sent_at: Optional[datetime] = None
    action: str = "send_email"
    mcp_server: str = "email-mcp"
    file_path: str = ""


@dataclass
class WhatsAppDraft:
    """Parsed WhatsAppDraft entity from vault/Pending_Approval/WhatsApp/"""
    draft_id: str
    original_message_id: str
    to: str
    chat_id: str
    draft_body: str
    status: str
    generated_at: datetime
    sent_at: Optional[datetime] = None
    keywords_matched: List[str] = field(default_factory=list)
    action: str = "send_message"
    mcp_server: str = "whatsapp-mcp"
    file_path: str = ""


@dataclass
class LinkedInDraft:
    """Parsed LinkedInDraft entity from vault/Pending_Approval/LinkedIn/"""
    draft_id: str
    scheduled_date: str
    business_goal_reference: str
    post_content: str
    character_count: int
    status: str
    generated_at: datetime
    posted_at: Optional[datetime] = None
    action: str = "create_post"
    mcp_server: str = "linkedin-mcp"
    file_path: str = ""


@dataclass
class OdooDraft:
    """Parsed OdooDraft entity from vault/Pending_Approval/Odoo/"""
    draft_id: str
    customer: str
    amount: float
    currency: str
    description: str
    action: str          # "create_draft_invoice" or "create_draft_expense"
    status: str
    created: datetime
    odoo_data: Dict[str, Any]  # Full data passed to MCP
    customer_email: str = ""   # optional — if set, Odoo sends invoice PDF to this email
    file_path: str = ""
    mcp_server: str = "odoo-mcp"


@dataclass
class OdooContact:
    """Parsed OdooContact entity from vault/Pending_Approval/Odoo/CONTACT_DRAFT_*.md"""
    draft_id: str
    name: str
    email: str
    phone: str
    action: str = "create_contact"
    status: str = "pending_approval"
    created: Optional[datetime] = None
    file_path: str = ""
    mcp_server: str = "odoo-mcp"


@dataclass
class OdooPayment:
    """Parsed OdooPayment entity from vault/Pending_Approval/Odoo/PAYMENT_DRAFT_*.md"""
    draft_id: str
    invoice_number: str
    amount: float
    action: str = "register_payment"
    status: str = "pending_approval"
    created: Optional[datetime] = None
    file_path: str = ""
    mcp_server: str = "odoo-mcp"


@dataclass
class OdooBill:
    """Parsed OdooBill entity from vault/Pending_Approval/Odoo/BILL_DRAFT_*.md"""
    draft_id: str
    vendor: str
    amount: float
    currency: str
    description: str
    action: str = "create_purchase_bill"
    status: str = "pending_approval"
    created: Optional[datetime] = None
    file_path: str = ""
    mcp_server: str = "odoo-mcp"


@dataclass
class PlanStep:
    """Parsed PlanStep from Plan YAML"""
    step_num: int
    description: str
    action_type: str
    action_params: Dict[str, Any]
    dependencies: List[int] = field(default_factory=list)
    status: str = "pending"
    mcp_action_log_id: Optional[str] = None
    retry_count: int = 0


@dataclass
class Plan:
    """Parsed Plan entity from vault/Plans/"""
    plan_id: str
    objective: str
    steps: List[PlanStep]
    total_steps: int
    completed_steps: int
    status: str
    approval_required: bool = True
    estimated_time: str = ""
    approval_file_path: str = ""
    iteration_count: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: str = ""


@dataclass
class ExecutionState:
    """Parsed ExecutionState from vault/In_Progress/{plan_id}/state.md"""
    plan_id: str
    current_step: int
    iterations_remaining: int
    last_action: str = ""
    last_action_timestamp: Optional[datetime] = None
    loop_start_time: Optional[datetime] = None
    file_path: str = ""


# ====== Parsing Functions ======

def parse_frontmatter(file_path: str) -> tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter and body from Obsidian markdown file.

    Args:
        file_path: Absolute path to markdown file

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If frontmatter is invalid YAML
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for frontmatter delimiters
    if not content.startswith('---\n'):
        return {}, content

    # Find closing delimiter — try all variants
    end_index = content.find('\n---\n', 4)
    body_offset = 5  # len('\n---\n')

    if end_index == -1:
        # File ends with ---\n (no content after) or ---<EOF>
        stripped = content.rstrip()
        if stripped.endswith('\n---'):
            end_index = stripped.rfind('\n---')
            body_offset = len('\n---')
        elif content.find('\r\n---\r\n', 4) != -1:
            end_index = content.find('\r\n---\r\n', 4)
            body_offset = 7  # len('\r\n---\r\n')
        else:
            return {}, content

    # Extract frontmatter and body
    frontmatter_text = content[4:end_index]
    body = content[end_index + body_offset:].strip()

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML frontmatter in {file_path}: {e}")

    return frontmatter, body


def parse_draft_file(file_path: str, draft_type: str = "email") -> Any:
    """
    Parse draft file (EmailDraft, WhatsAppDraft, or LinkedInDraft).

    Args:
        file_path: Absolute path to draft file
        draft_type: Type of draft ("email", "whatsapp", "linkedin")

    Returns:
        Parsed draft object (EmailDraft, WhatsAppDraft, or LinkedInDraft)

    Raises:
        ValueError: If draft_type is invalid or required fields missing
    """
    frontmatter, body = parse_frontmatter(file_path)

    # Helper to parse datetime fields
    def parse_datetime(value):
        if value is None or value == "null":
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

    if draft_type == "email":
        return EmailDraft(
            draft_id=frontmatter.get("draft_id", ""),
            original_email_id=frontmatter.get("original_email_id", ""),
            to=frontmatter.get("to", ""),
            subject=frontmatter.get("subject", ""),
            draft_body=frontmatter.get("draft_body", "") or body,
            status=frontmatter.get("status", "pending_approval"),
            generated_at=parse_datetime(frontmatter.get("generated_at")),
            sent_at=parse_datetime(frontmatter.get("sent_at")),
            action=frontmatter.get("action", "send_email"),
            mcp_server=frontmatter.get("mcp_server", "email-mcp"),
            file_path=file_path
        )

    elif draft_type == "whatsapp":
        return WhatsAppDraft(
            draft_id=frontmatter.get("draft_id", ""),
            original_message_id=frontmatter.get("original_message_id", ""),
            to=frontmatter.get("to", ""),
            chat_id=frontmatter.get("chat_id", "") or frontmatter.get("to", ""),
            draft_body=frontmatter.get("draft_body", "") or body,
            status=frontmatter.get("status", "pending_approval"),
            generated_at=parse_datetime(frontmatter.get("generated_at")),
            sent_at=parse_datetime(frontmatter.get("sent_at")),
            keywords_matched=frontmatter.get("keywords_matched", []),
            action=frontmatter.get("action", "send_message"),
            mcp_server=frontmatter.get("mcp_server", "whatsapp-mcp"),
            file_path=file_path
        )

    elif draft_type == "linkedin":
        return LinkedInDraft(
            draft_id=frontmatter.get("draft_id", ""),
            scheduled_date=frontmatter.get("scheduled_date", ""),
            business_goal_reference=frontmatter.get("business_goal_reference", ""),
            post_content=frontmatter.get("post_content", ""),
            character_count=frontmatter.get("character_count", 0),
            status=frontmatter.get("status", "pending_approval"),
            generated_at=parse_datetime(frontmatter.get("generated_at")),
            posted_at=parse_datetime(frontmatter.get("posted_at")),
            action=frontmatter.get("action", "create_post"),
            mcp_server=frontmatter.get("mcp_server", "linkedin-mcp"),
            file_path=file_path
        )

    elif draft_type == "odoo":
        action = frontmatter.get("action", "create_draft_invoice")
        amount_raw = frontmatter.get("amount", 0)
        try:
            amount = float(str(amount_raw).replace(",", "").replace("$", "").strip())
        except (ValueError, TypeError):
            amount = 0.0
        odoo_data = {
            "customer": frontmatter.get("customer", ""),
            "customer_email": frontmatter.get("customer_email", ""),
            "vendor": frontmatter.get("vendor", frontmatter.get("customer", "")),
            "amount": amount,
            "currency": frontmatter.get("currency", "USD"),
            "description": frontmatter.get("description", body.strip()),
            "invoice_date": frontmatter.get("invoice_date", None),
            "expense_date": frontmatter.get("expense_date", None),
        }
        return OdooDraft(
            draft_id=frontmatter.get("draft_id", Path(file_path).stem),
            customer=frontmatter.get("customer", frontmatter.get("vendor", "")),
            customer_email=frontmatter.get("customer_email", ""),
            amount=amount,
            currency=frontmatter.get("currency", "USD"),
            description=frontmatter.get("description", body.strip()[:200]),
            action=action,
            status=frontmatter.get("status", "pending"),
            created=parse_datetime(frontmatter.get("created", datetime.now().isoformat())) or datetime.now(),
            odoo_data=odoo_data,
            file_path=file_path,
            mcp_server=frontmatter.get("mcp_server", "odoo-mcp"),
        )

    elif draft_type == "contact":
        def _dt(v):
            if v is None or v == "null":
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        return OdooContact(
            draft_id=frontmatter.get("draft_id", Path(file_path).stem),
            name=frontmatter.get("name", frontmatter.get("customer", "")),
            email=frontmatter.get("email", ""),
            phone=frontmatter.get("phone", ""),
            action=frontmatter.get("action", "create_contact"),
            status=frontmatter.get("status", "pending_approval"),
            created=_dt(frontmatter.get("created")),
            file_path=file_path,
            mcp_server=frontmatter.get("mcp_server", "odoo-mcp"),
        )

    elif draft_type == "payment":
        def _dt(v):
            if v is None or v == "null":
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        amount_raw = frontmatter.get("amount", 0)
        try:
            amount = float(str(amount_raw).replace(",", "").strip())
        except (ValueError, TypeError):
            amount = 0.0
        return OdooPayment(
            draft_id=frontmatter.get("draft_id", Path(file_path).stem),
            invoice_number=frontmatter.get("invoice_number", ""),
            amount=amount,
            action=frontmatter.get("action", "register_payment"),
            status=frontmatter.get("status", "pending_approval"),
            created=_dt(frontmatter.get("created")),
            file_path=file_path,
            mcp_server=frontmatter.get("mcp_server", "odoo-mcp"),
        )

    elif draft_type == "bill":
        def _dt(v):
            if v is None or v == "null":
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        amount_raw = frontmatter.get("amount", 0)
        try:
            amount = float(str(amount_raw).replace(",", "").strip())
        except (ValueError, TypeError):
            amount = 0.0
        return OdooBill(
            draft_id=frontmatter.get("draft_id", Path(file_path).stem),
            vendor=frontmatter.get("vendor", frontmatter.get("customer", "")),
            amount=amount,
            currency=frontmatter.get("currency", "PKR"),
            description=frontmatter.get("description", body.strip()[:200]),
            action=frontmatter.get("action", "create_purchase_bill"),
            status=frontmatter.get("status", "pending_approval"),
            created=_dt(frontmatter.get("created")),
            file_path=file_path,
            mcp_server=frontmatter.get("mcp_server", "odoo-mcp"),
        )

    else:
        raise ValueError(f"Invalid draft_type: {draft_type}. Must be 'email', 'whatsapp', 'linkedin', 'odoo', 'contact', 'payment', or 'bill'")


def parse_plan_file(file_path: str) -> Plan:
    """
    Parse Plan file from vault/Plans/.

    Args:
        file_path: Absolute path to Plan file

    Returns:
        Parsed Plan object

    Raises:
        ValueError: If required fields missing or invalid structure
    """
    frontmatter, body = parse_frontmatter(file_path)

    # Helper to parse datetime
    def parse_datetime(value):
        if value is None or value == "null":
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

    # Parse steps array
    steps_data = frontmatter.get("steps", [])
    steps = []
    for step_data in steps_data:
        step = PlanStep(
            step_num=step_data.get("step_num", 0),
            description=step_data.get("description", ""),
            action_type=step_data.get("action_type", ""),
            action_params=step_data.get("action_params", {}),
            dependencies=step_data.get("dependencies", []),
            status=step_data.get("status", "pending"),
            mcp_action_log_id=step_data.get("mcp_action_log_id"),
            retry_count=step_data.get("retry_count", 0)
        )
        steps.append(step)

    return Plan(
        plan_id=frontmatter.get("plan_id", ""),
        objective=frontmatter.get("objective", ""),
        steps=steps,
        total_steps=frontmatter.get("total_steps", len(steps)),
        completed_steps=frontmatter.get("completed_steps", 0),
        status=frontmatter.get("status", "awaiting_approval"),
        approval_required=frontmatter.get("approval_required", True),
        estimated_time=frontmatter.get("estimated_time", ""),
        approval_file_path=frontmatter.get("approval_file_path", ""),
        iteration_count=frontmatter.get("iteration_count", 0),
        created_at=parse_datetime(frontmatter.get("created_at")),
        started_at=parse_datetime(frontmatter.get("started_at")),
        completed_at=parse_datetime(frontmatter.get("completed_at")),
        file_path=file_path
    )


def parse_execution_state(file_path: str) -> ExecutionState:
    """
    Parse ExecutionState from vault/In_Progress/{plan_id}/state.md.

    Args:
        file_path: Absolute path to state.md file

    Returns:
        Parsed ExecutionState object
    """
    frontmatter, body = parse_frontmatter(file_path)

    def parse_datetime(value):
        if value is None or value == "null":
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

    return ExecutionState(
        plan_id=frontmatter.get("plan_id", ""),
        current_step=frontmatter.get("current_step", 1),
        iterations_remaining=frontmatter.get("iterations_remaining", 10),
        last_action=frontmatter.get("last_action", ""),
        last_action_timestamp=parse_datetime(frontmatter.get("last_action_timestamp")),
        loop_start_time=parse_datetime(frontmatter.get("loop_start_time")),
        file_path=file_path
    )


def detect_draft_type(file_path: str) -> Optional[str]:
    """
    Auto-detect draft type from file path.

    Args:
        file_path: Path to draft file

    Returns:
        Draft type ("email", "whatsapp", "linkedin") or None if not a draft
    """
    path_str = str(file_path).lower()

    if "/email/" in path_str or "email_draft" in path_str:
        return "email"
    elif "/whatsapp/" in path_str or "whatsapp_draft" in path_str:
        return "whatsapp"
    elif "/linkedin/" in path_str or "linkedin_post" in path_str:
        return "linkedin"
    elif "contact_draft" in path_str:
        return "contact"
    elif "payment_draft" in path_str:
        return "payment"
    elif "bill_draft" in path_str:
        return "bill"
    elif "/odoo/" in path_str or "invoice_draft" in path_str or "odoo_draft" in path_str:
        return "odoo"

    return None


def parse_email_from_vault(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse an EMAIL_*.md file from vault/Inbox/ into a flat email dict.

    Args:
        file_path: Absolute path to EMAIL_*.md file

    Returns:
        Dict with keys: email_id, from, subject, body, priority, received_at
        or None if parsing fails (logs the actual error)
    """
    import logging
    _log = logging.getLogger(__name__)

    try:
        frontmatter, body = parse_frontmatter(file_path)

        # If frontmatter is empty but we have content, try raw line parse
        if not frontmatter:
            _log.warning(f"parse_email_from_vault: empty frontmatter in {file_path}")

        # Safely coerce 'from' field (may contain angle brackets or be a complex string)
        sender = frontmatter.get("from", "")
        if not isinstance(sender, str):
            sender = str(sender)

        # Body may be empty for short/notification emails — use subject as fallback
        email_body = (body or "").strip()
        if not email_body:
            email_body = frontmatter.get("subject", "(no body)")

        return {
            "email_id": str(frontmatter.get("email_id", Path(file_path).stem)),
            "from": sender,
            "subject": str(frontmatter.get("subject", "(no subject)")),
            "body": email_body,
            "priority": str(frontmatter.get("priority", "Normal")),
            "received_at": str(frontmatter.get("received_at", "")),
            "status": str(frontmatter.get("status", "new")),
        }
    except Exception as e:
        _log.error(f"parse_email_from_vault failed for {file_path}: {type(e).__name__}: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Example: Parse email draft
    email_draft = parse_draft_file("vault/Pending_Approval/Email/EMAIL_DRAFT_001.md", "email")
    print(f"Email draft: {email_draft.subject}")

    # Example: Parse plan
    plan = parse_plan_file("vault/Plans/PLAN_onboarding_2026-02-14.md")
    print(f"Plan: {plan.objective}, Steps: {plan.total_steps}")
