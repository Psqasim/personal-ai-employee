#!/usr/bin/env python3
"""
Gmail Watcher - Gold Tier Extension

Monitors Gmail inbox for high-priority emails and generates draft replies.
Extends Silver tier functionality with:
- Draft generation for high-priority emails (type="email", priority="High")
- Draft validation (email format, char limits)
- Draft file creation in vault/Pending_Approval/Email/

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T014 (watcher extension), T016 (validation), T017 (approval gate)
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add agent_skills to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.draft_generator import generate_email_draft
from agent_skills.vault_parser import parse_frontmatter
import yaml


def monitor_inbox_for_email_drafts(vault_path: str, poll_interval: int = 120):
    """
    Monitor vault/Inbox/ for high-priority email tasks and generate drafts.

    Args:
        vault_path: Absolute path to vault root
        poll_interval: Seconds between polls (default: 120)
    """
    vault = Path(vault_path)
    inbox_dir = vault / "Inbox"
    pending_approval_email = vault / "Pending_Approval" / "Email"
    company_handbook = vault / "Company_Handbook.md"

    # Ensure directories exist
    pending_approval_email.mkdir(parents=True, exist_ok=True)

    print(f"[gmail_watcher] Starting Gmail watcher (poll interval: {poll_interval}s)")
    print(f"[gmail_watcher] Monitoring: {inbox_dir}")
    print(f"[gmail_watcher] Draft output: {pending_approval_email}")

    processed_emails = set()  # Track processed email IDs

    while True:
        try:
            # Scan inbox for EMAIL_* files
            if inbox_dir.exists():
                for email_file in inbox_dir.glob("EMAIL_*.md"):
                    email_id = email_file.stem

                    # Skip already processed
                    if email_id in processed_emails:
                        continue

                    # Parse email file
                    try:
                        frontmatter, body = parse_frontmatter(str(email_file))

                        # T062: Cross-domain routing - Update task with domain field
                        _apply_domain_routing(email_file, frontmatter)

                        # Check if high priority AND type=email
                        if (frontmatter.get("type") == "email" and
                            frontmatter.get("priority") == "High"):

                            print(f"[gmail_watcher] High-priority email detected: {email_id}")

                            # Generate draft
                            original_email = {
                                "email_id": email_id,
                                "from": frontmatter.get("from", "unknown@example.com"),
                                "subject": frontmatter.get("subject", "No Subject"),
                                "body": body,
                                "priority": frontmatter.get("priority", "Medium")
                            }

                            # Generate draft using AI
                            draft = generate_email_draft(
                                original_email,
                                company_handbook_path=str(company_handbook) if company_handbook.exists() else None
                            )

                            # Validate draft (T016)
                            if not validate_email_draft(draft):
                                print(f"[gmail_watcher] Draft validation failed for {email_id}")
                                processed_emails.add(email_id)
                                continue

                            # Save draft to vault/Pending_Approval/Email/
                            draft_file = pending_approval_email / f"{draft['draft_id']}.md"
                            _save_email_draft(draft, draft_file)

                            print(f"[gmail_watcher] Draft saved: {draft_file.name}")
                            processed_emails.add(email_id)

                    except Exception as e:
                        print(f"[gmail_watcher] Error processing {email_file.name}: {e}")
                        processed_emails.add(email_id)

            # Sleep until next poll
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[gmail_watcher] Stopped by user")
            break
        except Exception as e:
            print(f"[gmail_watcher] Error in main loop: {e}")
            time.sleep(poll_interval)


def validate_email_draft(draft: Dict[str, Any]) -> bool:
    """
    Validate email draft (T016: email draft validation).

    Args:
        draft: EmailDraft dict from generate_email_draft()

    Returns:
        True if valid, False otherwise
    """
    # Validate recipient email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, draft.get("to", "")):
        print(f"[validation] Invalid recipient email: {draft.get('to')}")
        return False

    # Enforce 5000 char max for draft_body
    if len(draft.get("draft_body", "")) > 5000:
        print(f"[validation] Draft body exceeds 5000 chars: {len(draft['draft_body'])}")
        return False

    # Check required fields
    required_fields = ["draft_id", "to", "subject", "draft_body", "action", "mcp_server"]
    for field in required_fields:
        if field not in draft:
            print(f"[validation] Missing required field: {field}")
            return False

    return True


def _save_email_draft(draft: Dict[str, Any], output_path: Path):
    """Save EmailDraft to markdown file with YAML frontmatter"""
    import json
    # Quote subject to handle colons and special characters in YAML
    subject_quoted = json.dumps(draft['subject'])

    content = f"""---
draft_id: {draft['draft_id']}
original_email_id: {draft['original_email_id']}
to: {draft['to']}
subject: {subject_quoted}
draft_body: |
{_indent_multiline(draft['draft_body'], 2)}
status: {draft['status']}
generated_at: {draft['generated_at']}
sent_at: {draft['sent_at']}
action: {draft['action']}
mcp_server: {draft['mcp_server']}
---

# Email Draft

**Original Email**: [[{draft['original_email_id']}]]
**To**: {draft['to']}
**Subject**: {draft['subject']}

## Draft Body

{draft['draft_body']}

## Approval

- Move to `vault/Approved/Email/` to send
- Move to `vault/Rejected/` to discard

---

*Generated at: {draft['generated_at']}*
"""

    output_path.write_text(content, encoding='utf-8')


def _indent_multiline(text: str, spaces: int) -> str:
    """Indent multiline text for YAML"""
    indent = " " * spaces
    return "\n".join(indent + line for line in text.split("\n"))


def _apply_domain_routing(task_file: Path, frontmatter: Dict[str, Any]):
    """
    T062: Cross-domain routing logic.

    Read task category from Silver AI categorization and route to appropriate domain:
    - Work/Urgent tasks → Business domain (LinkedIn, Odoo)
    - Personal tasks → Personal domain (calendar, email)

    Updates task frontmatter with domain="Personal"|"Business"

    Args:
        task_file: Path to task file
        frontmatter: Parsed frontmatter dict
    """
    # Get category from Silver AI categorization
    category = frontmatter.get("category", "Uncategorized")

    # Determine domain based on category
    if category in ["Work", "Urgent"]:
        domain = "Business"
    elif category == "Personal":
        domain = "Personal"
    else:
        # Default to Personal for uncategorized tasks
        domain = "Personal"

    # Check if domain already set
    if frontmatter.get("domain") == domain:
        return  # Already set, no update needed

    # Update task file with domain field
    try:
        content = task_file.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        if not content.startswith("---"):
            return

        parts = content.split("---", 2)
        if len(parts) < 3:
            return

        # Update frontmatter
        frontmatter_dict = yaml.safe_load(parts[1])
        frontmatter_dict["domain"] = domain

        # Rebuild file content
        updated_content = "---\n" + yaml.dump(frontmatter_dict, default_flow_style=False, allow_unicode=True) + "---" + parts[2]

        # Write back atomically
        task_file.write_text(updated_content, encoding="utf-8")

        print(f"[gmail_watcher] Domain routing: {task_file.name} → {domain} (category={category})")

    except Exception as e:
        print(f"[gmail_watcher] ERROR applying domain routing to {task_file.name}: {e}")


if __name__ == "__main__":
    # Get vault path from environment or command line
    vault_path = os.getenv("VAULT_PATH", "vault")
    poll_interval = int(os.getenv("GMAIL_POLL_INTERVAL", "120"))

    if len(sys.argv) > 1:
        vault_path = sys.argv[1]

    monitor_inbox_for_email_drafts(vault_path, poll_interval)
