# Bronze Tier Architecture

Technical architecture, component design, data flow, and API reference for the Bronze tier Personal AI Employee system.

## System Overview

Bronze Tier is a **local-first monitoring system** that watches an Obsidian vault for new markdown files and maintains an up-to-date dashboard. The architecture prioritizes vault integrity, offline operation, and atomic writes.

**Design Principles**:
- **Vault Integrity First**: Atomic writes with backups, no data corruption
- **100% Offline**: Zero network requests, all processing local
- **Read-Heavy**: Minimal writes (Dashboard.md, Logs/ only)
- **No Autonomous Actions**: Human approval required for all operations

## Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     User Interactions                         │
├──────────────────────────────────────────────────────────────┤
│  [Drop .md file]  [Edit Handbook]  [Query via Claude Code]  │
└────────┬──────────────────┬─────────────────────┬────────────┘
         │                  │                     │
         v                  v                     v
┌────────────────┐  ┌───────────────┐   ┌──────────────────┐
│  File Watcher  │  │   Handbook    │   │  Agent Skills    │
│ (watch_inbox.py)◄──┤  Validator    │   │  (vault_watcher) │
└────────┬───────┘  └───────────────┘   └────────┬─────────┘
         │                                        │
         │ Detects new files                     │ Reads vault
         │                                        │
         v                                        v
┌────────────────────────────────────────────────────────────┐
│                    Vault Filesystem                        │
├────────────────────────────────────────────────────────────┤
│  Inbox/  Needs_Action/  Done/  Plans/  Logs/              │
│  Dashboard.md  Company_Handbook.md                         │
└────────┬───────────────────────────────────────────────────┘
         │
         v
┌────────────────────┐
│ Dashboard Updater  │
│(dashboard_updater) │
│  - Atomic Writes   │
│  - Backups (.bak)  │
│  - Corruption Check│
└────────────────────┘
```

## Data Flow

### 1. File Detection Flow

```
[User drops file in Inbox/]
         │
         v
[File Watcher polls every 30s]
         │
         v
[Detect new .md files]
         │
         v
[Filter: Ignore non-.md, .git/, .obsidian/]
         │
         v
[Log to vault/Logs/watcher-YYYY-MM-DD.md]
         │
         v
[Trigger Dashboard Update]
```

### 2. Dashboard Update Flow (Atomic Write)

```
[Update Requested]
         │
         v
[Create Backup: Dashboard.md → Dashboard.md.bak.TIMESTAMP]
         │
         v
[Parse Current Dashboard.md → Extract Task Table]
         │
         v
[Merge New Tasks + Existing Tasks]
         │
         v
[Recalculate Statistics (Total, Inbox, Needs Action, Done)]
         │
         v
[Render Markdown Table → Write to Dashboard.md.tmp]
         │
         v
[Validate Dashboard.md.tmp (Check Markdown Syntax)]
         │
         v
[Atomic Rename: Dashboard.md.tmp → Dashboard.md]
         │
         v
[Log Success to vault/Logs/]
```

### 3. Claude Code Query Flow

```
[Claude Code invokes Agent Skill function]
         │
         v
[read_vault_file() | list_vault_folder() | get_dashboard_summary()]
         │
         v
[Read from vault/ filesystem]
         │
         v
[Return data to Claude Code]
         │
         v
[Claude generates response to user]
```

### 4. Error Recovery Flow

```
[Dashboard.md Corruption Detected]
         │
         v
[List all Dashboard.md.bak.* files]
         │
         v
[Sort by timestamp (newest first)]
         │
         v
[Copy most recent .bak → Dashboard.md.tmp]
         │
         v
[Validate Dashboard.md.tmp]
         │
         v
[Atomic Rename: Dashboard.md.tmp → Dashboard.md]
         │
         v
