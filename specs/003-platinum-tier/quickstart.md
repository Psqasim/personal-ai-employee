# Quickstart: Platinum Tier Deployment Guide

**Feature**: 003-platinum-tier | **Version**: 1.0.0 | **Date**: 2026-02-15
**Target**: Deploy dual-agent architecture (Cloud VM + Local machine) with Next.js dashboard and Git vault sync

**Estimated Time**: 3-4 hours (Oracle VM setup: 1h, Odoo: 1h, Local setup: 1h, Git sync + dashboard: 1h)

---

## Prerequisites

### Cloud Infrastructure
- [ ] **Oracle Cloud Free Tier account** (ARM-based VM, 4 OCPU, 24GB RAM, 200GB storage)
  - Sign up: https://cloud.oracle.com/free
  - Verify: Email + phone verification complete
- [ ] **GitHub account** (for Git remote vault repository)
  - Private repository recommended for vault security

### Local Machine (User's Laptop)
- [ ] **Python 3.11+** installed (`python --version`)
- [ ] **Node.js 20+** installed (`node --version`)
- [ ] **Git** installed (`git --version`)
- [ ] **SSH key** generated (`~/.ssh/id_ed25519.pub`)
  - Generate if missing: `ssh-keygen -t ed25519 -C "your-email@example.com"`

### Gold Tier Verified
- [ ] **Gold tier fully functional** (email drafts, LinkedIn posts, WhatsApp drafts, plan execution, CEO Briefing)
- [ ] All Gold success criteria passing (SC-G001 through SC-G013)
- [ ] Vault structure validated (`vault/Inbox/`, `/Pending_Approval/`, `/Done/`, etc.)

---

## Phase 1: Cloud Agent Setup (Oracle VM)

### Step 1.1: Provision Oracle Cloud VM

1. **Log in to Oracle Cloud Console**: https://cloud.oracle.com

2. **Create Compute Instance**:
   - Navigate: Menu → Compute → Instances → Create Instance
   - Name: `personal-ai-employee-cloud`
   - Image: `Ubuntu 22.04 LTS` (ARM64)
   - Shape: `VM.Standard.A1.Flex` (4 OCPU, 24GB RAM — free tier)
   - VCN: Use default or create new
   - Public IP: Enable (assign public IP address)
   - SSH Keys: Upload `~/.ssh/id_ed25519.pub` (from local machine)

3. **Configure Security List** (allow inbound traffic):
   - SSH (port 22): 0.0.0.0/0
   - Odoo HTTPS (port 443): 0.0.0.0/0
   - Odoo HTTP (port 8069): 0.0.0.0/0 (temporary, redirect to 443 later)

4. **Note VM Public IP**: e.g., `129.80.x.x` (used for SSH and Odoo access)

5. **SSH into VM** (from local machine):
   ```bash
   ssh ubuntu@129.80.x.x
   ```

### Step 1.2: Install Dependencies on Cloud VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ (Ubuntu 22.04 has 3.10, upgrade if needed)
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install PM2 for process management
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Install PostgreSQL (for Odoo)
sudo apt install -y postgresql postgresql-contrib

# Install Nginx (for Odoo reverse proxy)
sudo apt install -y nginx certbot python3-certbot-nginx

# Verify installations
python3 --version  # Should be 3.10+ (or 3.11+ if upgraded)
node --version     # Should be v20.x
pm2 --version      # Should be latest
psql --version     # Should be 14+
```

### Step 1.3: Clone Repository on Cloud VM

```bash
# Clone repo to /opt/personal-ai-employee
sudo mkdir -p /opt/personal-ai-employee
sudo chown ubuntu:ubuntu /opt/personal-ai-employee
cd /opt
git clone git@github.com:user/personal-ai-employee.git
cd personal-ai-employee

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify agent_skills installed
python -c "import agent_skills; print('Agent skills OK')"
```

### Step 1.4: Configure Cloud Agent Environment

```bash
# Create .env.cloud (Cloud-only environment variables)
cat > .env.cloud <<'EOF'
# Platinum Cloud Agent Configuration

# Agent Identity
TIER=platinum
ENABLE_CLOUD_AGENT=true
CLOUD_AGENT_ID=cloud

# Vault Path (on Cloud VM)
VAULT_PATH=/opt/personal-ai-employee/vault

# Git Sync
GIT_REMOTE_URL=git@github.com:user/ai-employee-vault.git
GIT_BRANCH=main
GIT_SYNC_INTERVAL=60

