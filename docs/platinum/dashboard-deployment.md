# Next.js Dashboard — Deployment & Operations Guide

**URL**: `http://129.151.151.212:3000`
**Server**: Oracle Cloud VM (`ubuntu@129.151.151.212`)
**Process Manager**: PM2 (`nextjs_dashboard`, id: 17)
**Auto-Deploy**: GitHub Actions on every push to `main`

---

## How Auto-Deploy Works

```
You push code to GitHub (main branch)
        ↓
GitHub Actions triggers (only if nextjs_dashboard/ files changed)
        ↓
GitHub's server (7GB RAM, Ubuntu) runs:
  1. npm install
  2. npm run build   ← done on GitHub's server, NOT Oracle VM
  3. rsync .next/ → Oracle VM via SSH
  4. git pull on Oracle VM
  5. pm2 restart nextjs_dashboard
        ↓
Dashboard updated at http://129.151.151.212:3000
```

> **Why build on GitHub and not Oracle VM?**
> Oracle VM has 1GB RAM — Next.js Turbopack build needs 2GB+.
> GitHub Actions runners have 7GB RAM and are fast (~2 min build).

---

## Daily Operations

### Check Dashboard Status (SSH in first)

```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
```

```bash
pm2 list                          # see all processes + health
pm2 status                        # same, compact view
```

**Expected output:**
```
│ 17 │ nextjs_dashboard │ fork │ online │ 0% │ ~14mb │
```

---

### Check Logs

```bash
# Live tail (press Ctrl+C to stop)
pm2 logs nextjs_dashboard

# Last N lines then live tail
pm2 logs nextjs_dashboard --lines 50

# Only error logs
pm2 logs nextjs_dashboard --err --lines 30

# Only output logs (normal activity)
pm2 logs nextjs_dashboard --out --lines 30
```

**Log files location on VM:**
```
~/.pm2/logs/nextjs-dashboard-out.log    ← normal activity (requests, startup)
~/.pm2/logs/nextjs-dashboard-error.log  ← errors only
```

### What You'll See in Logs

| Action | Log line |
|--------|----------|
| Dashboard start | `✓ Ready in 8s` |
| User login | `GET /api/auth/session 200` |
| AI Generate button | `POST /api/ai-generate 200` |
| Create task | `POST /api/tasks/create 200` |
| Send email | `POST /api/email/send 200` |
| LinkedIn post | `POST /api/linkedin/post 200` |
| Error | Shows in red in error log |

---

### Restart Dashboard

```bash
pm2 restart nextjs_dashboard    # restart
pm2 reload nextjs_dashboard     # zero-downtime reload
```

### Verify Dashboard is Responding

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
# Should return: 200
```

---

## Deploy Code Changes

### Automatic (recommended)

1. Make code changes locally
2. Tell Claude: **"push and merge"**
3. Claude commits + pushes to GitHub
4. GitHub Actions auto-deploys in ~3 minutes
5. Watch progress: `github.com/Psqasim/personal-ai-employee → Actions tab`

### Manual Deploy (if needed)

```bash
# From your local PC (WSL2)
bash deployment/oracle/deploy_dashboard.sh
```

This script:
1. Pulls latest code on Oracle VM
2. Builds locally (fast, uses your PC RAM)
3. Rsyncs `.next/` to Oracle VM
4. Restarts PM2

---

## GitHub Actions Secrets (one-time setup)

Go to: `github.com/Psqasim/personal-ai-employee → Settings → Secrets → Actions`

| Secret Name | Description |
|-------------|-------------|
| `ORACLE_SSH_KEY` | Content of `~/.ssh/ssh-key-2026-02-17.key` (full RSA private key) |
| `NEXTAUTH_SECRET` | NextAuth secret from `.env.local` |

---

## Environment Variables on Oracle VM

File: `/opt/personal-ai-employee/nextjs_dashboard/.env.local`

```bash
NEXTAUTH_SECRET=...
NEXTAUTH_URL=http://129.151.151.212:3000
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_AUTHOR_URN=urn:li:person:...
SMTP_HOST=smtp.gmail.com
SMTP_USER=...
ODOO_URL=https://personal-ai-employee2.odoo.com
ODOO_USER=...
AUTH_TRUST_HOST=true          ← required for IP-based access (no domain)
```

> **`AUTH_TRUST_HOST=true`** — NextAuth requires this when accessed via IP address
> instead of a domain name. Without it: `UntrustedHost` error.

---

## Firewall (Two Layers)

Oracle VM has **two** firewall layers — both must allow port 3000:

| Layer | Where | Status |
|-------|-------|--------|
| UFW (OS firewall) | Inside VM | ✅ Port 3000 open |
| Oracle Security List | Oracle Cloud Console → Networking → VCN → Security Lists | ✅ Port 3000 open |

**To open a new port in UFW (inside VM):**
```bash
sudo ufw allow 3000/tcp
sudo ufw status
```

**To open a new port in Oracle Security List:**
> Oracle Cloud Console → Networking → Virtual Cloud Networks → VCN → Security Lists → Default → Add Ingress Rule
> Source: `0.0.0.0/0` | Protocol: TCP | Port: `3000`

---

## Troubleshooting

### Dashboard not loading externally (timeout)
1. Check UFW: `sudo ufw status` — port 3000 should be listed
2. Check Oracle Security List — port 3000 ingress rule must exist
3. Check PM2: `pm2 list` — `nextjs_dashboard` should be `online`

### `UntrustedHost` error in logs
```
[auth][error] UntrustedHost: Host must be trusted
```
**Fix**: Add `AUTH_TRUST_HOST=true` to `.env.local`, then:
```bash
pm2 restart nextjs_dashboard --update-env
```

### PM2 process `errored` or `stopped`
```bash
pm2 logs nextjs_dashboard --err --lines 30   # check what went wrong
pm2 restart nextjs_dashboard                  # try restart
```

### Dashboard returns 500 error
```bash
pm2 logs nextjs_dashboard --lines 50   # look for error message
# Common causes: missing env var, API key expired, Odoo unreachable
```

### GitHub Actions failed (red)
1. Go to `Actions` tab on GitHub → click the failed run
2. Expand the failed step to see error
3. Common issues:
   - SSH key secret wrong → re-add `ORACLE_SSH_KEY` secret
   - Oracle VM unreachable → check VM is running in Oracle Console
   - Build error → check `npm run build` locally first

---

## PM2 Cheat Sheet

```bash
pm2 list                          # list all processes
pm2 logs nextjs_dashboard         # live logs
pm2 logs nextjs_dashboard --lines 50  # last 50 lines
pm2 restart nextjs_dashboard      # restart
pm2 stop nextjs_dashboard         # stop
pm2 start nextjs_dashboard        # start
pm2 save                          # save process list (survives reboot)
pm2 flush                         # clear all log files
```

---

**Dashboard live at: `http://129.151.151.212:3000`**
