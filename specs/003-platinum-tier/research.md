# Research: Platinum Tier Architecture Decisions

**Feature**: 003-platinum-tier | **Date**: 2026-02-15
**Purpose**: Resolve all "NEEDS CLARIFICATION" items from Technical Context before Phase 1 design

---

## 1. Deployment Strategy: Next.js Dashboard

### Decision

**Self-hosted on Local Agent** (port 3000, accessible via localhost and local network)

### Rationale

- **Local-first architecture alignment**: Dashboard runs on same machine as Local Agent (vault authority)
- **Zero deployment cost**: No Vercel subscription, no cloud hosting fees
- **Instant vault access**: Next.js API routes read vault markdown files directly via filesystem (no API layer needed)
- **Security**: Dashboard only accessible on local network (no public exposure of approval workflow)
- **Mobile access**: Users can access via `http://{local_ip}:3000` from phone on same WiFi
- **PM2 integration**: Dashboard runs as PM2 process alongside local_orchestrator and whatsapp_watcher

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **Vercel deployment** | Easy deploy, CDN, auto-scaling | Requires vault API layer, $20/month Pro plan for private repos, public exposure | Breaks local-first principle, adds cost, requires API gateway |
| **Cloud VM deployment** | Always accessible remotely | Requires vault sync to cloud, breaks Local Agent authority, security risk | Cloud Agent should NOT approve (security partition) |
| **Expose localhost via ngrok** | Quick mobile access, free tier | Unstable URLs, session timeouts, security risk | Not production-ready, unreliable |

### Implementation Notes

- **Next.js start**: `npm run dev` for development, `npm run build && npm start` for production
- **PM2 config**: Add `nextjs_dashboard` process to `ecosystem.config.local.js`
- **Port**: Default 3000, configurable via `PORT` in .env.local
- **Local network access**: Users find Local Agent IP (`ifconfig` or `ipconfig`), access `http://192.168.x.x:3000` from mobile
- **Offline support**: Next.js static offline page cached via service worker (optional Phase 2 enhancement)

---

## 2. Database Selection: Dashboard State

### Decision

**No database** (read vault markdown files directly)

### Rationale

- **Simplicity**: Vault is already the source of truth; adding DB duplicates data
- **Real-time accuracy**: Always reads latest vault state (no sync lag between vault and DB)
- **Zero deployment overhead**: No PostgreSQL/SQLite installation, no schema migrations
- **Performance sufficient**: Reading 100 pending approval markdown files <500ms (vault size <500MB)
- **Stateless API**: Dashboard API routes are pure functions (read vault → return JSON)

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **SQLite** | Fast queries, indexed search, 1-file database | Requires vault→DB sync, schema migrations, potential sync lag | Adds unnecessary complexity when vault read is fast enough |
| **PostgreSQL** | Full SQL, production-grade | Heavy deployment, requires Docker/service, overkill for read-only dashboard | Over-engineered for simple file reads |
| **Redis cache** | Sub-millisecond reads | Requires Redis server, cache invalidation complexity | Vault read performance already meets <500ms requirement |

### Implementation Notes

- **API route pattern**:
  ```typescript
  // app/api/status/route.ts
  import { readVaultFolder } from '@/lib/vault';
  export async function GET() {
    const pending = await readVaultFolder('vault/Pending_Approval');
    return Response.json({ count: pending.length, files: pending });
  }
  ```
- **Vault read utility** (`lib/vault.ts`): Filesystem read + YAML frontmatter parse via `gray-matter` library
- **Caching** (optional): In-memory cache with 5s TTL for frequently polled endpoints (micro-optimization, not MVP)
- **Performance test**: Verify 10,000 markdown files read <500ms on target hardware

---

## 3. Real-Time Updates: Dashboard Live Data

### Decision

**HTTP polling every 5 seconds** (via `setInterval` + fetch `/api/status`)

### Rationale

