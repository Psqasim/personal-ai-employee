"""
WhatsApp Notifier - Send WhatsApp notifications to admin via vault queue

Notification types:
- urgent_email: Alert for high-priority email received
- pending_approvals: Alert when 5+ items waiting approval
- critical_error: Alert on system errors
- morning_summary: Daily 8 AM summary
- task_completed: Confirmation after successful send

Writes draft files to vault/Approved/WhatsApp/ which the whatsapp_watcher
picks up and sends in Phase 3.5. This avoids opening a second Chromium
browser (via MCP) which causes WhatsApp to log out the session.

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import logging
import time
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


def _send_via_vault(message: str, label: str) -> None:
    """
    Queue WhatsApp message by writing a draft file to vault/Approved/WhatsApp/.
    The whatsapp_watcher picks it up in Phase 3.5 and sends it — no second
    browser needed, so WhatsApp session stays stable.
    """
    chat_id = _get_admin_number()
    if not chat_id:
        logger.warning(f"[whatsapp_notifier] No WHATSAPP_NOTIFICATION_NUMBER set, skipping {label}")
        return

    try:
        vault_path = os.getenv("VAULT_PATH", "vault")
        wa_dir = Path(vault_path) / "Approved" / "WhatsApp"
        wa_dir.mkdir(parents=True, exist_ok=True)

        ts = int(time.time() * 1000)
        filename = f"NOTIFY_{label}_{ts}.md"
        draft = (
            f"---\n"
            f"action: send_message\n"
            f"chat_id: \"{chat_id}\"\n"
            f"draft_body: \"{message}\"\n"
            f"source: cloud_orchestrator\n"
            f"label: {label}\n"
            f"created: \"{datetime.now().isoformat()}\"\n"
            f"---\n"
        )
        (wa_dir / filename).write_text(draft, encoding="utf-8")
        logger.info(f"[whatsapp_notifier] ✅ Queued {label} → {filename}")
        _log_notification(label, message, "queued")
    except Exception as e:
        logger.warning(
            f"[whatsapp_notifier] ⚠️ Could not queue {label}: {e}"
        )
        _log_notification(label, message, "queue_failed", str(e))


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
    _send_via_vault(message,"urgent_email")


def notify_pending_approvals(count: int, oldest_item: str) -> None:
    """Send WhatsApp alert when 5+ items are waiting approval."""
    if not _is_enabled():
        return
    message = (
        f"⏳ *{count} Items Waiting Approval*\n"
        f"Oldest: {oldest_item}\n"
        "Open dashboard: http://localhost:3000/dashboard"
    )
    _send_via_vault(message,"pending_approvals")


def notify_critical_error(error_message: str) -> None:
    """Send WhatsApp alert on critical system error."""
    if not _is_enabled():
        return
    message = (
        "❌ *System Error*\n"
        f"Error: {error_message}\n"
        "Check logs: vault/Logs/Cloud/"
    )
    _send_via_vault(message,"critical_error")


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
    _send_via_vault(message,"morning_summary")


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
    _send_via_vault(message,"task_completed")