[Log Recovery Event]
```

## File Structure

### Source Code Organization

```
personal-ai-employee/
│
├── agent_skills/              # Reusable Python modules (importable)
│   ├── __init__.py            # Package initialization
│   ├── vault_watcher.py       # Agent Skills API (4 functions)
│   └── dashboard_updater.py   # Dashboard manipulation (atomic writes)
│
├── scripts/                   # Entry points (executable, not importable)
│   ├── init_vault.py          # One-time vault setup
│   └── watch_inbox.py         # Continuous monitoring daemon
│
├── tests/                     # Pytest test suite
│   ├── unit/                  # Unit tests for agent_skills/
│   │   ├── test_vault_watcher.py
│   │   └── test_dashboard_updater.py
│   ├── integration/           # End-to-end tests
│   │   ├── test_end_to_end.py
│   │   └── test_performance.py
│   └── fixtures/              # Test data (sample vaults)
│       └── sample_vault/
│
├── vault/                     # Product deliverable (Obsidian vault)
│   ├── Inbox/                 # Monitored folder (user drops tasks)
│   ├── Needs_Action/          # Manual move (Bronze tier)
│   ├── Done/                  # Manual move (Bronze tier)
│   ├── Plans/                 # Reserved for Silver+ tiers
│   ├── Logs/                  # System-generated logs
│   │   └── watcher-YYYY-MM-DD.md
│   ├── Dashboard.md           # Auto-maintained task table
│   └── Company_Handbook.md    # Human-editable configuration
│
├── docs/                      # Documentation
│   └── bronze/
│       ├── bronze-setup.md
│       ├── bronze-testing.md
│       ├── bronze-architecture.md  # This file
│       └── bronze-usage.md
│
├── pyproject.toml             # Python project configuration
├── mypy.ini                   # Type checking configuration
└── README.md                  # Getting started guide
```

### Vault Structure (Product)

```
vault/
│
├── Inbox/                     # User drops new tasks here
│   ├── 2026-02-10-task1.md
│   └── 2026-02-11-task2.md
│
├── Needs_Action/              # Tasks requiring immediate attention
│   └── 2026-02-09-urgent.md
│
├── Done/                      # Completed tasks (archived)
│   └── 2026-02-08-finished.md
│
├── Plans/                     # Reserved (Silver+ tiers)
│
├── Logs/                      # System-generated logs (append-only)
│   ├── watcher-2026-02-10.md
│   └── watcher-2026-02-11.md
│
├── Dashboard.md               # Auto-updated task overview
├── Dashboard.md.bak.2026-02-10_15-30-00  # Backup files
├── Dashboard.md.bak.2026-02-11_09-15-00
│
└── Company_Handbook.md        # Configuration file
```

## Module Architecture

### agent_skills/vault_watcher.py

**Purpose**: Agent Skills API for Claude Code integration (read-only operations)

**Functions**:

#### `read_vault_file(vault_path: str, filepath: str) -> str`

Reads markdown file content from vault.

**Implementation**:
```python
def read_vault_file(vault_path: str, filepath: str) -> str:
    # 1. Validate filepath (no directory traversal)
    if ".." in filepath or filepath.startswith("/"):
        raise ValueError("Invalid filepath: directory traversal detected")

    # 2. Construct full path
    full_path = Path(vault_path) / filepath

    # 3. Check file exists
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # 4. Read UTF-8 content
    try:
        return full_path.read_text(encoding="utf-8")
    except PermissionError:
        raise PermissionError(f"File locked: {filepath}")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Invalid UTF-8 encoding: {filepath}")
```

#### `list_vault_folder(vault_path: str, folder_name: str) -> list[str]`

Lists .md files in a vault folder.

**Implementation**:
```python
def list_vault_folder(vault_path: str, folder_name: str) -> list[str]:
    # 1. Validate folder_name
    ALLOWED_FOLDERS = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]
    if folder_name not in ALLOWED_FOLDERS:
        raise ValueError(f"Invalid folder: {folder_name}")

    # 2. Construct folder path
    folder_path = Path(vault_path) / folder_name

    # 3. Check folder exists
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_name}")

    # 4. List .md files (non-recursive)
    md_files = folder_path.glob("*.md")

    # 5. Return sorted filenames (not full paths)
    return sorted([f.name for f in md_files])
```

#### `get_dashboard_summary(vault_path: str) -> dict[str, int]`

Parses Dashboard.md and returns task counts.

**Implementation**:
```python
def get_dashboard_summary(vault_path: str) -> dict[str, int]:
    # 1. Read Dashboard.md
    dashboard_path = Path(vault_path) / "Dashboard.md"
    content = dashboard_path.read_text(encoding="utf-8")

    # 2. Find markdown table
    lines = content.split("\n")
    table_start = None
    for i, line in enumerate(lines):
        if line.startswith("| Filename"):
            table_start = i + 2  # Skip header and separator
            break

    # 3. Parse task rows
    tasks = {"total": 0, "inbox": 0, "needs_action": 0, "done": 0}
    for line in lines[table_start:]:
        if not line.startswith("|"):
            break
        columns = [col.strip() for col in line.split("|")[1:-1]]
        if len(columns) == 4:
            status = columns[2].lower()
            tasks["total"] += 1
            if status == "inbox":
                tasks["inbox"] += 1
            elif status == "needs action":
                tasks["needs_action"] += 1
            elif status == "done":
                tasks["done"] += 1

    return tasks
