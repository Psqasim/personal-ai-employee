# Odoo Integration Guide

**Personal AI Employee — Platinum Tier**

Automatically detects invoice/billing emails, extracts accounting data with Claude, creates draft invoice files for human approval, and posts approved drafts to Odoo as **draft invoices** (never auto-confirmed).

---

## Architecture

```
Gmail Inbox  →  Cloud Agent  →  vault/Pending_Approval/Odoo/INVOICE_DRAFT_*.md
                                          ↓ (human approves via dashboard)
                             vault/Approved/Odoo/
                                          ↓ (Local Agent polls)
                             Odoo XML-RPC → draft account.move (state=draft)
                                          ↓
                             vault/Done/Odoo/  +  WhatsApp confirmation
```

---

## Setup

### 1. Environment Variables

Add to your `.env` file:

```bash
# Required
ENABLE_ODOO=true
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USER=admin@example.com
ODOO_API_KEY=your_api_key_here          # preferred (Odoo 14+)

# Optional fallback
# ODOO_PASSWORD=your_password           # only if no API key
```

Also add to `nextjs_dashboard/.env.local` (for dashboard health check):

```bash
ODOO_URL=https://your-odoo-instance.com
```

### 2. Get Your Odoo API Key

1. Log in to Odoo → **Settings** → **Users & Companies** → **Users**
2. Open your user → **Account Security** tab
3. Click **New API Key** → copy the key
4. Paste into `.env` as `ODOO_API_KEY=...`

### 3. Verify Connection

```bash
python tests/manual/odoo_connection_test.py
```

Expected output: `✅ Authentication successful! User ID: 2`

---

## How It Works

### Phase 1 — Invoice Detection (Cloud Agent)

`cloud_agent/src/generators/odoo_draft.py`

The cloud orchestrator calls `OdooDraftGenerator.generate_and_save()` for every email in the inbox. Detection uses keyword matching:

```
invoice, bill, billing, payment, charge, receipt,
quote, quotation, estimate, fee, due, amount due,
please pay, attached invoice, proforma
```

If keywords match **and** `ENABLE_ODOO=true`, Claude extracts structured data:

```json
{
  "customer": "Acme Corp",
  "amount": 3500.00,
  "currency": "USD",
  "description": "Consulting services Q1 2026",
  "action": "create_draft_invoice"
}
```

A fallback regex extractor runs when Claude is unavailable.

**Output file:** `vault/Pending_Approval/Odoo/INVOICE_DRAFT_ODOO_<email_id>.md`

### Phase 2 — Human Approval (Dashboard)

Open the dashboard → **Pending Approvals** tab. Odoo drafts appear with a purple `Odoo` badge.

- **Approve** → file moves to `vault/Approved/Odoo/`
- **Reject** → file moves to `vault/Rejected/Odoo/`

You can also create manual invoice drafts: **New Task** → **Invoice (🧾)** tab.

### Phase 3 — Post to Odoo (Local Agent)

`local_agent/src/executors/odoo_poster.py`

The local agent's `ApprovalHandler` picks up files from `vault/Approved/Odoo/` and calls `OdooPoster.post_from_file()`, which:

1. Parses the YAML frontmatter
2. Authenticates with Odoo XML-RPC using `ODOO_API_KEY`
3. Finds or creates the customer in `res.partner`
4. Creates a **draft** `account.move` (invoice always stays `state=draft`)
5. Reads back the generated invoice number (e.g. `INV/2026/0001`)
6. Moves the file to `vault/Done/Odoo/`
7. Sends a WhatsApp confirmation

---

## Draft File Format

`vault/Pending_Approval/Odoo/INVOICE_DRAFT_ODOO_EMAIL_123.md`:

```yaml
---
type: odoo_invoice
draft_id: ODOO_EMAIL_123
action: create_draft_invoice
status: pending
customer: Acme Corp
amount: 3500.00
currency: USD
description: Consulting services Q1 2026
source_email_id: EMAIL_123
source_email_from: billing@acmecorp.com
created: 2026-02-19T10:00:00
mcp_server: odoo-mcp
---
```

---

## Testing

### Unit Tests (no Odoo needed)

```bash
# Test keyword detection, fallback extraction, draft creation
pytest tests/unit/test_odoo_draft_generator.py -v

# Test poster: guard, success flow, failure handling
pytest tests/unit/test_odoo_poster.py -v
```

### Integration Test (mocked XML-RPC)

```bash
pytest tests/integration/test_odoo_flow.py -v
```

### Manual Tests (real Odoo)

```bash
# Step 1: verify connection + auth
python tests/manual/odoo_connection_test.py

# Step 2: create customer + draft invoice
python tests/manual/odoo_create_invoice_test.py
```

### End-to-End Test via Dashboard

1. Drop a test email file into `vault/Inbox/`:
   ```bash
   cat > vault/Inbox/EMAIL_TEST_ODOO.md << 'EOF'
   ---
   email_id: EMAIL_TEST_ODOO
   from: test@example.com
   subject: Invoice #9999 for consulting
   body: Please pay USD 500 for consulting services.
   priority: Normal
   status: new
   ---
   Please pay USD 500 for consulting services.
   EOF
   ```
2. Wait for cloud agent cycle (or restart it) — check `vault/Pending_Approval/Odoo/`
3. Open dashboard → approve the draft
4. Local agent picks up → check `vault/Done/Odoo/` and Odoo web UI

---

## MCP Server

`mcp_servers/odoo_mcp/server.py` provides JSON-RPC tools:

| Tool | Description |
|------|-------------|
| `create_draft_invoice` | Create customer invoice (state=draft) |
| `create_draft_expense` | Create vendor bill (state=draft) |
| `list_invoices` | List recent invoices |
| `create_contact` | Find or create res.partner |

The local executor calls Odoo XML-RPC **directly** (not via the MCP subprocess) for reliability.

---

## Safety

- Invoices are **always** created as `state: "draft"` — never auto-confirmed
- `ENABLE_ODOO=false` (default) disables all Odoo activity
- Approval is required before any Odoo API call
- Failed drafts land in `vault/Failed/Odoo/` with error appended

---

## Vault Directory Layout

```
vault/
├── Pending_Approval/Odoo/   ← auto-generated drafts awaiting approval
├── Approved/Odoo/           ← human-approved, waiting for local agent
├── Done/Odoo/               ← successfully posted to Odoo
├── Failed/Odoo/             ← failed with error note appended
└── Logs/Odoo/               ← daily log files (odoo-YYYY-MM-DD.md)
```
