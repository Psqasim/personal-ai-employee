"""
WhatsApp Notifier - Send WhatsApp notifications to admin via MCP

Notification types:
- urgent_email: Alert for high-priority email received
- pending_approvals: Alert when 5+ items waiting approval
- critical_error: Alert on system errors
- morning_summary: Daily 8 AM summary
- task_completed: Confirmation after successful send

Uses existing WhatsApp MCP server in a thread with 65s timeout.
Falls back to vault/Logs/Notifications/ log file when Playwright
is unavailable (e.g. WSL2 /mnt/ filesystem limitation).

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Check if WhatsApp notifications are enabled via env flag."""
    return os.getenv("ENABLE_WHATSAPP_NOTIFICATIONS", "false").lower() == "true"


def _get_admin_number() -> str:
    """Get admin WhatsApp number from env."""
    return os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "")


def _log_notification(label: str, message: str, status: str, error: str = "") -> None:
    """
    Write notification record to vault/Logs/Notifications/notifications.md.
    Acts as fallback evidence when WhatsApp MCP is unavailable.
    """
    try:
        vault_path = os.getenv("VAULT_PATH", "vault")
        log_dir = Path(vault_path) / "Logs" / "Notifications"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "notifications.md"

        timestamp = datetime.now().isoformat()
        admin = _get_admin_number()
        error_col = error[:80] if error else "-"
        entry = f"| {timestamp} | {label} | {admin} | {status} | {error_col} |\n"

        if not log_file.exists():
            log_file.write_text(
                "# WhatsApp Notification Log\n\n"
                "| Timestamp | Type | To | Status | Error |\n"
                "|-----------|------|----|--------|-------|\n"
            )
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
            # Also write message body for traceability
            f.write(f"\n```\n{message}\n```\n\n")
    except Exception as e:
        logger.warning(f"[whatsapp_notifier] Could not write notification log: {e}")


def _send_in_thread(message: str, label: str) -> None:
    """
    Send WhatsApp message in a background thread with 65s hard timeout.
    Falls back to vault log if MCP/Playwright fails.
    Non-blocking — main loop continues immediately.
    """
    import sys
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    chat_id = _get_admin_number()
    if not chat_id:
        logger.warning(f"[whatsapp_notifier] No WHATSAPP_NOTIFICATION_NUMBER set, skipping {label}")
        return

    def _send():
        try:
            from agent_skills.mcp_client import get_mcp_client
            client = get_mcp_client(timeout=10)  # Fail fast; fallback to vault log
            result = client.call_tool(
                mcp_server="whatsapp-mcp",
                tool_name="send_message",
                arguments={"chat_id": chat_id, "message": message},
                retry_count=1,
                retry_delay=2
            )
            if result.get("success"):
                logger.info(f"[whatsapp_notifier] ✅ Sent {label} via WhatsApp")
                _log_notification(label, message, "sent")
            else:
                err = result.get("error", "unknown")
                logger.warning(f"[whatsapp_notifier] ⚠️ WhatsApp MCP failed {label}: {err}")
                _log_notification(label, message, "mcp_failed", err)
        except Exception as e:
            # Playwright/MCP unavailable — log to vault as fallback
            logger.warning(
                f"[whatsapp_notifier] ⚠️ WhatsApp unavailable ({label}), "
                f"logged to vault/Logs/Notifications/ — {type(e).__name__}: {e}"
            )
            _log_notification(label, message, "logged_fallback", str(e))

    thread = threading.Thread(target=_send, daemon=True, name=f"wa-notify-{label}")
    thread.start()
    # Do NOT join — non-blocking by design


def notify_urgent_email(sender: str, subject: str) -> None:
    """Send WhatsApp alert when urgent email is received."""
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
    """Send WhatsApp alert when 5+ items are waiting approval."""
    if not _is_enabled():
        return
    message = (
        f"⏳ *{count} Items Waiting Approval*\n"
        f"Oldest: {oldest_item}\n"
        "Open dashboard: http://localhost:3000/dashboard"
    )
    _send_in_thread(message, "pending_approvals")


def notify_critical_error(error_message: str) -> None:
    """Send WhatsApp alert on critical system error."""
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
    """Send WhatsApp morning summary at 8 AM daily."""
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
    """Send WhatsApp confirmation after successful task execution."""
    if not _is_enabled():
        return
    subject_line = f"\nSubject: {subject}" if subject else ""
    message = (
        "✅ *Task Completed*\n"
        f"{task_type} sent to {recipient}"
        f"{subject_line}"
    )
    _send_in_thread(message, "task_completed")
