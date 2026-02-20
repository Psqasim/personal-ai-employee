---
id: "0010"
title: "Odoo bugfixes dashboard email send"
stage: general
date: "2026-02-20"
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: Muhammad Qasim
command: "Fix Odoo integration bugs + dashboard done section + invoice email send"
labels: ["odoo", "bugfix", "dashboard", "email", "xml-rpc"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - local_agent/src/executors/odoo_poster.py
  - mcp_servers/odoo_mcp/server.py
  - local_agent/src/approval_handler.py
  - nextjs_dashboard/app/api/vault/route.ts
  - nextjs_dashboard/app/api/status/route.ts
  - nextjs_dashboard/lib/vault.ts
  - nextjs_dashboard/app/dashboard/page.tsx
  - nextjs_dashboard/components/CreateTaskModal.tsx
  - nextjs_dashboard/app/api/tasks/create/route.ts
  - agent_skills/vault_parser.py
tests: []
---

## Prompt

User reported:
1. Invoice visible in Odoo UI (INV/2026/00002) at `/odoo/accounting/8/invoicing/5`
2. Dashboard not showing new Done items ("old data not updated")
3. Want to input customer Gmail → have Odoo send invoice PDF email automatically

## Response / Work Done

### Bugs fixed

**Bug 1 – Odoo DatatypeMismatch (partner_id ARRAY[12] instead of int)**
- Root cause: `create([[{...}]])` passes list-of-dicts, Odoo 14+ returns `[id]` (list not int)
- Fix in `odoo_poster.py`: change all `create([[...]])` → `create([...])` + `raw[0] if isinstance(raw, list) else raw` extraction + `int()` cast
- Fix in `mcp_servers/odoo_mcp/server.py`: same fix for `create_draft_invoice`, `create_draft_expense`, `_find_or_create_partner`
- Also fixed `invoice.get("name", default)` → `invoice.get("name") or default` (Odoo returns `False` not `None` for unset draft sequence)

**Bug 2 – Stale vault dashboard**
- Added `export const dynamic = "force-dynamic"` to `api/vault/route.ts` and `api/status/route.ts`

**Bug 3 – Odoo approval routing**
- Added direct `OdooPoster` routing in `approval_handler.py` bypassing old MCP subprocess path

**Bug 4 – PM2 cache**
- Restarted PM2 after code changes with `pm2 restart local_approval_handler`

### New features

**Dashboard "Recently Completed" section**
- Added `getRecentDoneItems(10)` to `vault.ts` — reads `vault/Done/` recursively
- Exposed as `recentDone` in `/api/status` response
- Dashboard `page.tsx` shows inline "Recently Completed" list (live, 5s poll)
  - Shows category icon, title, Odoo details (amount/currency/customer), timestamp, "Done" badge

**Odoo invoice email send**
- Added optional `customer_email` field to `CreateTaskModal.tsx` Invoice tab
- Persisted to vault frontmatter in `api/tasks/create/route.ts`
- Added `customer_email: str = ""` to `OdooDraft` dataclass + parser in `vault_parser.py`
- In `odoo_poster.py._create_in_odoo()`: if `draft.customer_email` set:
  1. Updates `res.partner` email in Odoo
  2. Searches for `mail.template` where `model = account.move` and name contains "Invoice"
  3. Calls `mail.template.send_mail(template_id, record_id, force_send=True)`
  4. Non-fatal if email fails — invoice still created

### Verified
- Invoice ID 4 created in Odoo, moved to `vault/Done/Odoo/`
- Invoice INV/2026/00002 confirmed visible in Odoo web UI
- All changes committed and pushed (commits aeb58e4, e780c48)

## Outcome

DONE. Odoo integration fully functional end-to-end. Dashboard now shows live "Recently Completed" items. Customer email field triggers Odoo's own invoice email send.
---
