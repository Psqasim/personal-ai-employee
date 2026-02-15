#!/usr/bin/env python3
"""
LinkedIn Generator - Gold Tier

Generates LinkedIn posts on a schedule (daily/weekly), aligned with business goals
from Company_Handbook.md. Posts require human approval before publishing.

Features:
- Scheduled generation (daily/weekly)
- Business goals alignment from Company_Handbook.md
- Draft validation (3000 char max, auto-truncate)
- Deduplication (max 1 post/day)
- Rejected draft handling

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T021-T022 (generator + scheduling), T024 (validation), T025 (rejection handling)
"""

import os
import sys
import time
import schedule
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional

# Add agent_skills to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.draft_generator import generate_linkedin_draft


def run_linkedin_generator(vault_path: str, force: bool = False):
    """
    Generate LinkedIn post draft (scheduled or forced).

    Args:
        vault_path: Absolute path to vault root
        force: If True, bypass schedule and generate immediately
    """
    vault = Path(vault_path)
    pending_approval_linkedin = vault / "Pending_Approval" / "LinkedIn"
    done_dir = vault / "Done"
    company_handbook = vault / "Company_Handbook.md"

    # Ensure directories exist
    pending_approval_linkedin.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    # T022: Deduplication check (max 1 post/day)
    if not force:
        # Check if post already created for today
        existing_drafts = list(pending_approval_linkedin.glob(f"LINKEDIN_POST_{today}*.md"))
        if existing_drafts:
            print(f"[linkedin_generator] Post already pending for {today}, skipping")
            return

        # Check if post already published today
        published_today = list(done_dir.glob(f"LINKEDIN_POST_{today}*.md"))
        if published_today:
            print(f"[linkedin_generator] Post already published for {today}, skipping")
            return

    # Read business goals from Company_Handbook.md
    business_goals = ""
    if company_handbook.exists():
        business_goals = _extract_business_goals(company_handbook)
        if not business_goals:
            print("[linkedin_generator] Warning: No Business Goals section found in Company_Handbook.md")
            business_goals = "Promote our business and engage with professional network"

    print(f"[linkedin_generator] Generating LinkedIn post for {today}")

    # Generate LinkedIn draft
    try:
        draft = generate_linkedin_draft(
            business_goals=business_goals,
            posting_date=today
        )

        # Validate draft (T024)
        if not validate_linkedin_draft(draft):
            print("[linkedin_generator] Draft validation failed")
            return

        # Save draft to vault/Pending_Approval/LinkedIn/
        draft_file = pending_approval_linkedin / f"{draft['draft_id']}.md"
        _save_linkedin_draft(draft, draft_file)

        print(f"[linkedin_generator] Draft saved: {draft_file.name}")
        print(f"[linkedin_generator] Character count: {draft['character_count']}/3000")

    except Exception as e:
        print(f"[linkedin_generator] Error generating draft: {e}")


def validate_linkedin_draft(draft: Dict[str, Any]) -> bool:
    """
    Validate LinkedIn draft (T024: LinkedIn draft validation).

    Args:
        draft: LinkedInDraft dict from generate_linkedin_draft()

    Returns:
        True if valid, False otherwise
    """
    # Enforce 3000 char max
    if draft['character_count'] > 3000:
        print(f"[validation] Post exceeds 3000 chars: {draft['character_count']}")
        # Auto-truncate was already done in draft_generator, but log warning
        if len(draft['post_content']) > 3000:
            return False

    # Check required fields
    required_fields = ["draft_id", "post_content", "action", "mcp_server"]
    for field in required_fields:
        if field not in draft:
            print(f"[validation] Missing required field: {field}")
            return False

    # Check business goal reference exists
    if not draft.get("business_goal_reference"):
        print("[validation] Warning: No business goal reference")

    return True


def handle_rejected_drafts(vault_path: str):
    """
    Handle rejected LinkedIn drafts (T025: rejected draft handling).

    Detects drafts moved to vault/Rejected/, creates retry file in vault/Needs_Action/.
    """
    vault = Path(vault_path)
    rejected_dir = vault / "Rejected"
    needs_action_dir = vault / "Needs_Action"

    if not rejected_dir.exists():
        return

    # Scan for rejected LinkedIn drafts
    for rejected_file in rejected_dir.glob("LINKEDIN_POST_*.md"):
        # Extract date from filename
        try:
            # LINKEDIN_POST_2026-02-14.md -> 2026-02-14
            date_str = rejected_file.stem.replace("LINKEDIN_POST_", "")

            # Create retry file in Needs_Action
            retry_file = needs_action_dir / f"LINKEDIN_POST_{date_str}_retry.md"

            if not retry_file.exists():
                content = f"""---
original_draft: {rejected_file.name}
rejected_at: {datetime.now().isoformat()}
retry_required: true
---

# LinkedIn Post Regeneration Required

**Original Draft**: [[{rejected_file.name}]]
**Rejected At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Action Required

The LinkedIn post for {date_str} was rejected. Please:

1. Review the rejected draft in [[{rejected_file.name}]]
2. Determine if post should be regenerated or skipped
3. If regenerating, run:
   ```bash
   python scripts/linkedin_generator.py --force
   ```
4. If skipping, move this file to vault/Done/

## Next Steps

- [ ] Review original draft
- [ ] Decide: Regenerate or Skip
- [ ] Execute chosen action
"""

                retry_file.write_text(content, encoding='utf-8')
                print(f"[linkedin_generator] Retry file created: {retry_file.name}")

        except Exception as e:
            print(f"[linkedin_generator] Error handling rejected draft {rejected_file.name}: {e}")


