#!/usr/bin/env python3
"""
Natural Command CLI - Send commands to Personal AI Employee from terminal

Usage:
  python scripts/natural_command.py "send invoice to Ali for 5000 Rs web design"
  python scripts/natural_command.py "send email to john@gmail.com about meeting"
  python scripts/natural_command.py "post linkedin: We just shipped AI invoicing!"
  python scripts/natural_command.py "!invoice Ahmad 15000"

The command is parsed by Claude and a vault draft is created in
vault/Pending_Approval/<Type>/ — same as if received via WhatsApp.
Approve it from the dashboard or by moving the file to vault/Approved/.

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-20
"""

import os
import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.cloud", override=True)

logging.basicConfig(
    level=logging.WARNING,  # suppress internal logs; only show our output
    format="%(asctime)s %(levelname)s %(message)s"
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/natural_command.py \"<your command>\"")
        print()
        print("Examples:")
        print('  python scripts/natural_command.py "send invoice to Ali for 5000 Rs web design"')
        print('  python scripts/natural_command.py "send email to john@gmail.com about tomorrow meeting"')
        print('  python scripts/natural_command.py "post linkedin: We just shipped AI invoicing!"')
        print('  python scripts/natural_command.py "add contact John Smith john@co.com +923001234567"')
        print('  python scripts/natural_command.py "register payment for invoice INV/2026/00003"')
        print('  python scripts/natural_command.py "create purchase bill from Ali Traders 25000 Rs office supplies"')
        sys.exit(1)

    message = " ".join(sys.argv[1:])

    print(f"\n🤖 Parsing command: \"{message}\"")
    print("   Calling Claude API...")

    from cloud_agent.src.command_router import parse_command_with_claude, create_vault_draft

    # Step 1: Parse intent
    intent = parse_command_with_claude(message)
    action = intent.get("action", "unknown")

    if action == "unknown":
        print(f"\n❌ Could not parse command.")
        print(f"   Raw response: {intent}")
        print("\n💡 Try being more specific, e.g.:")
        print('   "Create invoice for Ali 5000 Rs web design"')
        sys.exit(1)

    print(f"\n✅ Parsed intent:")
    for k, v in intent.items():
        if k != "raw_command":
            print(f"   {k}: {v}")

    # Step 2: Create vault draft
    try:
        draft_path = create_vault_draft(intent)
        rel_path = Path(draft_path).relative_to(project_root)
    except Exception as e:
        print(f"\n❌ Failed to create vault draft: {e}")
        sys.exit(1)

    print(f"\n📄 Draft created: {rel_path}")
    print(f"\n👉 Next steps:")
    print(f"   1. Open dashboard → Pending Approvals")
    print(f"   2. Review and approve the draft")
    print(f"   3. Local agent will execute it automatically")
    print()

    # Show a preview of the action
    action_labels = {
        "create_draft_invoice": "📋 Odoo Sales Invoice (draft)",
        "create_draft_expense": "💸 Odoo Expense (draft)",
        "create_contact":       "👤 Odoo Contact",
        "register_payment":     "💳 Odoo Payment",
        "create_purchase_bill": "🧾 Odoo Vendor Bill",
        "send_email":           "📧 Email",
        "send_message":         "💬 WhatsApp Message",
        "create_post":          "🔗 LinkedIn Post",
    }
    label = action_labels.get(action, f"📝 {action}")
    print(f"   Action: {label}")

    # Show key fields
    if action in ("create_draft_invoice", "create_draft_expense", "create_purchase_bill"):
        print(f"   Amount: {intent.get('currency', 'PKR')} {intent.get('amount', 0):,}")
        print(f"   Party:  {intent.get('customer', intent.get('vendor', 'N/A'))}")
    elif action == "send_email":
        print(f"   To:      {intent.get('to', 'N/A')}")
        print(f"   Subject: {intent.get('subject', 'N/A')}")
    elif action == "send_message":
        print(f"   To:  {intent.get('chat_id', 'N/A')}")
    elif action == "create_contact":
        print(f"   Name:  {intent.get('customer', intent.get('name', 'N/A'))}")
        print(f"   Email: {intent.get('email', 'N/A')}")
    elif action == "register_payment":
        print(f"   Invoice: {intent.get('invoice_number', 'N/A')}")
    elif action == "create_post":
        content = intent.get("post_content", "")
        print(f"   Preview: {content[:80]}{'...' if len(content) > 80 else ''}")
    print()


if __name__ == "__main__":
    main()
