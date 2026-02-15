# Implementation Plan: Gold Tier - Autonomous Employee

**Branch**: `002-gold-tier` | **Date**: 2026-02-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-gold-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Gold Tier upgrades Silver by adding **autonomous draft generation, multi-step plan execution, and MCP-based external actions**. The system now drafts email replies, WhatsApp messages, and LinkedIn posts using Claude API, presents them for human approval via file-move workflow (`vault/Pending_Approval/` → `vault/Approved/`), and executes approved actions via MCP servers (email send, WhatsApp send via Playwright, LinkedIn post). The Ralph Wiggum loop enables autonomous multi-step task execution with progress tracking and human escalation on failure.

**Key capabilities**: Email draft-and-send, WhatsApp draft-and-send (Playwright automation), LinkedIn post-and-publish, multi-step plan execution (max 10 iterations), weekly CEO Briefing generation, Odoo accounting draft integration (optional), comprehensive audit logging.

## Technical Context

**Language/Version**: Python 3.11+ (async/await for watchers, type hints mandatory)
**Primary Dependencies**:
- `anthropic>=0.18.0` (Claude API for draft generation)
- `playwright>=1.40.0` (WhatsApp Web automation, browser control)
- `watchdog>=3.0.0` (vault file monitoring, inherited from Bronze)
- `pyyaml>=6.0` (YAML frontmatter parsing)
- `schedule>=1.2.0` (CEO Briefing weekly cron)
- `filelock>=3.12.0` (vault write conflict resolution)
- `requests>=2.31.0` (LinkedIn API calls)
- `smtplib`, `imaplib` (email send/receive, stdlib)

**Storage**: File-based (Obsidian vault markdown files), no external database. All state persists in `vault/` folder. WhatsApp session state stored in Playwright session directory.

**Testing**: pytest with pytest-asyncio for async watchers, pytest-playwright for browser automation tests. Minimum 80% coverage for `agent_skills/`.

**Target Platform**: Linux (WSL2 Ubuntu primary), macOS and Windows 11 secondary support. WhatsApp watcher requires Chromium browser (Playwright)

**Project Type**: Single project (agent-based automation system)

**Performance Goals**:
- Email/WhatsApp/LinkedIn draft generation: <15 seconds (including Claude API call)
- MCP action execution (send): <30 seconds
- Dashboard update: <2 seconds
- Plan execution step transition: <10 seconds
- WhatsApp watcher polling: every 30 seconds (configurable)

**Constraints**:
- Backward compatibility: All Bronze + Silver features must work identically in Gold
- Offline degradation: Core features (file watching, dashboard) work without network
- Human approval gate: NO MCP action without approval file in `vault/Approved/`
- Vault integrity: Never corrupt Obsidian markdown (atomic writes, YAML validation)
- API cost control: <$0.10/day Claude API usage for typical workload (100 tasks)
- Ralph Wiggum loop: Max 10 iterations before human escalation

**Scale/Scope**:
- Vault size: Up to 10,000 markdown files (performance tested)
- Concurrent watchers: 3-5 (Gmail, WhatsApp, LinkedIn, plan executor, dashboard updater)
- Active plans: Up to 10 concurrent multi-step plans
- Daily throughput: 100+ inbox items, 20+ WhatsApp messages, 5+ LinkedIn posts/week

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Tier Progression (Constitution §I)
- [x] Gold builds on Silver: All Silver features (AI analysis, Gmail/WhatsApp/LinkedIn watchers, Plan.md generation) remain functional
- [x] Bronze foundation: File watching, Dashboard updates, Obsidian vault integrity preserved
- [x] Feature flag: `ENABLE_PLAN_EXECUTION=true` enables Gold execution; when false, degrades to Silver (draft-only, no auto-send)

### ✅ Vault Integrity (Constitution §II)
- [x] Atomic file operations: Read → Validate YAML → Modify → Validate → Write
- [x] Backup before modify: Dashboard.md, Plan.md backed up (`.bak.YYYY-MM-DD_HH-MM-SS`, keep last 5)
- [x] Race condition handling: `filelock` for concurrent writes, max 3 retries with 500ms delay
- [x] Obsidian syntax preservation: YAML frontmatter, wiki links (`[[...]]`), tags (`#...`)