def _extract_business_goals(handbook_path: Path) -> str:
    """
    Extract Business Goals section from Company_Handbook.md.

    Args:
        handbook_path: Path to Company_Handbook.md

    Returns:
        Business goals text (max 500 chars)
    """
    try:
        content = handbook_path.read_text(encoding='utf-8')

        # Find "Business Goals" section
        import re
        pattern = r'## Business Goals(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            goals = match.group(1).strip()
            return goals[:500]  # Limit to 500 chars for API cost control

    except Exception as e:
        print(f"[linkedin_generator] Error reading handbook: {e}")

    return ""


def _save_linkedin_draft(draft: Dict[str, Any], output_path: Path):
    """Save LinkedInDraft to markdown file with YAML frontmatter"""
    # Convert None to YAML null for posted_at
    posted_at_value = "null" if draft['posted_at'] is None else draft['posted_at']

    content = f"""---
draft_id: {draft['draft_id']}
scheduled_date: {draft['scheduled_date']}
business_goal_reference: {draft['business_goal_reference']}
post_content: |
{_indent_multiline(draft['post_content'], 2)}
character_count: {draft['character_count']}
status: {draft['status']}
generated_at: {draft['generated_at']}
posted_at: {posted_at_value}
action: {draft['action']}
mcp_server: {draft['mcp_server']}
---

# LinkedIn Post Draft

**Scheduled Date**: {draft['scheduled_date']}
**Business Goal**: {draft['business_goal_reference']}
**Character Count**: {draft['character_count']}/3000

## Post Content

{draft['post_content']}

## Approval

- Move to `vault/Approved/LinkedIn/` to publish
- Move to `vault/Rejected/` to discard (will create retry file)

---

*Generated at: {draft['generated_at']}*
"""

    output_path.write_text(content, encoding='utf-8')


def _indent_multiline(text: str, spaces: int) -> str:
    """Indent multiline text for YAML"""
    indent = " " * spaces
    return "\n".join(indent + line for line in text.split("\n"))


def start_scheduled_generator(vault_path: str):
    """
    Start LinkedIn generator with schedule (T022: scheduling).

    Schedule based on LINKEDIN_POSTING_FREQUENCY env var:
    - daily: Every day at 09:00
    - weekly: Every Monday at 09:00
    - biweekly: Every other Monday at 09:00
    """
    frequency = os.getenv("LINKEDIN_POSTING_FREQUENCY", "daily").lower()

    print(f"[linkedin_generator] Starting LinkedIn generator (frequency: {frequency})")

    if frequency == "daily":
        schedule.every().day.at("09:00").do(run_linkedin_generator, vault_path=vault_path)
        print("[linkedin_generator] Scheduled: Daily at 09:00")

    elif frequency == "weekly":
        schedule.every().monday.at("09:00").do(run_linkedin_generator, vault_path=vault_path)
        print("[linkedin_generator] Scheduled: Weekly (Monday at 09:00)")

    elif frequency == "biweekly":
        schedule.every(2).weeks.at("09:00").do(run_linkedin_generator, vault_path=vault_path)
        print("[linkedin_generator] Scheduled: Biweekly (every 2 weeks at 09:00)")

    else:
        print(f"[linkedin_generator] Unknown frequency: {frequency}, defaulting to daily")
        schedule.every().day.at("09:00").do(run_linkedin_generator, vault_path=vault_path)

    # Also schedule rejected draft handler (runs hourly)
    schedule.every().hour.do(handle_rejected_drafts, vault_path=vault_path)

    # Run scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Post Generator")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "vault"),
                       help="Path to vault directory")
    parser.add_argument("--force", action="store_true",
                       help="Force generation immediately (bypass schedule)")
    parser.add_argument("--schedule", action="store_true",
                       help="Run in scheduled mode (blocking)")

    args = parser.parse_args()

    if args.force:
        # Force immediate generation
        run_linkedin_generator(args.vault, force=True)
    elif args.schedule:
        # Run scheduled generator
        start_scheduled_generator(args.vault)
    else:
        # Default: run once
        run_linkedin_generator(args.vault)
