"""
Email Sender Executor - Send approved email drafts via Email MCP

Reads an approved email .md file, extracts fields from YAML frontmatter,
and invokes the email-mcp send_email tool. Logs results to vault/Logs/MCP_Actions/.

Reuses: agent_skills/mcp_client.py for MCP invocation
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.mcp_client import get_mcp_client
from agent_skills.vault_parser import parse_frontmatter

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Sends approved email drafts via the email-mcp server.

    Usage:
        sender = EmailSender(vault_path)
        result = sender.send_from_file("/path/to/vault/Approved/Email/EMAIL_DRAFT_xxx.md")
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.log_path = self.vault_path / "Logs" / "MCP_Actions"
        self.log_path.mkdir(parents=True, exist_ok=True)

    def send_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read an approved email .md file and send via email-mcp.

        Args:
            file_path: Absolute path to the approved email draft .md file

        Returns:
            Dict with keys: success (bool), message_id (str), error (str)
        """
        file_path = Path(file_path)

        try:
            frontmatter, body = parse_frontmatter(str(file_path))

            # Extract required fields (prefer frontmatter, fallback to body)
            to = frontmatter.get("to", "")
            subject = frontmatter.get("subject", "")

            # draft_body may be in frontmatter or in body section
            draft_body = frontmatter.get("draft_body", "") or body

            if not to or not subject:
                raise ValueError(f"Missing required fields (to={to!r}, subject={subject!r})")

            if not draft_body:
                raise ValueError("Email body is empty")

            return self.send(to=to, subject=subject, body=draft_body)

        except Exception as e:
            logger.error(f"Failed to send email from {file_path.name}: {e}")
            self._log_action(str(file_path), "error", str(e))
            return {"success": False, "message_id": None, "error": str(e)}

    def send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send email via email-mcp.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text

        Returns:
            Dict with keys: success (bool), message_id (str or None), error (str or None)
        """
        mcp_client = get_mcp_client()

        try:
            result = mcp_client.call_tool(
                mcp_server="email-mcp",
                tool_name="send_email",
                arguments={"to": to, "subject": subject, "body": body},
                retry_count=3,
                retry_delay=5,
            )

            self._log_action(
                reference=f"to={to}",
                status="success",
                message_id=result.get("message_id", ""),
            )
            logger.info(f"✅ Email sent to {to}: {subject}")
            return {"success": True, "message_id": result.get("message_id"), "error": None}

        except Exception as e:
            logger.error(f"Email MCP failed: {e}")
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
                    "# Email Sender MCP Actions\n\n"
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
