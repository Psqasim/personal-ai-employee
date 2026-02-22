# Personal AI Employee — Manual Setup & Operations Guide

> **Last updated:** 2026-02-22
> **Covers:** Local machine setup · Oracle Cloud VM setup · PM2 · WhatsApp watcher · Claude API · Re-auth · Restart / Stop / Troubleshoot

---

## Where to Run Commands — Quick Reference

| Command type | Where to run | Example prompt |
|---|---|---|
| WhatsApp setup/reauth | **WSL `/tmp`** | `ps_qasim@MUHAMMADQASIM:/tmp$` |
| PM2 start/stop/logs | **Project folder** | `ps_qasim@MUHAMMADQASIM:~/...personal-ai-employee$` |
| git commands | **Project folder** | same as above |
| Oracle SSH | **Anywhere (WSL root fine)** | `ps_qasim@MUHAMMADQASIM:~$` |
| Oracle VM commands | **Inside SSH session** | `ubuntu@personal-ai-vcn:~$` |

**Project folder shortcut:**
```bash
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
```

**Why `/tmp` for WhatsApp setup?**
WSL2 Playwright hangs indefinitely if the working directory is on a Windows mount (`/mnt/d/...`).
Always `cd /tmp` before running any `wa_local_setup.py` or `wa_reauth.py` locally.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Local Machine Setup](#3-local-machine-setup)
4. [Oracle Cloud VM Setup](#4-oracle-cloud-vm-setup)
5. [WhatsApp Setup — How It Works](#5-whatsapp-setup--how-it-works)
6. [PM2 Commands Reference](#6-pm2-commands-reference)
7. [Claude API Service](#7-claude-api-service)
8. [Stop / Restart / Re-authenticate](#8-stop--restart--re-authenticate)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP (Local)                  │
│                                                         │
│  PM2: local_approval_handler                            │
│    └─ scripts/run_local_agent.sh                        │
│         └─ local_agent/src/orchestrator.py              │
│              ├─ Reads vault/Approved/ (email drafts)    │
│              └─ Sends via SMTP                          │
│                                                         │
│  MCP Server (Claude Desktop / Claude Code)              │
│    └─ mcp_servers/whatsapp_mcp/server.py                │
│         └─ Playwright → WhatsApp Web (send/read)        │
└─────────────────────────────────────────────────────────┘
                          │
                    git push/pull
                          │
┌─────────────────────────────────────────────────────────┐
│              ORACLE CLOUD VM (24/7)                     │
│              ubuntu@129.151.151.212                     │
│                                                         │
│  PM2: cloud_orchestrator                                │
│    └─ cloud_agent/src/orchestrator.py                   │
│         ├─ Gmail watcher → AI draft → vault             │
│         ├─ LinkedIn post generator                      │
│         └─ CEO briefing (weekly)                        │
│                                                         │
│  PM2: git_sync_cloud                                    │
│    └─ cloud_agent/src/git_sync.py                       │
│         └─ Pulls latest code from GitHub every 5 min   │
│                                                         │
│  PM2: whatsapp_watcher                                  │
│    └─ scripts/whatsapp_watcher.py                       │
│         ├─ Playwright (headless Chrome)                 │
│         ├─ Reads WhatsApp Web every 30s                 │
│         ├─ Generates AI reply via Claude API            │
│         └─ Sends reply back in WhatsApp                 │
└─────────────────────────────────────────────────────────┘
```

**Key files:**

| File | Purpose |
|------|---------|
| `ecosystem.config.js` | PM2 config for Oracle Cloud |
| `ecosystem.config.local.js` | PM2 config for local machine |
| `scripts/whatsapp_watcher.py` | WhatsApp AI auto-reply watcher |
| `scripts/wa_reauth.py` | WhatsApp re-authentication helper |
| `mcp_servers/whatsapp_mcp/server.py` | MCP server for WhatsApp (local) |
| `.env` | Local environment variables |
| `.env.cloud` | Cloud environment variables (on VM only) |

---

## 2. Prerequisites

### Both Local & Cloud

- Python 3.11+
- Node.js 18+ (for PM2)
- PM2: `npm install -g pm2`
- Playwright: `pip install playwright && playwright install chromium`
- Anthropic API key (Claude)

### Local only

- Gmail OAuth credentials (`credentials.json`)
- WhatsApp session directory (`~/.whatsapp_session/` or path in `.env`)

### Cloud only

- Oracle Cloud free-tier VM (Ubuntu 22.04, 1 OCPU, 1GB RAM)
- SSH key pair (`~/.ssh/ssh-key-2026-02-17.key`)
- VM IP: `129.151.151.212`

---

## 3. Local Machine Setup

### 3.1 Clone & Install

```bash
git clone <repo-url> personal-ai-employee
cd personal-ai-employee

# Create virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
pip install anthropic playwright
playwright install chromium
```

### 3.2 Environment Variables

Copy and fill in `.env`:

```bash
cp .env.example .env
```

Key variables in `.env`:

```env
# Claude / Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Gmail
GMAIL_ADDRESS=you@gmail.com
GMAIL_POLL_INTERVAL=120

# WhatsApp Watcher (local)
ENABLE_WHATSAPP_WATCHER=true
PLAYWRIGHT_HEADLESS=false           # false = show browser window locally
WHATSAPP_SESSION_PATH=~/.whatsapp_session_dir
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_ADMIN_NUMBER=923460326429  # Your number (no + sign)
CHATS_TO_CHECK=5
```

### 3.3 WhatsApp Session — First Time (Local / WSL2)

> **WSL2 users:** Use `wa_local_setup.py` (headless + pairing code).
> `setup_whatsapp_session.py` opens a visible browser window which WSL2 cannot display.

```bash
# Delete old/invalid session first (if re-authenticating)
rm -rf ~/.whatsapp_session_dir

# MUST cd to /tmp first — WSL2 Playwright hangs if CWD is on /mnt/d Windows mount
cd /tmp
python "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/scripts/wa_local_setup.py"
```

1. Script starts headless Chrome (~25s to load)
2. Prints `PAIRING CODE: XXXX-YYYY`
3. Phone → **WhatsApp** → **⋮** → **Linked Devices** → **Link a Device** → **"Link with phone number instead"** → enter code within 60s
4. Script prints `✅ AUTH SUCCESS` — session saved

### 3.4 Start Local Agent via PM2

> **PM2 v6 + WSL2 note:** `pm2 start ecosystem.config.local.js` breaks when the project path has
> spaces (e.g. `/mnt/d/gov ai code/...`). PM2 doesn't quote the path, so bash splits on the space.
> The fix: use trampoline scripts stored at `$HOME` (no spaces) + `pm2.local.json`.

**One-time trampoline setup** (only needed after a fresh clone):

```bash
# The trampoline scripts are already at ~/pai_agent.sh and ~/pai_whatsapp.sh
# If they don't exist (new machine), recreate them:
cat > ~/pai_agent.sh << 'EOF'
#!/bin/bash
PROJECT="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
exec bash "$PROJECT/scripts/run_local_agent.sh"
EOF

cat > ~/pai_whatsapp.sh << 'EOF'
#!/bin/bash
PROJECT="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
exec bash "$PROJECT/scripts/pm2_whatsapp_wrapper.sh"
EOF

chmod +x ~/pai_agent.sh ~/pai_whatsapp.sh
```

**Start all local services:**

```bash
# From the project folder
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"

# Start both processes using the JSON config
pm2 start pm2.local.json

# Check status (should show local_approval_handler + whatsapp_watcher_local)
pm2 list

# View logs
pm2 logs local_approval_handler
pm2 logs whatsapp_watcher_local

# Save so processes survive WSL2 restart
pm2 save
pm2 startup     # follow the printed command
```

### 3.5 Start WhatsApp Watcher Locally (without PM2)

```bash
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
source venv/bin/activate
python scripts/whatsapp_watcher.py
```

---

## 4. Oracle Cloud VM Setup

### 4.1 SSH into the VM

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
```

### 4.2 First-Time VM Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Node, git
sudo apt install -y python3.11 python3.11-venv python3-pip git nodejs npm

# Install PM2 globally
sudo npm install -g pm2

# Clone repo
sudo mkdir -p /opt/personal-ai-employee
sudo chown ubuntu:ubuntu /opt/personal-ai-employee
git clone <repo-url> /opt/personal-ai-employee
cd /opt/personal-ai-employee

# Create venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install anthropic playwright

# Install Playwright browser (headless Chromium)
playwright install chromium
```

### 4.3 Environment Variables on Cloud

Create `.env.cloud` on the VM (never commit this file):

```bash
nano /opt/personal-ai-employee/.env.cloud
```

```env
# Claude / Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Gmail
GMAIL_ADDRESS=you@gmail.com
GMAIL_POLL_INTERVAL=120
ENABLE_CLOUD_AGENT=true
ENABLE_WHATSAPP_NOTIFICATIONS=true

# WhatsApp Watcher (cloud)
ENABLE_WHATSAPP_WATCHER=true
PLAYWRIGHT_HEADLESS=true            # MUST be true on cloud (no display)
WHATSAPP_SESSION_PATH=/home/ubuntu/.whatsapp_session_dir
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_ADMIN_NUMBER=923460326429
CHATS_TO_CHECK=5
```

### 4.4 Start All Cloud Services

```bash
cd /opt/personal-ai-employee

# Start all PM2 processes
pm2 start ecosystem.config.js

# Check status
pm2 list

# Save PM2 config (survives VM reboot)
pm2 save

# Register PM2 on system startup
pm2 startup
# Copy and run the printed command (starts with sudo)
```

### 4.5 WhatsApp Authentication on Cloud (First Time)

WhatsApp sessions **cannot be transferred** from local to cloud — the cloud VM must authenticate independently using phone number pairing:

```bash
# On cloud VM, run the reauth script
cd /opt/personal-ai-employee
pm2 start scripts/wa_reauth.py \
  --name wa_auth \
  --interpreter venv/bin/python \
  --no-autorestart \
  --kill-timeout 600000

# Watch the logs — a pairing code will appear
pm2 logs wa_auth
```

**When you see the code:**

```
==================================================
  PAIRING CODE: XXXX-YYYY
==================================================
```

On your phone:
1. Open **WhatsApp**
2. Tap **⋮ (3-dot menu)** → **Linked Devices** → **Link a Device**
3. Tap **"Link with phone number instead"**
4. Enter the 8-character code (e.g., `XXXX-YYYY`)
5. The script auto-starts `whatsapp_watcher` on success

```bash
# Clean up auth helper after success
pm2 delete wa_auth
```

---

## 5. WhatsApp Setup — How It Works

### 5.1 How the Watcher Works

The WhatsApp watcher (`scripts/whatsapp_watcher.py`) runs on a **3-phase cycle** every 30 seconds:

```
┌─────────────────────────────────────────────────────────┐
│  Every 30 seconds:                                      │
│                                                         │
│  Phase 1 — READ (browser open, locked)                  │
│    • Open Chromium → WhatsApp Web                       │
│    • Wait for chat list to load                         │
│    • Read top N chats (default: 5)                      │
│    • Extract sender + last message                      │
│    • Close browser                                      │
│                                                         │
│  Phase 2 — GENERATE (no browser, ~5-10s)                │
│    • For each unread message:                           │
│      - Call Claude API (claude-haiku-4-5)               │
│      - Generate contextual reply                        │
│      - Same language as sender                          │
│                                                         │
│  Phase 3 — SEND (browser open, locked)                  │
│    • Open Chromium → WhatsApp Web                       │
│    • Navigate to each sender's chat                     │
│    • Type and send the AI reply                         │
│    • Close browser                                      │
└─────────────────────────────────────────────────────────┘
```

**Why 3 phases?** Keeping the browser open during the 5-10s Claude API call was causing Chrome to crash. The browser is only open when actually needed.

### 5.2 Deduplication & Safety

- **`_replied_cache`** (persistent across cycles): remembers sender+message pairs already replied to
- **`_seen_this_cycle`** (per-cycle): prevents duplicate replies if WhatsApp shows the same chat twice
- **Admin number filtering**: never replies to your own number (`WHATSAPP_ADMIN_NUMBER`)

### 5.3 Browser Lock (Prevents Chrome Conflicts)

Both the watcher and the local MCP server (`mcp_servers/whatsapp_mcp/server.py`) use the same Chrome profile directory. Simultaneous access causes crashes.

A **file lock** at `/tmp/whatsapp_browser.lock` (using `fcntl.flock`) ensures only one process uses Chrome at a time:

```python
@contextmanager
def _browser_lock(timeout=90):
    lock_f = open('/tmp/whatsapp_browser.lock', 'w')
    fcntl.flock(lock_f, fcntl.LOCK_EX)  # blocks until free
    try:
        yield
    finally:
        fcntl.flock(lock_f, fcntl.LOCK_UN)
        lock_f.close()
```

### 5.4 WhatsApp Session Storage

| Environment | Session Path | Notes |
|-------------|-------------|-------|
| Local | `~/.whatsapp_session_dir` (or `.env` value) | Visible Chrome, QR scan once |
| Cloud | `/home/ubuntu/.whatsapp_session_dir` | Headless Chrome, phone pairing |

Sessions persist across restarts — you only need to authenticate once (until WhatsApp invalidates it, typically after 14+ days of inactivity on a linked device).

### 5.5 User Agent (Critical for Cloud)

WhatsApp Web blocks the default `HeadlessChrome` user-agent. We spoof a real Chrome UA:

```python
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')
```

### 5.6 Local vs Cloud Differences

| Feature | Local | Cloud |
|---------|-------|-------|
| `PLAYWRIGHT_HEADLESS` | `false` (visible) | `true` (headless) |
| First auth | Phone number pairing code (`wa_local_setup.py`) | Phone number pairing code (`wa_reauth.py`) |
| Browser lock | Shared with MCP server | Watcher only |
| Session dir | Custom path in `.env` | `/home/ubuntu/.whatsapp_session_dir` |
| PM2 config | `ecosystem.config.local.js` | `ecosystem.config.js` |

---

## 6. PM2 Commands Reference

### Basic Commands

```bash
# ── STATUS ──────────────────────────────────────────────
pm2 list                          # Show all processes
pm2 status                        # Alias for list
pm2 show <name>                   # Detailed info for one process

# ── START ───────────────────────────────────────────────
pm2 start ecosystem.config.js                    # Start all (cloud)
pm2 start ecosystem.config.local.js              # Start all (local)
pm2 start ecosystem.config.js --only whatsapp_watcher  # Start one only

# ── STOP ────────────────────────────────────────────────
pm2 stop all                      # Stop everything
pm2 stop whatsapp_watcher         # Stop one process
pm2 stop ecosystem.config.js      # Stop all defined in file

# ── RESTART ─────────────────────────────────────────────
pm2 restart all                   # Restart all
pm2 restart whatsapp_watcher      # Restart one
pm2 reload whatsapp_watcher       # Graceful reload (zero-downtime)

# ── DELETE ──────────────────────────────────────────────
pm2 delete all                    # Remove all from PM2
pm2 delete whatsapp_watcher       # Remove one

# ── LOGS ────────────────────────────────────────────────
pm2 logs                          # Tail all logs
pm2 logs whatsapp_watcher         # Tail one process logs
pm2 logs whatsapp_watcher --lines 100  # Last 100 lines
pm2 logs whatsapp_watcher --nostream   # Print and exit (no tailing)
pm2 flush                         # Clear all log files

# ── SAVE / STARTUP ──────────────────────────────────────
pm2 save                          # Save current process list to disk
pm2 startup                       # Generate startup script (run once)
pm2 resurrect                     # Restore saved process list

# ── MONITORING ──────────────────────────────────────────
pm2 monit                         # Live CPU/memory dashboard
```

### Process Names (Cloud)

| PM2 Name | Script | Purpose |
|----------|--------|---------|
| `cloud_orchestrator` | `cloud_agent/src/orchestrator.py` | Main AI agent |
| `git_sync_cloud` | `cloud_agent/src/git_sync.py` | Auto git pull |
| `whatsapp_watcher` | `scripts/whatsapp_watcher.py` | WhatsApp AI reply |

### Process Names (Local)

| PM2 Name | Script | Purpose |
|----------|--------|---------|
| `local_approval_handler` | `~/pai_agent.sh` → `scripts/run_local_agent.sh` | Email approval & send |
| `whatsapp_watcher_local` | `~/pai_whatsapp.sh` → `scripts/pm2_whatsapp_wrapper.sh` | WhatsApp AI reply (local) |

> **Why `~/pai_*.sh` trampolines?** PM2 v6 on WSL2 doesn't quote paths that have spaces.
> Project lives at `/mnt/d/gov ai code/...` (spaces!). Trampolines at `$HOME` have no spaces.

---

## 7. Claude API Service

### How It's Used

The watcher calls Claude (`claude-haiku-4-5`) for each WhatsApp reply:

```python
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

response = client.messages.create(
    model='claude-haiku-4-5-20251001',
    max_tokens=300,
    messages=[{
        'role': 'user',
        'content': f"Message from {sender}: {message}\n\nReply in same language."
    }],
    system="You are Qasim's personal AI assistant..."
)
```

### Environment Variable

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Get your key at: https://console.anthropic.com/

### Cost Estimate

Claude Haiku is the cheapest model:
- Input: $0.80 / 1M tokens
- Output: $0.40 / 1M tokens
- Typical reply: ~200 input + 100 output tokens = ~$0.0002 per reply

---

## 8. Stop / Restart / Re-authenticate

### 8.1 Restart Everything (Cloud)

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
cd /opt/personal-ai-employee
pm2 restart all
pm2 list   # verify all online
```

### 8.2 Restart Only WhatsApp Watcher (Cloud)

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 restart whatsapp_watcher
pm2 logs whatsapp_watcher --lines 30
```

### 8.3 Restart Everything (Local)

```bash
pm2 restart local_approval_handler
pm2 restart whatsapp_watcher_local
# or
pm2 restart all
```

### 8.4 Stop Everything

```bash
# Cloud
pm2 stop all

# Local (individual)
pm2 stop local_approval_handler
pm2 stop whatsapp_watcher_local
```

### 8.5 Re-authenticate WhatsApp on Cloud

WhatsApp sessions can expire (typically after 14+ days inactive, or if you remove the linked device). When the watcher logs show `QR code` instead of chat list:

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
cd /opt/personal-ai-employee

# Stop watcher first (needs exclusive Chrome access)
pm2 stop whatsapp_watcher

# Run the reauth helper
pm2 start scripts/wa_reauth.py \
  --name wa_auth \
  --interpreter venv/bin/python \
  --no-autorestart \
  --kill-timeout 600000

# Watch for the pairing code (appears after ~45s)
pm2 logs wa_auth
```

**When `PAIRING CODE: XXXX-YYYY` appears:**

On your phone:
1. Open WhatsApp
2. **⋮** → **Linked Devices** → **Link a Device**
3. Tap **"Link with phone number instead"**
4. Enter the 8-char code within 60 seconds

After success, the script auto-starts `whatsapp_watcher`. Clean up:

```bash
pm2 delete wa_auth
pm2 save
```

### 8.6 Re-authenticate WhatsApp on Local (WSL2)

**When to do this:** If watcher logs show `Session expired`, `QR code`, or AI replies stop coming.

```bash
# 1. Stop the watcher (needs exclusive Chrome access)
pm2 stop whatsapp_watcher_local

# 2. Delete old/stale session
rm -rf ~/.whatsapp_session_dir

# 3. MUST cd to /tmp first — WSL2 Playwright hangs if CWD is on /mnt/d Windows mount
cd /tmp
python "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/scripts/wa_local_setup.py"
```

**After ~25 seconds you'll see:**
```
==================================================
  PAIRING CODE: XXXX-YYYY
==================================================
```

On your phone:
1. Open **WhatsApp**
2. **⋮ (3-dot menu)** → **Linked Devices** → **Link a Device**
3. Tap **"Link with phone number instead"**
4. Enter the 8-character code within 60 seconds

After `✅ AUTH SUCCESS`:

```bash
# 4. Restart the watcher — session is now saved
pm2 start whatsapp_watcher_local
pm2 save

# 5. Verify it's polling
pm2 logs whatsapp_watcher_local --lines 20
# Should see: "Found N chats, checking first 5"
```

**Note:** The WhatsApp session persists across PC restarts. You only need to re-auth if:
- You manually remove a linked device in WhatsApp
- Session is inactive for 14+ days
- Browser profile gets corrupted

### 8.7 Update Code on Cloud (Manual)

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
cd /opt/personal-ai-employee
git pull origin main
pip install -r requirements.txt   # if dependencies changed
pm2 restart all
```

> The `git_sync_cloud` PM2 process does this automatically every 5 minutes.

---

## 9. Troubleshooting

### WhatsApp Watcher Not Replying

```bash
pm2 logs whatsapp_watcher --lines 50
```

| Log message | Cause | Fix |
|-------------|-------|-----|
| `QR code` / `Scan` | Session expired | Re-authenticate (Section 8.5) |
| `This site can't be reached` | No internet | Check VM network |
| `Update Chrome` | Wrong user-agent | Check UA spoof in `_make_browser()` |
| `BrowserType.launch: ...lock` | Chrome already open | `pkill chromium` then restart |
| `Thanks for your message!` | Fallback reply | Check `ANTHROPIC_API_KEY` |
| `Module 'anthropic' not found` | Not installed | `venv/bin/pip install anthropic` |
| Killed (exit 137) | Out of memory | Stop other PM2 processes first |

### Chrome Lock Conflict

If two processes fight over the same Chrome profile:

```bash
# Kill any stale chrome processes
pkill -f chromium
rm -f /tmp/whatsapp_browser.lock

# Restart
pm2 restart whatsapp_watcher
```

### PM2 Process Keeps Restarting

```bash
pm2 logs <name> --lines 100 --nostream  # check the error
pm2 show <name>                          # see restart count
```

If restart count is high, stop it and fix the underlying error:

```bash
pm2 stop <name>
# fix the issue
pm2 start <name>
```

### PM2 v6 + WSL2: "Is a directory" / "cannot execute binary file"

**Symptom:** Logs show `/usr/bin/bash: line 1: /mnt/d/gov: Is a directory`

**Cause:** PM2 v6 on WSL2 doesn't quote paths with spaces. The project path `/mnt/d/gov ai code/...`
gets split at the space — bash sees `/mnt/d/gov` (a directory) instead of the script.

**Fix:** Always use the trampoline scripts and `pm2.local.json`:

```bash
# Wrong — will fail:
pm2 start ecosystem.config.local.js

# Correct:
pm2 start pm2.local.json

# Or start individually using the trampoline scripts:
pm2 start ~/pai_agent.sh --name local_approval_handler
pm2 start ~/pai_whatsapp.sh --name whatsapp_watcher_local
```

If trampolines don't exist yet (new machine):
```bash
cat > ~/pai_agent.sh << 'EOF'
#!/bin/bash
PROJECT="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
exec bash "$PROJECT/scripts/run_local_agent.sh"
EOF
cat > ~/pai_whatsapp.sh << 'EOF'
#!/bin/bash
PROJECT="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
exec bash "$PROJECT/scripts/pm2_whatsapp_wrapper.sh"
EOF
chmod +x ~/pai_agent.sh ~/pai_whatsapp.sh
```

### WhatsApp AI Replies Are Generic ("Qasim is currently busy")

**Cause:** `CLAUDE_API_KEY` is in `.env` but the watcher expects `ANTHROPIC_API_KEY`.
The wrapper script `scripts/pm2_whatsapp_wrapper.sh` maps one to the other automatically.

**Check:**
```bash
pm2 logs whatsapp_watcher_local --lines 20
# Look for: "Claude API error: Could not resolve authentication method"
```

**Fix:** Confirm `.env` has `CLAUDE_API_KEY=sk-ant-...` set, then restart:
```bash
pm2 restart whatsapp_watcher_local
```

### Check VM Memory

```bash
free -h          # RAM usage
df -h            # Disk usage
pm2 monit        # Live CPU + RAM per process
```

If RAM is low (< 200MB free), Chrome may get OOM-killed:

```bash
# Temporarily stop non-essential processes
pm2 stop cloud_orchestrator git_sync_cloud
# Run whatsapp_watcher alone
pm2 restart whatsapp_watcher
# Restart others after watcher is stable
pm2 start cloud_orchestrator git_sync_cloud
```

### SSH Connection Issues

```bash
# Test connection
ssh -o ConnectTimeout=10 -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 "echo ok"

# If timeout: VM may be stopped in Oracle Console
# Start it at: cloud.oracle.com → Compute → Instances
```

### Claude API Errors

```bash
# Verify key is set
ssh ubuntu@129.151.151.212 "grep ANTHROPIC /opt/personal-ai-employee/.env.cloud"

# Test API directly
python3 -c "import anthropic; c=anthropic.Anthropic(); print(c.models.list())"
```

---

## 10. Viewing Logs — PM2 & Cloud

### 10.1 PM2 Logs (All Processes)

```bash
# Live tail — all processes combined
pm2 logs

# Live tail — one process only
pm2 logs whatsapp_watcher
pm2 logs cloud_orchestrator
pm2 logs git_sync_cloud
pm2 logs local_approval_handler

# Last N lines then exit (no live tail)
pm2 logs whatsapp_watcher --lines 100 --nostream

# Last 50 lines, show errors only
pm2 logs whatsapp_watcher --lines 50 --nostream --err

# Clear / flush all logs
pm2 flush

# Clear logs for one process
pm2 flush whatsapp_watcher
```

### 10.2 PM2 Log File Locations

PM2 saves logs as files on disk. You can read them directly:

```bash
# Cloud VM log files
~/.pm2/logs/whatsapp-watcher-out.log    # stdout (normal output)
~/.pm2/logs/whatsapp-watcher-error.log  # stderr (errors)
~/.pm2/logs/cloud_orchestrator-out.log
~/.pm2/logs/cloud_orchestrator-error.log
~/.pm2/logs/git_sync_cloud-out.log
~/.pm2/logs/git_sync_cloud-error.log

# Local machine log files (defined in ecosystem.config.local.js)
vault/Logs/Local/pm2_out.log
vault/Logs/Local/pm2_error.log
```

Read log files directly via SSH (no need to log in interactively):

```bash
# Last 50 lines of watcher output remotely
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "tail -50 ~/.pm2/logs/whatsapp-watcher-out.log"

# Watch live (like `tail -f`) over SSH
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "tail -f ~/.pm2/logs/whatsapp-watcher-out.log"

# Last 30 lines of errors
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "tail -30 ~/.pm2/logs/whatsapp-watcher-error.log"
```

### 10.3 Filter Logs for Useful Info

```bash
# See only replies sent (💬 lines)
pm2 logs whatsapp_watcher --lines 200 --nostream | grep "💬"

# See only unread messages detected
pm2 logs whatsapp_watcher --lines 200 --nostream | grep "📩"

# See only errors
pm2 logs whatsapp_watcher --lines 200 --nostream | grep -i "error\|fail\|exception"

# See only Claude API calls
pm2 logs whatsapp_watcher --lines 200 --nostream | grep "anthropic.com"

# See auth / login events
pm2 logs whatsapp_watcher --lines 200 --nostream | grep -i "login\|auth\|QR\|logged"
```

### 10.4 Vault Logs (WhatsApp Reply Records)

Every WhatsApp reply is also logged to the Obsidian vault:

```bash
# Local vault
ls vault/Done/WhatsApp/
cat vault/Done/WhatsApp/MANUAL_WHATSAPP_*.md

# Cloud vault (via SSH)
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "ls /opt/personal-ai-employee/vault/Done/WhatsApp/ | tail -10"
```

### 10.5 PM2 Live Dashboard

For a full live CPU + memory + logs dashboard:

```bash
pm2 monit
```

Shows all processes in a terminal UI with:
- CPU % per process
- Memory per process
- Live log tail
- Process uptime and restart count

### 10.6 One-Shot Remote Log Check

Quick command to check everything from your local machine without a full SSH session:

```bash
# All process status + last 20 watcher lines
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "pm2 list --no-color && echo '---WATCHER---' && pm2 logs whatsapp_watcher --lines 20 --nostream --no-color 2>&1 | tail -20"
```

### 10.7 Verify git_sync Auto-Pull is Working

`git_sync_cloud` now pulls code from GitHub every 60 seconds automatically.
You do NOT need to SSH and `git pull` manually anymore.

**How to check:**

```bash
# SSH into VM and check git_sync logs
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
  "grep 'Code pull\|Code fetch\|Code merge' ~/.pm2/logs/git_sync_cloud-error.log | tail -10"
```

**What the log messages mean:**

| Log message | Meaning |
|---|---|
| `✅ Code pull: Updating abc123..def456` | New code was pulled from GitHub — lists which files changed |
| `✅ Code pull: Fast-forward` | Same as above (fast-forward merge) |
| *(no Code pull line)* | No new code on GitHub — `Already up to date` (normal, silent) |
| `⚠️ Code fetch failed: ...` | Network issue — will retry next cycle (60s) |
| `⚠️ Code merge skipped: ...` | Local commits diverged — rare, check manually |

**Expected flow after you push new code:**
1. You push from local: `git push origin main`
2. Within 60 seconds, cloud VM git_sync logs: `✅ Code pull: Updating ... 3 files changed`
3. **Then restart the affected PM2 process** so it picks up the new code in memory:
   ```bash
   ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212 \
     "pm2 restart whatsapp_watcher --update-env"
   ```
   > Note: git_sync pulls code to disk automatically, but PM2 processes run from memory.
   > They only load the new code when restarted. You need to restart after a code deploy.

**Why we had to manually pull once (history):**
The git_sync HTTPS-pull feature was itself the fix for the broken sync. Since git_sync
couldn't pull before being fixed, we had to manually `git pull` once to deploy the fix.
After that first manual pull, everything is automatic.

---

## Quick Reference Card

```bash
# ── CLOUD SSH ───────────────────────────────────────────
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212

# ── CHECK EVERYTHING ─────────────────────────────────────
pm2 list

# ── LOGS (live) ──────────────────────────────────────────
pm2 logs                              # all
pm2 logs whatsapp_watcher             # WhatsApp only

# ── RESTART ──────────────────────────────────────────────
pm2 restart all                       # everything
pm2 restart whatsapp_watcher          # WhatsApp only

# ── RE-AUTH WHATSAPP ─────────────────────────────────────
pm2 stop whatsapp_watcher
pm2 start scripts/wa_reauth.py --name wa_auth --interpreter venv/bin/python --no-autorestart
pm2 logs wa_auth   # watch for PAIRING CODE, enter on phone
pm2 delete wa_auth

# ── UPDATE CODE ──────────────────────────────────────────
git pull && pm2 restart all

# ── SAVE STATE ───────────────────────────────────────────
pm2 save
```
