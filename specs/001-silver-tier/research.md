# Research: Silver Tier Technology Decisions

**Date**: 2026-02-11
**Feature**: 001-silver-tier
**Purpose**: Resolve technical unknowns from Technical Context and validate architecture decisions

## Overview

This document captures research findings for Silver tier implementation, focusing on AI integration, async watcher architecture, cost control mechanisms, and backward compatibility strategies.

## Research Areas

### 1. Claude API Integration

**Question**: How to integrate Claude API for priority analysis with timeout, retry, and caching?

**Research Findings**:

**Option 1: Anthropic Python SDK (anthropic>=0.18.0)**
- Official SDK with automatic retries and exponential backoff
- Built-in timeout support via `timeout` parameter
- Streaming responses supported (not needed for Silver)
- Type-safe with TypedDict for structured outputs
- **Pros**: Official support, automatic retries, well-documented
- **Cons**: Adds dependency, requires API key management

**Option 2: Direct HTTP calls with aiohttp**
- Manual control over retries and timeouts
- Lower-level access to API
- **Pros**: Minimal dependencies, full control
- **Cons**: Must implement retry logic manually, error handling complex

**Option 3: LangChain Claude integration**
- Higher-level abstraction with caching built-in
- Supports multiple LLM providers (future-proof)
- **Pros**: Caching layer, provider abstraction
- **Cons**: Heavy dependency (overkill for Silver), learning curve

**Decision**: **Option 1: Anthropic Python SDK**

**Rationale**:
- Official support reduces maintenance burden
- Built-in retries match spec requirement (FR-S006: 5-second timeout)
- Type safety aligns with Python 3.11+ type hints requirement
- Lightweight compared to LangChain (NFR-S-USE-001: simple upgrade path)
- Easy to mock for unit tests (test_ai_analyzer.py)

**Implementation Pattern**:
```python
from anthropic import Anthropic, AsyncAnthropic
import asyncio

client = AsyncAnthropic(
    api_key=os.getenv("CLAUDE_API_KEY"),
    timeout=5.0  # FR-S006: 5-second timeout
)

async def analyze_priority(task_title: str, task_snippet: str) -> dict:
    try:
        response = await client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"Analyze task priority: {task_title}\n{task_snippet[:200]}"
            }]
        )
        return {"priority": parse_priority(response.content), "cost": estimate_cost(response.usage)}
    except asyncio.TimeoutError:
        return {"priority": "Medium", "cost": 0.0, "fallback": True}
```

---

### 2. Async Watcher Architecture

**Question**: How to structure async watchers for Gmail, WhatsApp, LinkedIn without blocking?

**Research Findings**:

**Option 1: asyncio with separate processes (PM2/systemd)**
- Each watcher runs as independent process (gmail_watcher.py, whatsapp_watcher.py, linkedin_generator.py)
- Orchestrated via PM2 (Node) or systemd (Linux)
- **Pros**: Process isolation (one crash doesn't affect others), PM2 provides process management, restart on failure
- **Cons**: Requires PM2 installation, multi-process complexity

**Option 2: asyncio with single event loop (asyncio.gather)**
- Single Python process running 3 async tasks concurrently
- `asyncio.gather(poll_gmail(), poll_whatsapp(), generate_linkedin())`
- **Pros**: Simpler deployment (one process), easier to debug
- **Cons**: One task blocking affects all, harder to restart individual watchers

**Option 3: Threading with ThreadPoolExecutor**
- Each watcher runs in separate thread
- **Pros**: Simpler than multiprocessing, shared memory
- **Cons**: GIL contention, blocking I/O not parallelized

**Decision**: **Option 1: Separate processes with PM2**

**Rationale**:
- Constitution Section IV.5: Each watcher logs independently → process isolation desired
- Hackathon doc recommends PM2 for process management (persistent across reboots)
- Spec NFR-S-REL-002: Watchers must recover from errors independently
- Allows independent restart (e.g., WhatsApp session expires, restart only WhatsApp watcher)
- Aligns with Bronze watcher pattern (watch_inbox.py runs as separate process)

**Implementation Pattern**:
```bash
# pm2 ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "bronze-watcher",
      script: "python scripts/watch_inbox.py",
      cwd: "/path/to/vault",
      instances: 1
    },
    {
      name: "gmail-watcher",
      script: "python watchers/gmail_watcher.py",
      cwd: "/path/to/vault",
      instances: 1,
      env: { ENABLE_AI_ANALYSIS: "true" }
    },
    {
      name: "whatsapp-watcher",
      script: "python watchers/whatsapp_watcher.py",
      cwd: "/path/to/vault",
      instances: 1,
      env: { ENABLE_AI_ANALYSIS: "true" }
    },
    {
      name: "linkedin-generator",
      script: "python watchers/linkedin_generator.py",
      cwd: "/path/to/vault",
      instances: 1,
      cron_restart: "0 9 * * *"  # Daily at 9 AM
    }
  ]
};
```

---

### 3. Gmail API OAuth2 Flow

**Question**: How to authenticate with Gmail API and refresh tokens automatically?

**Research Findings**:

**OAuth2 Flow for Gmail API**:
1. Create OAuth2 credentials in Google Cloud Console (https://console.cloud.google.com/)
2. Download `credentials.json` (client ID + client secret)
3. First run: `python setup_gmail_auth.py` → Opens browser → User authorizes → Saves `token.json`
4. Subsequent runs: gmail_watcher.py reads `token.json`, auto-refreshes on expiry

**Required Scopes**:
- `https://www.googleapis.com/auth/gmail.readonly` (read emails)
- `https://www.googleapis.com/auth/gmail.labels` (read labels like "important")

**Token Storage**:
- **Option A**: Store in ~/.config/personal-ai-employee/token.json (user-scoped)
- **Option B**: Store in vault/Logs/gmail_token.json (vault-scoped, easier for multi-user)
- **Option C**: OS keychain (macOS Keychain, Windows Credential Manager)

**Decision**: **Option A: ~/.config/personal-ai-employee/gmail_token.json**

**Rationale**:
- Keeps secrets out of vault/ (NFR-S-SEC-004: credentials in ~/.config/)
- Cross-vault compatibility (one auth works for multiple vaults)
- Easier to exclude from Git (no .gitignore needed in vault/)
- Spec FR-S020: Handle Gmail API errors (403 Forbidden → auth error)

**Implementation**:
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = Path.home() / ".config/personal-ai-employee/gmail_token.json"

def get_gmail_credentials():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Auto-refresh
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("GMAIL_CREDENTIALS_PATH"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds
```

---

### 4. WhatsApp Web Automation with Playwright

**Question**: How to monitor WhatsApp Web reliably with session persistence?

**Research Findings**:

**Playwright Architecture**:
- Headless Chromium browser with persistent context (maintains session across restarts)
- Session stored in `WHATSAPP_SESSION_PATH` (includes cookies, localStorage)
- First run: Manual QR code scan (browser opens in headed mode)
- Subsequent runs: Headless mode reuses session

**Session Expiry Detection**:
- Check for QR code element: `page.query_selector('[data-testid="qrcode"]')`
- If present → session expired, log error, create notification in vault/Needs_Action/

**Keyword Detection**:
- Scan unread chats: `page.query_selector_all('[aria-label*="unread"]')`
- Extract text: `chat.inner_text()`
- Match keywords: `if any(kw in text.lower() for kw in KEYWORDS)`

**Decision**: **Playwright with persistent context**

**Rationale**:
- Spec FR-S021: Monitor WhatsApp Web (Playwright officially supported)
- Spec FR-S024: Handle session expiry gracefully
- Headless mode reduces resource usage (NFR-S-PERF-004: <500MB memory)
- Session persistence avoids daily QR scans

**Implementation**:
```python
from playwright.sync_api import sync_playwright

SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH")

def check_whatsapp():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            SESSION_PATH,
            headless=True
        )
        page = browser.pages[0]
        page.goto('https://web.whatsapp.com')

        # Check session
        if page.query_selector('[data-testid="qrcode"]'):
            log_error("WhatsApp session expired")
            create_notification("vault/Needs_Action/WHATSAPP_SESSION_EXPIRED.md")
            return

        # Find unread messages with keywords
        unread = page.query_selector_all('[aria-label*="unread"]')
        for chat in unread:
            text = chat.inner_text().lower()
            if any(kw in text for kw in ["urgent", "invoice", "payment"]):
                create_whatsapp_task(chat)

        browser.close()
```

---

### 5. API Cost Tracking and Alerting

**Question**: How to track Claude API costs and alert at $0.10/day threshold?

**Research Findings**:

**Cost Estimation**:
- Claude API pricing (as of 2026-01-01):
  - claude-3-5-sonnet-20241022: $3.00/MTok input, $15.00/MTok output
- Typical priority analysis request:
  - Input: ~150 tokens (prompt + task title + 200 char snippet)
  - Output: ~50 tokens (priority + category + reasoning)
  - Cost per request: (150 * $3.00 / 1M) + (50 * $15.00 / 1M) = $0.00045 + $0.00075 = $0.0012
- 100 tasks/day: 100 * $0.0012 = $0.12/day (exceeds $0.10 limit)

**Optimization Strategies**:
1. **Batch requests**: Analyze 5 tasks in one API call (reduce prompt overhead)
   - Cost per batch: ~$0.004 (vs $0.006 for 5 individual calls)
   - Savings: ~33%
2. **Cache responses**: 24h TTL, hash(task_title) → cached priority
   - Cache hit rate: >30% (spec NFR-S-REL-003)
   - Effective cost: $0.12 * 0.7 = $0.084/day (under $0.10 limit)
3. **Reduce output tokens**: Use structured output (JSON) instead of prose
   - Output: ~20 tokens (JSON: {"priority": "High", "category": "Work"})
   - Cost per request: $0.00045 + $0.00030 = $0.00075
   - 100 tasks/day: $0.075/day (under $0.10 limit)

**Decision**: **Structured output + 24h caching**

**Rationale**:
- Spec FR-S010: Cache responses for 24 hours
- Spec NFR-S-COST-001: Daily cost <$0.10 for 100 tasks
- Spec NFR-S-COST-002: Batch requests when possible
- Structured output reduces tokens and improves parsing reliability

**Implementation**:
```python
import hashlib
import json
from pathlib import Path

CACHE_DIR = Path("vault/Logs/API_Cache")
CACHE_TTL = 86400  # 24 hours

def get_cache_key(task_title: str) -> str:
    return hashlib.sha256(task_title.encode()).hexdigest()

def get_cached_response(task_title: str) -> dict | None:
    cache_file = CACHE_DIR / f"{get_cache_key(task_title)}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        if time.time() - data["timestamp"] < CACHE_TTL:
            return data["response"]
    return None

def cache_response(task_title: str, response: dict):
    cache_file = CACHE_DIR / f"{get_cache_key(task_title)}.json"
    cache_file.write_text(json.dumps({
        "timestamp": time.time(),
        "response": response
    }))
```

---

### 6. MCP Email Server Integration

**Question**: How to configure MCP server for email sending with human-in-the-loop approval?

**Research Findings**:

**MCP Server Options**:
- **Option 1**: email-mcp (community package) - https://github.com/modelcontextprotocol/servers/tree/main/src/email
- **Option 2**: Custom MCP server using Gmail API (reuse OAuth2 from watcher)
- **Option 3**: SMTP MCP server (simpler, no OAuth)

**Decision**: **Option 1: email-mcp package**

**Rationale**:
- Spec FR-S038: Configure one MCP server (email recommended)
- Community-maintained, follows MCP standards
- Supports Gmail via OAuth2 or SMTP
- Human-in-the-loop approval workflow via file-based triggers (spec FR-S040)

**MCP Configuration** (~/.config/claude-code/mcp.json):
```json
{
  "servers": [
    {
      "name": "email",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-email"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/home/user/.config/personal-ai-employee/gmail_credentials.json",
        "GMAIL_TOKEN_PATH": "/home/user/.config/personal-ai-employee/gmail_token.json"
      }
    }
  ]
}
```

**Approval Workflow**:
1. Watcher detects email needs reply
2. Create approval file: `vault/Pending_Approval/Email/REPLY_{email_id}.md`
3. User reviews, moves to `vault/Approved/Email/`
4. Orchestrator watches Approved/, calls MCP email server to send
5. Log action to `vault/Logs/MCP_Actions/YYYY-MM-DD.md`

---

## Summary of Decisions

| Decision Area | Choice | Key Rationale |
|---------------|--------|---------------|
| Claude API Integration | Anthropic Python SDK (>=0.18.0) | Official support, built-in retries, timeout |
| Async Watcher Architecture | Separate processes with PM2 | Process isolation, independent restart, persistent |
| Gmail OAuth2 | ~/.config/ token storage | Secrets out of vault, cross-vault compatibility |
| WhatsApp Automation | Playwright persistent context | Session persistence, headless mode, keyword detection |
| API Cost Tracking | Structured output + 24h caching | <$0.10/day target, 30% cache hit rate |
| MCP Email Server | email-mcp community package | Standard compliance, OAuth2 support, HITL approval |

---

**Next Step**: Proceed to Phase 1 - Generate data-model.md, contracts/, and quickstart.md based on these research findings.
