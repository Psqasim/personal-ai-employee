"""
WhatsApp Notifier - Send WhatsApp notifications to admin via MCP

Notification types:
- urgent_email: Alert for high-priority email received
- pending_approvals: Alert when 5+ items waiting approval
- critical_error: Alert on system errors
- morning_summary: Daily 8 AM summary
- task_completed: Confirmation after successful send

Uses existing WhatsApp MCP server in a thread with 65s timeout
to avoid blocking the main orchestration loop.

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Check if WhatsApp notifications are enabled via env flag."""
    return os.getenv("ENABLE_WHATSAPP_NOTIFICATIONS", "false").lower() == "true"


def _get_admin_number() -> str:
    """Get admin WhatsApp number from env."""
    return os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "")


def _send_in_thread(message: str, label: str) -> None:
    """
    Send WhatsApp message in a background thread with 65s hard timeout.
    Non-blocking — main loop continues immediately.

    Args:
        message: WhatsApp message text
        label: Log label for this notification type
    """
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from agent_skills.mcp_client import get_mcp_client

    chat_id = _get_admin_number()
    if not chat_id:
        logger.warning(f"[whatsapp_notifier] No WHATSAPP_NOTIFICATION_NUMBER set, skipping {label}")
        return

    def _send():
        try:
            client = get_mcp_client(timeout=65)
            result = client.call_tool(
                mcp_server="whatsapp-mcp",
                tool_name="send_message",
                arguments={"chat_id": chat_id, "message": message},
                retry_count=1,
                retry_delay=2
            )
            if result.get("success"):
                logger.info(f"[whatsapp_notifier] ✅ Sent {label} notification")
            else:
                logger.warning(f"[whatsapp_notifier] ⚠️ Failed {label}: {result.get('error')}")
        except Exception as e:
            logger.error(f"[whatsapp_notifier] ❌ Error sending {label}: {e}")

    thread = threading.Thread(target=_send, daemon=True, name=f"wa-notify-{label}")
    thread.start()
    # Do NOT join — non-blocking by design


def notify_urgent_email(sender: str, subject: str) -> None:
    """
    Send WhatsApp alert when urgent email is received.

    Args:
        sender: Email sender address
        subject: Email subject line
    """
    if not _is_enabled():
        return

    message = (
        "🚨 *Urgent Email Received*\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        "Action needed: http://localhost:3000/dashboard"
    )
    _send_in_thread(message, "urgent_email")


def notify_pending_approvals(count: int, oldest_item: str) -> None:
    """
    Send WhatsApp alert when 5+ items are waiting approval.

    Args:
        count: Number of pending approval items
        oldest_item: Description of the oldest pending item
    """
    if not _is_enabled():
        return

    message = (
        f"⏳ *{count} Items Waiting Approval*\n"
        f"Oldest: {oldest_item}\n"
        "Open dashboard: http://localhost:3000/dashboard"
    )
    _send_in_thread(message, "pending_approvals")


def notify_critical_error(error_message: str) -> None:
    """
    Send WhatsApp alert on critical system error.

    Args:
        error_message: Error description
    """
    if not _is_enabled():
        return

    message = (
        "❌ *System Error*\n"
        f"Error: {error_message}\n"
        "Check logs: vault/Logs/Cloud/"
    )
    _send_in_thread(message, "critical_error")


def notify_morning_summary(
    emails_pending: int,
    processed_yesterday: int,
    api_cost_today: float
) -> None:
    """
    Send WhatsApp morning summary at 8 AM daily.

    Args:
        emails_pending: Number of emails waiting in inbox/pending
        processed_yesterday: Tasks processed the previous day
        api_cost_today: Claude API cost so far today in USD
    """
    if not _is_enabled():
        return

    message = (
        "☀️ *Good Morning Muhammad!*\n"
        f"📧 Emails pending: {emails_pending}\n"
        f"✅ Processed yesterday: {processed_yesterday}\n"
        f"💰 API cost today: ${api_cost_today:.4f}"
    )
    _send_in_thread(message, "morning_summary")


def notify_task_completed(
    task_type: str,
    recipient: str,
    subject: Optional[str] = None
) -> None:
    """
    Send WhatsApp confirmation after successful task execution.

    Args:
        task_type: Type of task (e.g., "Email", "WhatsApp")
        recipient: Recipient name or number
        subject: Subject line (optional, for email tasks)
    """
    if not _is_enabled():
        return

    subject_line = f"\nSubject: {subject}" if subject else ""
    message = (
        "✅ *Task Completed*\n"
        f"{task_type} sent to {recipient}"
        f"{subject_line}"
    )
    _send_in_thread(message, "task_completed")