- **Simplicity**: Standard fetch API, no WebSocket server setup, no connection state management
- **Acceptable latency**: 5s polling meets NFR-P-PERF-003 (<500ms API response), user sees update within 5s
- **Stateless**: No persistent connections to manage, no reconnection logic
- **Works with PM2 restart**: Dashboard reconnects automatically on next poll (no manual reconnect)
- **Mobile friendly**: HTTP polling survives mobile browser backgrounding better than WebSockets

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **WebSockets** | True real-time (<1s latency), push updates instantly | Requires ws server, connection state management, reconnection logic on PM2 restart | Over-engineered for 5s latency requirement |
| **Server-Sent Events (SSE)** | Simpler than WebSockets, one-way push | Requires persistent HTTP connection, browser connection limits | Still requires connection management complexity |
| **10s polling** | Lower server load | 10s latency feels slow for approval workflow | 5s is good balance (acceptable latency + low load) |

### Implementation Notes

- **Client-side polling**:
  ```typescript
  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch('/api/status');
      const data = await res.json();
      setState(data);
    }, 5000); // 5 seconds
    return () => clearInterval(interval);
  }, []);
  ```
- **API response caching**: Add `Cache-Control: no-cache` to prevent stale data
- **Error handling**: On fetch failure, retry after 10s (exponential backoff)
- **Pause polling when tab inactive** (optional): Use `document.visibilityState` to pause when tab hidden

---

## 4. Authentication Strategy: Dashboard Security

### Decision

**Simple password authentication** (bcrypt-hashed password in .env, session cookie)

### Rationale

- **Local-only access**: Dashboard on localhost, low security risk (attacker needs physical/network access)
- **Single-user system**: Personal AI Employee is single-user by design (no multi-user auth needed)
- **Simple setup**: User sets `DASHBOARD_PASSWORD` in .env, no OAuth configuration
- **Optional**: `NEXT_AUTH_ENABLED=false` disables auth for fully trusted local network
- **Session persistence**: Cookie-based session (7-day expiry) avoids re-login on every visit

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **NextAuth.js (credentials)** | Full auth framework, session management, callbacks | Overkill for single-user, adds dependency weight, complex config | Over-engineered for simple password gate |
| **OAuth2 (Google)** | Secure delegated auth | Requires Google Cloud project, OAuth flow, internet dependency | Breaks local-first, requires internet to log in |
| **No authentication** | Zero complexity | Security risk if Local Agent IP exposed on network | Rejected for default, but offered as `NEXT_AUTH_ENABLED=false` option |
| **Token-based (JWT)** | Stateless auth | Requires token refresh logic, secure token storage | More complex than cookie session for single-user |

### Implementation Notes

- **Login page** (`app/login/page.tsx`):
  ```typescript
  const handleLogin = async (password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    if (res.ok) router.push('/');
  };
  ```
- **Password validation** (`app/api/auth/login/route.ts`):
  ```typescript
  import bcrypt from 'bcrypt';
  const isValid = await bcrypt.compare(password, process.env.DASHBOARD_PASSWORD_HASH);
  if (isValid) {
    cookies().set('session', generateSessionToken(), { maxAge: 7 * 24 * 60 * 60 }); // 7 days
  }
  ```
- **Middleware** (`middleware.ts`): Redirect unauthenticated requests to `/login`
- **Setup**: User runs `npm run hash-password` script to generate bcrypt hash for .env
- **Disable auth**: Set `NEXT_AUTH_ENABLED=false` to skip login page entirely

---

## 5. Git Sync Strategy: Commit Frequency

### Decision

**Batched commits every 60 seconds** (Git sync cycle: add all changes → commit → push/pull)

### Rationale

