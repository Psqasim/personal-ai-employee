# Bronze Tier Usage Guide

Daily workflow, Claude Code integration, Dashboard format, and Company_Handbook.md configuration options.

## Daily Workflow

### Morning Routine

#### 1. Start Watcher (if not running 24/7)

```bash
# Check if watcher is running
ps aux | grep watch_inbox.py

# If not running, start it
python3 scripts/watch_inbox.py ~/my-vault
```

Or use PM2:
```bash
pm2 start bronze-watcher  # If configured
pm2 logs bronze-watcher
```

#### 2. Check Dashboard

Open `~/my-vault/Dashboard.md` in Obsidian to see pending tasks:

```markdown
## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|
| [[Inbox/2026-02-10-client-meeting.md]] | 2026-02-10 09:00 | Inbox | Medium |
| [[Inbox/2026-02-10-review-proposal.md]] | 2026-02-10 09:30 | Inbox | Medium |
| [[Needs_Action/2026-02-09-urgent-fix.md]] | 2026-02-09 15:00 | Needs Action | Medium |

## Statistics
- **Total Tasks**: 3
- **Inbox**: 2
- **Needs Action**: 1
- **Done**: 0
```

#### 3. Review Inbox Tasks

Click on each `[[Inbox/...]]` link in Dashboard to review task details.

