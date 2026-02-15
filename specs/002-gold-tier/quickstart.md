# Gold Tier Quickstart Guide

**Feature**: 002-gold-tier | **Date**: 2026-02-13

## Overview

This guide walks you through upgrading from Silver tier to Gold tier, which adds:
- Email draft generation & auto-send (with approval)
- WhatsApp draft generation & auto-send (with approval)
- LinkedIn post generation & auto-publish (with approval)
- Multi-step plan execution (Ralph Wiggum loop)
- Weekly CEO Briefing generation

**Prerequisites**:
- Silver tier fully deployed and functional
- Python 3.11+
- Playwright installed
- SMTP credentials (Gmail app password or custom SMTP server)
- WhatsApp phone number for QR authentication
- LinkedIn developer account with OAuth2 token (optional but recommended)

---

## Installation Steps

### 1. Upgrade to Gold Tier Branch

```bash
cd /path/to/personal-ai-employee
git fetch --all
git checkout 002-gold-tier
```

### 2. Install Gold Tier Dependencies

```bash
# Install Python dependencies
pip install -r requirements-gold.txt

# Install Playwright browsers (for WhatsApp automation)
playwright install chromium

# Verify installations
python -c "import playwright; print('Playwright OK')"
python -c "import anthropic; print('Claude API OK')"
```

**requirements-gold.txt** (incremental, includes Silver):
```
# Inherits from Silver: anthropic>=0.18.0, playwright>=1.40.0, watchdog>=3.0.0, pyyaml>=6.0, google-api-python-client>=2.80.0, aiohttp>=3.9.0

# Gold additions
schedule>=1.2.0          # CEO Briefing weekly cron
filelock>=3.12.0         # Vault write conflict resolution
requests>=2.31.0         # LinkedIn API
```

### 3. Configure Environment Variables

Add Gold tier variables to your existing `.env` file:

```.env
# ====== EXISTING SILVER TIER CONFIG ======
VAULT_PATH=/path/to/vault
ENABLE_AI_ANALYSIS=true
CLAUDE_API_KEY=sk-ant-api03-xxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
GMAIL_CREDENTIALS_PATH=/path/to/gmail_credentials.json
# ... (other Silver vars)

# ====== GOLD TIER ADDITIONS ======
ENABLE_PLAN_EXECUTION=true
TIER=gold

# Email MCP (required for email draft-and-send)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password    # See "Get Gmail App Password" below

# WhatsApp MCP (required for WhatsApp draft-and-send)
WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session
WHATSAPP_POLL_INTERVAL=30                # Seconds between polls
WHATSAPP_KEYWORDS=urgent,meeting,payment,deadline,invoice,asap,help,client,contract

# LinkedIn MCP (required for LinkedIn auto-post)
LINKEDIN_ACCESS_TOKEN=your-linkedin-oauth2-token
LINKEDIN_AUTHOR_URN=urn:li:person:your-linkedin-id

# Optional: Odoo integration (skip if not using Odoo)
ENABLE_ODOO=false
ODOO_URL=http://localhost:8069
ODOO_DB=your-odoo-db
ODOO_USER=admin
ODOO_PASSWORD=your-odoo-password
```

### 4. Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (required for app passwords)
3. Go to **App Passwords** section
4. Select app: **Mail**, device: **Other (Custom name)**, name it "Personal AI Employee"
5. Google generates a 16-character password (e.g., `abcd efgh ijkl mnop`)
6. Copy to `.env` as `SMTP_PASSWORD=abcdefghijklmnop` (remove spaces)

### 5. Get LinkedIn OAuth2 Token

