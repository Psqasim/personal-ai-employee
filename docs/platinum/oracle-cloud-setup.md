# Oracle Cloud VM Setup Guide

**Target**: Deploy Cloud Agent on Oracle Cloud Free Tier (Ubuntu 22.04)
**Estimated Time**: 45-60 minutes
**Prerequisites**: Oracle Cloud account, GitHub account, SSH key pair

---

## Step 1: Create Oracle Cloud Free Tier Account

1. **Sign up**: https://cloud.oracle.com/free
2. **Verify email** and **phone number**
3. **Add payment method** (credit card, won't be charged for free tier)
4. **Verify identity** (may require government ID upload)

> **Free Tier**: 4 OCPU ARM, 24GB RAM, 200GB storage (always free)

---

## Step 2: Provision Compute Instance (VM)

### 2.1 Create VM

1. Log in to Oracle Cloud Console
2. Navigate: **Menu** → **Compute** → **Instances**
3. Click **Create Instance**

### 2.2 Configure Instance

**Name**: `personal-ai-employee-cloud`

**Image and Shape**:
- Image: **Ubuntu 22.04 LTS** (Canonical-Ubuntu-22.04-aarch64)
- Shape: **VM.Standard.A1.Flex** (Ampere ARM)
  - OCPU count: **4** (max free tier)
  - Memory: **24 GB** (max free tier)

**Networking**:
- VCN: Use default (or create new VCN if first VM)
- Subnet: Public subnet
- **Public IP address**: ✅ Assign a public IPv4 address
- Note the public IP (e.g., `129.80.x.x`)

**SSH Keys**:
- Upload your local SSH public key: `~/.ssh/id_ed25519.pub`
- Or generate new key pair and download private key

**Boot Volume**:
- Size: **200 GB** (max free tier)

4. Click **Create**

5. **Wait 2-3 minutes** for VM to provision (Status: Running)

---

## Step 3: Configure Security List (Firewall)

### 3.1 Open Required Ports

1. Navigate to VM Details → **Primary VNIC** → **Subnet** → **Security List**
2. Click **Add Ingress Rule** for each port:

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | 0.0.0.0/0 | SSH access |
| 443 | TCP | 0.0.0.0/0 | HTTPS (future use) |
| 8069 | TCP | 0.0.0.0/0 | Odoo (temporary, redirect to 443 later) |

**Egress Rules**: Default "Allow All" is fine

---

## Step 4: SSH Access

### 4.1 Get VM Public IP

From VM details page, note: **Public IP Address** (e.g., `129.80.x.x`)

### 4.2 SSH into VM

```bash
# From your local machine
ssh ubuntu@129.80.x.x

# If you downloaded Oracle's private key:
ssh -i ~/Downloads/oracle_vm_key.pem ubuntu@129.80.x.x
```

**First login**: Accept host fingerprint (type `yes`)

### 4.3 Test Connection

```bash
# Inside VM
whoami  # Should show: ubuntu
hostname  # Should show: personal-ai-employee-cloud
df -h  # Should show ~200GB disk
```

---

## Step 5: Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Reboot if kernel was upgraded
sudo reboot  # Wait 1 min, then SSH back in
```

---

## Step 6: Install Dependencies

### 6.1 Install Python 3.11+

```bash
# Ubuntu 22.04 has Python 3.10 by default
python3 --version  # Check current version

# Install Python 3.11 from deadsnakes PPA (optional, for latest)
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Set python3.11 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify
python3 --version  # Should show 3.11.x
```

### 6.2 Install Git

```bash
sudo apt install -y git
git --version  # Should show 2.34+
```

### 6.3 Install Node.js 20+ (for PM2)

```bash
# Install Node.js via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version  # Should show v20.x
npm --version  # Should show 10.x
```

### 6.4 Install PM2

```bash
sudo npm install -g pm2

# Verify
pm2 --version  # Should show 5.x
```

---

## Step 7: Configure Git SSH Key

### 7.1 Generate SSH Key

```bash
# Generate ED25519 key for Git
ssh-keygen -t ed25519 -C "cloud-agent@oracle-vm" -f ~/.ssh/id_ed25519_cloud

# Start SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_cloud
```

### 7.2 Add Key to GitHub

```bash
# Display public key
cat ~/.ssh/id_ed25519_cloud.pub
```

**Copy output**, then:

1. Go to GitHub: **Settings** → **SSH and GPG keys** → **New SSH key**
2. Title: `Oracle Cloud VM - personal-ai-employee`
3. Key: Paste public key
4. Click **Add SSH key**

### 7.3 Test GitHub Connection

```bash
ssh -T git@github.com
# Expected output: "Hi username! You've successfully authenticated..."
```

### 7.4 Configure Git Identity

```bash
git config --global user.name "Cloud Agent"
git config --global user.email "cloud-agent@oracle-vm"
```

---

## Step 8: Clone Repository

```bash
# Create project directory
sudo mkdir -p /opt/personal-ai-employee
sudo chown ubuntu:ubuntu /opt/personal-ai-employee

# Clone repo
cd /opt
git clone git@github.com:YOUR_USERNAME/personal-ai-employee.git

# Verify
cd personal-ai-employee
ls -la  # Should show project files
```

---

## Step 9: Install Python Dependencies

```bash
cd /opt/personal-ai-employee

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify agent_skills installed
python -c "import agent_skills; print('✓ Agent skills OK')"
```

---

## Step 10: Configure Environment

### 10.1 Create .env.cloud

```bash
cp .env.cloud.example .env.cloud
nano .env.cloud
```

**Edit these values**:

```bash
# Vault Path (on Cloud VM)
VAULT_PATH=/opt/personal-ai-employee/vault

# Git Sync
GIT_REMOTE_URL=git@github.com:YOUR_USERNAME/ai-employee-vault.git
GIT_BRANCH=main

# Claude API Key (get from https://console.anthropic.com/)
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# WhatsApp Notifications (your phone number)
WHATSAPP_NOTIFICATION_NUMBER=+1234567890
FALLBACK_EMAIL=your-email@gmail.com

# Gmail Monitoring (upload credentials.json to VM)
GMAIL_CREDENTIALS_PATH=/opt/personal-ai-employee/credentials.json
```

**Save**: `Ctrl+O`, `Enter`, `Ctrl+X`

### 10.2 Secure .env.cloud

```bash
chmod 600 .env.cloud
```

### 10.3 Upload Gmail Credentials (Optional)

If using Gmail monitoring:

```bash
# From your local machine (where you have credentials.json)
scp ~/credentials.json ubuntu@129.80.x.x:/opt/personal-ai-employee/
```

---

## Step 11: Initialize Vault (Git)

### Option A: Clone Existing Vault

If vault already exists in Git remote:

```bash
cd /opt/personal-ai-employee
git clone git@github.com:YOUR_USERNAME/ai-employee-vault.git vault

# Verify vault structure
ls -la vault/
# Should show: Inbox/, Pending_Approval/, Done/, Logs/, Dashboard.md
```

### Option B: Create New Vault

If first deployment:

```bash
cd /opt/personal-ai-employee
mkdir -p vault/{Inbox,Needs_Action,Pending_Approval,Approved,Done,In_Progress,Rejected,Plans,Logs,Briefings}
mkdir -p vault/Logs/{Cloud,Local,API_Usage,MCP_Health,MCP_Actions,Plan_Execution}

# Create placeholder files
touch vault/Dashboard.md
touch vault/Company_Handbook.md

# Initialize Git
cd vault
git init
git remote add origin git@github.com:YOUR_USERNAME/ai-employee-vault.git
git add .
git commit -m "Initial vault structure (Cloud Agent)"
git push -u origin main
```

---

## Step 12: Verify Installation

### 12.1 Test Cloud Orchestrator

```bash
cd /opt/personal-ai-employee
source venv/bin/activate
python cloud_agent/src/orchestrator.py
```

**Expected output**:
```
2026-02-16 10:30:00 - [CLOUD-ORCH] - INFO - Cloud Orchestrator initialized
2026-02-16 10:30:00 - [CLOUD-ORCH] - INFO - 🚀 Cloud Orchestrator started
```

**Press `Ctrl+C`** to stop

### 12.2 Test Git Sync

```bash
python cloud_agent/src/git_sync.py &
# Wait 60 seconds
jobs  # Should show [1]+ Running
kill %1  # Stop background process
```

**Check Git log**:
```bash
cd vault
git log -1  # Should show recent commit from Cloud Agent
```

---

## Step 13: Setup PM2 (Process Manager)

### 13.1 Start Cloud Processes

```bash
cd /opt/personal-ai-employee
pm2 start ecosystem.config.js

# Verify all processes online
pm2 list
```

**Expected output**:
```
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ mode        │ ↺       │ status  │ cpu      │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┤
│ 0   │ cloud_orchestrator   │ fork        │ 0       │ online  │ 0.2%     │
│ 1   │ git_sync_cloud       │ fork        │ 0       │ online  │ 0.1%     │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┘
```

### 13.2 Enable Startup on Boot

```bash
# Generate systemd startup script
pm2 startup systemd

# Follow the output instructions (run the sudo command shown)
# Example:
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Save current process list
pm2 save
```

### 13.3 Test PM2 Restart

```bash
# Reboot VM
sudo reboot

# Wait 1 minute, SSH back in
ssh ubuntu@129.80.x.x

# Verify processes auto-started
pm2 list  # Should show all processes online
```

---

## Step 14: Monitor Logs

```bash
# View all logs
pm2 logs

# View specific process
pm2 logs cloud_orchestrator

# View last 50 lines
pm2 logs --lines 50

# Clear logs
pm2 flush
```

---

## Step 15: Maintenance

### Update Code

```bash
cd /opt/personal-ai-employee
git pull origin main
pip install -r requirements.txt  # If dependencies changed
pm2 restart all
```

### Restart Single Process

```bash
pm2 restart cloud_orchestrator
```

### Stop All Processes

```bash
pm2 stop all
```

### Remove from Startup

```bash
pm2 unstartup systemd
```

---

## Troubleshooting

### SSH Connection Refused

**Issue**: `ssh: connect to host 129.80.x.x port 22: Connection refused`

**Fix**:
1. Check VM is running (Oracle Cloud Console → Instances → Status: Running)
2. Verify Security List allows port 22 from your IP
3. Check Ubuntu firewall: `sudo ufw status` (should be inactive)

### Git Push Authentication Failed

**Issue**: `Permission denied (publickey)`

**Fix**:
```bash
# Verify SSH key added to ssh-agent
ssh-add -l

# If empty, add key
ssh-add ~/.ssh/id_ed25519_cloud

# Test GitHub connection
ssh -T git@github.com
```

### PM2 Processes Errored

**Issue**: `pm2 list` shows status `errored`

**Fix**:
```bash
# View error logs
pm2 logs cloud_orchestrator --err

# Common issues:
# - .env.cloud missing: Create from .env.cloud.example
# - VAULT_PATH not set: Check .env.cloud
# - Python import errors: Reinstall requirements.txt
```

### Out of Disk Space

**Issue**: `No space left on device`

**Fix**:
```bash
# Check disk usage
df -h

# Clean up old logs
pm2 flush
sudo apt autoremove
sudo apt clean

# Delete old backups (if any)
rm -rf /opt/odoo_backups/*.sql.gz
```

---

## Security Checklist

- [ ] `.env.cloud` has `chmod 600` permissions
- [ ] No `SMTP_PASSWORD` in `.env.cloud` (Cloud Agent NEVER has send credentials)
- [ ] No `WHATSAPP_SESSION_PATH` in `.env.cloud`
- [ ] SSH key added to GitHub (not hardcoded in repo)
- [ ] Security List allows only required ports (22, 443, 8069)
- [ ] Ubuntu firewall disabled or configured correctly (`sudo ufw status`)

---

## Next Steps

1. **Deploy Local Agent**: Follow `docs/platinum/local-agent-setup.md`
2. **Setup Next.js Dashboard**: Follow `docs/platinum/dashboard-setup.md`
3. **Test End-to-End**: Follow `docs/platinum/phase3-testing.md`

---

**Oracle Cloud VM setup complete! ✅ Cloud Agent ready for 24/7 operation.**