### ✅ Local-First Architecture (Constitution §III)
- [x] Offline core: File watching, dashboard updates, Bronze/Silver features work without network
- [x] Optional AI enhancements: Claude API for draft generation (graceful fallback to manual templates)
- [x] Optional MCP actions: External integrations degrade gracefully if MCP servers unavailable
- [x] No cloud dependencies: All data in `vault/`, configs in `.env`

### ✅ Agent Skills Mandate (Constitution §VII)
- [x] All AI functionality as reusable skills in `agent_skills/`:
  - `ai_analyzer.py` (extended for email/WhatsApp/LinkedIn draft generation)
  - `vault_parser.py` (Obsidian markdown parsing, unchanged from Bronze/Silver)
  - `dashboard_updater.py` (extended for Gold tier status section)
  - `plan_executor.py` (NEW: Ralph Wiggum loop implementation)
  - `mcp_client.py` (NEW: MCP server invocation abstraction)

### ✅ Test-Driven Safety (Constitution §VIII)
- [x] Unit tests: 80%+ coverage for `agent_skills/` modules
- [x] Integration tests: Email draft → approve → send; WhatsApp draft → approve → send; LinkedIn draft → approve → post; Plan execute → steps complete
- [x] Mock external APIs: Claude API, LinkedIn API, SMTP mocked in tests
- [x] Idempotency tests: Dashboard update, plan step execution safe to re-run

### ✅ Audit Logging (Constitution §V Gold, FR-G060–G062)
- [x] ALL actions logged to `vault/Logs/` BEFORE execution
- [x] Log format: `YYYY-MM-DD_HH-MM-SS_action-name.md` with YAML frontmatter (timestamp, tier="gold", action, reasoning, outcome, human_approved)
- [x] Log categories: `Watcher_Activity/`, `MCP_Actions/`, `API_Usage/`, `Error_Recovery/`, `Human_Approvals/`, `Plan_Execution/`
- [x] Log retention: 90 days minimum, auto-prune on weekly audit run

### ⚠️ Complexity Justification Required
- **Playwright for WhatsApp**: Required for WhatsApp Web automation (no official API). Alternatives (unofficial APIs, Selenium) are less stable or deprecated.
- **Multiple MCP servers**: Required for isolated permissions (email-mcp for SMTP, whatsapp-mcp for Playwright, linkedin-mcp for LinkedIn API). Single MCP would violate separation of concerns.
- **Ralph Wiggum loop**: Required for Gold tier multi-step execution. Max 10 iterations prevents infinite loops.

## Project Structure

### Documentation (this feature)

