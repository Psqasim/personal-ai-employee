# Silver Tier Quickstart (5 Minutes)

> AI-powered priority analysis + Gmail monitoring on top of your Bronze foundation.

---

## What Silver MVP Adds

- **AI Priority Analysis** — Claude assigns High/Medium/Low priority to every inbox task
- **Task Categorization** — Work / Personal / Urgent classification
- **Gmail Watcher** — Monitors important emails and creates vault tasks automatically
- **Graceful Fallback** — Falls back to Bronze behavior if API is unavailable

---

## Step 1: Get Your Claude API Key (2 min)

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up / log in → **API Keys** → **Create Key**
3. Name it `personal-ai-employee-silver`
4. Copy the key (starts with `sk-ant-api03-`)

---

## Step 2: Configure Environment (1 min)

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Edit `.env` — set these values:

```bash
ENABLE_AI_ANALYSIS=true
CLAUDE_API_KEY=sk-ant-api03-YOUR_KEY_HERE
CLAUDE_MODEL=claude-3-5-sonnet-20241022
API_DAILY_COST_LIMIT=0.10
```

---

## Step 3: Install Silver Dependencies (1 min)

```bash
pip install anthropic>=0.18.0 google-api-python-client>=2.80.0 \
  google-auth-oauthlib>=1.0.0 google-auth-httplib2>=0.1.0
```

Or install everything at once:

```bash
pip install -e .[dev]
```

---

## Step 4: Enable Gmail Watcher (optional, 5 min)

### 4a. Create Google Cloud credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create project → enable **Gmail API**
3. Create **OAuth 2.0 Client ID** (Desktop app)
4. Download JSON → save as `~/.config/personal-ai-employee/gmail_credentials.json`

### 4b. Authorize Gmail access

```bash
mkdir -p ~/.config/personal-ai-employee
python3 scripts/setup_gmail_auth.py
```

Follow the browser prompt — click Allow. A `gmail_token.json` file is saved automatically.

### 4c. Start the Gmail watcher

```bash
python3 watchers/gmail_watcher.py
```

The watcher polls every 2 minutes for important/unread emails and creates `vault/Inbox/EMAIL_*.md` files.

---

## Step 5: Test AI Analysis

```bash
# Drop a test task
echo "# Urgent client proposal — due today" > vault/Inbox/test-urgent.md

# Start the watcher (if not already running)
python3 scripts/watch_inbox.py

# Wait ~30 seconds, then check Dashboard.md
grep "test-urgent" vault/Dashboard.md
# Expected: | [[Inbox/test-urgent.md]] | ... | High | Work |
```

---

## Testing Checklist

| Test | Expected Result |
|------|----------------|
| Drop urgent task → wait 30s | Dashboard shows `Priority: High` |
| Drop routine task → wait 30s | Dashboard shows `Priority: Medium` |
| Drop personal task → wait 30s | Dashboard shows `Category: Personal` |
| Send important Gmail → wait 2min | `vault/Inbox/EMAIL_*.md` created |
| Set `ENABLE_AI_ANALYSIS=false` | Falls back to Bronze (Priority: Medium) |

---

## Cost Control

Silver tier uses the Claude API. Default limits are set conservatively:

- **Daily limit**: $0.10 (configurable via `API_DAILY_COST_LIMIT`)
- **24h caching**: Identical tasks reuse cached responses (no extra cost)
- **Typical cost**: ~$0.001 per task analysis

Monitor usage: `cat vault/Logs/API_Usage/$(date +%Y-%m).md`

---

## Rollback to Bronze

If anything goes wrong:

```bash
# Disable AI in .env
ENABLE_AI_ANALYSIS=false

# Restart watcher — Bronze defaults kick in automatically
python3 scripts/watch_inbox.py
```

---

## Full Setup Guide

For WhatsApp watcher, LinkedIn auto-posting, PM2 process management, and MCP server setup, see:
[docs/silver/setup-guide.md](setup-guide.md)

---

**Done!** Your AI Employee now thinks before it files.