```

#### `validate_handbook(vault_path: str) -> tuple[bool, list[str]]`

Validates Company_Handbook.md structure.

**Implementation**:
```python
def validate_handbook(vault_path: str) -> tuple[bool, list[str]]:
    # 1. Read Company_Handbook.md
    handbook_path = Path(vault_path) / "Company_Handbook.md"
    content = handbook_path.read_text(encoding="utf-8")

    # 2. Extract markdown headers
    headers = []
    for line in content.split("\n"):
        if line.startswith("##"):
            headers.append(line.strip("# ").lower())

    # 3. Check required sections
    REQUIRED_SECTIONS = [
        "file naming convention",
        "folder usage guidelines",
        "forbidden operations",
        "escalation rules",
        "bronze tier limitations"
    ]

    missing = []
    for section in REQUIRED_SECTIONS:
        found = any(section in header.lower() for header in headers)
        if not found:
            missing.append(section)

    return (len(missing) == 0, missing)
```

---

### agent_skills/dashboard_updater.py

**Purpose**: Dashboard.md manipulation with atomic writes and backups

**Functions**:

#### `update_dashboard(vault_path: str, new_files: list[tuple[str, str]]) -> bool`

Atomically updates Dashboard.md with new tasks.

**Algorithm**:
1. Create backup: `Dashboard.md → Dashboard.md.bak.TIMESTAMP`
2. Parse current `Dashboard.md` (extract task table)
3. Merge new tasks with existing tasks
4. Recalculate statistics (Total, Inbox, Needs Action, Done)
5. Render markdown table
6. Write to `Dashboard.md.tmp` (temporary file)
7. Validate `Dashboard.md.tmp` (check markdown syntax)
8. Atomic rename: `Dashboard.md.tmp → Dashboard.md`
9. Return True (or False if any step fails)

**Key Implementation Detail**:
```python
# Step 8: Atomic rename (POSIX guarantees atomicity)
temp_path.replace(dashboard_path)  # Atomic operation
```

#### `create_backup(dashboard_path: Path) -> Path`

Creates timestamped backup file.

**Implementation**:
```python
def create_backup(dashboard_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = dashboard_path.with_name(f"Dashboard.md.bak.{timestamp}")
    shutil.copy2(dashboard_path, backup_path)
    return backup_path
```

#### `restore_from_backup(vault_path: str, backup_filename: str = None) -> bool`

Restores Dashboard.md from most recent backup.

**Algorithm**:
1. List all `Dashboard.md.bak.*` files
2. Sort by timestamp (newest first)
3. Copy backup → `Dashboard.md.tmp`
4. Validate `Dashboard.md.tmp`
5. Atomic rename: `Dashboard.md.tmp → Dashboard.md`

---

### scripts/watch_inbox.py

**Purpose**: Continuous monitoring daemon with 30-second polling

**Functions**:

#### `poll_inbox(vault_path: Path, config: dict) -> None`

Main polling loop.

**Algorithm**:
```python
while True:
    try:
        # Detect new files
        new_files = detect_new_files(vault_path, processed_files)

        if new_files:
            # Log detection
            log_event(vault_path, "file_detected", {"files": new_files})

            # Update dashboard
            success = update_dashboard(vault_path, new_files)

            if success:
                log_event(vault_path, "dashboard_updated", {"count": len(new_files)})
                processed_files.update([f[0] for f in new_files])
            else:
                log_event(vault_path, "dashboard_update_failed", {"files": new_files})

    except Exception as e:
        # Graceful degradation: log error, continue
        log_event(vault_path, "error", {"message": str(e)})

    # Sleep until next cycle
    time.sleep(config.get("polling_interval", 30))
```

#### `detect_new_files(vault_path: Path, processed_files: set) -> list[tuple[str, str]]`

Detects new .md files in Inbox/.

**Implementation**:
```python
def detect_new_files(vault_path: Path, processed_files: set) -> list[tuple[str, str]]:
    inbox_path = vault_path / "Inbox"
    all_files = inbox_path.glob("*.md")

    new_files = []
    for file_path in all_files:
        if file_path.name not in processed_files:
            new_files.append((f"Inbox/{file_path.name}", "Inbox"))

    return new_files
```

#### `log_event(vault_path: Path, event_type: str, details: dict) -> None`

Logs events to daily log file.

**Implementation**:
```python
def log_event(vault_path: Path, event_type: str, details: dict) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    log_path = vault_path / "Logs" / f"watcher-{date_str}.md"

    event_log = f"## {time_str} - {event_type.replace('_', ' ').title()}\n"
    for key, value in details.items():
        event_log += f"- {key.replace('_', ' ').title()}: {value}\n"
    event_log += "\n"

    # Append to log file (create if doesn't exist)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(event_log)
```

## API Reference

### Agent Skills API

All functions in `agent_skills/vault_watcher.py`:

| Function | Input | Output | Raises |
|----------|-------|--------|--------|
| `read_vault_file(vault_path, filepath)` | `str, str` | `str` | `FileNotFoundError`, `PermissionError`, `ValueError` |
| `list_vault_folder(vault_path, folder_name)` | `str, str` | `list[str]` | `ValueError`, `FileNotFoundError` |
| `get_dashboard_summary(vault_path)` | `str` | `dict[str, int]` | `FileNotFoundError`, `ValueError` |
| `validate_handbook(vault_path)` | `str` | `tuple[bool, list[str]]` | `FileNotFoundError` |

### Dashboard Updater API

All functions in `agent_skills/dashboard_updater.py`:

| Function | Input | Output | Notes |
|----------|-------|--------|-------|
| `update_dashboard(vault_path, new_files)` | `str, list[tuple[str, str]]` | `bool` | Atomic write with backup |
| `create_backup(dashboard_path)` | `Path` | `Path` | Creates timestamped .bak file |
| `restore_from_backup(vault_path, backup_filename)` | `str, Optional[str]` | `bool` | Restores from most recent .bak |
| `parse_dashboard(dashboard_path)` | `Path` | `list[dict]` | Internal helper function |
| `render_dashboard(tasks)` | `list[dict]` | `str` | Internal helper function |

### Watcher Entry Points

Scripts in `scripts/`:

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `init_vault.py` | One-time vault setup | `0` = success, `1` = path exists, `3` = permission error |
| `watch_inbox.py` | Continuous monitoring | `0` = graceful stop, `1` = invalid vault, `2` = handbook validation failed, `3` = permission error |

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| File detection | O(n) | n = number of files in Inbox/ |
| Dashboard parsing | O(m) | m = number of lines in Dashboard.md |
| Dashboard update | O(n + m) | Merge existing + new tasks |
| Backup creation | O(k) | k = size of Dashboard.md (typically <100KB) |

### Space Complexity

| Component | Memory Usage | Notes |
|-----------|-------------|-------|
| Watcher process | 40-80 MB | Python interpreter + libraries |
| Processed files set | O(n) | n = number of processed files |
| Dashboard task list | O(m) | m = number of tasks in dashboard |

### I/O Operations

| Operation | Frequency | Performance Target |
|-----------|----------|-------------------|
| Poll Inbox/ | Every 30 seconds | <100ms |
| Read Dashboard.md | On every update | <200ms |
| Write Dashboard.md | Per new file | <2 seconds (atomic write) |
| Create backup | Per update | <500ms |

## Security Model

### Filesystem Isolation

**Principle**: System only accesses `vault/` directory.

**Enforcement**:
- Path validation: All functions reject paths with `..` or leading `/`
- No shell commands: All file operations use Python `pathlib` (no `os.system()`)
- Read-only except Dashboard.md and Logs/: Other folders are never written to

### Offline Operation

**Principle**: Zero network requests (100% offline).

**Verification**:
```bash
# Monitor network traffic during watcher runtime
tcpdump -i any -n host $(hostname) &
python3 scripts/watch_inbox.py ~/my-vault

# Expected: Zero packets sent/received
```

### No Code Execution

**Principle**: Never execute vault contents.

**Enforcement**:
- No `eval()` or `exec()` calls in codebase
- Markdown files treated as data only (not code)
- YAML frontmatter parsed with `pyyaml` (safe loader)

## Next Steps

- **Setup**: See [bronze-setup.md](./bronze-setup.md) for installation guide
- **Usage**: See [bronze-usage.md](./bronze-usage.md) for daily workflow
- **Testing**: See [bronze-testing.md](./bronze-testing.md) for test suite
