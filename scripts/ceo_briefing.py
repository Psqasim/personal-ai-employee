#!/usr/bin/env python3
"""
CEO Briefing Generator - Weekly Business Audit & Summary

Generates weekly executive briefings every Sunday at 23:00 containing:
- Task completion counts by category (Email, WhatsApp, LinkedIn, Odoo)
- Pending/blocked items
- API cost summary
- Proactive suggestions
- WhatsApp notification to admin

Saves briefing to vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
Also updates vault/Dashboard.md with latest stats.

Usage:
    python scripts/ceo_briefing.py --force          # generate now (test)
    python scripts/ceo_briefing.py --schedule       # run Sunday 23:00 loop
    python scripts/generate_ceo_briefing.py         # alias for --force
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.vault_parser import parse_frontmatter


# ─── Date helpers ─────────────────────────────────────────────────────────────

def calculate_week_dates() -> Dict[str, datetime]:
    """Calculate rolling 7-day window ending now (inclusive of today's work)."""
    now = datetime.now()
    week_end = now
    week_start = now - timedelta(days=7)
    briefing_date = now

    return {
        "week_start": week_start.replace(hour=0, minute=0, second=0, microsecond=0),
        "week_end": week_end,
        "briefing_date": briefing_date.replace(hour=0, minute=0, second=0, microsecond=0),
    }


# ─── Data collectors ───────────────────────────────────────────────────────────

def count_done_by_category(vault_path: str, week_start: datetime, week_end: datetime) -> Dict[str, int]:
    """
    Count completed tasks in vault/Done/<category>/ subdirectories.
    Returns dict: { "Email": N, "WhatsApp": N, "LinkedIn": N, "Odoo": N, "Total": N }
    """
    vault = Path(vault_path)
    done_dir = vault / "Done"
    counts: Dict[str, int] = {}

    if not done_dir.exists():
        return {"Email": 0, "WhatsApp": 0, "LinkedIn": 0, "Odoo": 0, "Total": 0}

    total = 0
    for category_dir in done_dir.iterdir():
        if not category_dir.is_dir():
            continue
        cat_name = category_dir.name
        cat_count = 0
        for md_file in category_dir.glob("*.md"):
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if week_start <= mtime <= week_end:
                    cat_count += 1
            except Exception:
                continue
        if cat_count:
            counts[cat_name] = cat_count
        total += cat_count

    counts.setdefault("Email", 0)
    counts.setdefault("WhatsApp", 0)
    counts.setdefault("LinkedIn", 0)
    counts.setdefault("Odoo", 0)
    counts["Total"] = total
    return counts


def count_pending_approvals(vault_path: str) -> int:
    """Count files in vault/Pending_Approval/ subdirs."""
    vault = Path(vault_path)
    pending_dir = vault / "Pending_Approval"
    if not pending_dir.exists():
        return 0
    count = 0
    for subdir in pending_dir.iterdir():
        if subdir.is_dir():
            count += sum(1 for f in subdir.glob("*.md"))
        elif subdir.suffix == ".md":
            count += 1
    return count


def calculate_api_cost_week(vault_path: str, week_start: datetime, week_end: datetime) -> float:
    """
    Sum API cost from vault/Logs/API_Usage/YYYY-MM-DD.md files.
    Parses the markdown table column: | $0.0042 |
    """
    vault = Path(vault_path)
    api_dir = vault / "Logs" / "API_Usage"
    if not api_dir.exists():
        return 0.0

    total = 0.0
    for log_file in api_dir.glob("*.md"):
        try:
            date_str = log_file.stem
            log_date = datetime.strptime(date_str, "%Y-%m-%d")
            if not (week_start.date() <= log_date.date() <= week_end.date()):
                continue
            content = log_file.read_text(encoding="utf-8")
            # Try YAML frontmatter first (cost: 0.003552)
            cost_match = re.search(r'^cost:\s*([\d.]+)', content, re.MULTILINE)
            if cost_match:
                total += float(cost_match.group(1))
                continue
            # Fallback: markdown table format (| $0.0042 |)
            for line in content.splitlines():
                if line.startswith("|") and "$" in line:
                    for part in line.split("|"):
                        m = re.search(r'\$(\d+\.\d+)', part.strip())
                        if m:
                            total += float(m.group(1))
                            break
        except Exception:
            continue
    return round(total, 4)


def get_completed_items_list(vault_path: str, week_start: datetime, week_end: datetime) -> List[str]:
    """Get list of completed task titles from Done/ subdirs."""
    vault = Path(vault_path)
    done_dir = vault / "Done"
    items = []
    if not done_dir.exists():
        return items

    for cat_dir in done_dir.iterdir():
        if not cat_dir.is_dir():
            continue
        cat = cat_dir.name
        for md_file in sorted(cat_dir.glob("*.md")):
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if not (week_start <= mtime <= week_end):
                    continue
                fm, _ = parse_frontmatter(str(md_file))
                title = (fm.get("subject") or fm.get("title") or
                         fm.get("customer") or md_file.stem)
                items.append(f"- [{cat}] {title} — {mtime.strftime('%b %d')}")
            except Exception:
                items.append(f"- [{cat}] {md_file.stem}")

    return items[:30]


def get_suggestions(vault_path: str) -> List[str]:
    """Generate proactive suggestions based on vault state."""
    vault = Path(vault_path)
    suggestions = []

    # Old pending approvals
    pending_dir = vault / "Pending_Approval"
    if pending_dir.exists():
        for subdir in pending_dir.iterdir():
            if not subdir.is_dir():
                continue
            for f in subdir.glob("*.md"):
                age = (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days
                if age >= 3:
                    suggestions.append(
                        f"**{subdir.name} approval pending {age} days** – `{f.name}` needs review"
                    )

    # High-priority emails in Inbox
    inbox_dir = vault / "Inbox"
    if inbox_dir.exists():
        hp = [f for f in inbox_dir.glob("EMAIL_*.md")
              if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() > 86400]
        if hp:
            suggestions.append(f"**{len(hp)} emails in Inbox >24h old** – review vault/Inbox/")

    if not suggestions:
        suggestions.append("**All systems healthy** – no urgent items detected")
        suggestions.append("**Continue current pace** – task throughput is on track")

    return suggestions[:6]


# ─── WhatsApp notification ─────────────────────────────────────────────────────

def send_whatsapp_briefing(counts: Dict[str, int], api_cost: float, date_str: str) -> None:
    """Send CEO briefing summary via WhatsApp."""
    try:
        from cloud_agent.src.notifications.whatsapp_notifier import _send_in_thread, _is_enabled
        if not _is_enabled():
            print("[ceo_briefing] WhatsApp notifications disabled (ENABLE_WHATSAPP_NOTIFICATIONS != true)")
            return
        msg = (
            f"📊 *CEO Briefing — Week of {date_str}*\n\n"
            f"📧 Emails processed: {counts.get('Email', 0)}\n"
            f"💬 WhatsApp replies: {counts.get('WhatsApp', 0)}\n"
            f"💼 LinkedIn posts: {counts.get('LinkedIn', 0)}\n"
            f"🧾 Odoo invoices: {counts.get('Odoo', 0)}\n"
            f"✅ Total completed: {counts.get('Total', 0)}\n"
            f"💰 API cost: ${api_cost:.4f}\n\n"
            f"Full report: vault/Briefings/latest"
        )
        _send_in_thread(msg, "ceo_briefing")
        print("[ceo_briefing] WhatsApp notification sent")
    except Exception as e:
        print(f"[ceo_briefing] WhatsApp notification failed (non-fatal): {e}")


# ─── Dashboard.md update ───────────────────────────────────────────────────────

def update_dashboard(vault_path: str, counts: Dict[str, int], api_cost: float,
                     briefing_file: str, week_start: datetime) -> None:
    """Overwrite the ## 📊 CEO Briefing Stats section in vault/Dashboard.md."""
    dashboard_path = Path(vault_path) / "Dashboard.md"
    if not dashboard_path.exists():
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    stats_block = (
        f"\n## 📊 CEO Briefing — {week_start.strftime('%b %d')} week\n\n"
        f"| Category | Completed |\n"
        f"|----------|----------|\n"
        f"| 📧 Email | {counts.get('Email', 0)} |\n"
        f"| 💬 WhatsApp | {counts.get('WhatsApp', 0)} |\n"
        f"| 💼 LinkedIn | {counts.get('LinkedIn', 0)} |\n"
        f"| 🧾 Odoo | {counts.get('Odoo', 0)} |\n"
        f"| **Total** | **{counts.get('Total', 0)}** |\n\n"
        f"💰 **API Cost (week):** ${api_cost:.4f}  \n"
        f"📄 **Report:** `{Path(briefing_file).name}`  \n"
        f"🕐 **Generated:** {now}\n"
    )

    content = dashboard_path.read_text(encoding="utf-8")
    marker = "## 📊 CEO Briefing"
    if marker in content:
        # Replace existing block
        idx = content.index(marker)
        # Find next ## after the block
        next_h2 = content.find("\n## ", idx + 1)
        if next_h2 != -1:
            content = content[:idx] + stats_block.strip() + "\n\n" + content[next_h2:]
        else:
            content = content[:idx] + stats_block.strip() + "\n"
    else:
        content += stats_block

    dashboard_path.write_text(content, encoding="utf-8")
    print(f"[ceo_briefing] Dashboard.md updated")


# ─── Main generator ────────────────────────────────────────────────────────────

def generate_briefing(vault_path: str, send_wa: bool = True) -> str:
    """
    Generate complete CEO Briefing, update Dashboard.md, send WhatsApp.

    Returns:
        Path to generated briefing file
    """
    vault = Path(vault_path)
    briefings_dir = vault / "Briefings"
    briefings_dir.mkdir(parents=True, exist_ok=True)

    dates = calculate_week_dates()
    week_start = dates["week_start"]
    week_end = dates["week_end"]
    briefing_date = dates["briefing_date"]

    counts = count_done_by_category(vault_path, week_start, week_end)
    pending_count = count_pending_approvals(vault_path)
    api_cost = calculate_api_cost_week(vault_path, week_start, week_end)
    suggestions = get_suggestions(vault_path)
    completed_items = get_completed_items_list(vault_path, week_start, week_end)

    on_track = "✓ on track" if api_cost < 0.70 else "⚠️ above target"
    briefing_filename = f"{briefing_date.strftime('%Y-%m-%d')}_Monday_Briefing.md"
    briefing_file = briefings_dir / briefing_filename

    content = f"""---
briefing_date: {briefing_date.strftime('%Y-%m-%d')}
week_start: {week_start.strftime('%Y-%m-%d')}
week_end: {week_end.strftime('%Y-%m-%d')}
email_completed: {counts.get('Email', 0)}
whatsapp_completed: {counts.get('WhatsApp', 0)}
linkedin_completed: {counts.get('LinkedIn', 0)}
odoo_completed: {counts.get('Odoo', 0)}
total_completed: {counts.get('Total', 0)}
pending_approvals: {pending_count}
api_cost_week: {api_cost}
generated_at: {datetime.now().isoformat()}
---

# CEO Briefing: Week of {week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')}

## Executive Summary

| Metric | Value |
|--------|-------|
| 📧 Emails processed | {counts.get('Email', 0)} |
| 💬 WhatsApp replies | {counts.get('WhatsApp', 0)} |
| 💼 LinkedIn posts | {counts.get('LinkedIn', 0)} |
| 🧾 Odoo invoices | {counts.get('Odoo', 0)} |
| ✅ **Total completed** | **{counts.get('Total', 0)}** |
| ⏳ Pending approvals | {pending_count} |
| 💰 API cost (week) | ${api_cost:.4f} ({on_track}) |

---

## Completed This Week

{chr(10).join(completed_items) if completed_items else "- No tasks completed this week"}

---

## Pending Items

**{pending_count}** item(s) awaiting approval in `vault/Pending_Approval/`.

---

## Proactive Suggestions

{chr(10).join(f"{i}. {s}" for i, s in enumerate(suggestions, 1))}

---

## Next Week Focus

1. **Clear Pending Approvals** — review `vault/Pending_Approval/`
2. **Monitor API costs** — {"maintain current usage" if api_cost < 0.70 else "reduce API calls to stay under $0.10/day target"}
3. **Continue task flow** — {counts.get('Total', 0)} completions/week pace

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Personal AI Employee (Gold Tier)*
*Next briefing: {(briefing_date + timedelta(days=7)).strftime('%Y-%m-%d')}*
"""

    briefing_file.write_text(content, encoding="utf-8")
    print(f"[ceo_briefing] Briefing saved: {briefing_file}")

    # Update Dashboard.md
    update_dashboard(vault_path, counts, api_cost, str(briefing_file), week_start)

    # WhatsApp notification
    if send_wa:
        send_whatsapp_briefing(counts, api_cost, week_start.strftime("%b %d"))

    return str(briefing_file)


def schedule_weekly_briefing(vault_path: str) -> None:
    """Run in loop and trigger every Sunday at 23:00."""
    import schedule
    import time

    def job():
        print("[ceo_briefing] Sunday 23:00 — generating briefing…")
        try:
            generate_briefing(vault_path, send_wa=True)
        except Exception as e:
            print(f"[ceo_briefing] Error: {e}")

    schedule.every().sunday.at("23:00").do(job)
    print("[ceo_briefing] Scheduler running (Sunday 23:00)")

    while True:
        schedule.run_pending()
        time.sleep(60)


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEO Briefing Generator")
    parser.add_argument("--vault", default="vault", help="Path to vault directory")
    parser.add_argument("--force", action="store_true", help="Generate immediately")
    parser.add_argument("--no-wa", action="store_true", help="Skip WhatsApp notification")
    parser.add_argument("--schedule", action="store_true", help="Run scheduled loop (Sunday 23:00)")
    args = parser.parse_args()

    vault_path = os.path.abspath(args.vault)
    if not Path(vault_path).exists():
        print(f"[ceo_briefing] Vault not found: {vault_path}")
        sys.exit(1)

    if args.force:
        path = generate_briefing(vault_path, send_wa=not args.no_wa)
        print(f"[ceo_briefing] Done → {path}")
    elif args.schedule:
        schedule_weekly_briefing(vault_path)
    else:
        print("Use --force to generate now, or --schedule for Sunday 23:00 loop")
        print("Example: python scripts/ceo_briefing.py --vault vault --force")
