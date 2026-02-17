"""
Email Sender Executor - Send approved email drafts via direct SMTP

Reads an approved email .md file, extracts fields from YAML frontmatter,
and sends via Gmail SMTP using credentials from .env.

SMTP config (from .env):
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=465
  SMTP_USER=mmfake78@gmail.com
  SMTP_PASSWORD=<app-password>
  SMTP_USE_SSL=true

Reuses: agent_skills/vault_parser.py for frontmatter parsing
"""
import os
import sys
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.vault_parser import parse_frontmatter

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Sends approved email drafts via Gmail SMTP.

    Usage:
        sender = EmailSender(vault_path)
        result = sender.send_from_file("/path/to/vault/Approved/Email/EMAIL_DRAFT_xxx.md")
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.log_path = self.vault_path / "Logs" / "MCP_Actions"
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Load SMTP config from environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP_USER or SMTP_PASSWORD not set — emails will fail to send")

    def send_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read an approved email .md file and send via SMTP.

        Args:
            file_path: Absolute path to the approved email draft .md file

        Returns:
            Dict with keys: success (bool), message_id (str), error (str)
        """
        file_path = Path(file_path)

        try:
            frontmatter, body = parse_frontmatter(str(file_path))

            to = frontmatter.get("to", "")
            subject = frontmatter.get("subject", "")

            # draft_body may be in frontmatter or in body section
            draft_body = frontmatter.get("draft_body", "") or body

            if not to or not subject:
                raise ValueError(f"Missing required fields (to={to!r}, subject={subject!r})")

            if not draft_body:
                raise ValueError("Email body is empty")

            logger.info(f"Sending email to={to} subject={subject!r}")
            return self.send(to=to, subject=subject, body=draft_body)

        except Exception as e:
            logger.error(f"Failed to send email from {file_path.name}: {e}")
            self._log_action(str(file_path), "error", error=str(e))
            return {"success": False, "message_id": None, "error": str(e)}

    def send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send email via Gmail SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text

        Returns:
            Dict with keys: success (bool), message_id (str or None), error (str or None)
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_user
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, [to], msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, [to], msg.as_string())

            message_id = msg.get("Message-ID", f"smtp-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            self._log_action(reference=f"to={to}", status="success", message_id=message_id)
            logger.info(f"✅ Email sent to {to}: {subject}")
            return {"success": True, "message_id": message_id, "error": None}

        except smtplib.SMTPAuthenticationError as e:
            err = f"SMTP auth failed — check SMTP_USER/SMTP_PASSWORD: {e}"
            logger.error(err)
            self._log_action(reference=f"to={to}", status="auth_error", error=err)
            return {"success": False, "message_id": None, "error": err}

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            self._log_action(reference=f"to={to}", status="error", error=str(e))
            return {"success": False, "message_id": None, "error": str(e)}

    def _log_action(
        self,
        reference: str,
        status: str,
        message_id: str = "",
        error: str = "",
    ) -> None:
        """Append log entry to vault/Logs/MCP_Actions/email_sender.md."""
        log_file = self.log_path / "email_sender.md"
        timestamp = datetime.now().isoformat()
        entry = (
            f"| {timestamp} | {reference[:60]} | {status} | "
            f"{message_id[:40] if message_id else '-'} | "
            f"{error[:80] if error else '-'} |\n"
        )

        try:
            if not log_file.exists():
                log_file.write_text(
                    "# Email Sender Actions\n\n"
                    "| Timestamp | Reference | Status | MessageID | Error |\n"
                    "|-----------|-----------|--------|-----------|-------|\n"
                )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            logger.warning(f"Could not write email sender log: {e}")


def send_email(to: str, subject: str, body: str, vault_path: Optional[str] = None) -> bool:
    """
    Convenience function: send an email and return True/False.

    Args:
        to: Recipient email
        subject: Subject line
        body: Body text
        vault_path: Vault path for logging (uses VAULT_PATH env if None)

    Returns:
        True if sent successfully, False otherwise
    """
    vp = vault_path or os.getenv("VAULT_PATH", "vault")
    sender = EmailSender(vp)
    result = sender.send(to=to, subject=subject, body=body)
    return result["success"]