```text
specs/002-gold-tier/
├── spec.md              # Feature requirements (WHAT to build)
├── plan.md              # This file (HOW to build)
├── research.md          # Phase 0 output: Playwright patterns, MCP architecture, loop patterns
├── data-model.md        # Phase 1 output: EmailDraft, WhatsAppDraft, LinkedInDraft, Plan, ExecutionState entities
├── quickstart.md        # Phase 1 output: Setup instructions for Gold tier
├── contracts/           # Phase 1 output: MCP server interfaces (OpenAPI-like)
│   ├── email-mcp.md     # Email MCP contract (send_email, get_inbox)
│   ├── whatsapp-mcp.md  # WhatsApp MCP contract (send_message, get_chats, auth_qr)
│   ├── linkedin-mcp.md  # LinkedIn MCP contract (create_post, get_feed)
│   └── mcp-protocol.md  # Common MCP protocol patterns (JSON-RPC over stdio)
├── checklists/
│   └── requirements.md  # Spec quality checklist (all items PASS)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
agent_skills/                  # Reusable Python modules (callable by Claude Code, watchers)
├── __init__.py
├── ai_analyzer.py             # Extended: draft generation for email/WhatsApp/LinkedIn
├── vault_parser.py            # Unchanged: Obsidian markdown parsing (from Bronze)
├── dashboard_updater.py       # Extended: Gold tier status section (MCP servers, active plans)
├── plan_executor.py           # NEW: Ralph Wiggum loop, plan step execution, state tracking
├── mcp_client.py              # NEW: MCP server invocation abstraction (JSON-RPC over stdio)
├── draft_generator.py         # NEW: Email/WhatsApp/LinkedIn draft logic (uses ai_analyzer)
└── approval_watcher.py        # NEW: Monitor vault/Pending_Approval/ and vault/Approved/

scripts/                       # Background processes (watchers, schedulers)
├── gmail_watcher.py           # Extended: triggers email draft generation (from Silver)
├── whatsapp_watcher.py        # Extended: monitors ALL messages, triggers drafts for important ones (from Silver)
├── linkedin_generator.py      # Extended: invokes LinkedIn MCP after approval (from Silver)
├── plan_watcher.py            # NEW: monitors vault/Approved/Plans/, triggers Ralph Wiggum loop
├── approval_watcher.py        # NEW: monitors vault/Approved/*, invokes MCP for approved actions
├── ceo_briefing.py            # NEW: weekly Sunday 23:00 CEO Briefing generator
└── gold_watcher.sh            # NEW: supervisor script (runs all Gold watchers via PM2/supervisord)

mcp_servers/                   # MCP server implementations (separate processes)
├── email_mcp/
│   ├── server.py              # Email MCP: SMTP send, IMAP read
│   └── config.json            # SMTP/IMAP credentials
├── whatsapp_mcp/
│   ├── server.py              # WhatsApp MCP: Playwright automation, QR auth, send
│   ├── session/               # Playwright session storage
│   └── config.json            # WhatsApp session path
├── linkedin_mcp/
│   ├── server.py              # LinkedIn MCP: LinkedIn API v2, OAuth2
│   └── config.json            # LinkedIn access token
└── odoo_mcp/                  # Optional: Odoo Community JSON-RPC
    ├── server.py
    └── config.json

vault/                         # Obsidian vault (product deliverable, Bronze/Silver unchanged)
├── Dashboard.md               # Agent-maintained task dashboard (Bronze)
├── Company_Handbook.md        # Agent operational rules (Bronze)
├── Inbox/                     # New task files (Bronze)
│   ├── EMAIL_*.md             # Email tasks (Silver)
│   ├── WHATSAPP_*.md          # WhatsApp tasks (Silver/Gold)
│   └── *.md                   # Other tasks
├── Pending_Approval/          # NEW (Gold): Drafts awaiting human approval
│   ├── Email/                 # Email drafts
│   ├── WhatsApp/              # WhatsApp drafts
│   ├── LinkedIn/              # LinkedIn drafts
│   ├── Plans/                 # Plan approval requests
│   └── Odoo/                  # Odoo draft entries (optional)
├── Approved/                  # NEW (Gold): Approved drafts ready for execution
│   ├── Email/
│   ├── WhatsApp/
│   ├── LinkedIn/
│   ├── Plans/
│   └── Odoo/
├── Rejected/                  # NEW (Gold): Rejected drafts
├── Plans/                     # Multi-step plans (Silver creates, Gold executes)
│   └── PLAN_*.md
├── In_Progress/               # NEW (Gold): Active plan execution state
│   └── {plan_id}/
│       └── state.md           # Ralph Wiggum loop state (current_step, iterations_remaining)
├── Done/                      # Completed tasks (Bronze)
├── Needs_Action/              # Escalations, errors, blocked plans (Bronze/Silver/Gold)
├── Briefings/                 # NEW (Gold): CEO Briefings
│   └── YYYY-MM-DD_Monday_Briefing.md
└── Logs/                      # Agent reasoning logs (Bronze/Silver/Gold)
    ├── Watcher_Activity/
    ├── MCP_Actions/           # NEW (Gold): MCP invocation logs
    ├── API_Usage/
    ├── Error_Recovery/
    ├── Human_Approvals/       # NEW (Gold): Approval file movements
    └── Plan_Execution/        # NEW (Gold): Ralph Wiggum loop iterations

tests/                         # Pytest test suites
├── unit/                      # Unit tests for agent_skills/
│   ├── test_ai_analyzer.py    # Draft generation logic
│   ├── test_plan_executor.py  # Ralph Wiggum loop logic
│   ├── test_mcp_client.py     # MCP invocation abstraction
│   └── test_draft_generator.py
├── integration/               # Integration tests for watchers + MCP
│   ├── test_email_workflow.py      # Email draft → approve → send (mocked SMTP)
│   ├── test_whatsapp_workflow.py   # WhatsApp draft → approve → send (mocked Playwright)
│   ├── test_linkedin_workflow.py   # LinkedIn draft → approve → post (mocked API)
│   ├── test_plan_execution.py      # Multi-step plan execution (mocked MCPs)
│   └── test_approval_watcher.py    # File-move approval detection
├── fixtures/                  # Test data
│   ├── mock_vault/            # Test Obsidian vault structure
│   └── mock_mcp_responses.json
└── conftest.py                # pytest fixtures (mock MCP servers, vault setup)

docs/gold/                     # NEW (Gold): Setup documentation
├── whatsapp-setup.md          # WhatsApp Web QR auth, Playwright install, session mgmt
├── mcp-setup.md               # MCP server configuration, mcp.json examples
└── ceo-briefing-config.md     # CEO Briefing customization guide

.env                           # Environment variables (extended for Gold)
# Inherits all Silver .env variables (CLAUDE_API_KEY, GMAIL_CREDENTIALS_PATH, etc.)
# Gold additions:
# ENABLE_PLAN_EXECUTION=true
# TIER=gold
# SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (email MCP)
# LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN (LinkedIn MCP)
# WHATSAPP_SESSION_PATH, WHATSAPP_POLL_INTERVAL, WHATSAPP_KEYWORDS (WhatsApp MCP)
```