1. Go to https://www.linkedin.com/developers/apps
2. Create app → Select **Sign In with LinkedIn**
3. Request scopes: `w_member_social` (post creation)
4. Complete OAuth2 flow (redirect URL: `http://localhost:8000/callback`)
5. Exchange authorization code for access token
6. Copy access token to `.env` as `LINKEDIN_ACCESS_TOKEN=...`
7. Get your LinkedIn person URN:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.linkedin.com/v2/me | jq .id
   # Response: "abc123xyz" → use as LINKEDIN_AUTHOR_URN=urn:li:person:abc123xyz
   ```

**LinkedIn Token Lifespan**: 60 days → you'll need to refresh periodically

### 6. Authenticate WhatsApp (QR Code)

**First-time setup** (run once):

```bash
python scripts/whatsapp_qr_setup.py
```

**Expected output**:
```
[Playwright] Launching Chromium browser...
[WhatsApp] Opening https://web.whatsapp.com...
[WhatsApp] QR Code detected. Scan with your phone:

  [QR CODE DISPLAYED IN TERMINAL]

Waiting for authentication...
[WhatsApp] Authenticated successfully!
[WhatsApp] Session saved to /home/user/.whatsapp_session
```

**Scan QR code** with WhatsApp mobile app (Settings → Linked Devices → Link a Device).

**Session Persistence**: Once authenticated, session persists across restarts. No need to re-scan unless session expires (weeks/months).

### 7. Configure MCP Servers (T013, T020, T029)

Create/update `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/email_mcp/server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-gmail-app-password"
      }
    },
    "whatsapp-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/whatsapp_mcp/server.py"],
      "env": {
        "WHATSAPP_SESSION_PATH": "/home/user/.whatsapp_session"
      }
    },
    "linkedin-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/linkedin_mcp/server.py"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "your-oauth2-token",
        "LINKEDIN_AUTHOR_URN": "urn:li:person:xxxxx"
      }
    },
    "facebook-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/facebook_mcp/server.py"],
      "env": {
        "FACEBOOK_ACCESS_TOKEN": "your-facebook-page-access-token",
        "FACEBOOK_PAGE_ID": "your-facebook-page-id"
      }
    },
    "instagram-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/instagram_mcp/server.py"],
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "your-instagram-long-lived-token",
        "INSTAGRAM_USER_ID": "your-instagram-user-id"
      }
    },
    "twitter-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/twitter_mcp/server.py"],
      "env": {
        "TWITTER_BEARER_TOKEN": "your-twitter-bearer-token"
      }
    },
    "odoo-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/personal-ai-employee/mcp_servers/odoo_mcp/server.py"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.odoo.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USER": "admin@example.com",
        "ODOO_PASSWORD": "your-odoo-password"
      }
    }
  }
}
```

**Replace**:
- `/absolute/path/to/personal-ai-employee` with your actual repo path
- `your-email@gmail.com` with your Gmail address
- `your-gmail-app-password` with app password from docs/gold/email-setup.md
- `/home/user/.whatsapp_session` with your session path from .env
- `your-oauth2-token` with LinkedIn access token from docs/gold/linkedin-setup.md
- `urn:li:person:xxxxx` with your LinkedIn person URN

**Note**: These are also configured in .env - MCP servers will read from environment variables.

### 8. Initialize Vault Folders (Gold Extensions)

```bash
cd vault

# Create Gold tier folders
mkdir -p Pending_Approval/{Email,WhatsApp,LinkedIn,Plans,Odoo}
mkdir -p Approved/{Email,WhatsApp,LinkedIn,Plans,Odoo}
mkdir -p Rejected
mkdir -p In_Progress
mkdir -p Briefings
mkdir -p Logs/{MCP_Actions,Human_Approvals,Plan_Execution}

# Verify structure
tree -L 2 .
```

**Expected structure**:
```
vault/
├── Dashboard.md (existing, Bronze)
├── Company_Handbook.md (existing, Bronze)
├── Inbox/ (existing, Bronze)
├── Pending_Approval/ (NEW, Gold)
│   ├── Email/
│   ├── WhatsApp/
│   ├── LinkedIn/
│   ├── Plans/
│   └── Odoo/
├── Approved/ (NEW, Gold)
│   ├── Email/
│   ├── WhatsApp/
│   ├── LinkedIn/
│   ├── Plans/
│   └── Odoo/
├── Rejected/ (NEW, Gold)
├── In_Progress/ (NEW, Gold)
├── Briefings/ (NEW, Gold)
├── Plans/ (existing, Silver)
├── Done/ (existing, Bronze)
├── Needs_Action/ (existing, Bronze)
└── Logs/ (existing, Bronze, extended for Gold)
    ├── MCP_Actions/ (NEW)
    ├── Human_Approvals/ (NEW)
    └── Plan_Execution/ (NEW)