# Claude API (Read-only)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# WhatsApp Notifications (Send-only, no session)
WHATSAPP_NOTIFICATION_NUMBER=+1234567890
FALLBACK_EMAIL=user@example.com

# Email Monitoring (Gmail API read-only)
GMAIL_API_CREDENTIALS=/opt/personal-ai-employee/credentials.json

# Security: No sensitive credentials on Cloud
# SMTP_PASSWORD, WHATSAPP_SESSION_PATH, BANK_API_TOKEN prohibited
# See .gitignore for excluded files

# Logging
LOG_LEVEL=INFO
EOF

# Secure .env.cloud
chmod 600 .env.cloud

# CRITICAL: Verify no sensitive credentials in .env.cloud
# Cloud Agent MUST NOT have: SMTP_PASSWORD, WHATSAPP_SESSION_PATH, BANK_API_TOKEN
```

### Step 1.5: Setup Git SSH Key on Cloud VM

```bash
# Generate SSH key for Git (Cloud VM)
ssh-keygen -t ed25519 -C "cloud-agent@oracle-vm" -f ~/.ssh/id_ed25519_cloud
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_cloud

# Add public key to GitHub
cat ~/.ssh/id_ed25519_cloud.pub
# Copy output, go to GitHub → Settings → SSH Keys → New SSH key → Paste

# Test Git SSH connection
ssh -T git@github.com
# Expected: "Hi user! You've successfully authenticated..."

# Configure Git identity
git config --global user.name "Cloud Agent"
git config --global user.email "cloud-agent@oracle-vm"
```

### Step 1.6: Initialize Vault on Cloud VM (from Git Remote)

```bash
# Clone vault repository (or create if first deployment)
cd /opt/personal-ai-employee
git clone git@github.com:user/ai-employee-vault.git vault

# OR if vault already exists on Local, skip clone (will pull in Phase 5)

# Verify vault structure
ls -la vault/
# Expected: Inbox/, Pending_Approval/, Done/, Logs/, Dashboard.md, Company_Handbook.md
```

### Step 1.7: Configure PM2 for Cloud Agent

```bash
# Create PM2 ecosystem config for Cloud processes
cat > /opt/personal-ai-employee/ecosystem.config.cloud.js <<'EOF'
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
      min_uptime: 5000,
      restart_delay: 1000,
      error_file: '/home/ubuntu/.pm2/logs/cloud_orchestrator-error.log',
      out_file: '/home/ubuntu/.pm2/logs/cloud_orchestrator-out.log',
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
EOF

# Start Cloud Agent processes
pm2 start ecosystem.config.cloud.js

# Verify all processes running
pm2 list
# Expected: cloud_orchestrator (online), gmail_watcher (online), git_sync_cloud (online)

# View logs
pm2 logs cloud_orchestrator

# Enable PM2 startup on VM reboot
pm2 startup systemd
# Follow output instructions (run sudo command)
pm2 save
```

---

## Phase 2: Odoo Community Deployment (Cloud VM)

### Step 2.1: Install Odoo 19+

```bash
# Add Odoo repository
wget -O- https://nightly.odoo.com/odoo.key | sudo gpg --dearmor -o /usr/share/keyrings/odoo-archive-keyring.gpg
echo 'deb [signed-by=/usr/share/keyrings/odoo-archive-keyring.gpg] https://nightly.odoo.com/19.0/nightly/deb/ ./' | sudo tee /etc/apt/sources.list.d/odoo.list

# Install Odoo
sudo apt update
sudo apt install -y odoo

# Create Odoo PostgreSQL database
sudo -u postgres createuser -s odoo
sudo -u postgres createdb platinum_business -O odoo
```

### Step 2.2: Configure Odoo

```bash
# Edit Odoo config
sudo nano /etc/odoo/odoo.conf

# Set the following:
[options]
admin_passwd = STRONG_MASTER_PASSWORD_HERE
db_host = localhost
db_port = 5432
db_user = odoo
db_password = False
addons_path = /usr/lib/python3/dist-packages/odoo/addons

# Enable and start Odoo service
sudo systemctl enable odoo
sudo systemctl start odoo
sudo systemctl status odoo  # Should show "active (running)"

# Verify Odoo accessible locally
curl http://localhost:8069
# Should return HTML (Odoo login page)
```

### Step 2.3: Configure Nginx Reverse Proxy for HTTPS

```bash
# Create Nginx config for Odoo
sudo nano /etc/nginx/sites-available/odoo