- **Reduces commit noise**: Avoids 100+ commits/day for every single file change
- **Atomic batches**: Each commit contains all changes from 60s window (easier rollback)
- **Git performance**: Fewer commits = smaller .git/ directory, faster git log
- **Meets latency requirement**: 60s sync interval → max 2min delay (Cloud drafts, Local pulls after 60s + 60s) is acceptable for email/social workflow
- **Audit trail**: Each commit message lists all files changed: `Cloud: 3 email drafts, 1 LinkedIn post, Dashboard update`

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **Auto-commit every file change** | Zero latency (instant sync) | Hundreds of commits/day, huge .git/ directory, Git log noise | Degrades Git performance, clutters history |
| **Manual commit triggers** | User controls when to sync | Requires user action, defeats 24/7 autonomy | Breaks Platinum autonomous operation |
| **5-minute batches** | Even fewer commits | 5min latency too slow for urgent email drafts | Violates NFR-P-PERF-001 (email draft <15s + sync <10s + pull <10s = 35s acceptable, 5min not) |

### Implementation Notes

- **Cloud Agent Git sync** (`cloud_agent/src/git_sync.py`):
  ```python
  def sync_cloud_to_remote():
      repo = git.Repo(VAULT_PATH)
      repo.git.add('.')
      changed_files = repo.index.diff('HEAD')
      if changed_files:
          summary = summarize_changes(changed_files)  # "3 email drafts, 1 LinkedIn post"
          repo.index.commit(f"Cloud: {summary}")
          repo.remote('origin').push()
  ```
- **Local Agent Git sync** (`local_agent/src/git_sync.py`):
  ```python
  def sync_remote_to_local():
      repo = git.Repo(VAULT_PATH)
      repo.remote('origin').pull(rebase=True)  # Rebase to avoid merge commits
      # Auto-resolve conflicts (Dashboard.md: accept Cloud /Updates/, keep Local main)
      resolve_conflicts_if_any(repo)
  ```
- **Conflict resolution**: Local Agent detects merge conflicts in `Dashboard.md`, auto-resolves via custom merge driver:
  - Cloud owns `/## Updates/` section (timestamped status messages)
  - Local owns main content (task table, statistics)
  - Log conflicts to `vault/Logs/Local/git_conflicts.md`
- **Failure handling**: On Git push/pull failure, retry 3x (10s, 30s, 90s backoff), queue to `vault/.git_queue/pending_ops.md`

---

## 6. Odoo Deployment: 24/7 Cloud Setup

### Decision

**Odoo Community 19+ on Oracle VM** (systemd service, Nginx HTTPS reverse proxy, PostgreSQL backend)

### Rationale

- **24/7 availability**: Cloud VM always-on, Odoo accessible from anywhere via HTTPS
- **Free infrastructure**: Oracle Cloud Free Tier (ARM VM) sufficient for single-user Odoo
- **Self-hosted control**: No Odoo SaaS fees ($24/user/month), full database access for backups
- **Integration-ready**: Odoo JSON-RPC API for draft invoice/expense creation
- **Production-grade**: systemd watchdog auto-restarts Odoo on crash, Nginx handles SSL termination

### Odoo Installation Steps (Ubuntu 22.04)

1. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx certbot python3-certbot-nginx
   ```

2. **Install Odoo**:
   ```bash
   sudo wget -O- https://nightly.odoo.com/odoo.key | sudo gpg --dearmor -o /usr/share/keyrings/odoo-archive-keyring.gpg
   echo 'deb [signed-by=/usr/share/keyrings/odoo-archive-keyring.gpg] https://nightly.odoo.com/19.0/nightly/deb/ ./' | sudo tee /etc/apt/sources.list.d/odoo.list
   sudo apt update
   sudo apt install -y odoo
   ```

3. **Configure PostgreSQL**:
   ```bash
   sudo -u postgres createuser -s odoo
   sudo -u postgres createdb platinum_business -O odoo
   ```

4. **Configure Odoo** (`/etc/odoo/odoo.conf`):
   ```ini
   [options]
   admin_passwd = strong_master_password
   db_host = localhost
   db_port = 5432
   db_user = odoo
   db_password = False
   addons_path = /usr/lib/python3/dist-packages/odoo/addons
   ```

5. **Setup systemd service** (already included in Odoo package, verify `/etc/systemd/system/odoo.service`):
   ```ini
   [Unit]
   Description=Odoo
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=odoo
   ExecStart=/usr/bin/odoo -c /etc/odoo/odoo.conf
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