**Structure Decision**: Single project structure chosen because this is an agent-based automation system, not a web/mobile app. All components (watchers, MCP servers, agent skills) run as background processes or Python modules. The `vault/` folder is the product deliverable (Obsidian-compatible markdown), while `agent_skills/` and `scripts/` are the engine.

## Complexity Tracking

> **Justification for complexity beyond Constitution defaults**

| Violation/Complexity | Why Needed | Simpler Alternative Rejected Because |
|----------------------|------------|-------------------------------------|
| **Playwright for WhatsApp** | WhatsApp has no official API. Playwright is the only stable way to automate WhatsApp Web. | Unofficial APIs (e.g., whatsapp-web.js) are frequently broken by WhatsApp updates. Selenium is more brittle than Playwright for modern SPAs. Manual WhatsApp handling defeats Gold tier's autonomy goal. |
| **3 MCP Servers (email, whatsapp, linkedin)** | Each integration has different auth/permissions (SMTP vs Playwright vs OAuth2). Isolating MCPs follows principle of least privilege. | Single MCP server would require one process to hold SMTP password + WhatsApp session + LinkedIn OAuth token, violating security isolation. MCP protocol designed for granular tool servers. |
| **Ralph Wiggum Loop (max 10 iterations)** | Multi-step plan execution requires autonomous retry and progress tracking. Loop enables self-correction on transient errors. | Sequential script execution (no loop) fails on first error without retry. Hard limit (10) prevents infinite loops while allowing reasonable retry attempts (3 retries/step × 3 steps = 9 iterations). |
| **Approval workflow via file-move** | Obsidian users are non-technical. File drag-and-drop is the most intuitive UX. No CLI, no web UI required. | CLI approval (`approve-draft.sh <id>`) requires terminal access. Web UI adds deployment complexity (server, auth). File-move is Obsidian-native and zero-install. |

## Phase 0: Research & Technical Discovery

**Objective**: Resolve all NEEDS CLARIFICATION markers from Technical Context and research best practices for key technologies.

### Research Tasks

