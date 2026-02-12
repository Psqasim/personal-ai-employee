# Manual Testing Guide — Silver Tier MVP

**Who this is for**: You, testing T001–T036 locally right now.
**Time needed**: ~30 minutes (most time is Gmail OAuth setup)

---

## Step 1: Get Your Claude API Key (5 min)

1. Go to **https://console.anthropic.com/**
2. Sign up / log in
3. Click **"API Keys"** in the left sidebar
4. Click **"Create Key"** → name it "personal-ai-employee"
5. Copy the key — it looks like `sk-ant-api03-xxxxxxxxx`
6. **Save it somewhere safe** — you only see it once

---

## Step 2: Configure Your `.env` File (2 min)

In the project root:

```bash
cp .env.example .env
```

Open `.env` and fill in these **required** values:

```env
# 1. Absolute path to your vault folder
VAULT_PATH=/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/vault

# 2. Enable Silver AI features
ENABLE_AI_ANALYSIS=true

# 3. Paste your Claude API key
CLAUDE_API_KEY=sk-ant-api03-your-key-here

# Leave the rest as defaults
CLAUDE_MODEL=claude-3-5-sonnet-20241022
GMAIL_POLL_INTERVAL=120
API_DAILY_COST_LIMIT=0.10
API_CACHE_DURATION=86400
```

---

## Step 3: Activate Virtual Environment (1 min)

```bash
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"

source .venv/bin/activate

# Verify Claude SDK is installed
python -c "import anthropic; print('Claude SDK ready:', anthropic.__version__)"
```

---

## Step 4: Test AI Priority Analysis — No Gmail Needed (5 min)

### 4.1 Create 3 test files

```bash
# HIGH priority — urgent keywords
cat > vault/Inbox/test_urgent.md << 'EOF'
# URGENT: Client invoice needs immediate approval

Client is requesting urgent approval for invoice #4521 worth $12,000.
Payment must be processed by end of business today or we lose the contract.
Please review ASAP.
EOF

# MEDIUM priority — routine work
cat > vault/Inbox/test_routine.md << 'EOF'
# items: update tickets, send status report by Friday.
No urgent items.
EOF

# LOW priority — personal
cat > vault/Inbox/test_personal.md << 'EOF'
# Grocery list for weekend

Milk, eggs, bread, vegetables for salad.
Nothing Weekly team sync meeting notes

Discussed project milestones for Q1.
Action urgent, just personal errands.
EOF
```

### 4.2 Run the watcher

```bash
export $(cat .env | grep -v '^#' | grep '=' | xargs)
python scripts/watch_inbox.py vault/
```

Expected terminal output:
```
[INFO]: Starting file watcher (polling interval: 30s)
[INFO]: Detected 3 new file(s)
[INFO]: Dashboard updated successfully
```

### 4.3 Check Dashboard.md

```bash
cat vault/Dashboard.md
```

Expected (Silver mode — has Category column):
```
| Filename               | Date Added       | Status | Priority | Category |
|------------------------|------------------|--------|----------|----------|
| [[Inbox/test_urgent]]  | 2026-02-12 10:00 | Inbox  | High     | Urgent   |
| [[Inbox/test_routine]] | 2026-02-12 10:00 | Inbox  | Medium   | Work     |
| [[Inbox/test_personal]]| 2026-02-12 10:00 | Inbox  | Low      | Personal |
```

✅ **Pass**: Priority + Category columns filled by AI

### 4.4 Test Bronze fallback (Ctrl+C to stop, then):

```bash
ENABLE_AI_ANALYSIS=false python scripts/watch_inbox.py vault/
```

Drop another file:
```bash
echo "# Another task" > vault/Inbox/test_fallback.md
```

Check Dashboard — new task shows `Medium | Uncategorized` (Bronze defaults, no API call).

✅ **Pass**: Works without API key, no errors

---

## Step 5: Gmail OAuth Setup (15–20 min)

### 5.1 Create Google Cloud Project

1. Open **https://console.cloud.google.com/**
2. Top bar → "Select a project" → **"New Project"**
3. Name: `personal-ai-employee` → **Create**
4. Wait ~30 seconds for it to be ready

### 5.2 Enable Gmail API

1. Left menu → **"APIs & Services"** → **"Library"**
2. Search: `Gmail API` → Click it → **"Enable"**

### 5.3 Configure OAuth Consent Screen

1. Left menu → **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** → **Create**
3. Fill in:
   - App name: `Personal AI Employee`
   - User support email: *(your Gmail)*
   - Developer contact email: *(your Gmail)*
4. Click **Save and Continue** through all screens
5. On **"Test users"** screen → **"+ Add Users"** → type your Gmail address → **Add**
6. **Save and Continue** → Back to Dashboard

### 5.4 Create OAuth2 Credentials

1. Left menu → **"APIs & Services"** → **"Credentials"**
2. **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `personal-ai-employee`
5. **Create**
6. Popup appears → click **"Download JSON"**
7. Move the file to the config folder:

```bash
mkdir -p ~/.config/personal-ai-employee

# Replace with actual downloaded filename
mv ~/Downloads/client_secret_*.json \
   ~/.config/personal-ai-employee/gmail_credentials.json

# Verify it's there
ls ~/.config/personal-ai-employee/
# Should show: gmail_credentials.json
```

### 5.5 Add Gmail path to `.env`

Open `.env` and add/update:
```env
GMAIL_CREDENTIALS_PATH=~/.config/personal-ai-employee/gmail_credentials.json
```

### 5.6 Run the authorization script

```bash
source .venv/bin/activate
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

python scripts/setup_gmail_auth.py
```

**What happens:**
1. A browser window opens automatically
2. Choose your Google account
3. Click **"Continue"** (app is in test mode — that's fine)
4. Click **"Allow"** to grant read access
5. Browser shows: *"The authentication flow has completed"*
6. Terminal shows:
   ```
   Authorization successful! Token saved to ~/.config/personal-ai-employee/gmail_token.json
   ```

---

## Step 6: Test Gmail Watcher (5 min)

### 6.1 Mark an email as Important in Gmail

1. Open **https://mail.google.com/**
2. Find any unread email
3. Click the **yellow tag/bookmark icon** (⬛) next to it
   - Or open email → click the **Important** marker at the top
   - Or: search for an important email — Gmail auto-marks some as important

### 6.2 Start the Gmail watcher

```bash
export $(cat .env | grep -v '^#' | grep '=' | xargs)
python watchers/gmail_watcher.py
```

Expected output:
```
[INFO] [gmail]: Starting Gmail watcher (poll interval: 120s)
[INFO] [gmail]: Polled Gmail: 1 new important email(s)
[INFO] [gmail]: Created email task: EMAIL_18d3a2f1c4b5e6a7.md
```

> Tip: The default poll interval is 120 seconds (2 min). To test faster, temporarily set `GMAIL_POLL_INTERVAL=10` in `.env`.

### 6.3 Check the created file

```bash
ls vault/Inbox/EMAIL_*.md

cat vault/Inbox/EMAIL_*.md
```

Expected file structure:
```markdown
---
type: email
from: "sender@example.com"
subject: "Your email subject"
received: "2026-02-12T10:00:00"
priority: high
status: pending
source: gmail
---

# Your email subject

**From**: sender@example.com
**Received**: 2026-02-12T10:00:00

## Email Summary

First 200 chars of the email snippet...

## Suggested Actions

- [ ] Read full email
- [ ] Reply if needed
- [ ] File or archive when complete
```

✅ **Pass**: `EMAIL_{id}.md` created with YAML frontmatter and email details

### 6.4 Check duplicate prevention

Let the watcher poll again (wait for next cycle). It should NOT create a second file for the same email.

```bash
# Should still show only 1 file
ls vault/Inbox/EMAIL_*.md | wc -l

# See processed IDs
cat vault/Logs/gmail_processed_ids.txt
```

✅ **Pass**: Same email ID only appears once

---

## Step 7: Run All Automated Tests

```bash
python -m pytest tests/ -v --no-cov
```

Expected: **47 passed** in ~3 seconds

---

## Quick Reference

| Test | How to run | Expected |
|------|-----------|----------|
| AI Priority | Drop `URGENT` file in `vault/Inbox/` | Dashboard: `High \| Urgent` |
| AI Category | Drop `client proposal` file | Dashboard: `Work` category |
| Bronze Fallback | `ENABLE_AI_ANALYSIS=false` | Dashboard: `Medium \| Uncategorized` |
| Cache | Drop same file twice | 2nd analysis: instant (no API call) |
| Gmail watcher | Mark email Important in Gmail | `EMAIL_{id}.md` appears |
| No duplicates | Wait for 2 poll cycles | Only 1 file per email |
| Full test suite | `pytest tests/ -v` | 47/47 pass |

---

## Troubleshooting

**All priorities show "Medium" (Bronze fallback)**
```bash
# Check key is loaded
echo $CLAUDE_API_KEY

# Test API directly
python -c "
import anthropic, os
c = anthropic.Anthropic(api_key=os.environ['CLAUDE_API_KEY'])
r = c.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=10,
    messages=[{'role':'user','content':'hi'}])
print('OK:', r.content[0].text)
"
```

**"GMAIL_CREDENTIALS_PATH not set"**
```bash
ls ~/.config/personal-ai-employee/
# Must show gmail_credentials.json
```

**"Gmail token not found" / 403 error**
```bash
rm -f ~/.config/personal-ai-employee/gmail_token.json
python scripts/setup_gmail_auth.py   # Re-authorize
```

**No emails being picked up**
- Make sure at least one email has the **Important** label (yellow marker)
- Gmail only returns `is:important` emails — not just unread
- Check errors: `cat vault/Logs/gmail_watcher_errors.md`

**VAULT_PATH with spaces (WSL)**
```env
# Use quotes in .env
VAULT_PATH="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/vault"
```