# Add the following (replace DOMAIN with your domain or VM public IP):
server {
    listen 80;
    server_name odoo.yourdomain.com;  # Or: 129.80.x.x

    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t  # Test config
sudo systemctl reload nginx

# Test Odoo via Nginx
curl http://odoo.yourdomain.com
```

### Step 2.4: Setup Let's Encrypt SSL

```bash
# Obtain SSL certificate (requires domain, skip if using IP only)
sudo certbot --nginx -d odoo.yourdomain.com

# OR if using IP address (self-signed cert):
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/odoo-selfsigned.key \
  -out /etc/ssl/certs/odoo-selfsigned.crt

# Update Nginx to use SSL (certbot auto-configures, or manually add):
sudo nano /etc/nginx/sites-available/odoo
# Add SSL directives (certbot does this automatically)

# Verify HTTPS
curl https://odoo.yourdomain.com
```

### Step 2.5: Setup Daily Odoo Backups

```bash
# Create backup directory
sudo mkdir -p /opt/odoo_backups
sudo chown ubuntu:ubuntu /opt/odoo_backups

# Create backup script
sudo nano /etc/cron.daily/odoo-backup

# Add the following:
#!/bin/bash
BACKUP_DIR="/opt/odoo_backups"
DATE=$(date +%Y-%m-%d)
sudo -u postgres pg_dump platinum_business | gzip > "$BACKUP_DIR/odoo_db_$DATE.sql.gz"
find "$BACKUP_DIR" -name "odoo_db_*.sql.gz" -mtime +30 -delete
echo "$(date): Backup completed" >> /var/log/odoo_backup.log

# Make executable
sudo chmod +x /etc/cron.daily/odoo-backup

# Test backup script
sudo /etc/cron.daily/odoo-backup
ls -lh /opt/odoo_backups/
```

---

## Phase 3: Local Agent Setup (User's Laptop)

### Step 3.1: Clone Repository on Local Machine

```bash
# Clone repo to local machine (if not already cloned during Gold setup)
cd ~/projects  # Or your preferred directory
git clone git@github.com:user/personal-ai-employee.git
cd personal-ai-employee

# Install Python dependencies (if not already installed)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify agent_skills
python -c "import agent_skills; print('Agent skills OK')"
```

### Step 3.2: Configure Local Agent Environment

```bash
# Create .env.local (Local-only with ALL credentials)
cat > .env.local <<'EOF'
# Platinum Local Agent Configuration

# Agent Identity
TIER=platinum
ENABLE_CLOUD_AGENT=false  # Local Agent, not Cloud
LOCAL_AGENT_ID=local

# Vault Path (on Local machine)
VAULT_PATH=/home/user/personal-ai-employee/vault  # Adjust to your path

# Git Sync
GIT_REMOTE_URL=git@github.com:user/ai-employee-vault.git
GIT_BRANCH=main
GIT_SYNC_INTERVAL=60

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Email MCP (SMTP send - LOCAL ONLY)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-specific-password-here

# LinkedIn MCP
LINKEDIN_ACCESS_TOKEN=your-oauth2-token
LINKEDIN_AUTHOR_URN=urn:li:person:xxxxx

# WhatsApp MCP (Playwright session - LOCAL ONLY)
WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session.json
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_KEYWORDS=urgent,meeting,payment,deadline,invoice,asap

# Social Media MCPs (LOCAL ONLY)
FACEBOOK_ACCESS_TOKEN=your-token
INSTAGRAM_ACCESS_TOKEN=your-token
TWITTER_API_KEY=your-key
TWITTER_API_SECRET=your-secret
TWITTER_ACCESS_TOKEN=your-token
TWITTER_ACCESS_SECRET=your-secret

# Odoo MCP (draft creation - LOCAL ONLY)
ENABLE_ODOO=true
ODOO_URL=https://odoo.yourdomain.com:8069
ODOO_DB=platinum_business
ODOO_USER=admin
ODOO_PASSWORD=your-odoo-password

# Next.js Dashboard
DASHBOARD_URL=http://localhost:3000
NEXT_PUBLIC_AGENT_TYPE=local
NEXT_AUTH_ENABLED=true
DASHBOARD_PASSWORD=your-secure-password  # Will be bcrypt-hashed
SESSION_SECRET=random-secret-key-32-chars-min
PORT=3000

# Cost Alerts
COST_ALERT_THRESHOLD=50  # Weekly USD threshold

# Logging
LOG_LEVEL=INFO
EOF

# Secure .env.local
chmod 600 .env.local
```

### Step 3.3: Setup WhatsApp Session (Playwright)

```bash
# Install Playwright browsers
playwright install chromium

# Run WhatsApp QR code authentication (one-time)
python local_agent/src/watchers/whatsapp_setup.py
# This opens browser, displays QR code
# Scan QR code with WhatsApp mobile app
# Session saved to WHATSAPP_SESSION_PATH

# Verify session file exists
ls -la ~/.whatsapp_session.json
```

### Step 3.4: Configure PM2 for Local Agent

```bash
# Create PM2 ecosystem config for Local processes
cat > ecosystem.config.local.js <<'EOF'
module.exports = {
  apps: [
    {
      name: 'local_orchestrator',
      script: 'local_agent/src/orchestrator.py',
      interpreter: 'python3',
      cwd: '/home/user/personal-ai-employee',  # Adjust to your path
      env: {
        PYTHONPATH: '/home/user/personal-ai-employee',
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
      cwd: '/home/user/personal-ai-employee',
      autorestart: true,
      max_restarts: 10,
    },
    {
      name: 'git_sync_local',
      script: 'local_agent/src/git_sync.py',
      interpreter: 'python3',
      cwd: '/home/user/personal-ai-employee',
      autorestart: true,
    },
    {
      name: 'nextjs_dashboard',
      script: 'npm',
      args: 'start',
      cwd: '/home/user/personal-ai-employee/nextjs_dashboard',
      autorestart: true,
      max_restarts: 10,
      env: {
        PORT: 3000,
        NODE_ENV: 'production',
      },
    },
  ],
};
EOF

# Install PM2 (if not already installed)
npm install -g pm2

# Start Local Agent processes
pm2 start ecosystem.config.local.js

# Verify all processes running
pm2 list
# Expected: local_orchestrator (online), whatsapp_watcher (online), git_sync_local (online), nextjs_dashboard (online)
```

---

## Phase 4: Next.js Dashboard Setup

### Step 4.1: Install Dashboard Dependencies

```bash
cd nextjs_dashboard

# Install Node.js dependencies
npm install

# Verify Next.js version
npx next --version  # Should be 14.x
```

### Step 4.2: Configure Dashboard Environment

```bash
# Create .env.local for Next.js
cat > .env.local <<'EOF'
# Next.js Dashboard Configuration

# Vault Path (read vault markdown files)
VAULT_PATH=/home/user/personal-ai-employee/vault

# Authentication (optional, set to false for localhost-only)
NEXT_AUTH_ENABLED=true
DASHBOARD_PASSWORD_HASH=$2b$10$abcdefghijklmnopqrstuvwxyz123456789  # bcrypt hash
SESSION_SECRET=random-secret-key-min-32-chars

# API URLs
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_AGENT_TYPE=local
EOF

# Generate bcrypt password hash
node -e "const bcrypt = require('bcrypt'); bcrypt.hash('your-password', 10, (err, hash) => console.log(hash));"
# Copy output hash to DASHBOARD_PASSWORD_HASH in .env.local
```

### Step 4.3: Build and Start Dashboard

```bash
# Build Next.js for production
npm run build

# Start Next.js server
npm start
# OR use PM2 (already configured in Phase 3.4)

# Verify dashboard accessible
curl http://localhost:3000
# Should return HTML (Next.js page)

# Open in browser
open http://localhost:3000
# OR on Windows: start http://localhost:3000
```

### Step 4.4: Test Dashboard (Manual)

1. **Login** (if NEXT_AUTH_ENABLED=true):
   - Navigate to http://localhost:3000
   - Enter password from DASHBOARD_PASSWORD in .env.local
   - Click "Login"

2. **Verify Dashboard Sections**:
   - ✅ Pending Approvals (shows counts by category)
   - ✅ Real-time Task Status (active plans, completed today)
   - ✅ MCP Server Health (email ✓, whatsapp ✓, linkedin ✓)
   - ✅ API Usage Stats (calls today, cost this week)

3. **Test Approval Workflow**:
   - Create test email draft: `vault/Pending_Approval/Email/EMAIL_DRAFT_test.md`
   - Refresh dashboard (or wait 5s for auto-polling)
   - Click "Approve" button
   - Verify file moved to `vault/Approved/Email/`
   - Verify Email MCP sends email (check logs: `vault/Logs/MCP_Actions/`)

4. **Test Mobile Access**:
   - Find Local Agent IP: `ifconfig` (Linux/Mac) or `ipconfig` (Windows)
   - On mobile browser: http://192.168.x.x:3000
   - Verify responsive layout (cards stack vertically, buttons ≥44px)

---

## Phase 5: Git Sync Initialization

### Step 5.1: Create Git Remote Repository

```bash
# On GitHub, create new private repository
# Name: ai-employee-vault
# Privacy: Private (important for security)
# Initialize: No (will push from Local)

# Copy SSH URL: git@github.com:user/ai-employee-vault.git
```

### Step 5.2: Initialize Vault Git (Local Agent)

```bash
cd ~/personal-ai-employee/vault

# Initialize Git (if not already initialized)
git init
git remote add origin git@github.com:user/ai-employee-vault.git

# Create .gitignore (enforce security partition)
cat > .gitignore <<'EOF'
# Sensitive files
.env
.env.*
*.session
*.pem
*.key
credentials.json
.secrets/

# Build artifacts
node_modules/
__pycache__/
.next/
.pytest_cache/

# Logs (except vault/Logs/ which ARE synced)
*.log

# Backups
odoo_backups/
*.bak

# Database files
*.sqlite
*.db
EOF

# Add all vault files
git add .
git commit -m "Initial vault commit (Local)"
git push -u origin main

# Verify push succeeded
git status  # Should show "Your branch is up to date with 'origin/main'"
```

### Step 5.3: Sync Cloud Agent with Git Remote

```bash
# SSH into Cloud VM
ssh ubuntu@129.80.x.x

# Navigate to vault
cd /opt/personal-ai-employee/vault

# Pull from Git remote
git pull origin main

# Verify vault synced
ls -la  # Should show Inbox/, Pending_Approval/, Done/, etc.

# Test Git sync cycle (Cloud Agent)
# Trigger Cloud Agent to create test file
touch vault/test_cloud_sync.md
# Wait 60s for git_sync_cloud process to commit + push

# On Local Agent, verify pull
cd ~/personal-ai-employee/vault
git pull origin main
ls -la | grep test_cloud_sync.md  # Should exist
```

---

## Phase 6: End-to-End Testing

### Test 1: Email Draft (Cloud → Local Workflow)

1. **Simulate urgent email** (while Local offline):
   - SSH to Cloud VM
   - Create test email: `vault/Inbox/EMAIL_urgent_test.md` with priority="High"
   - Wait 60s for Cloud Agent to process
   - Verify draft created: `vault/Pending_Approval/Email/EMAIL_DRAFT_*.md`
   - Verify Git push: `git log -1` shows "Cloud: 1 email draft"

2. **Bring Local online**:
   - On Local Agent, verify Git pull: `cd vault && git pull origin main`
   - Verify draft file appears: `ls vault/Pending_Approval/Email/`

3. **Approve via Dashboard**:
   - Open http://localhost:3000
   - See email draft card in Pending Approvals
   - Click "Approve"
   - Verify file moved to `vault/Approved/Email/`

4. **Verify Email MCP sends**:
   - Check logs: `cat vault/Logs/MCP_Actions/$(date +%Y-%m-%d).md`
   - Verify email sent successfully
   - Verify task moved to `vault/Done/`

**Expected**: Email drafted by Cloud, approved by user via dashboard, sent by Local Agent. Full workflow within 5 minutes.

### Test 2: WhatsApp Notification (Cloud Alert)

1. **Trigger urgent email** (on Cloud VM)
2. **Verify WhatsApp notification sent** (within 60s):
   - Check user's phone for WhatsApp message
   - Format: "⚠️ [URGENT] Email from {sender}..."
   - Verify dashboard URL clickable
3. **Click dashboard URL** in WhatsApp message
4. **Verify dashboard loads** approval page directly

### Test 3: Dashboard Polling (Real-time Updates)

1. **Create new draft** (on Cloud VM): `vault/Pending_Approval/LinkedIn/LINKEDIN_POST_test.md`
2. **Wait for Git sync** (60s)
3. **Watch Local dashboard** (without refresh)
4. **Verify count updates** within 5 seconds (polling detects new file)

### Test 4: MCP Health Monitoring

1. **Stop email-mcp** (simulate offline): `pm2 stop email-mcp` (if running as PM2 process)
2. **Wait 5 minutes** (health check cycle)
3. **Verify dashboard shows** "Email MCP: ✗ Offline"
4. **Restart email-mcp**: `pm2 restart email-mcp`
5. **Verify dashboard updates** to "Email MCP: ✓ Online"

---

## Troubleshooting

### Cloud Agent Not Syncing

**Symptom**: Git push from Cloud fails, logs show "Authentication failed"

**Fix**:
```bash
# On Cloud VM, verify SSH key added to GitHub
ssh -T git@github.com
# If fails, regenerate key and re-add to GitHub (see Phase 1.5)
```

### Local Agent Git Conflicts

**Symptom**: Local Agent logs show "Merge conflict in Dashboard.md"

**Fix**:
```bash
# Check auto-resolve worked
cat vault/Logs/Local/git_conflicts.md
# If manual intervention needed, review conflict file and resolve
git add vault/Dashboard.md
git rebase --continue
```

### Dashboard Not Loading

**Symptom**: http://localhost:3000 shows "ERR_CONNECTION_REFUSED"

**Fix**:
```bash
# Check Next.js process running
pm2 list | grep nextjs_dashboard
# If stopped, restart
pm2 restart nextjs_dashboard
# Check logs
pm2 logs nextjs_dashboard
```

### WhatsApp Session Expired

**Symptom**: WhatsApp watcher logs show "QR code detected"

**Fix**:
```bash
# Re-authenticate WhatsApp session
python local_agent/src/watchers/whatsapp_setup.py
# Scan QR code with phone
# Verify session saved
ls -la ~/.whatsapp_session.json
# Restart watcher
pm2 restart whatsapp_watcher
```

### Odoo Not Accessible

**Symptom**: https://odoo.yourdomain.com shows "502 Bad Gateway"

**Fix**:
```bash
# On Cloud VM, check Odoo service
sudo systemctl status odoo
# If stopped, restart
sudo systemctl restart odoo
# Check Nginx
sudo systemctl status nginx
sudo nginx -t  # Test config
```

---

## Verification Checklist

### Cloud Agent
- [ ] Cloud VM accessible via SSH
- [ ] PM2 processes running (cloud_orchestrator, gmail_watcher, git_sync_cloud)
- [ ] Git push succeeds every 60s (check `git log`)
- [ ] Odoo accessible via HTTPS (https://odoo.yourdomain.com)
- [ ] No sensitive credentials in .env.cloud (SMTP, WhatsApp session, banking)

### Local Agent
- [ ] PM2 processes running (local_orchestrator, whatsapp_watcher, git_sync_local, nextjs_dashboard)
- [ ] Git pull succeeds every 60s (check `git log`)
- [ ] WhatsApp session authenticated (QR scanned, session file exists)
- [ ] All MCP servers configured (email, whatsapp, linkedin, social)
- [ ] Dashboard accessible (http://localhost:3000 and http://LOCAL_IP:3000)

### Git Sync
- [ ] Cloud pushes appear in `git log` with "Cloud:" prefix
- [ ] Local pulls succeed without manual intervention
- [ ] Merge conflicts auto-resolved (check `vault/Logs/Local/git_conflicts.md`)
- [ ] .gitignore blocks sensitive files (test: `git add .env` should fail)

### Dashboard
- [ ] Login works (if NEXT_AUTH_ENABLED=true)
- [ ] Pending approvals display correctly
- [ ] Approve button moves file to /Approved/
- [ ] MCP health shows online/offline status
- [ ] API usage displays costs
- [ ] Mobile responsive (test on phone at http://LOCAL_IP:3000)

### End-to-End
- [ ] Cloud drafts email while Local offline → Local approves → Email MCP sends
- [ ] WhatsApp notification received on phone for urgent email
- [ ] Dashboard polling updates counts within 5 seconds
- [ ] All Gold tier features still functional (backward compatibility)

---

## Next Steps

1. **Run Integration Tests**: `pytest tests/integration/test_dual_agent_sync.py`
2. **Generate Tasks**: `/sp.tasks 003-platinum-tier` to create dependency-ordered tasks.md
3. **Monitor for 24 hours**: Verify Cloud Agent uptime, Git sync stability, MCP health
4. **Read Documentation**: See `docs/platinum/` for architecture diagrams, troubleshooting, advanced configuration

---

**Quickstart complete. Platinum tier deployed and verified. Cloud Agent runs 24/7, Local Agent approves, dashboard enables mobile approvals.**