6. **Enable and start Odoo**:
   ```bash
   sudo systemctl enable odoo
   sudo systemctl start odoo
   ```

7. **Configure Nginx reverse proxy** (`/etc/nginx/sites-available/odoo`):
   ```nginx
   server {
       listen 80;
       server_name odoo.yourdomain.com;  # Or VM public IP

       location / {
           proxy_pass http://127.0.0.1:8069;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. **Enable Nginx site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

9. **Setup Let's Encrypt SSL**:
   ```bash
   sudo certbot --nginx -d odoo.yourdomain.com
   ```

10. **Setup daily backups** (`/etc/cron.daily/odoo-backup`):
    ```bash
    #!/bin/bash
    BACKUP_DIR="/opt/odoo_backups"
    DATE=$(date +%Y-%m-%d)
    sudo -u postgres pg_dump platinum_business | gzip > "$BACKUP_DIR/odoo_db_$DATE.sql.gz"
    find "$BACKUP_DIR" -name "odoo_db_*.sql.gz" -mtime +30 -delete  # Keep 30 days
    ```

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **Odoo SaaS** | Zero setup, managed updates | $24/user/month, no API access on free tier | Monthly cost, limited API |
| **Docker Odoo** | Easy deployment, version pinning | Requires Docker, more complex restart logic | systemd service simpler, better Oracle VM integration |
| **Local Odoo only** | No cloud costs | Not accessible 24/7, Cloud Agent can't draft entries | Violates Platinum 24/7 requirement |

### Implementation Notes

- **Health monitoring**: Cloud Agent polls `https://odoo.yourdomain.com/web/health` every 5min
- **Backup verification**: Weekly backup restore test (restore to temp DB, verify tables exist)
- **SSL renewal**: Certbot auto-renewal via cron (`certbot renew --quiet`)
- **Odoo MCP integration**: Local Agent calls Odoo JSON-RPC API to create draft invoices (state="draft", never post)

---

## 7. PM2 Configuration: Process Management

### Decision

**PM2 ecosystem files** (separate configs for Cloud and Local, systemd startup hooks)

### PM2 Ecosystem Config Pattern

**Cloud Agent** (`deployment/pm2/ecosystem.config.cloud.js`):
```javascript
module.exports = {
  apps: [
    {
      name: 'cloud_orchestrator',
      script: 'cloud_agent/src/orchestrator.py',
      interpreter: 'python3',
      cwd: '/opt/personal-ai-employee',
      env: {
        PYTHONPATH: '/opt/personal-ai-employee',
        ENV_FILE: '.env.cloud',
      },
      autorestart: true,
      max_restarts: 10,
      min_uptime: 5000,  // 5s min uptime before restart counted
      restart_delay: 1000,  // 1s delay between restarts
      error_file: '~/.pm2/logs/cloud_orchestrator-error.log',
      out_file: '~/.pm2/logs/cloud_orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'gmail_watcher',
      script: 'cloud_agent/src/watchers/gmail_watcher.py',
      interpreter: 'python3',
      cwd: '/opt/personal-ai-employee',
      autorestart: true,
      max_restarts: 10,
    },
    {
      name: 'git_sync_cloud',
      script: 'cloud_agent/src/git_sync.py',
      interpreter: 'python3',
      cwd: '/opt/personal-ai-employee',
      autorestart: true,
    },
  ],
};
```

