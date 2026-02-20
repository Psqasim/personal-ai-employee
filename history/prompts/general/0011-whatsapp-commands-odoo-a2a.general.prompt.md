---
id: "0011"
title: WhatsApp Commands + More Odoo + A2A Implementation
stage: green
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: whatsapp-commands-odoo-a2a
branch: main
user: Muhammad Qasim
command: implement plan
labels: ["whatsapp", "odoo", "a2a", "command-router", "cli", "natural-language", "orchestration"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - cloud_agent/src/command_router.py (NEW)
  - scripts/natural_command.py (NEW)
  - scripts/whatsapp_watcher.py (MODIFIED - admin command wiring)
  - local_agent/src/orchestrator.py (MODIFIED - monitor_needs_action A2A implementation)
  - local_agent/src/executors/odoo_poster.py (MODIFIED - create_contact, register_payment, create_purchase_bill)
  - local_agent/src/approval_handler.py (MODIFIED - new Odoo action routing)
  - agent_skills/vault_parser.py (MODIFIED - OdooContact, OdooPayment, OdooBill dataclasses)
tests:
  - venv/bin/python3 scripts/natural_command.py "send invoice to Ali for 5000 Rs web design" → PASS
  - venv/bin/python3 scripts/natural_command.py "send email to john@gmail.com about tomorrow meeting" → PASS
  - venv/bin/python3 scripts/natural_command.py "post linkedin: We just shipped AI invoicing!" → PASS
  - venv/bin/python3 scripts/natural_command.py "add contact John Smith john@company.com +923001234567" → PASS
  - venv/bin/python3 scripts/natural_command.py "create purchase bill from Ali Traders 25000 Rs office supplies" → PASS
  - venv/bin/python3 scripts/natural_command.py "register payment for invoice INV/2026/00003" → PASS
  - venv/bin/python3 scripts/natural_command.py "!invoice Ahmad 200 USD consulting" → PASS
  - OdooPoster.create_contact / register_payment / create_purchase_bill methods confirmed present → PASS
  - monitor_needs_action all 6 action branches confirmed → PASS
  - OdooContact / OdooPayment / OdooBill dataclasses and detect_draft_type → PASS
---

## Prompt

Implement the following plan:

# Plan: WhatsApp Commands + More Odoo + A2A

User wants:
1. WhatsApp → send commands to Claude ("Send invoice to Ali 5000 Rs") → AI creates draft → approval → executes
2. Claude CLI natural language interface (same as above but from terminal)
3. More Odoo features: customer contacts, register payment, purchase bills
4. A2A (Agent-to-Agent) explanation and basic implementation

All 4 are connected: WhatsApp commands → vault draft → approval → executor
The vault workflow already handles execution — we just need the FRONT END (command ingestion + intent parsing).

Files to Create/Modify:
1. cloud_agent/src/command_router.py — core intent parser
2. scripts/natural_command.py — CLI wrapper
3. scripts/whatsapp_watcher.py — wire admin commands
4. local_agent/src/orchestrator.py — fill monitor_needs_action()
5. local_agent/src/executors/odoo_poster.py — add 3 new methods
6. agent_skills/vault_parser.py — new dataclasses

After all work: test all, make PHR, update README.md, push and merge.

## Response snapshot

Implemented all 6 files in order. Key decisions:

**command_router.py**: Uses `CLAUDE_API_KEY` (falling back to `ANTHROPIC_API_KEY`), few-shot Claude prompt with 11 examples covering all action types, returns structured dict. `is_admin_command()` checks sender name match against `WHATSAPP_ADMIN_NAME` env var OR `!`/`/` prefix. `create_vault_draft()` writes correct frontmatter for each action type to vault/Pending_Approval/<Type>/. `route_command()` combines parse + create in one call.

**natural_command.py**: Simple CLI wrapper using venv python, loads .env, shows parsed intent + draft path + next steps. Handles all 8 action types with human-readable labels.

**whatsapp_watcher.py**: Added `handle_admin_command()` and `VAULT_PATH` const. In Phase 2 of `run_cycle()`, calls `handle_admin_command()` before `generate_reply()` — if it returns a string, that's the reply (confirmation of draft creation). Non-admin messages flow unchanged.

**orchestrator.py**: Implemented `monitor_needs_action()` with atomic claim-by-move, frontmatter parsing, routing to `_execute_needs_action_task()`. Added `_execute_needs_action_task()` with branches for: invoice/expense → OdooPoster.post_from_file(); contact → OdooPoster.create_contact(); payment → OdooPoster.register_payment(); bill → OdooPoster.create_purchase_bill(); email/whatsapp/linkedin → process_approval(). This completes the A2A loop.

**odoo_poster.py**: Added `create_contact()` (res.partner.create), `register_payment()` (account.payment.create + action_post + reconcile attempt), `create_purchase_bill()` (account.move with move_type=in_invoice). All use same XML-RPC pattern. Added `_notify_whatsapp()` helper.

**vault_parser.py**: Added `OdooContact`, `OdooPayment`, `OdooBill` dataclasses. Updated `parse_draft_file()` with 3 new branches. Updated `detect_draft_type()` with contact/payment/bill patterns.

**Bug fixed during testing**: env var `CLAUDE_API_KEY` vs `ANTHROPIC_API_KEY` — fixed command_router to check both.

All 7 CLI tests passed. All import checks passed.

## Outcome

- ✅ Impact: Full natural language command pipeline operational — WhatsApp or terminal → Claude parses intent → vault draft → approval → Odoo/Email/LinkedIn execution. A2A orchestration loop complete (cloud writes Needs_Action, local claims and executes). 3 new Odoo operations: contacts, payments, bills.
- 🧪 Tests: 7/7 CLI tests PASS (invoice, email, LinkedIn, contact, bill, payment, prefix command). All imports verified.
- 📁 Files: 2 new, 5 modified. No unrelated edits.
- 🔁 Next prompts: Test WhatsApp end-to-end with real phone → "!invoice Ali 5000"; test Odoo create_contact/register_payment against live Odoo instance; add WhatsApp send_message command draft support.
- 🧠 Reflection: The env var mismatch (CLAUDE_API_KEY vs ANTHROPIC_API_KEY) is a recurring pattern — should standardize to one name. Few-shot prompting with 11 examples produced accurate intent extraction including PKR default, k-suffix handling, and action routing.

## Evaluation notes (flywheel)

- Failure modes observed: (1) API key env var name mismatch — fixed with fallback chain; (2) `python` command not found in WSL2 (use `python3` or venv path)
- Graders run and results (PASS/FAIL): CLI test suite 7/7 PASS; import validation PASS
- Prompt variant (if applicable): few-shot with 11 examples for intent extraction
- Next experiment: test with ambiguous commands like "send 5000 to Ali" to check fallback behavior
