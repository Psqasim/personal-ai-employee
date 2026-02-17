"""
Email Draft Generator (Cloud Agent)

Thin wrapper around agent_skills/draft_generator.py that:
1. Takes raw email data (dict)
2. Uses Claude API to generate a smart reply draft
3. Saves the draft to vault/Pending_Approval/Email/
4. Returns the saved draft file path

Reuses: agent_skills/draft_generator.generate_email_draft
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

from agent_skills.draft_generator import generate_email_draft

logger = logging.getLogger(__name__)


class EmailDraftGenerator:
    """
    Generates email reply drafts for Cloud Agent.

    Cloud Agent is responsible for DRAFTING only - never sending.
    Drafts are saved to vault/Pending_Approval/Email/ for Local Agent to approve.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pending_dir = self.vault_path / "Pending_Approval" / "Email"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

        self.handbook_path = self.vault_path / "Company_Handbook.md"

    def generate_and_save(self, email_data: Dict[str, Any]) -> Optional[Path]:
        """
        Generate AI reply draft for email_data and save to vault/Pending_Approval/Email/.

        Args:
            email_data: Dict with keys: email_id, from, subject, body, priority

        Returns:
            Path to saved draft file, or None if failed
        """
        email_id = email_data.get("email_id", f"EMAIL_{int(datetime.now().timestamp())}")

        # Check if draft already exists (idempotent)
        draft_path = self.pending_dir / f"EMAIL_DRAFT_{email_id}.md"
        if draft_path.exists():
            logger.debug(f"Draft already exists for {email_id}")
            return draft_path

        try:
            draft = generate_email_draft(
                original_email=email_data,
                company_handbook_path=str(self.handbook_path)
                if self.handbook_path.exists()
                else None,
            )

            self._save_draft(draft, draft_path)
            logger.info(f"✅ Email draft saved: {draft_path.name}")
            return draft_path

        except Exception as e:
            logger.error(f"Failed to generate draft for {email_id}: {e}")
            return None

    def _save_draft(self, draft: Dict[str, Any], dest: Path) -> None:
        """Write draft dict to .md file with YAML frontmatter."""
        dest.parent.mkdir(parents=True, exist_ok=True)

        content = (
            f"---\n"
            f"draft_id: {draft['draft_id']}\n"
            f"original_email_id: {draft.get('original_email_id', '')}\n"
            f"to: {draft['to']}\n"
            f"subject: {draft['subject']}\n"
            f"status: pending_approval\n"
            f"action: send_email\n"
            f"mcp_server: email-mcp\n"
            f"generated_at: {draft.get('generated_at', datetime.now().isoformat())}\n"
            f"sent_at: null\n"
            f"---\n\n"
            f"{draft['draft_body']}\n"
        )

        dest.write_text(content, encoding="utf-8")


def generate_and_save_email_draft(
    email_data: Dict[str, Any], vault_path: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function: generate and save email draft.

    Args:
        email_data: Raw email dict (email_id, from, subject, body)
        vault_path: Vault path (uses VAULT_PATH env if None)

    Returns:
        Path string of saved draft, or None if failed
    """
    vp = vault_path or os.getenv("VAULT_PATH", "vault")
    gen = EmailDraftGenerator(vp)
    path = gen.generate_and_save(email_data)
    return str(path) if path else None
