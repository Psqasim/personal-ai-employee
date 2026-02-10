# Bronze Tier Testing Guide

Comprehensive testing guide for unit tests, integration tests, and manual end-to-end validation.

## Testing Overview

Bronze tier test suite:
- **Unit tests**: Test individual functions in isolation (agent_skills/ modules)
- **Integration tests**: Test end-to-end workflows (drop file → detect → update → query)
- **Manual tests**: Human verification with Obsidian
- **Performance tests**: Verify response times and resource usage

**Target Coverage**: 80%+ for all agent_skills/ modules (enforced by CI)

## Prerequisites

```bash
# Install test dependencies
pip install -e .[dev]

# Verify pytest installation
pytest --version
```

## Unit Testing

### Run All Unit Tests

```bash
# Run all unit tests with coverage
pytest tests/unit/ --cov=agent_skills --cov-report=term-missing

# Run with verbose output
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_vault_watcher.py -v
```

Expected output:
```
tests/unit/test_vault_watcher.py::test_read_valid_file PASSED
tests/unit/test_vault_watcher.py::test_read_missing_file PASSED
tests/unit/test_vault_watcher.py::test_list_inbox_folder PASSED
tests/unit/test_vault_watcher.py::test_get_dashboard_summary PASSED
tests/unit/test_vault_watcher.py::test_validate_handbook PASSED

---------- coverage: platform linux, python 3.11.7-final-0 ----------
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
agent_skills/__init__.py                0      0   100%
agent_skills/vault_watcher.py         120     12    90%   45-48, 156-160
agent_skills/dashboard_updater.py     150     18    88%   78-82, 201-205
-----------------------------------------------------------------
TOTAL                                 270     30    89%

============================== 20 passed in 2.45s ==============================
```

### Test Fixtures

Unit tests use sample vault in `tests/fixtures/sample_vault/`:

```
tests/fixtures/sample_vault/
├── Inbox/
│   └── test-task.md
├── Needs_Action/
│   └── urgent-task.md
├── Done/
│   └── completed-task.md
├── Plans/
├── Logs/
├── Dashboard.md
└── Company_Handbook.md
```

### Key Unit Tests

#### vault_watcher.py Tests

```bash
# Test read_vault_file()
pytest tests/unit/test_vault_watcher.py::test_read_valid_file
pytest tests/unit/test_vault_watcher.py::test_read_missing_file
pytest tests/unit/test_vault_watcher.py::test_directory_traversal_attack

# Test list_vault_folder()
pytest tests/unit/test_vault_watcher.py::test_list_inbox_folder
pytest tests/unit/test_vault_watcher.py::test_list_invalid_folder_name

# Test get_dashboard_summary()
pytest tests/unit/test_vault_watcher.py::test_summary_with_tasks
pytest tests/unit/test_vault_watcher.py::test_summary_empty_dashboard

# Test validate_handbook()
pytest tests/unit/test_vault_watcher.py::test_validate_complete_handbook
pytest tests/unit/test_vault_watcher.py::test_validate_missing_sections
```

#### dashboard_updater.py Tests

```bash
# Test atomic writes
pytest tests/unit/test_dashboard_updater.py::test_update_creates_backup
pytest tests/unit/test_dashboard_updater.py::test_update_idempotency

# Test corruption recovery
pytest tests/unit/test_dashboard_updater.py::test_update_corruption_recovery
pytest tests/unit/test_dashboard_updater.py::test_restore_from_backup
```

### Writing New Unit Tests

Example unit test structure:

```python
# tests/unit/test_vault_watcher.py
import pytest
from pathlib import Path
from agent_skills.vault_watcher import read_vault_file

def test_read_valid_file(sample_vault):
    """Test reading a valid markdown file."""
    content = read_vault_file(str(sample_vault), "Inbox/test-task.md")

    assert isinstance(content, str)
    assert "# Test Task" in content
    assert len(content) > 0

def test_read_missing_file(sample_vault):
    """Test reading non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_vault_file(str(sample_vault), "Inbox/nonexistent.md")

def test_directory_traversal_attack(sample_vault):
    """Test path traversal protection."""
    with pytest.raises(ValueError, match="directory traversal"):
        read_vault_file(str(sample_vault), "../../etc/passwd")
```

## Integration Testing

### Run Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_end_to_end.py::test_drop_file_detect_update_query -v