```

### 9. Start Gold Tier Watchers

```bash
# Option 1: Manual start (for testing)
python scripts/gmail_watcher.py &         # Extends Silver, adds draft generation
python scripts/whatsapp_watcher.py &      # Extends Silver, adds draft generation
python scripts/linkedin_generator.py &    # Extends Silver, adds LinkedIn MCP
python scripts/approval_watcher.py &      # NEW: monitors vault/Approved/ for MCP invocations
python scripts/plan_watcher.py &          # NEW: monitors vault/Approved/Plans/ for Ralph Wiggum loop
python scripts/ceo_briefing.py &          # NEW: weekly Sunday 23:00 briefing

# Option 2: Supervised start (recommended for production)
./scripts/gold_watcher.sh start           # Starts all watchers via PM2/supervisord

# Verify watchers running
ps aux | grep python | grep watcher
# OR
pm2 list                                  # If using PM2
```

### 10. Verify Gold Tier Setup

Open `vault/Dashboard.md` in Obsidian. Check for **Gold Tier Status** section:

```markdown
## Gold Tier Status

**Plan Execution**: Enabled ✓
**API Cost Today**: $0.02
**Active Plans**: 0

**MCP Servers**:
- email-mcp: ✓ Active
- whatsapp-mcp: ✓ Active (session valid)
- linkedin-mcp: ✓ Active

**Pending Approvals**:
- Email: 0
- WhatsApp: 0
- LinkedIn: 0
- Plans: 0
```

If status shows `✗ Inactive` for any MCP server → check `mcp.json` configuration and `.env` credentials.

---

## Testing Gold Tier

### Test 1: Email Draft-and-Send

1. **Trigger email draft**:
   ```bash
   # Create a high-priority email task in vault/Inbox/
   cat > vault/Inbox/EMAIL_test_001.md <<EOF
   ---
   type: email
   from: testclient@example.com
   subject: "Test email for draft generation"
   priority: High
   status: new
   ---

   # Test Email

   Can you send me the project proposal by end of week?
   EOF
   ```

2. **Wait 15 seconds** → Gold watcher processes and generates draft

3. **Check `vault/Pending_Approval/Email/`** → should see `EMAIL_DRAFT_test_001.md` with AI-generated reply

4. **Approve draft**: In Obsidian, drag file from `Pending_Approval/Email/` to `Approved/Email/`

5. **Wait 30 seconds** → Email MCP sends email, logs to `vault/Logs/MCP_Actions/`

6. **Verify**: Check your sent folder in Gmail for sent email

### Test 2: WhatsApp Draft-and-Send

1. **Send WhatsApp message** to yourself containing keyword "urgent payment reminder"

2. **Wait 30 seconds** → WhatsApp watcher detects message, creates task in `vault/Inbox/WHATSAPP_*.md`, generates draft

3. **Check `vault/Pending_Approval/WhatsApp/`** → should see draft reply

4. **Approve**: Drag to `vault/Approved/WhatsApp/`

5. **Wait 30 seconds** → WhatsApp MCP sends reply via Playwright

6. **Verify**: Check WhatsApp Web for sent message

### Test 3: LinkedIn Post-and-Publish

1. **Trigger LinkedIn post generation**:
   ```bash
   # Manually run LinkedIn generator (bypasses weekly schedule)
   python scripts/linkedin_generator.py --force
   ```

2. **Check `vault/Pending_Approval/LinkedIn/`** → should see `LINKEDIN_POST_YYYY-MM-DD.md` with AI-generated post

3. **Approve**: Drag to `vault/Approved/LinkedIn/`

4. **Wait 30 seconds** → LinkedIn MCP posts to LinkedIn

5. **Verify**: Check your LinkedIn profile for new post

### Test 4: Multi-Step Plan Execution

1. **Create a multi-step plan**:
   ```bash
   cat > vault/Inbox/onboard_client.md <<EOF
   ---
   type: task
   priority: High
   ---

   # Onboard New Client

   Plan the onboarding: send intro email, schedule kick-off meeting, post LinkedIn announcement
   EOF
   ```

2. **Wait** → Plan generator creates `vault/Plans/PLAN_onboarding_*.md` and approval request in `vault/Pending_Approval/Plans/`

3. **Review plan** in Obsidian → check steps are correct

4. **Approve**: Drag approval file to `vault/Approved/Plans/`

5. **Wait** → Ralph Wiggum loop executes steps (email sent, calendar invite created, LinkedIn post published)

6. **Monitor**: Check `vault/In_Progress/PLAN_onboarding_*/state.md` for execution state

7. **Verify**: All steps marked `[x]` in Plan.md, plan moved to `vault/Done/`

---

## Troubleshooting

### WhatsApp Session Expired

**Symptom**: `vault/Needs_Action/whatsapp_session_expired.md` appears

**Solution**:
```bash
python scripts/whatsapp_qr_setup.py  # Re-authenticate with QR code
```

### LinkedIn Rate Limited

**Symptom**: LinkedIn draft status shows `rate_limited_retry`

**Solution**: Wait 60 minutes (LinkedIn API limit). System auto-retries after backoff.

### Email MCP Authentication Failed

**Symptom**: `vault/Logs/MCP_Actions/` shows `SMTP_AUTH_FAILED`

**Solution**:
- Verify Gmail app password in `.env` (16 chars, no spaces)
- Check 2-Step Verification enabled on Google account
- Try regenerating app password

### Ralph Wiggum Loop Escalated

**Symptom**: `vault/Needs_Action/plan_escalated_{id}.md` appears, plan status="escalated"

**Cause**: Plan exceeded 10 iterations without completing

**Solution**:
- Review `vault/In_Progress/{plan_id}/state.md` → check which step is looping
- Manually complete blocked step or simplify plan
- Restart plan execution

### MCP Server Not Active

**Symptom**: Dashboard shows `email-mcp: ✗ Inactive`

**Solution**:
```bash
# Test MCP server directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_servers/email_mcp/server.py