1. **Playwright WhatsApp Web Automation Patterns** (CRITICAL)
   - **Goal**: Determine stable selectors for WhatsApp Web elements (message input, send button, chat list), handle QR code auth flow, persist session across restarts
   - **Deliverable**: Documented Playwright script patterns with selectors, session management strategy, error recovery for session expiry
   - **Acceptance**: Prototype script can authenticate, send 1 message, persist session, and restart without re-auth

2. **MCP Server Architecture & JSON-RPC over stdio** (CRITICAL)
   - **Goal**: Understand MCP protocol (JSON-RPC 2.0 over stdin/stdout), server lifecycle, tool registration, error handling
   - **Deliverable**: MCP server template (Python) that registers 1 tool, accepts JSON-RPC requests, returns responses
   - **Acceptance**: Template server responds to `tools/list` and `tools/call` requests correctly

3. **Ralph Wiggum Loop Implementation Pattern** (CRITICAL)
   - **Goal**: Design loop state machine: plan parsing → step execution → state update → next step or exit. Handle max iterations, error retry, human escalation.
   - **Deliverable**: Pseudocode for loop with state persistence (`vault/In_Progress/{plan_id}/state.md`), iteration counter, exit conditions
   - **Acceptance**: Pseudocode covers all edge cases: max iterations reached, step blocked, all steps complete, mid-loop restart

4. **Email Draft Generation Best Practices**
   - **Goal**: Research professional email templates (greeting, body structure, CTA, signature), Claude API prompting for context-aware replies
   - **Deliverable**: Claude prompt template for email draft generation with examples (acknowledge, decline, request info)
   - **Acceptance**: Template produces professional drafts for 3 test scenarios

5. **WhatsApp Draft Generation Best Practices**
   - **Goal**: Research conversational messaging patterns (brevity, tone, emoji usage), keyword-based importance detection
   - **Deliverable**: Claude prompt template for WhatsApp drafts (max 500 chars), keyword list for priority flagging
   - **Acceptance**: Template produces appropriate WhatsApp replies (professional but casual) for business contexts

6. **LinkedIn Post Generation Best Practices**
   - **Goal**: Research LinkedIn post structure (hook, value, CTA), character limits (3000), engagement drivers, business tone alignment
   - **Deliverable**: Claude prompt template for LinkedIn posts referencing Company_Handbook.md business goals
   - **Acceptance**: Template produces engaging LinkedIn posts aligned with sample business goals

7. **File-based Approval Workflow Implementation**
   - **Goal**: Design watchdog-based file-move detection (`vault/Approved/` folder monitoring), idempotent action execution, race condition handling
   - **Deliverable**: Approval watcher design with file locking, deduplication (process each approval file once), error recovery
   - **Acceptance**: Design handles concurrent approvals, no duplicate sends, logs all actions

**Output**: `research.md` with all findings, decisions, and code examples

---

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete, all NEEDS CLARIFICATION resolved

### 1. Data Model (`data-model.md`)

Extract from spec.md Key Entities section + add state transitions:

**Entities**:
1. **EmailDraft** (vault/Pending_Approval/Email/EMAIL_DRAFT_{id}.md)
   - Fields: draft_id, original_email_id, to, subject, draft_body, status, generated_at, sent_at
   - States: pending_approval → approved/rejected → sent/failed
   - Transitions: file-move triggers state change

2. **WhatsAppDraft** (vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_{id}.md)
   - Fields: draft_id, original_message_id, to (contact_name), chat_id, draft_body, status, generated_at, sent_at, keywords_matched
   - States: pending_approval → approved/rejected → sent/failed
   - Transitions: file-move triggers MCP invocation

3. **LinkedInDraft** (vault/Pending_Approval/LinkedIn/LINKEDIN_POST_{date}.md)
   - Fields: draft_id, scheduled_date, business_goal_reference, post_content, character_count, status, generated_at, posted_at
   - States: pending_approval → approved/rejected → posted/failed/rate_limited_retry
   - Transitions: daily schedule limit (max 1/day), rate limit handling