# Run with detailed logs
pytest tests/integration/ -v -s
```

### End-to-End Flow Test

**Test**: `test_drop_file_detect_update_query`

**What it tests**:
1. Initialize vault with `init_vault()`
2. Start watcher in background thread
3. Drop test file in Inbox/
4. Wait 35 seconds (30s polling + 5s buffer)
5. Verify Dashboard.md updated with new task
6. Verify `get_dashboard_summary()` returns correct counts
7. Verify watcher log exists with "File Detected" event

**Run manually**:
```bash
pytest tests/integration/test_end_to_end.py::test_drop_file_detect_update_query -v -s
```

Expected output:
```
tests/integration/test_end_to_end.py::test_drop_file_detect_update_query
  Setup: Initializing test vault...
  Setup: Starting watcher in background...
  Action: Dropping test file in Inbox/...
  Waiting: 35 seconds for detection and update...
  Assert: Dashboard.md contains new task ✓
  Assert: get_dashboard_summary() returns {"inbox": 1, "total": 1} ✓
  Assert: Watcher log contains "File Detected" event ✓
PASSED [100%]
```

### Race Condition Test

**Test**: `test_simultaneous_file_detection`

**What it tests**: Add 10 files to Inbox/ at once, verify all detected without dropped events.

```bash
pytest tests/integration/test_end_to_end.py::test_simultaneous_file_detection -v
```

### File Lock Handling Test

**Test**: `test_file_lock_graceful_degradation`

**What it tests**: Lock a file (simulate Obsidian lock), verify watcher logs warning and continues.

```bash
pytest tests/integration/test_end_to_end.py::test_file_lock_graceful_degradation -v
```

### Performance Test

**Test**: `test_vault_with_1000_files`

**What it tests**: Create vault with 1000 files, measure dashboard update time (must be <2 seconds).

```bash
pytest tests/integration/test_performance.py::test_vault_with_1000_files -v
```

## Manual End-to-End Testing

### Scenario: User's First Run

**Purpose**: Verify complete setup and usage workflow from a user's perspective.

#### Step 1: Initialize Vault

```bash
python3 scripts/init_vault.py /tmp/test-vault
```

**Expected**:
- Terminal output: "Vault initialized at /tmp/test-vault"
- Folders created: Inbox/, Needs_Action/, Done/, Plans/, Logs/
- Files created: Dashboard.md, Company_Handbook.md

#### Step 2: Start Watcher

```bash
python3 scripts/watch_inbox.py /tmp/test-vault
```

**Expected**:
- Terminal output: "Watcher started"
- No error messages
- Process continues running (don't exit)

#### Step 3: Drop Test File

In a new terminal:

```bash
echo "# Test Task

Due: 2026-02-15

Review client proposal and provide feedback." > /tmp/test-vault/Inbox/2026-02-10-review-proposal.md
```

#### Step 4: Wait and Verify

**Wait 30-60 seconds** (one polling cycle)

**Check watcher terminal output**:
```
[2026-02-10 15:30:45] File Detected
- File: Inbox/2026-02-10-review-proposal.md
- Size: 62 bytes
- Encoding: UTF-8

[2026-02-10 15:30:47] Dashboard Updated
- New tasks: 1
- Total tasks: 1
- Update time: 1.8 seconds
```

**Check Dashboard.md**:
```bash
cat /tmp/test-vault/Dashboard.md
```

Expected content:
```markdown
# Personal AI Employee Dashboard

## Task Overview
| Filename | Date Added | Status | Priority |
|----------|-----------|--------|----------|
| [[Inbox/2026-02-10-review-proposal.md]] | 2026-02-10 15:30 | Inbox | Medium |

## Statistics
- **Total Tasks**: 1
- **Inbox**: 1
- **Needs Action**: 0
- **Done**: 0
```

**Check watcher log**:
```bash
cat /tmp/test-vault/Logs/watcher-$(date +%Y-%m-%d).md
```

Expected content:
```markdown
## 15:30:00 - Watcher Started
- Vault path: /tmp/test-vault
- Polling interval: 30 seconds

## 15:30:45 - File Detected
- File: Inbox/2026-02-10-review-proposal.md