**Prioritize** based on your own judgment (Bronze tier doesn't auto-prioritize).

#### 4. Move Tasks Between Folders

Bronze tier requires **manual file movement**:

```bash
# Move task to Needs_Action/
mv ~/my-vault/Inbox/2026-02-10-client-meeting.md ~/my-vault/Needs_Action/

# Or move to Done/ when completed
mv ~/my-vault/Needs_Action/2026-02-09-urgent-fix.md ~/my-vault/Done/
```

Or use Obsidian:
1. Right-click task file
2. Select **Move file to...**
3. Choose folder (Needs_Action/ or Done/)

**Note**: Dashboard.md will reflect changes on next watcher cycle (within 30 seconds).

---

### Adding New Tasks

#### Method 1: Create File in Inbox/ (Recommended)

In Obsidian:
1. Click **New note** button
2. Save to `Inbox/` folder
3. Use naming convention: `YYYY-MM-DD-brief-description.md`
4. Add task details (due date, notes, etc.)
5. Wait 30 seconds for watcher to detect and update Dashboard

#### Method 2: Drop File from External Source

From command line:
```bash
# Create task file
echo "# Fix Bug in Login Flow

Due: 2026-02-15

Steps:
1. Reproduce bug
2. Identify root cause
3. Write fix
4. Test" > ~/my-vault/Inbox/2026-02-10-fix-login-bug.md
```

From file manager:
- Drag .md file into `~/my-vault/Inbox/` folder
- Watcher detects within 30 seconds

#### Method 3: Email-to-Inbox (Silver Tier)

**Not available in Bronze tier** - deferred to Silver tier with email integration.

---

### Completing Tasks

#### 1. Mark Task as Done

When you finish a task:

1. **Move file to Done/ folder**:
   ```bash
   mv ~/my-vault/Inbox/2026-02-10-fix-login-bug.md ~/my-vault/Done/
   ```

2. **Wait 30 seconds** - Dashboard automatically updates Status to "Done"

3. **Verify in Dashboard.md**:
   ```markdown
   | [[Done/2026-02-10-fix-login-bug.md]] | 2026-02-10 10:00 | Done | Medium |
   ```

#### 2. Archive Completed Tasks (Weekly)

Bronze tier doesn't auto-archive. Manual process:

```bash
# Create archive folder
mkdir -p ~/my-vault-archive/2026-02-week6

# Move old Done/ tasks
mv ~/my-vault/Done/2026-02-*.md ~/my-vault-archive/2026-02-week6/

# Dashboard will remove archived tasks on next update
```

**Recommended**: Archive weekly to keep vault under 1000 files (Bronze tier performance limit).

---

### Evening Review

#### 1. Check Watcher Logs

Review today's events:

```bash
cat ~/my-vault/Logs/watcher-$(date +%Y-%m-%d).md
```

Expected entries:
```markdown
## 09:00:00 - Watcher Started
## 09:05:45 - File Detected
- File: Inbox/2026-02-10-client-meeting.md
## 09:05:47 - Dashboard Updated
- New tasks: 1
- Total tasks: 3
## 17:30:00 - File Detected
- File: Inbox/2026-02-10-review-proposal.md
```

**Look for**:
- Errors (file locks, corruption, encoding issues)
- Warnings (performance degradation, vault size limit)

#### 2. Update Company Handbook (if needed)

Edit `~/my-vault/Company_Handbook.md` to update:
- File naming rules
- Folder usage guidelines
- Escalation rules

**Restart watcher** to reload configuration:
```bash
# Stop watcher (Ctrl+C or)
pm2 stop bronze-watcher

# Restart
pm2 start bronze-watcher
```

---

## Claude Code Integration

### Querying Vault via Agent Skills

Use Claude Code to query vault data interactively:

#### Example 1: Check Task Counts

**User**: "How many tasks do I have?"

**Claude Code executes**:
```python
from agent_skills.vault_watcher import get_dashboard_summary
summary = get_dashboard_summary("/home/user/my-vault")
print(f"You have {summary['total']} tasks:")
print(f"  - Inbox: {summary['inbox']}")
print(f"  - Needs Action: {summary['needs_action']}")
print(f"  - Done: {summary['done']}")
```

**Output**:
```
You have 3 tasks:
  - Inbox: 2
  - Needs Action: 1
  - Done: 0
```

#### Example 2: Read Specific Task

**User**: "Show me the details of 2026-02-10-client-meeting.md"

**Claude Code executes**:
```python
from agent_skills.vault_watcher import read_vault_file
content = read_vault_file(
    "/home/user/my-vault",
    "Inbox/2026-02-10-client-meeting.md"
)
print(content)
```

**Output**:
```markdown
# Client Meeting - Project Kickoff

Date: 2026-02-10 14:00
Location: Office Conference Room A

Agenda:
1. Project scope discussion
2. Timeline and deliverables
3. Budget review
4. Next steps
```

#### Example 3: List All Completed Tasks

**User**: "What tasks have I completed this week?"

**Claude Code executes**:
```python
from agent_skills.vault_watcher import list_vault_folder
done_files = list_vault_folder("/home/user/my-vault", "Done")
print(f"Completed tasks ({len(done_files)}):")
for filename in done_files:
    print(f"  - {filename}")
```

**Output**:
```
Completed tasks (5):
  - 2026-02-08-client-email.md
  - 2026-02-09-bug-fix.md
  - 2026-02-09-code-review.md
  - 2026-02-10-meeting-prep.md
  - 2026-02-10-report-draft.md
```

#### Example 4: Validate Handbook

**User**: "Is my handbook configured correctly?"

**Claude Code executes**:
```python
from agent_skills.vault_watcher import validate_handbook
is_valid, missing = validate_handbook("/home/user/my-vault")

if is_valid:
    print("✓ Handbook is properly configured")
else:
    print("✗ Handbook validation failed")
    print(f"Missing sections: {', '.join(missing)}")
```

**Output**:
```
✓ Handbook is properly configured
```

### Claude Code Usage Tips

1. **Import Agent Skills** in your Claude Code prompts:
   ```python
   from agent_skills.vault_watcher import read_vault_file, list_vault_folder, get_dashboard_summary, validate_handbook
   ```

2. **Always provide absolute vault path**:
   ```python
   # Good
   summary = get_dashboard_summary("/home/user/my-vault")

   # Bad (relative paths don't work)
   summary = get_dashboard_summary("~/my-vault")  # Will fail
   ```

3. **Handle exceptions** for better error messages:
   ```python
   try:
       content = read_vault_file(vault_path, "Inbox/task.md")
   except FileNotFoundError:
       print("Task file not found. Check filename spelling.")
   except PermissionError:
       print("File is locked by Obsidian. Close Obsidian and retry.")
   ```

---

## Dashboard.md Format

### Markdown Table Structure

```markdown
# Personal AI Employee Dashboard

## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|
| [[Inbox/2026-02-10-task.md]] | 2026-02-10 15:30 | Inbox | Medium |

## Statistics
- **Total Tasks**: 1
- **Inbox**: 1
- **Needs Action**: 0
- **Done**: 0

---
*Last Updated: 2026-02-10 15:30:45*
```

### Column Definitions

| Column | Format | Values | Notes |
|--------|--------|--------|-------|
| **Filename** | `[[relative/path.md]]` | Obsidian wiki link | Clickable in Obsidian |
| **Date Added** | `YYYY-MM-DD HH:MM` | ISO 8601 (no timezone) | Timestamp when file detected |
| **Status** | `Inbox` or `Needs Action` or `Done` | Case-sensitive | Reflects current folder location |
| **Priority** | `Medium` (Bronze default) | Always "Medium" | AI priority scoring in Silver+ tiers |

### Statistics Section

Auto-calculated from task table:
- **Total Tasks**: Count of all rows in table
- **Inbox**: Count where Status = "Inbox"
- **Needs Action**: Count where Status = "Needs Action"
- **Done**: Count where Status = "Done"

### Last Updated Timestamp

Format: `*Last Updated: YYYY-MM-DD HH:MM:SS*`

Updated every time Dashboard.md is modified by watcher.

---

## Company_Handbook.md Configuration

### YAML Frontmatter

```yaml
---
version: 1.0.0              # Handbook version (semver)
tier: bronze                # Current tier ("bronze", "silver", "gold", "platinum")
last_updated: 2026-02-10    # ISO 8601 date (YYYY-MM-DD)
polling_interval: 30        # Watcher polling interval (10-300 seconds)
---
```

### Configuration Options

#### polling_interval (Optional)

**Default**: 30 seconds

**Valid range**: 10-300 seconds (10 seconds minimum, 5 minutes maximum)

**Example**:
```yaml
polling_interval: 60  # Check every minute (slower, lower CPU usage)
```

**Effect**: Watcher checks Inbox/ every N seconds for new files.

**When to change**:
- **Lower (10-15s)**: If you need faster detection (higher CPU usage)
- **Higher (60-120s)**: If CPU usage is a concern (slower detection)

---

### Section 1: File Naming Convention (Required, User-defined)

**Purpose**: Define your preferred task file naming style.

**Example (default)**:
```markdown
## 1. File Naming Convention

All task files in Inbox/ should follow this format:
- Format: `YYYY-MM-DD-brief-description.md`
- Example: `2026-02-10-review-client-proposal.md`
- Hyphens for word separation (no spaces)
- Dates in ISO 8601 format (YYYY-MM-DD)
```

**Customization examples**:

**Option A - Project Prefixes**:
```markdown
- Format: `YYYY-MM-DD-[PROJECT]-description.md`
- Example: `2026-02-10-[ACME]-review-proposal.md`
```

**Option B - Priority Tags**:
```markdown
- Format: `YYYY-MM-DD-description-[P1|P2|P3].md`
- Example: `2026-02-10-urgent-fix-[P1].md`
```

**Option C - Free-form** (not recommended, but supported):
```markdown
- Any filename ending in .md
- Watcher will detect and display in Dashboard
```

---

### Section 2: Folder Usage Guidelines (Required, User-defined)

**Purpose**: Define how you use each vault folder.

**Example (default)**:
```markdown
## 2. Folder Usage Guidelines

- **Inbox/**: Drop all new tasks here. Watcher monitors this folder.
- **Needs_Action/**: (Manual move in Bronze) Tasks requiring immediate attention.
- **Done/**: (Manual move in Bronze) Completed tasks for archival.
- **Plans/**: Reserved for future use (Silver tier and above).
- **Logs/**: System-generated logs. Do not manually edit.
```

**Customization examples**:

**Option A - Priority-based**:
```markdown
- **Inbox/**: All new tasks (triage required)
- **Needs_Action/**: High-priority tasks (work on these first)
- **Done/**: Completed this week (archive weekly)
```

**Option B - Time-based**:
```markdown
- **Inbox/**: Tasks to review later
- **Needs_Action/**: Tasks for today (move here each morning)
- **Done/**: Completed tasks (archive monthly)
```

---

### Section 3: Forbidden Operations (Required, System-defined, Read-only)

**Purpose**: Documents what Bronze tier does and doesn't do.

**Do not modify this section** - it's informational for users.

```markdown
## 3. Forbidden Operations (Bronze Tier)

The Bronze tier AI Employee is **monitoring only**. It will:
- ✅ Detect new files in Inbox/
- ✅ Update Dashboard.md automatically
- ✅ Log events to vault/Logs/

It will **NOT**:
- ❌ Delete any files
- ❌ Move files between folders
- ❌ Modify file contents
- ❌ Execute code from vault files
- ❌ Make network requests
```

---

### Section 4: Escalation Rules (Required, User-defined)

**Purpose**: Define when human intervention is required.

**Example (default)**:
```markdown
## 4. Escalation Rules

The watcher logs warnings for:
- Obsidian file locks (will retry automatically)
- Dashboard.md corruption (will restore from backup)
- Vault exceeding 1000 files (performance warning)
- Invalid file encoding (UTF-8 required)

**Human intervention required for**:
- Watcher process crashes (check vault/Logs/ for errors)
- Persistent file lock conflicts (close Obsidian temporarily)
- Backup restoration failures (manual recovery from .bak files)
```

**Customization examples**:

**Option A - Email alerts** (Silver tier integration):
```markdown
**Send email alert for**:
- ERROR-level events (watcher crashes, corruption)
- WARNING-level events after 3 consecutive occurrences
```

**Option B - Slack notifications** (Gold tier integration):
```markdown
**Post to #notifications Slack channel for**:
- Vault size exceeds 1000 files (upgrade warning)
- Dashboard update time exceeds 5 seconds (performance issue)
```

---

### Section 5: Bronze Tier Limitations (Required, System-defined, Read-only)

**Purpose**: Sets expectations for Bronze tier capabilities.

**Do not modify this section** - it's informational for users.

```markdown
## 5. Bronze Tier Limitations

This is a **foundation tier**. The AI Employee:
- Operates 100% offline (no AI analysis, no external APIs)
- Requires manual file movement (no autonomous actions)
- Defaults all tasks to "Medium" priority (no smart prioritization)
- Polls every 30 seconds (not real-time monitoring)
- Supports up to 1000 files (performance limit)

**Upgrade to Silver Tier for**:
- AI-powered priority analysis
- Automatic file movement with approval workflow
- Integration with email/WhatsApp
```

---

## Advanced Usage

### Multiple Vaults

Run separate watchers for multiple vaults:

```bash
# Terminal 1: Personal vault
python3 scripts/watch_inbox.py ~/personal-vault

# Terminal 2: Work vault
python3 scripts/watch_inbox.py ~/work-vault
```

Or use PM2:
```bash
pm2 start "python3 scripts/watch_inbox.py ~/personal-vault" --name personal-watcher
pm2 start "python3 scripts/watch_inbox.py ~/work-vault" --name work-watcher
```

### Custom Polling Interval

Edit `Company_Handbook.md` YAML frontmatter:

```yaml
polling_interval: 15  # Check every 15 seconds (faster)
```

Or override via command-line (future feature - not in Bronze v0.1.0):
```bash
python3 scripts/watch_inbox.py ~/my-vault --polling-interval 15
```

### Dashboard Backup Management

List all backups:
```bash
ls -lt ~/my-vault/Dashboard.md.bak.*
```

Restore specific backup manually:
```bash
cp ~/my-vault/Dashboard.md.bak.2026-02-10_15-30-00 ~/my-vault/Dashboard.md
```

Prune old backups (older than 7 days):
```bash
find ~/my-vault -name "Dashboard.md.bak.*" -mtime +7 -delete
```

**Note**: Watcher prunes old backups automatically on startup (Bronze tier default: keep 7 days).

---

## Troubleshooting Common Workflows

### "I dropped a file but Dashboard didn't update"

1. **Check watcher is running**:
   ```bash
   ps aux | grep watch_inbox.py
   ```

2. **Wait for polling cycle** (30-60 seconds default)

3. **Check watcher logs**:
   ```bash
   tail -f ~/my-vault/Logs/watcher-$(date +%Y-%m-%d).md
   ```

4. **Check file extension** (must be .md):
   ```bash
   ls ~/my-vault/Inbox/
   ```

### "Dashboard shows old tasks I already moved"

**Cause**: Dashboard updates on watcher cycle (30 seconds delay).

**Solution**: Wait 30-60 seconds, refresh Dashboard.md in Obsidian.

### "Watcher keeps logging 'File locked' warnings"

**Cause**: Obsidian has file open for editing.

**Solution**: Close file in Obsidian, watcher will retry on next cycle.

### "Vault size exceeds 1000 files"

**Cause**: Bronze tier performance limit reached.

**Solution**:
1. Archive old Done/ tasks to external folder
2. Upgrade to Silver tier for better performance

---

## Next Steps

- **Setup**: See [bronze-setup.md](./bronze-setup.md) for installation guide
- **Testing**: See [bronze-testing.md](./bronze-testing.md) for test suite
- **Architecture**: See [bronze-architecture.md](./bronze-architecture.md) for technical details
