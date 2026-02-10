# Bronze Tier Setup Guide

Complete installation and configuration guide for the Bronze tier Personal AI Employee system.

## Prerequisites

- **Python 3.11+** - Check version: `python --version`
- **Obsidian 1.5+** - Download from [obsidian.md/download](https://obsidian.md/download)
- **Git** (optional but recommended)
- **8GB RAM minimum**
- **1GB disk space** for vault storage

## Installation Steps

### 1. Clone or Download Repository

```bash
cd ~/projects
git clone <repository-url> personal-ai-employee
cd personal-ai-employee
```

### 2. Create Python Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate venv (Linux/macOS)
source venv/bin/activate

# Activate venv (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Bronze tier + development tools
pip install -e .[dev]

# Verify installation
pip list | grep -E "watchdog|pyyaml|pytest"
```

Expected output:
```
watchdog    3.0.0+
pyyaml      6.0+
pytest      7.0+
```

### 4. Verify Installation

```bash
# Check Python modules import correctly
python -c "from agent_skills.vault_watcher import read_vault_file; print('✓ Agent Skills OK')"
python -c "from agent_skills.dashboard_updater import update_dashboard; print('✓ Dashboard Updater OK')"
```

## Vault Initialization

### Create Your Vault

```bash
# Initialize vault at ~/my-vault
python scripts/init_vault.py ~/my-vault

# Or specify custom path
python scripts/init_vault.py /path/to/vault
```

Expected output:
```
Creating vault structure...
✓ Created Inbox/ folder
✓ Created Needs_Action/ folder
✓ Created Done/ folder
✓ Created Plans/ folder
✓ Created Logs/ folder
✓ Created Dashboard.md
✓ Created Company_Handbook.md

Vault initialized at /home/user/my-vault
Ready to use with Obsidian
```

### Vault Structure

After initialization, your vault contains:

```
~/my-vault/
├── Inbox/              # Drop new tasks here (monitored)
├── Needs_Action/       # Manual move (Bronze tier)
├── Done/               # Manual move (Bronze tier)
├── Plans/              # Reserved for Silver+ tiers
├── Logs/               # System-generated logs (auto-created)
├── Dashboard.md        # Auto-updated task overview
└── Company_Handbook.md # Configuration file
```

### Overwrite Existing Vault

If you need to recreate an existing vault:

```bash
# WARNING: This will overwrite existing files
python scripts/init_vault.py ~/my-vault --overwrite
```

## Configuration

### Edit Company_Handbook.md

Open `~/my-vault/Company_Handbook.md` in your text editor and customize:

#### 1. File Naming Convention (Required)

```markdown
## 1. File Naming Convention

All task files in Inbox/ should follow this format:
- Format: `YYYY-MM-DD-brief-description.md`
- Example: `2026-02-10-review-client-proposal.md`
- Hyphens for word separation (no spaces)
- Dates in ISO 8601 format (YYYY-MM-DD)
```

**Edit this section** to match your preferred naming style.

#### 2. Folder Usage Guidelines (Required)

```markdown
## 2. Folder Usage Guidelines

- **Inbox/**: Drop all new tasks here. Watcher monitors this folder.
- **Needs_Action/**: (Manual move in Bronze) Tasks requiring immediate attention.
- **Done/**: (Manual move in Bronze) Completed tasks for archival.
```

**Add your own folder rules** (e.g., color-coding, priority labels).

#### 3. Forbidden Operations (System-defined, Read-only)

```markdown
## 3. Forbidden Operations (Bronze Tier)

The Bronze tier AI Employee is **monitoring only**. It will:
- ✅ Detect new files in Inbox/
- ✅ Update Dashboard.md automatically
- ✅ Log events to vault/Logs/

It will **NOT**:
- ❌ Delete any files
- ❌ Move files between folders
```

**Do not modify this section** - it documents Bronze tier limitations.

#### 4. Escalation Rules (Required)

```markdown
## 4. Escalation Rules

**Human intervention required for**:
- Watcher process crashes (check vault/Logs/ for errors)
- Persistent file lock conflicts (close Obsidian temporarily)
- Backup restoration failures (manual recovery from .bak files)
```

**Add your escalation rules** (e.g., Slack notifications, email alerts for Silver tier).

#### 5. Bronze Tier Limitations (System-defined, Read-only)

```markdown
## 5. Bronze Tier Limitations

This is a **foundation tier**. The AI Employee:
- Operates 100% offline (no AI analysis, no external APIs)
- Requires manual file movement (no autonomous actions)
- Defaults all tasks to "Medium" priority (no smart prioritization)
- Polls every 30 seconds (not real-time monitoring)
- Supports up to 1000 files (performance limit)
```

**Read-only** - documents what Bronze tier does and doesn't do.

### Optional: Configure Polling Interval

Add this to YAML frontmatter in `Company_Handbook.md`:

```yaml
---
version: 1.0.0
tier: bronze
last_updated: 2026-02-10
polling_interval: 30  # seconds (default: 30)
---
```

Valid values: 10-300 seconds (10 seconds minimum, 5 minutes maximum).

## Starting the Watcher

### Run Watcher (Foreground)

```bash
# Start monitoring (Ctrl+C to stop)
python scripts/watch_inbox.py ~/my-vault
```

Expected output:
```
Validating vault structure...
✓ Vault path exists
✓ All folders present
✓ Dashboard.md found
✓ Company_Handbook.md found

Validating Company_Handbook.md...
✓ All required sections present

Starting file watcher...
Polling interval: 30 seconds
Monitoring: ~/my-vault/Inbox/

[2026-02-10 15:30:00] Watcher started
```

### Run Watcher (Background - PM2)

Install PM2 (Node.js process manager):

```bash
npm install -g pm2

# Start watcher as background service
pm2 start "python scripts/watch_inbox.py ~/my-vault" --name bronze-watcher

# View logs
pm2 logs bronze-watcher

# Stop watcher
pm2 stop bronze-watcher

# Auto-start on reboot
pm2 save
pm2 startup
```

### Run Watcher (Background - systemd)

Create service file `/etc/systemd/system/bronze-watcher.service`:

```ini
[Unit]
Description=Bronze Tier AI Employee Watcher
After=network.target

[Service]
Type=simple
User=myuser
WorkingDirectory=/home/myuser/personal-ai-employee
ExecStart=/usr/bin/python3 scripts/watch_inbox.py /home/myuser/my-vault
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bronze-watcher
sudo systemctl start bronze-watcher

# Check status
sudo systemctl status bronze-watcher

# View logs
sudo journalctl -u bronze-watcher -f
```

## Verification

### Test File Detection

1. **Start watcher** (if not already running):
   ```bash
   python scripts/watch_inbox.py ~/my-vault
   ```

2. **Drop test file** in Inbox/:
   ```bash
   echo "# Test Task\n\nThis is a test." > ~/my-vault/Inbox/2026-02-10-test-task.md
   ```

3. **Wait 30-60 seconds** for detection (one polling cycle)

4. **Check watcher log** (in terminal or vault/Logs/watcher-YYYY-MM-DD.md):
   ```
   [2026-02-10 15:30:45] File Detected
   - File: Inbox/2026-02-10-test-task.md
   - Size: 28 bytes
   - Encoding: UTF-8

   [2026-02-10 15:30:47] Dashboard Updated
   - New tasks: 1
   - Total tasks: 1
   - Update time: 1.8 seconds
   ```

5. **Check Dashboard.md** in Obsidian or text editor:
   ```markdown
   | Filename | Date Added | Status | Priority |
   |----------|-----------|--------|----------|
   | [[Inbox/2026-02-10-test-task.md]] | 2026-02-10 15:30 | Inbox | Medium |
   ```

### Open Vault in Obsidian

1. Launch Obsidian Desktop App
2. Click **Open folder as vault**
3. Select `~/my-vault`
4. Navigate to `Dashboard.md` - verify table renders correctly
5. Click on a task link (e.g., `[[Inbox/2026-02-10-test-task.md]]`) - should open the file

## Troubleshooting

### Watcher Won't Start

**Exit code 1** (Invalid vault path):
```bash
python scripts/init_vault.py ~/my-vault
```

**Exit code 2** (Handbook validation failed):
- Open `~/my-vault/Company_Handbook.md`
- Verify all 5 required sections exist
- Check YAML frontmatter is valid

**Exit code 3** (Permission error):
```bash
chmod -R u+rw ~/my-vault
```

### Dashboard Not Updating

1. Check watcher is running:
   ```bash
   ps aux | grep watch_inbox.py
   ```

2. Check watcher logs:
   ```bash
   tail -f ~/my-vault/Logs/watcher-$(date +%Y-%m-%d).md
   ```

3. Check for file lock errors (Obsidian conflict):
   - Close Obsidian temporarily
   - Watcher will retry on next cycle

### Vault Exceeds 1000 Files

Bronze tier performance limit is 1000 files. If you exceed this:

1. Archive old tasks:
   ```bash
   mkdir ~/my-vault-archive
   mv ~/my-vault/Done/* ~/my-vault-archive/
   ```

2. Upgrade to Silver tier for better performance

## Next Steps

- **Testing**: See [bronze-testing.md](./bronze-testing.md) for unit and integration tests
- **Usage**: See [bronze-usage.md](./bronze-usage.md) for daily workflow
- **Architecture**: See [bronze-architecture.md](./bronze-architecture.md) for technical details