**Local Agent** (`deployment/pm2/ecosystem.config.local.js`):
```javascript
module.exports = {
  apps: [
    {
      name: 'local_orchestrator',
      script: 'local_agent/src/orchestrator.py',
      interpreter: 'python3',
      cwd: '/path/to/personal-ai-employee',
      env: {
        PYTHONPATH: '/path/to/personal-ai-employee',
        ENV_FILE: '.env.local',
      },
      autorestart: true,
      max_restarts: 10,
      min_uptime: 5000,
      restart_delay: 1000,
    },
    {
      name: 'whatsapp_watcher',
      script: 'local_agent/src/watchers/whatsapp_watcher.py',
      interpreter: 'python3',
      cwd: '/path/to/personal-ai-employee',
      autorestart: true,
      max_restarts: 10,
    },
    {
      name: 'git_sync_local',
      script: 'local_agent/src/git_sync.py',
      interpreter: 'python3',
      cwd: '/path/to/personal-ai-employee',
      autorestart: true,
    },
    {
      name: 'nextjs_dashboard',
      script: 'npm',
      args: 'start',
      cwd: '/path/to/personal-ai-employee/nextjs_dashboard',
      autorestart: true,
      max_restarts: 10,
      env: {
        PORT: 3000,
        NODE_ENV: 'production',
      },
    },
  ],
};
```

### PM2 Commands

- **Start all processes**: `pm2 start ecosystem.config.cloud.js` (on Cloud VM) or `pm2 start ecosystem.config.local.js` (on Local)
- **List processes**: `pm2 list`
- **View logs**: `pm2 logs cloud_orchestrator`
- **Restart single process**: `pm2 restart gmail_watcher`
- **Stop all**: `pm2 stop all`
- **Save process list**: `pm2 save` (freezes current process list for startup)
- **Setup systemd startup**: `pm2 startup systemd` (generates systemd service), then `sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME`

### Log Rotation

PM2 log module (`pm2 install pm2-logrotate`):
```bash
pm2 set pm2-logrotate:max_size 10M       # Rotate at 10MB
pm2 set pm2-logrotate:retain 10          # Keep 10 rotated files
pm2 set pm2-logrotate:compress true      # Gzip old logs
```

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **systemd services directly** | Native Linux init, no PM2 dependency | Requires separate .service file per process, no unified dashboard | PM2 provides better process monitoring UI (pm2 list) |
| **Supervisor** | Python-native process manager | Less popular than PM2, no Node.js integration | PM2 better for Next.js dashboard integration |
| **Docker Compose** | Containerized processes | Requires Docker, more deployment complexity | systemd + PM2 simpler on Oracle VM |

### Implementation Notes

- **Health monitoring**: PM2 reports CPU/memory per process via `pm2 list` or `pm2 jlist` (JSON)
- **Alerts**: Optional PM2 webhook (`PM2_WEBHOOK_URL` in .env) sends alerts on crash
- **Graceful shutdown**: Processes handle `SIGTERM` for clean shutdown (save state before exit)

---

## 8. WhatsApp Notifications: Cloud → User

### Decision

**Playwright automation of WhatsApp Web** (send message via browser automation)

### Rationale

- **No WhatsApp Business API required**: WhatsApp Business API costs $0.005-$0.09 per message (not free tier)
- **Personal WhatsApp account**: Works with user's existing WhatsApp number (no business account setup)
- **Session persistence**: Playwright saves WhatsApp Web session to disk (no QR scan on every restart)
- **Proven pattern**: WhatsApp watcher (Gold tier) already uses Playwright for receiving messages; sending is same pattern

### Playwright Send Implementation

**Pseudocode** (`cloud_agent/src/notifications/whatsapp_notifier.py`):
```python
from playwright.sync_api import sync_playwright

def send_whatsapp_notification(recipient_number: str, message: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=WHATSAPP_SESSION_PATH)
        page = context.new_page()

        # Navigate to WhatsApp Web chat
        page.goto(f'https://web.whatsapp.com/send?phone={recipient_number}&text={message}')

        # Wait for chat to load
        page.wait_for_selector('div[contenteditable="true"][data-tab="10"]', timeout=10000)

        # Click send button
        send_button = page.locator('button[aria-label="Send"]')
        send_button.click()

        # Wait for message to appear in chat (confirmation)
        page.wait_for_selector(f'span:has-text("{message[:20]}")', timeout=5000)

        browser.close()
```

