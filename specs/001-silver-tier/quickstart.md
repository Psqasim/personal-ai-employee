# Quick Start: Silver Tier Setup

**Feature**: 001-silver-tier
**Date**: 2026-02-11
**Estimated Time**: 45-60 minutes (includes Gmail/WhatsApp setup)

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed (`python --version`)
- **Obsidian 1.5+** installed (from https://obsidian.md/)
- **Git** installed (for version control, optional but recommended)
- **Node.js 18+** (for PM2 process manager: `node --version`)
- **Stable internet connection** (for API calls)
- **Gmail account** (for email watcher)
- **Claude API key** (from https://console.anthropic.com/)

**Optional**:
- WhatsApp account (for WhatsApp watcher)
- LinkedIn account (for LinkedIn post generator)

---

## Part 1: Install Dependencies (10 minutes)

### Step 1.1: Clone Repository and Install Python Packages

```bash
# Navigate to project directory
cd /path/to/personal-ai-employee

# Install Python dependencies (includes Silver tier packages)
pip install -r requirements.txt

# Verify anthropic package installed
python -c "import anthropic; print('Claude SDK:', anthropic.__version__)"
```

### Step 1.2: Install Playwright Browsers (for WhatsApp watcher)

```bash
# Install Chromium browser for Playwright
playwright install chromium

# Verify installation
playwright --version
```

### Step 1.3: Install PM2 Process Manager

```bash
# Install PM2 globally via npm
npm install -g pm2

# Verify installation
pm2 --version
```

---

## Part 2: Configure Silver Tier (15 minutes)

### Step 2.1: Create .env File

Create `.env` file in project root with Silver tier configuration:

```bash
# Bronze config (inherited)
VAULT_PATH=/path/to/vault

# Silver additions
ENABLE_AI_ANALYSIS=true
CLAUDE_API_KEY=sk-ant-api03-xxx  # Get from https://console.anthropic.com/
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Gmail watcher config
GMAIL_CREDENTIALS_PATH=/home/user/.config/personal-ai-employee/gmail_credentials.json
GMAIL_POLL_INTERVAL=120  # 2 minutes

# WhatsApp watcher config (optional)
WHATSAPP_SESSION_PATH=/home/user/.config/personal-ai-employee/whatsapp_session
WHATSAPP_KEYWORDS=urgent,invoice,payment,help,asap

# LinkedIn config (optional)
LINKEDIN_POSTING_FREQUENCY=daily
LINKEDIN_BUSINESS_GOALS_SECTION=Business Goals

# Cost control
API_DAILY_COST_LIMIT=0.10
API_RATE_LIMIT_PER_MIN=10
API_CACHE_DURATION=86400  # 24 hours
```

**Important**: Replace `/path/to/vault` with your actual vault path.

### Step 2.2: Get Claude API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create new key (name: "personal-ai-employee-silver")
5. Copy key (starts with `sk-ant-api03-`)
6. Paste into `.env` file: `CLAUDE_API_KEY=sk-ant-api03-xxx`

### Step 2.3: Verify Configuration

```bash
# Verify .env file is valid
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('API Key:', os.getenv('CLAUDE_API_KEY')[:20])"

# Expected output: API Key: sk-ant-api03-xxxxxx
```

---

## Part 3: Gmail Watcher Setup (10 minutes)

### Step 3.1: Create Google Cloud Project and OAuth2 Credentials

1. Go to https://console.cloud.google.com/
2. Create new project: "Personal AI Employee"
3. Enable Gmail API: APIs & Services → Enable APIs → Gmail API → Enable
4. Create OAuth2 credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: Desktop app
   - Name: "Personal AI Employee Gmail Watcher"
   - Download JSON credentials file
5. Save as `~/.config/personal-ai-employee/gmail_credentials.json`

### Step 3.2: Authorize Gmail Access (First Time Only)

```bash
# Create config directory
mkdir -p ~/.config/personal-ai-employee

# Move downloaded credentials
mv ~/Downloads/client_secret_*.json ~/.config/personal-ai-employee/gmail_credentials.json

# Run Gmail auth setup (opens browser for authorization)
python setup_gmail_auth.py

# Follow browser prompts:
# 1. Select your Gmail account
# 2. Click "Allow" to grant access
# 3. Browser will show "Authentication successful"

# Verify token created
ls ~/.config/personal-ai-employee/gmail_token.json
```

**Expected Result**: `gmail_token.json` file created with OAuth2 refresh token.

---

## Part 4: WhatsApp Watcher Setup (Optional, 10 minutes)

### Step 4.1: Create WhatsApp Session

```bash
# Run WhatsApp auth setup (opens Chromium browser)
python setup_whatsapp_session.py

# Follow on-screen instructions:
# 1. Browser opens to web.whatsapp.com
# 2. Scan QR code with WhatsApp mobile app
# 3. Wait for chats to load (30 seconds)
# 4. Close browser window (session saved)

# Verify session created
ls ~/.config/personal-ai-employee/whatsapp_session/
```

**Expected Result**: `whatsapp_session/` directory created with cookies and localStorage.

**Note**: Session expires after 14 days of inactivity. Re-run setup if needed.

---

## Part 5: Start Silver Tier Watchers (5 minutes)

### Step 5.1: Create PM2 Ecosystem File

Create `ecosystem.config.js` in project root:

```javascript
module.exports = {
  apps: [
    {
      name: "bronze-watcher",
      script: "python",
      args: "scripts/watch_inbox.py",
      cwd: process.env.HOME + "/path/to/vault",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000
    },
    {
      name: "gmail-watcher",
      script: "python",
      args: "watchers/gmail_watcher.py",
      cwd: process.env.HOME + "/path/to/vault",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      env: {
        ENABLE_AI_ANALYSIS: "true"
      }
    },
    {
      name: "whatsapp-watcher",
      script: "python",
      args: "watchers/whatsapp_watcher.py",
      cwd: process.env.HOME + "/path/to/vault",
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      env: {
        ENABLE_AI_ANALYSIS: "true"
      }
    },
    {
      name: "linkedin-generator",
      script: "python",
      args: "watchers/linkedin_generator.py",
      cwd: process.env.HOME + "/path/to/vault",
      instances: 1,
      autorestart: true,
      cron_restart: "0 9 * * *"  // Daily at 9 AM
    }
  ]
};
```

### Step 5.2: Start All Watchers

```bash
# Start all watchers
pm2 start ecosystem.config.js

# Verify all processes running
pm2 status

# Expected output:
# ┌────┬──────────────────────┬─────────┬─────────┐
# │ id │ name                 │ status  │ restart │
# ├────┼──────────────────────┼─────────┼─────────┤
# │ 0  │ bronze-watcher       │ online  │ 0       │
# │ 1  │ gmail-watcher        │ online  │ 0       │
# │ 2  │ whatsapp-watcher     │ online  │ 0       │
# │ 3  │ linkedin-generator   │ online  │ 0       │
# └────┴──────────────────────┴─────────┴─────────┘

# Save PM2 configuration (auto-start on reboot)
pm2 save
pm2 startup
```

---

## Part 6: Verify Silver Tier Active (5 minutes)

### Step 6.1: Check Dashboard.md for Silver Status

```bash
# Open Dashboard.md in Obsidian
# OR view in terminal:
cat vault/Dashboard.md
```

**Expected Silver Tier Status section**:
```markdown
## Silver Tier Status
- **AI Analysis**: ✓ Enabled (Cost Today: $0.00)
- **Gmail Watcher**: ✓ Active (last poll: 2026-02-11 14:28)
- **WhatsApp Watcher**: ✓ Active (last poll: 2026-02-11 14:29)
- **LinkedIn Generator**: ⏸ Paused (next run: 2026-02-12 09:00)
```

### Step 6.2: Test AI Priority Analysis

```bash
# Create test task file
echo "# Urgent client proposal\n\nClient requesting proposal by end of day. High priority." > vault/Inbox/test-urgent.md

# Wait 30 seconds (Bronze watcher poll cycle)
sleep 30

# Check Dashboard.md for Priority="High"
grep "test-urgent" vault/Dashboard.md

# Expected output:
# | [[Inbox/test-urgent.md]] | 2026-02-11 14:30 | Inbox | High | Work |
```

### Step 6.3: Test Gmail Watcher

```bash
# Send test email to yourself with subject "Important: Test Silver Tier"
# Mark email as important in Gmail UI (star icon)

# Wait 2 minutes (Gmail watcher poll cycle)
sleep 120

# Check vault/Inbox/ for EMAIL_* file
ls vault/Inbox/EMAIL_*

# Expected output: vault/Inbox/EMAIL_abc123.md
```

### Step 6.4: Check API Usage Logs

```bash
# View API cost tracking
cat vault/Logs/API_Usage/$(date +%Y-%m).md

# Expected output:
# # API Usage Log: February 2026
# ## Daily Summary
# - 2026-02-11: 1 calls, $0.0012 total
```

---

## Part 7: MCP Email Server Setup (Optional, 5 minutes)

### Step 7.1: Configure MCP Server in Claude Code

Edit `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-email"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/home/user/.config/personal-ai-employee/gmail_credentials.json",
        "GMAIL_TOKEN_PATH": "/home/user/.config/personal-ai-employee/gmail_token.json"
      }
    }
  ]
}
```

### Step 7.2: Test MCP Email Server

```bash
# Restart Claude Code to load MCP server
# In Claude Code, run:
# /tools

# Expected output should include:
# - email.send_email
# - email.draft_email
```

---

## Troubleshooting

### Issue: "Claude API key invalid"

**Symptoms**: All tasks show Priority="Medium", logs show "API key invalid"

**Solution**:
```bash
# Verify API key in .env
cat .env | grep CLAUDE_API_KEY

# Test API key manually
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'

# If 401 error, get new key from https://console.anthropic.com/
```

### Issue: "Gmail watcher not detecting emails"

**Symptoms**: No EMAIL_* files created despite important emails arriving

**Solution**:
```bash
# Check Gmail watcher logs
pm2 logs gmail-watcher

# Common issues:
# - 403 Forbidden: OAuth2 token expired, run `python setup_gmail_auth.py`
# - 429 Rate Limit: Wait 60 seconds, watcher auto-resumes
# - No "is:important" label: Create Gmail filter or manually star emails
```

### Issue: "WhatsApp session expired"

**Symptoms**: File created in vault/Needs_Action/WHATSAPP_SESSION_EXPIRED.md

**Solution**:
```bash
# Re-authenticate WhatsApp Web
python setup_whatsapp_session.py

# Scan QR code with WhatsApp mobile app

# Restart watcher
pm2 restart whatsapp-watcher
```

### Issue: "Daily cost exceeds $0.10"

**Symptoms**: Entry in vault/Logs/cost_alerts.md

**Solution**:
```bash
# Option A: Temporarily disable AI analysis
echo "ENABLE_AI_ANALYSIS=false" >> .env
pm2 restart all

# Option B: Clear API cache (force re-analysis with lower frequency)
rm -rf vault/Logs/API_Cache/*

# Option C: Increase cache duration (reduce API calls)
echo "API_CACHE_DURATION=172800" >> .env  # 48 hours
```

---

## Next Steps

1. ✅ Silver tier is now active with AI analysis and Gmail watcher
2. Drop test tasks in `vault/Inbox/` and verify AI prioritization
3. Review Dashboard.md daily to monitor costs and watcher status
4. Customize Company_Handbook.md with business goals for LinkedIn generator
5. Set up approval workflow: Review `vault/Pending_Approval/` folder daily

---

## Rollback to Bronze

If Silver tier causes issues, revert to Bronze mode:

```bash
# Stop Silver watchers
pm2 stop gmail-watcher whatsapp-watcher linkedin-generator

# Disable AI analysis
echo "ENABLE_AI_ANALYSIS=false" >> .env

# Restart Bronze watcher
pm2 restart bronze-watcher

# Verify Bronze mode active
cat vault/Dashboard.md | grep "Silver Tier Status"
# Should show: AI Analysis: ✗ Disabled (Bronze Mode)
```

---

**Setup Complete!** Silver tier is now running with AI-powered analysis and multi-channel monitoring.