## 15:30:47 - Dashboard Updated
- New tasks: 1
- Total tasks: 1
```

#### Step 5: Verify in Obsidian

1. Open Obsidian Desktop App
2. **Open folder as vault** → Select `/tmp/test-vault`
3. Open `Dashboard.md`
4. Verify markdown table renders correctly
5. Click on `[[Inbox/2026-02-10-review-proposal.md]]` link
6. Verify task file opens

**Expected**: All markdown renders correctly, links are clickable, no syntax errors.

#### Step 6: Stop Watcher

In watcher terminal, press **Ctrl+C**

**Expected**:
```
^C
[2026-02-10 15:35:00] Watcher Stopped
- Reason: SIGINT received
- Uptime: 5 minutes
- Total files processed: 1
```

**Success**: Manual end-to-end test passed ✓

## Troubleshooting Common Issues

### Test Failures

#### "FileNotFoundError: fixtures/sample_vault not found"

**Cause**: Test fixtures not initialized

**Fix**:
```bash
pytest tests/unit/ --fixtures-only  # Generate fixtures
pytest tests/unit/                  # Re-run tests
```

#### "AssertionError: Dashboard.md not updated after 35 seconds"

**Cause**: Watcher not starting in test environment

**Fix**:
1. Check Python version: `python --version` (must be 3.11+)
2. Check watchdog installed: `pip show watchdog`
3. Run test with debug logs: `pytest tests/integration/ -v -s --log-cli-level=DEBUG`

#### "Coverage below 80% threshold"

**Cause**: New code added without tests

**Fix**:
```bash
# Identify uncovered lines
pytest --cov=agent_skills --cov-report=html
open htmlcov/index.html  # View coverage report

# Add tests for uncovered lines in tests/unit/
```

### Integration Test Timeouts

If integration tests fail with timeout:

1. **Increase wait time** (if running on slow hardware):
   ```python
   # tests/integration/test_end_to_end.py
   time.sleep(60)  # Increase from 35 to 60 seconds
   ```

2. **Check watcher is actually running**:
   ```python
   assert watcher_thread.is_alive(), "Watcher thread died"
   ```

3. **Check logs**:
   ```bash
   pytest tests/integration/ -v -s --log-cli-level=DEBUG
   ```

### Type Checking Errors

Run mypy to check for type errors:

```bash
mypy agent_skills/ scripts/
```

Common errors:

- **"Missing return type"**: Add `-> ReturnType` to function
- **"Incompatible types"**: Fix type annotation (e.g., `str` vs `Path`)

## Test Coverage Report

Generate HTML coverage report:

```bash
pytest --cov=agent_skills --cov-report=html
open htmlcov/index.html
```

Coverage summary:
```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
agent_skills/__init__.py                0      0   100%
agent_skills/vault_watcher.py         120     12    90%
agent_skills/dashboard_updater.py     150     18    88%
-------------------------------------------------------
TOTAL                                 270     30    89%
```

**Target**: All modules ≥80% coverage

## Continuous Integration

### Pre-commit Checks

Before committing code:

```bash
# Run all tests
pytest

# Check coverage
pytest --cov=agent_skills --cov-report=term-missing

# Type checking
mypy agent_skills/ scripts/

# Code formatting
black --check agent_skills/ scripts/ tests/
```

### CI Pipeline

GitHub Actions workflow (`.github/workflows/bronze-tests.yml`):

```yaml
name: Bronze Tier Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest --cov=agent_skills --cov-report=xml
      - run: mypy agent_skills/ scripts/
      - run: black --check agent_skills/ scripts/ tests/
```

## Performance Benchmarks

### Dashboard Update Time

**Target**: <2 seconds

**Measure**:
```bash
pytest tests/integration/test_performance.py::test_dashboard_update_time -v
```

**Results**:
```
Dashboard update time: 1.8 seconds ✓
Target: <2 seconds ✓
```

### Vault Scan Time

**Target**: <5 seconds for 1000 files

**Measure**:
```bash
pytest tests/integration/test_performance.py::test_vault_scan_time -v
```

### Memory Usage

**Target**: <100MB

**Measure**:
```bash
# Start watcher
python3 scripts/watch_inbox.py ~/my-vault &
PID=$!

# Monitor memory usage
ps aux | grep $PID | awk '{print $6 " KB"}'
```

Expected: 40-80 MB (well under 100MB target)

## Next Steps

- **Architecture**: See [bronze-architecture.md](./bronze-architecture.md) for component design
- **Usage**: See [bronze-usage.md](./bronze-usage.md) for daily workflow
- **Setup**: See [bronze-setup.md](./bronze-setup.md) for installation guide
