# Silver Tier Setup Guide

**Personal AI Employee - Silver Tier (AI-Powered)**
**Date**: 2026-02-12

Silver Tier adds Claude AI analysis, Gmail monitoring, and task categorization to your Bronze foundation.

---

## Prerequisites

- Python 3.11+ (`python3 --version`)
- Obsidian 1.5+ (from https://obsidian.md/)
- Node.js 18+ (for PM2: `node --version`)
- Gmail account + Google Cloud project
- Claude API key (from https://console.anthropic.com/)

---

## Part 1: Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install all Silver tier dependencies
pip install anthropic>=0.18.0 google-auth>=2.16.0 google-api-python-client>=2.80.0 \
  google-auth-oauthlib>=1.0.0 google-auth-httplib2>=0.1.0 playwright>=1.40.0 aiohttp>=3.9.0 \
  watchdog>=3.0.0 pyyaml>=6.0

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Install Playwright browser (for WhatsApp watcher)
playwright install chromium

# Install PM2 globally
npm install -g pm2
```

---

## Part 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set required values:
#   VAULT_PATH=/absolute/path/to/your/vault
#   ENABLE_AI_ANALYSIS=true
#   CLAUDE_API_KEY=sk-ant-api03-your-key-here
```

Create `~/.config/personal-ai-employee/` for credentials:
```bash
mkdir -p ~/.config/personal-ai-employee
```

---

## Part 3: Gmail Setup

### 3.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create new project: "Personal AI Employee"
3. Enable Gmail API: APIs & Services → Library → "Gmail API" → Enable
4. Create credentials: APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: **Desktop application**
   - Name: "Personal AI Employee"
5. Download JSON → save as `~/.config/personal-ai-employee/gmail_credentials.json`

### 3.2 Set credentials path in `.env`:
```
GMAIL_CREDENTIALS_PATH=~/.config/personal-ai-employee/gmail_credentials.json
```

### 3.3 Authorize Gmail access:
```bash
python scripts/setup_gmail_auth.py
# Browser opens → Sign in → Authorize → Token saved automatically
```

---

## Part 4: Start Watchers

### With PM2 (recommended for always-on):
```bash
pm2 start ecosystem.config.js
pm2 status
pm2 logs
```

### For development/testing:
```bash
# Bronze inbox watcher (with AI analysis)
ENABLE_AI_ANALYSIS=true python scripts/watch_inbox.py /path/to/vault

# Gmail watcher
VAULT_PATH=/path/to/vault python watchers/gmail_watcher.py
```

---

## Part 5: Verify Installation

```bash
# Run all tests
python -m pytest tests/ -v

# Expected: 47+ tests pass
```

Drop a test file in `vault/Inbox/`:
```bash
echo "# Urgent client invoice review" > vault/Inbox/test_task.md
```

With `ENABLE_AI_ANALYSIS=true`, verify `vault/Dashboard.md` shows:
- Priority column with High/Medium/Low
- Category column with Work/Personal/Urgent/Uncategorized

---

## Troubleshooting

### Issue: Claude API key invalid
```
Symptom: Tasks show Priority="Medium" (Bronze fallback)
Fix: Check CLAUDE_API_KEY in .env
     Get key from: https://console.anthropic.com/
```

### Issue: Gmail watcher not creating EMAIL_* files
```
Symptom: Important emails arrive but no EMAIL_* files in vault/Inbox/
Fix 1 (403 error): Re-run python scripts/setup_gmail_auth.py
Fix 2 (no is:important): Create Gmail filter to mark emails as Important
Fix 3: Check vault/Logs/gmail_watcher_errors.md for details
```

### Issue: Daily cost exceeds $0.10
```
Symptom: Entry in vault/Logs/cost_alerts.md
Fix 1: Clear duplicate tasks from Inbox (caching reduces repeat costs)
Fix 2: Temporarily set ENABLE_AI_ANALYSIS=false
Fix 3: Increase API_CACHE_DURATION=172800 (48h cache)
```

### Issue: AI analysis slow or timing out
```
Symptom: Logs show "Claude API timeout (>5s)"
Fix: Check network connectivity
     Verify CLAUDE_API_KEY is valid
     Fallback to Bronze is automatic - no action needed
```

---

## Architecture Overview

```
vault/Inbox/          ← Drop tasks or EMAIL_* files here
       ↓
scripts/watch_inbox.py ← Detects new files
       ↓
agent_skills/ai_analyzer.py ← Claude API (with cache + fallback)
       ↓
agent_skills/dashboard_updater.py ← Atomic Dashboard.md update
       ↓
vault/Dashboard.md    ← Priority + Category table (auto-maintained)

watchers/gmail_watcher.py ← Polls Gmail every 2min → creates EMAIL_* files
```

---

## Rollback to Bronze

If Silver causes issues:
```bash
# Stop Silver watchers
pm2 stop gmail-watcher whatsapp-watcher linkedin-generator

# Disable AI analysis
sed -i 's/ENABLE_AI_ANALYSIS=true/ENABLE_AI_ANALYSIS=false/' .env

# Restart Bronze watcher
pm2 restart bronze-watcher

# Verify Bronze mode
# Dashboard.md should show Priority="Medium" (Bronze default)
```