4. **Plan** (vault/Plans/PLAN_{name}_{date}.md)
   - Fields: plan_id, objective, steps (array), total_steps, completed_steps, status, approval_file_path, iteration_count
   - States: awaiting_approval → executing → completed/blocked/escalated
   - Transitions: approval triggers execution, max 10 iterations enforced

5. **PlanStep** (within Plan YAML)
   - Fields: step_num, description, action_type (mcp_email|mcp_whatsapp|mcp_linkedin|create_file|notify_human), dependencies, status, mcp_action_log_id
   - States: pending → executing → completed/blocked
   - Transitions: dependency check before execution

6. **ExecutionState** (vault/In_Progress/{plan_id}/state.md)
   - Fields: plan_id, current_step, iterations_remaining, last_action, last_action_timestamp, loop_start_time
   - Persistence: written after each step completes, read on loop start/restart

7. **MCPActionLog** (vault/Logs/MCP_Actions/YYYY-MM-DD.md)
   - Fields: log_id, mcp_server, action, payload_summary, outcome, plan_id, step_num, timestamp, human_approved, approval_file_path
   - Append-only log for audit trail

8. **CEOBriefing** (vault/Briefings/YYYY-MM-DD_Monday_Briefing.md)
   - Fields: briefing_date, week_start, week_end, tasks_completed_count, tasks_pending_count, proactive_suggestions (array), api_cost_week, generated_by ("ai"|"data_only")
   - Generated weekly (Sunday 23:00), read-only

### 2. API Contracts (`contracts/`)

Generate MCP server contracts based on functional requirements:

**File**: `contracts/email-mcp.md`
```markdown
# Email MCP Server Contract

## Tools

### send_email
**Input**: { "to": string, "subject": string, "body": string }
**Output**: { "message_id": string, "sent_at": timestamp }
**Errors**: SMTP_AUTH_FAILED, NETWORK_ERROR, INVALID_EMAIL

### get_inbox (optional, for future)
**Input**: { "filter": "is:important", "max_results": int }
**Output**: { "emails": array of { "id", "from", "subject", "snippet" } }
```

**File**: `contracts/whatsapp-mcp.md`
```markdown
# WhatsApp MCP Server Contract

## Tools

### authenticate_qr
**Input**: {}
**Output**: { "qr_code_base64": string, "status": "waiting"|"authenticated" }
**Errors**: SESSION_PATH_INVALID, BROWSER_LAUNCH_FAILED

### send_message
**Input**: { "chat_id": string, "message": string }
**Output**: { "message_id": string, "sent_at": timestamp }
**Errors**: SESSION_EXPIRED, CHAT_NOT_FOUND, NETWORK_ERROR

### get_chats (optional, for watcher)
**Input**: { "unread_only": bool }
**Output**: { "chats": array of { "id", "name", "last_message" } }
```

**File**: `contracts/linkedin-mcp.md`
```markdown
# LinkedIn MCP Server Contract

## Tools

### create_post
**Input**: { "text": string, "author_urn": string }
**Output**: { "post_id": string, "post_url": string }
**Errors**: AUTH_FAILED, RATE_LIMITED, INVALID_TOKEN

### get_feed (optional, for future)
**Input**: { "max_results": int }
**Output**: { "posts": array of { "id", "author", "text", "engagement" } }
```

**File**: `contracts/mcp-protocol.md`
```markdown
# MCP Protocol Patterns (JSON-RPC 2.0 over stdio)

## Common Request Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "send_email",
    "arguments": { "to": "...", "subject": "...", "body": "..." }
  }
}
```

## Common Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "message_id": "...", "sent_at": "..." }
}
```

## Error Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": { "code": -32000, "message": "SMTP_AUTH_FAILED" }
}
```
```

### 3. Quickstart Guide (`quickstart.md`)

Setup instructions for Gold tier (references Silver setup, adds Gold-specific steps):

```markdown
# Gold Tier Quickstart