### Session Setup (First Time)

1. **User scans QR code** on Local Agent (one-time setup):
   ```python
   browser = p.chromium.launch(headless=False)  # User sees browser
   page = browser.new_page()
   page.goto('https://web.whatsapp.com')
   input("Scan QR code, press Enter when logged in...")
   context.storage_state(path=WHATSAPP_SESSION_PATH)  # Save session
   ```

2. **Session file** (`WHATSAPP_SESSION_PATH = ~/.whatsapp_session.json`):
   - Contains cookies and localStorage for WhatsApp Web
   - Persists across restarts (no re-scan needed)
   - Valid for ~30 days (WhatsApp Web session expiry)

3. **Session expiry handling**:
   - Detect login screen: `page.locator('canvas[aria-label*="QR"]').is_visible()`
   - If detected, create `vault/Needs_Action/whatsapp_session_expired.md`, alert user to re-scan
   - Pause notifications until re-authenticated

### Notification Message Format

**Urgent Email Alert**:
```
⚠️ [URGENT] Email from John Doe
Subject: Project deadline tomorrow
AI drafted reply ready
Approve: http://192.168.1.100:3000/approvals/email/EMAIL_DRAFT_12345
Or check vault/Pending_Approval/Email/
```

**Critical Error Alert**:
```
🚨 [ERROR] Git sync failing
Cloud/Local agents out of sync for 5+ min
Check logs: vault/Logs/Cloud/errors.md
Action: Verify Git remote accessible
```

**Approval Summary** (Local Agent sends when coming online):
```
📋 Good morning! 5 items pending approval:
- 3 Email drafts
- 1 LinkedIn post
- 1 WhatsApp reply
Review: http://192.168.1.100:3000/approvals
```

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **WhatsApp Business API** | Official API, webhook support | Costs $0.005-$0.09/message, requires Meta Business account verification | Not free, complex setup |
| **Twilio WhatsApp** | Twilio integration, SMS fallback | Costs $0.005/message, sandbox limitations | Monthly costs add up |
| **Telegram Bot** | Free, simple API, no browser automation | User must use Telegram (not WhatsApp) | Platinum spec requires WhatsApp |
| **Email notifications** | Free, simple SMTP | User may not check email promptly | WhatsApp more immediate for mobile alerts |

### Implementation Notes

- **Rate limiting**: Max 1 notification per minute (avoid WhatsApp spam detection)
- **Retry logic**: If send fails (element not found, timeout), retry 2x (5s, 10s backoff)
- **Fallback**: On 3 failures, send email to `FALLBACK_EMAIL` instead
- **Cloud Agent only**: Only Cloud Agent sends WhatsApp notifications (Local Agent doesn't notify itself)
- **Security**: WhatsApp session file (`~/.whatsapp_session.json`) MUST be in .gitignore (never sync to Git)

---

## Summary: All Decisions Locked

| Decision Area | Choice | Key Rationale |
|---------------|--------|---------------|
| **Next.js Deployment** | Self-hosted on Local (port 3000) | Local-first, zero cost, instant vault access |
| **Database** | None (read vault directly) | Simplicity, vault is source of truth, fast enough |
| **Real-Time Updates** | HTTP polling (5s interval) | Simple, acceptable latency, stateless |
| **Authentication** | Simple password (bcrypt + cookie) | Single-user, local-only, optional disable |
| **Git Sync** | Batched commits (60s interval) | Atomic batches, reduces noise, meets latency req |
| **Odoo Deployment** | systemd service on Oracle VM | 24/7 availability, free infrastructure, production-grade |
| **PM2 Config** | Ecosystem files (Cloud + Local) | Unified process management, systemd startup, log rotation |
| **WhatsApp Notifications** | Playwright automation | Free, works with personal account, proven pattern |

**All unknowns resolved. Ready for Phase 1 design artifacts: data-model.md, contracts/, quickstart.md.**
