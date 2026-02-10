"""Agent Skills API for Bronze Tier Personal AI Employee.

This module provides read-only functions for Claude Code to query vault data:
- read_vault_file(): Read markdown file content
- list_vault_folder(): List .md files in a folder
- get_dashboard_summary(): Parse Dashboard.md task counts
- validate_handbook(): Check Company_Handbook.md sections

All functions are pure (no side effects) and operate on local filesystem only.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


ALLOWED_FOLDERS = ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]
REQUIRED_HANDBOOK_SECTIONS = [
    "file naming convention",
    "folder usage guidelines",
    "forbidden operations",
    "escalation rules",
    "bronze tier limitations"
]


def read_vault_file(vault_path: str, filepath: str) -> str:
    """Read markdown file from vault.

    Args:
        vault_path: Absolute path to vault root directory
        filepath: Relative path from vault root (e.g., "Inbox/task.md")

    Returns:
        File content as UTF-8 string

    Raises:
        FileNotFoundError: If file doesn't exist at vault_path/filepath
        PermissionError: If file is locked by Obsidian (unreadable)
        UnicodeDecodeError: If file is not valid UTF-8 encoding
        ValueError: If filepath attempts directory traversal (e.g., "../etc/passwd")

    Example:
        >>> content = read_vault_file("/path/to/vault", "Inbox/task.md")
        >>> print(content[:50])
        # Task: Review Proposal

        Due: 2026-02-15
    """
    # Security: Prevent directory traversal
    if ".." in filepath or filepath.startswith("/"):
        raise ValueError(
            f"Invalid filepath: directory traversal detected in '{filepath}'"
        )

    # Construct full path
    vault = Path(vault_path).resolve()
    full_path = (vault / filepath).resolve()

    # Validate path is within vault
    if not str(full_path).startswith(str(vault)):
        raise ValueError(
            f"Invalid filepath: path escapes vault directory: '{filepath}'"
        )

    # Check file exists
    if not full_path.exists():
        raise FileNotFoundError(
            f"File not found: {filepath} (vault: {vault_path})"
        )

    # Check file is not too large (10MB limit)
    if full_path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError(
            f"File too large: {filepath} ({full_path.stat().st_size} bytes, max 10MB)"
        )

    # Read UTF-8 content
    try:
        return full_path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(
            f"File locked or not readable: {filepath}"
        ) from e
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"Invalid UTF-8 encoding in file: {filepath}"
        ) from e


def list_vault_folder(vault_path: str, folder_name: str) -> List[str]:
    """List all .md files in a vault folder (non-recursive).

    Args:
        vault_path: Absolute path to vault root directory
        folder_name: One of ["Inbox", "Needs_Action", "Done", "Plans", "Logs"]

    Returns:
        List of filenames (not full paths), sorted alphabetically.
        Example: ["2026-02-10-task1.md", "2026-02-11-task2.md"]

    Raises:
        FileNotFoundError: If folder doesn't exist at vault_path/folder_name
        ValueError: If folder_name is not one of the 5 allowed folders
        PermissionError: If folder is not readable

    Example:
        >>> files = list_vault_folder("/path/to/vault", "Inbox")
        >>> print(files)
        ["2026-02-10-review-proposal.md", "2026-02-11-fix-bug.md"]
    """
    # Validate folder_name
    if folder_name not in ALLOWED_FOLDERS:
        raise ValueError(
            f"Invalid folder name: '{folder_name}'. "
            f"Must be one of: {', '.join(ALLOWED_FOLDERS)}"
        )

    # Construct folder path
    vault = Path(vault_path).resolve()
    folder_path = vault / folder_name

    # Check folder exists
    if not folder_path.exists():
        raise FileNotFoundError(
            f"Folder not found: {folder_name} (vault: {vault_path})"
        )

    # Check folder is readable
    if not folder_path.is_dir():
        raise ValueError(
            f"Not a directory: {folder_name} (vault: {vault_path})"
        )

    # List .md files (non-recursive)
    try:
        md_files = list(folder_path.glob("*.md"))
    except PermissionError as e:
        raise PermissionError(
            f"Folder not readable: {folder_name}"
        ) from e

    # Check file count limit (Bronze tier: 1000 files max)
    if len(md_files) > 1000:
        raise ValueError(
            f"Folder exceeds 1000 file limit: {folder_name} has {len(md_files)} files"
        )

    # Return sorted filenames (not full paths)
    return sorted([f.name for f in md_files])


def get_dashboard_summary(vault_path: str) -> Dict[str, int]:
    """Parse Dashboard.md and return task counts by status.

    Args:
        vault_path: Absolute path to vault root directory

    Returns:
        Dictionary with task counts:
        {
            "total": 5,
            "inbox": 2,
            "needs_action": 2,
            "done": 1
        }

    Raises:
        FileNotFoundError: If Dashboard.md doesn't exist at vault_path
        ValueError: If Dashboard.md is corrupted (invalid markdown table)

    Example:
        >>> summary = get_dashboard_summary("/path/to/vault")
        >>> print(f"You have {summary['inbox']} tasks in Inbox")
        You have 2 tasks in Inbox
    """
    # Construct Dashboard.md path
    vault = Path(vault_path).resolve()
    dashboard_path = vault / "Dashboard.md"

    # Check file exists
    if not dashboard_path.exists():
        raise FileNotFoundError(
            f"Dashboard.md not found in vault: {vault_path}"
        )

    # Read content
    try:
        content = dashboard_path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(
            "Dashboard.md is locked or not readable"
        ) from e

    # Initialize counts
    counts: Dict[str, int] = {
        "total": 0,
        "inbox": 0,
        "needs_action": 0,
        "done": 0
    }

    # Find markdown table (starts with "| Filename |")
    lines = content.split("\n")
    table_start = None

    for i, line in enumerate(lines):
        if line.strip().startswith("| Filename"):
            # Skip header and separator rows
            table_start = i + 2
            break

    # No table found (empty dashboard)
    if table_start is None:
        return counts

    # Parse table rows
    for line in lines[table_start:]:
        # Stop at end of table (empty line or non-table line)
        if not line.strip() or not line.strip().startswith("|"):
            break

        # Parse row: | Filename | Date Added | Status | Priority |
        columns = [col.strip() for col in line.split("|")[1:-1]]

        # Validate row has 4 columns
        if len(columns) != 4:
            continue  # Skip malformed rows

        # Extract status (3rd column, index 2)
        status = columns[2].lower().strip()

        # Increment counts
        counts["total"] += 1
        if status == "inbox":
            counts["inbox"] += 1
        elif status == "needs action":
            counts["needs_action"] += 1
        elif status == "done":
            counts["done"] += 1

    return counts


def validate_handbook(vault_path: str) -> Tuple[bool, List[str]]:
    """Check if Company_Handbook.md has all required sections.

    Args:
        vault_path: Absolute path to vault root directory

    Returns:
        Tuple of (is_valid, missing_sections):
        - is_valid: True if all 5 required sections present, False otherwise
        - missing_sections: List of missing section names (empty if is_valid=True)

    Raises:
        FileNotFoundError: If Company_Handbook.md doesn't exist at vault_path

    Example:
        >>> is_valid, missing = validate_handbook("/path/to/vault")
        >>> if not is_valid:
        ...     print(f"Handbook missing sections: {', '.join(missing)}")
        Handbook missing sections: Escalation Rules, Bronze Tier Limitations

    Required Sections (case-insensitive):
        1. "File Naming Convention"
        2. "Folder Usage Guidelines"
        3. "Forbidden Operations (Bronze Tier)" or "Forbidden Operations"
        4. "Escalation Rules"
        5. "Bronze Tier Limitations"
    """
    # Construct Company_Handbook.md path
    vault = Path(vault_path).resolve()
    handbook_path = vault / "Company_Handbook.md"

    # Check file exists
    if not handbook_path.exists():
        raise FileNotFoundError(
            f"Company_Handbook.md not found in vault: {vault_path}"
        )

    # Read content
    try:
        content = handbook_path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(
            "Company_Handbook.md is locked or not readable"
        ) from e

    # Extract markdown headers (lines starting with ##)
    headers: List[str] = []
    for line in content.split("\n"):
        if re.match(r"^##+ ", line):
            # Remove markdown prefix and numbering
            header_text = re.sub(r"^##+ (\d+\. )?", "", line).strip()
            headers.append(header_text.lower())

    # Check for required sections (case-insensitive, fuzzy match)
    missing: List[str] = []
    for required in REQUIRED_HANDBOOK_SECTIONS:
        found = any(required in header for header in headers)
        if not found:
            missing.append(required.title())

    return (len(missing) == 0, missing)