## Prerequisites
- Silver tier fully deployed and functional
- Python 3.11+
- Playwright installed: `playwright install chromium`
- SMTP credentials (Gmail app password or custom SMTP server)
- LinkedIn OAuth2 access token (optional but recommended)
- WhatsApp phone number for QR auth

## Installation

1. **Upgrade Silver → Gold**:
   ```bash
   git checkout 002-gold-tier
   pip install -r requirements-gold.txt
   ```

2. **Configure .env** (add to existing Silver .env):
   ```bash
   ENABLE_PLAN_EXECUTION=true
   TIER=gold

   # Email MCP
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password

   # WhatsApp MCP
   WHATSAPP_SESSION_PATH=/home/user/.whatsapp_session
   WHATSAPP_POLL_INTERVAL=30
   WHATSAPP_KEYWORDS=urgent,meeting,payment,deadline,invoice,asap,help,client,contract

   # LinkedIn MCP
   LINKEDIN_ACCESS_TOKEN=your-oauth2-token
   LINKEDIN_AUTHOR_URN=urn:li:person:xxxxx
   ```

3. **Initialize MCP Servers**:
   ```bash
   # Email MCP (starts automatically via mcp.json)
   # WhatsApp MCP (requires QR auth first time)
   python scripts/whatsapp_qr_setup.py  # Displays QR code, scan with phone
   # LinkedIn MCP (starts automatically)
   ```

4. **Start Gold Watchers**:
   ```bash
   ./scripts/gold_watcher.sh start  # Starts all Gold watchers via PM2
   ```

5. **Verify Setup**:
   - Check Dashboard.md → "Gold Tier Status" section shows MCP servers active
   - Send test WhatsApp message with "urgent" keyword → verify draft appears in vault/Pending_Approval/WhatsApp/
   - Move draft to vault/Approved/WhatsApp/ → verify message sends

## Testing

```bash
pytest tests/integration/test_gold_workflows.py -v
```

## Troubleshooting

See docs/gold/troubleshooting.md for common issues.
```

### 4. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to add Gold tier technologies to Claude Code context.

---

## Phase 2: Task Breakdown

**NOT INCLUDED IN THIS PLAN** - Run `/sp.tasks 002-gold-tier` separately after plan approval to generate `tasks.md` with dependency-ordered implementation tasks.

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **WhatsApp Web UI changes break Playwright selectors** | High (WhatsApp MCP fails) | Medium (WhatsApp updates ~monthly) | Selector abstraction layer, fallback to manual handling, session persistence reduces re-auth |
| **Ralph Wiggum loop exceeds 10 iterations on simple plans** | Medium (human escalation noise) | Low (proper step design prevents loops) | Clear plan validation, step dependency checks, unit tests for loop logic |
| **MCP server process crashes silently** | High (approved actions not executed) | Medium | Health monitoring in gold_watcher.sh, auto-restart via PM2/supervisord, alerts to vault/Needs_Action/ |
| **File-move approval race condition** | Medium (duplicate sends) | Low | File locking with `filelock`, atomic file moves, deduplication log |
| **Claude API cost exceeds $0.10/day** | Low (budget overrun) | Medium (100+ tasks/day) | API usage tracking, daily alerts at $0.10/$0.25/$0.50 thresholds, response caching (24h TTL) |
| **Obsidian vault corruption due to concurrent writes** | Critical (user data loss) | Very Low (file locking prevents) | Atomic writes, backup before modify (`.bak`), vault corruption recovery tests |

---

## Post-Planning Checklist

- [ ] All NEEDS CLARIFICATION resolved in research.md
- [ ] Constitution Check re-evaluated post-design (all gates still pass)
- [ ] data-model.md includes all entities from spec with state transitions
- [ ] contracts/ includes all MCP server interfaces
- [ ] quickstart.md provides end-to-end setup instructions
- [ ] Agent context updated with Gold tier technologies
- [ ] Risks documented with mitigation strategies
- [ ] Ready for `/sp.tasks 002-gold-tier` to generate implementation tasks

---

**Next Step**: Generate `research.md` (Phase 0) then `data-model.md`, `contracts/`, `quickstart.md` (Phase 1).