# If error → check .env credentials
# If works → check mcp.json absolute paths
```

---

## Next Steps

1. **Monitor Dashboard**: Check `vault/Dashboard.md` daily for pending approvals
2. **Review CEO Briefing**: Every Monday morning, check `vault/Briefings/` for weekly summary
3. **Tune AI Prompts**: Edit `agent_skills/draft_generator.py` to customize email/WhatsApp/LinkedIn tone
4. **Add Custom Keywords**: Update `WHATSAPP_KEYWORDS` in `.env` for domain-specific urgency detection
5. **Scale Up**: As you approve more drafts, API costs may increase → monitor `vault/Logs/API_Usage/`

---

## Documentation

- **WhatsApp Setup**: `docs/gold/whatsapp-setup.md`
- **MCP Configuration**: `docs/gold/mcp-setup.md`
- **CEO Briefing Customization**: `docs/gold/ceo-briefing-config.md`
- **Troubleshooting**: `docs/gold/troubleshooting.md` (create as issues arise)

---

## Maintenance

**Weekly**:
- Review CEO Briefing (Monday)
- Check `vault/Needs_Action/` for escalations
- Prune old logs (auto-pruned after 90 days)

**Monthly**:
- Refresh LinkedIn OAuth2 token (60-day expiry)
- Review API costs (`vault/Logs/API_Usage/`)
- Update Playwright (WhatsApp UI may change): `playwright install chromium`

**As Needed**:
- Re-authenticate WhatsApp (if session expires)
- Regenerate Gmail app password (if changed Google password)

---

**Congratulations!** You've successfully upgraded to Gold tier. Your AI employee now autonomously drafts emails, WhatsApp messages, and LinkedIn posts — all with human approval before sending.
