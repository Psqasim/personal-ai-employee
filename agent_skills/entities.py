"""
Platinum Tier - Entity Definitions
Defines all data models for dual-agent architecture
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ========================================
# ENUMS
# ========================================

class SyncStatus(Enum):
    """Git sync state"""
    SYNCED = "synced"
    DIVERGED = "diverged"
    CONFLICT = "conflict"
    OFFLINE = "offline"


class ApprovalStatus(Enum):
    """Dashboard approval workflow states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    FAILED = "failed"


class HealthStatus(Enum):
    """MCP server and service health"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


# ========================================
# CLOUD AGENT
# ========================================

@dataclass
class CloudAgent:
    """
    Cloud Agent (Oracle VM, 24/7 always-on)
    Role: Email triage, social drafts, Git push
    Security: NO send credentials (SMTP, WhatsApp session, banking)
    """
    agent_id: str = "cloud"  # Hardcoded
    vault_path: str = "/opt/personal-ai-employee/vault"
    git_remote_url: str = ""
    whatsapp_notification_number: str = ""
    anthropic_api_key: str = ""
    last_sync_timestamp: Optional[datetime] = None
    uptime_hours: int = 0

    def __post_init__(self):
        """Validate Cloud Agent configuration"""
        if self.agent_id != "cloud":
            raise ValueError(f"Cloud Agent ID must be 'cloud', got '{self.agent_id}'")
        if not self.git_remote_url.startswith("git@"):
            raise ValueError("git_remote_url must be SSH format (git@...)")
        if self.anthropic_api_key and not self.anthropic_api_key.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")


# ========================================
# LOCAL AGENT
# ========================================

@dataclass
class LocalAgent:
    """
    Local Agent (User's laptop, on-demand)
    Role: Approvals, MCP execution, final send/post actions
    Security: HAS ALL credentials (SMTP, WhatsApp, Social, Odoo, Banking)
    """
    agent_id: str = "local"  # Hardcoded
    vault_path: str = ""
    mcp_servers: List[str] = field(default_factory=list)
    session_files_path: str = ""
    last_online_timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Validate Local Agent configuration"""
        if self.agent_id != "local":
            raise ValueError(f"Local Agent ID must be 'local', got '{self.agent_id}'")
        if not self.mcp_servers:
            raise ValueError("Local Agent must have at least one MCP server configured")


# ========================================
# GIT SYNC STATE
# ========================================

@dataclass
class GitSyncState:
    """
    Git synchronization state between Cloud, Local, and remote
    Tracks commits, conflicts, and sync status
    """
    sync_id: str
    last_pull_timestamp: Optional[datetime] = None
    last_push_timestamp: Optional[datetime] = None
    commit_hash_cloud: str = ""
    commit_hash_local: str = ""
    pending_conflicts: List[str] = field(default_factory=list)
    sync_status: SyncStatus = SyncStatus.SYNCED

    def __post_init__(self):
        """Validate Git sync state"""
        if self.commit_hash_cloud and len(self.commit_hash_cloud) != 40:
            raise ValueError(f"Invalid commit hash (cloud): {self.commit_hash_cloud}")
        if self.commit_hash_local and len(self.commit_hash_local) != 40:
            raise ValueError(f"Invalid commit hash (local): {self.commit_hash_local}")

    def is_synced(self) -> bool:
        """Check if Cloud and Local are in sync"""
        return self.commit_hash_cloud == self.commit_hash_local and not self.pending_conflicts

    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts"""
        return len(self.pending_conflicts) > 0


# ========================================
# DASHBOARD APPROVAL
# ========================================

@dataclass
class DashboardApproval:
    """
    Single pending approval displayed in Next.js dashboard
    Derived from vault files in /Pending_Approval/
    """
    approval_id: str
    category: str  # Email, LinkedIn, WhatsApp, Odoo, Social
    title: str
    preview_text: str
    timestamp: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    file_path: str = ""

    def __post_init__(self):
        """Validate approval"""
        if len(self.title) > 60:
            self.title = self.title[:60]  # Truncate for UI
        if len(self.preview_text) > 100:
            self.preview_text = self.preview_text[:100]  # Truncate preview


# ========================================
# MCP SERVER HEALTH
# ========================================

@dataclass
class MCPServerHealth:
    """
    Real-time health status of MCP server
    Updated on each health check
    """
    mcp_name: str
    status: HealthStatus = HealthStatus.OFFLINE
    last_successful_call_timestamp: Optional[datetime] = None
    last_call_status: str = "unknown"
    error_message: Optional[str] = None

    def is_online(self) -> bool:
        """Check if MCP is currently online"""
        return self.status == HealthStatus.ONLINE


# ========================================
# API USAGE LOG
# ========================================

@dataclass
class APIUsageLog:
    """
    Single Claude API call record for cost tracking
    Logged to vault/Logs/API_Usage/YYYY-MM-DD.md
    """
    log_id: str
    timestamp: datetime
    agent_id: str  # "cloud" or "local"
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    task_type: str  # email_draft, linkedin_draft, etc.

    def __post_init__(self):
        """Validate and calculate cost"""
        if self.prompt_tokens <= 0 or self.completion_tokens <= 0:
            raise ValueError("Token counts must be > 0")

        # Cost formula: (prompt * $3 + completion * $15) / 1M tokens
        calculated_cost = (self.prompt_tokens * 3 + self.completion_tokens * 15) / 1_000_000
        if abs(self.cost_usd - calculated_cost) > 0.000001:  # Floating point tolerance
            raise ValueError(f"Cost mismatch: {self.cost_usd} != {calculated_cost}")


# ========================================
# PM2 PROCESS
# ========================================

@dataclass
class PM2Process:
    """
    Managed background process (watcher, orchestrator, dashboard)
    Runtime state from `pm2 jlist`
    """
    process_name: str
    agent_type: str  # "cloud" or "local"
    status: str  # online, stopped, errored, launching
    uptime_seconds: int = 0
    restart_count: int = 0
    cpu_percent: float = 0.0
    memory_mb: int = 0
    log_file_path: str = ""

    def is_healthy(self) -> bool:
        """Check if process is running normally"""
        return self.status == "online" and self.restart_count < 5
