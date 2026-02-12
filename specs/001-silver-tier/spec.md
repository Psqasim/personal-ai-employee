# Feature Specification: Silver Tier - Functional AI Assistant

**Feature Branch**: `001-silver-tier`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Create Silver tier specification with AI-powered priority analysis, multiple watchers (Gmail+WhatsApp+LinkedIn), Plan.md generation, and graceful fallback to Bronze defaults"

## Overview

Silver Tier upgrades the Bronze foundation by adding **AI-powered analysis and multi-channel monitoring** while maintaining 100% backward compatibility. The agent now analyzes tasks using Claude API to assign intelligent priorities (High/Medium/Low) and categorize tasks (Work/Personal/Urgent), monitors multiple communication channels (Gmail, WhatsApp, LinkedIn), and generates Plan.md files for multi-step workflows. All AI features gracefully degrade to Bronze behavior if the API is unavailable.

**Core Principle**: Bronze Compatibility First - All Bronze features work identically. Silver features are optional enhancements with graceful fallback.

**Key Additions**:
- AI-powered priority analysis (High/Medium/Low) using Claude API
- Task categorization (Work/Personal/Urgent) based on content analysis
- Multiple watchers: Gmail (emails), WhatsApp (messages), LinkedIn (auto-posting)
- Plan.md generation for multi-step workflows with human approval
- Cost-aware API usage (<$0.10/day target)
- One MCP server (email) for external actions

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI-Powered Priority Analysis (Priority: P1)

As a **user overwhelmed with tasks**, I want the AI to automatically analyze inbox items and assign priority levels (High/Medium/Low) based on content urgency and keywords so I can focus on what matters most.

**Why this priority**: This is the core value proposition of Silver tier - intelligent prioritization. Without this, Silver is just Bronze with more watchers.

**Independent Test**: Add 3 test files to Inbox/ with different urgency levels (urgent client request, routine task, low-priority note). With ENABLE_AI_ANALYSIS=true, verify Dashboard.md shows High/Medium/Low priorities instead of all "Medium". This can be tested independently of other Silver features.

**Acceptance Scenarios**:

1. **Given** ENABLE_AI_ANALYSIS=true in .env and valid CLAUDE_API_KEY is configured, **When** a file containing "urgent client" is added to Inbox/, **Then** Dashboard.md shows Priority="High" for that task within 10 seconds

2. **Given** AI analysis is enabled, **When** a file containing routine keywords ("review", "update", "consider") is added to Inbox/, **Then** Dashboard.md shows Priority="Medium" for that task

3. **Given** AI analysis is enabled, **When** a file containing low-priority keywords ("maybe", "someday", "idea") is added to Inbox/, **Then** Dashboard.md shows Priority="Low" for that task

4. **Given** AI analysis is enabled, **When** the Claude API is unreachable (network timeout), **Then** the system falls back to Bronze behavior (Priority="Medium") and logs "API unavailable, using default priority"

5. **Given** ENABLE_AI_ANALYSIS=false in .env, **When** any file is added to Inbox/, **Then** Dashboard.md shows Priority="Medium" (Bronze behavior) regardless of content

6. **Given** AI analysis is enabled and API call succeeds, **When** the API response takes longer than 5 seconds, **Then** the system times out, falls back to "Medium" priority, and logs a timeout warning

---

**Note**: Due to message length limits, I'm providing the critical sections. The full spec includes:
- All 7 user stories (AI Analysis, Categorization, Gmail/WhatsApp/LinkedIn watchers, Plan generation, Cost control)
- Edge cases for API failures and multi-watcher scenarios
- 44 Functional Requirements (FR-S001 through FR-S044)
- Non-functional requirements for Performance, Reliability, Cost Control, Security, Usability
- 8 Key Entities (AIAnalysisResult, EmailTask, WhatsAppTask, LinkedInPost, Plan, PlanStep, APIUsageLog, WatcherStatus)
- 12 Success Criteria (SC-S001 through SC-S012)
- Definition of Done with backward compatibility verification
- Dependencies (Python packages, external tools, .env configuration)
- Out of Scope items (Gold/Platinum features explicitly excluded)
- Assumptions document

**Next Step**: Proceed to `/sp.plan 001-silver-tier` to design the implementation architecture.

### User Story 2 - Task Categorization (Priority: P1)

As a **user managing both work and personal tasks**, I want the AI to automatically categorize tasks as Work/Personal/Urgent based on content so I can filter and organize my dashboard by domain.

**Why this priority**: Categorization enables domain separation (Personal vs Business), which is critical for Gold tier cross-domain integration. It provides immediate value by organizing the dashboard.

**Independent Test**: Add files with work-related content ("client proposal", "meeting notes") and personal content ("grocery list", "vacation planning"). Verify Dashboard.md includes a "Category" column with correct classifications.

**Acceptance Scenarios**:

1. **Given** AI analysis is enabled, **When** a file contains business keywords ("client", "invoice", "proposal", "meeting"), **Then** Dashboard.md shows Category="Work" for that task

2. **Given** AI analysis is enabled, **When** a file contains personal keywords ("family", "vacation", "health", "home"), **Then** Dashboard.md shows Category="Personal" for that task

3. **Given** AI analysis is enabled, **When** a file contains urgent markers ("URGENT", "ASAP", "deadline today", "emergency"), **Then** Dashboard.md shows Category="Urgent" (overrides Work/Personal) and Priority="High"

4. **Given** AI analysis is enabled but the API fails, **When** a file is added, **Then** Dashboard.md shows Category="Uncategorized" (Bronze fallback)

---

### User Story 3 - Gmail Watcher Integration (Priority: P1)

As a **professional receiving important emails**, I want a Gmail watcher that automatically creates task files in Inbox/ for unread important emails so I don't miss critical client communications.

**Why this priority**: Email is the primary communication channel for most professionals. Without email monitoring, Silver tier lacks practical utility.

**Independent Test**: Send a test email to your Gmail account with "is:important" label. Verify the Gmail watcher creates a file in vault/Inbox/ within 2 minutes with email subject, sender, and snippet.

**Acceptance Scenarios**:

1. **Given** Gmail watcher is running and credentials are configured, **When** an unread email with "is:important" label arrives, **Then** a file EMAIL_{message_id}.md is created in vault/Inbox/ within 2 minutes

2. **Given** an important email is detected, **When** the watcher creates the task file, **Then** the file contains YAML frontmatter with type="email", from={sender}, subject={subject}, received={timestamp}, priority="high", status="pending"

3. **Given** 10 important emails arrive simultaneously, **When** the Gmail watcher processes them, **Then** all 10 files are created in vault/Inbox/ without race conditions or dropped emails

---

### User Story 4 - WhatsApp Watcher Integration (Priority: P2)

As a **business owner communicating with clients via WhatsApp**, I want a watcher that monitors WhatsApp Web for urgent keywords and creates task files so I can respond promptly.

**Why this priority**: WhatsApp is critical for business communication. This is P2 because email (P1) covers most professional use cases.

**Independent Test**: Send a test WhatsApp message containing "urgent invoice request". Verify the watcher creates a file in vault/Inbox/ within 30 seconds.

**Acceptance Scenarios**:

1. **Given** WhatsApp watcher is running with valid session, **When** an unread message contains keywords ("urgent", "invoice", "payment", "help", "asap"), **Then** a file WHATSAPP_{chat_id}_{timestamp}.md is created in vault/Inbox/ within 30 seconds

2. **Given** WhatsApp Web is not logged in (session expired), **When** the watcher attempts to poll, **Then** it logs "WhatsApp session expired, please re-authenticate" and pauses polling

---

### User Story 5 - LinkedIn Auto-Posting (Priority: P2)

As a **business owner promoting my services**, I want the AI to draft LinkedIn posts about my business and save them to vault/Pending_Approval/ so I can review and approve before posting.

**Why this priority**: Social media presence drives sales. This is P2 because it's proactive (not reactive like email/WhatsApp).

**Independent Test**: Configure business goals in Company_Handbook.md. Trigger LinkedIn post generation. Verify a draft post file appears in vault/Pending_Approval/LinkedIn/.

**Acceptance Scenarios**:

1. **Given** Company_Handbook.md contains business goals and LinkedIn posting schedule, **When** the scheduled LinkedIn post generation runs, **Then** a file LINKEDIN_POST_{date}.md is created in vault/Pending_Approval/LinkedIn/ with drafted content

2. **Given** LinkedIn post generation runs, **When** AI API is unavailable, **Then** the system logs "LinkedIn post generation skipped, API unavailable" and retries on next scheduled run

---

### User Story 6 - Plan.md Generation Workflow (Priority: P1)

As a **user facing multi-step tasks**, I want Claude to analyze complex tasks and generate a Plan.md file with checkboxes for each step so I have a clear action roadmap.

**Why this priority**: Plan generation is the foundation for Gold tier's autonomous multi-step execution.

**Independent Test**: Add a file to Inbox/ containing a complex request ("Plan Q1 marketing campaign"). With AI analysis enabled, verify a Plan.md file is created in vault/Plans/ with multi-step breakdown.

**Acceptance Scenarios**:

1. **Given** AI analysis is enabled and a task in Inbox/ contains multi-step work (keywords: "plan", "campaign", "project"), **When** the watcher processes the file, **Then** a Plan.md file is created in vault/Plans/ with YAML frontmatter (objective, steps, approval_required=true)

2. **Given** a Plan.md file is generated, **When** the file is opened, **Then** it contains a checklist with `[ ]` for pending steps, numbered sequentially

---

### User Story 7 - Cost-Aware API Usage (Priority: P2)

As a **cost-conscious user**, I want the system to track Claude API usage and alert me if daily costs exceed $0.10 so I can control expenses.

**Why this priority**: Cost control is critical for sustainability. This is P2 because the system works without cost tracking.

**Independent Test**: Process 50 tasks with AI analysis enabled. Check vault/Logs/API_Usage/YYYY-MM.md for cumulative cost tracking.

**Acceptance Scenarios**:

1. **Given** AI analysis is enabled, **When** the system makes a Claude API call for priority analysis, **Then** the call is logged to vault/Logs/API_Usage/YYYY-MM.md with timestamp, request_type="priority_analysis", input_tokens, output_tokens, estimated_cost

2. **Given** API usage log exists, **When** cumulative daily cost exceeds $0.10, **Then** a warning is logged to vault/Logs/cost_alerts.md

---

### Edge Cases

- **What happens when Claude API returns an error (500 Internal Server Error)?** → System logs the error, falls back to Bronze behavior (Priority="Medium"), and retries on next polling cycle

- **What happens when Gmail API quota is exceeded?** → Gmail watcher logs "API quota exceeded, pausing for 60 seconds" and resumes after backoff period

- **What happens when WhatsApp Web session expires mid-polling?** → Watcher detects expiry, logs error, creates notification in vault/Needs_Action/, and pauses

- **What happens when API key is invalid or missing in .env?** → On watcher startup, system validates API key. If invalid, logs warning and continues with Bronze mode

- **What happens when multiple watchers create files simultaneously?** → Each watcher writes to unique files (EMAIL_{id}.md, WHATSAPP_{id}.md). No collisions


## Requirements *(mandatory)*

### Functional Requirements

#### AI Analysis & Prioritization (Silver Core)

- **FR-S001**: System MUST provide ENABLE_AI_ANALYSIS flag in .env file (default: false for safety). When true, system uses Claude API for priority analysis; when false, system operates in Bronze mode

- **FR-S002**: System MUST validate CLAUDE_API_KEY on watcher startup. If key is missing or invalid, system MUST log warning and fall back to Bronze behavior

- **FR-S003**: System MUST analyze task content (title + first 200 characters) using Claude API and assign priority: "High" (urgent), "Medium" (routine), "Low" (backlog)

- **FR-S004**: System MUST categorize tasks using Claude API: "Work" (business), "Personal" (non-work), "Urgent" (time-critical), "Uncategorized" (API unavailable)

- **FR-S005**: System MUST sanitize inputs before API calls: remove email addresses, phone numbers, account numbers. Only send task title + first 200 characters

- **FR-S006**: System MUST implement 5-second timeout for Claude API calls. If timeout, fall back to Bronze defaults and log timeout warning

- **FR-S007**: System MUST implement rate limiting: max 10 API calls/minute, max 100 calls/day

- **FR-S008**: System MUST track API usage in vault/Logs/API_Usage/YYYY-MM.md with timestamp, request_type, input_tokens, output_tokens, estimated_cost_usd

- **FR-S009**: System MUST alert user if daily API cost exceeds $0.10 via vault/Logs/cost_alerts.md

- **FR-S010**: System MUST cache API responses for 24 hours. If identical task title seen within 24 hours, reuse cached priority/category

#### Dashboard Enhancements (Silver)

- **FR-S011**: Dashboard.md MUST include "Category" column after "Priority" column

- **FR-S012**: Dashboard.md MUST display tasks in priority order: Urgent first, then High, Medium, Low

- **FR-S013**: Dashboard.md Statistics section MUST include: "High Priority: X", "Medium Priority: Y", "Low Priority: Z", "Work Tasks: A", "Personal Tasks: B"

- **FR-S014**: Dashboard.md MUST include "Silver Tier Status" section showing: AI Analysis (Enabled/Disabled), API Cost Today, Watchers Active (Gmail: ✓/✗, WhatsApp: ✓/✗)

#### Gmail Watcher (Silver)

- **FR-S015**: System MUST provide Gmail watcher script (scripts/gmail_watcher.py) that polls Gmail API every 2 minutes for unread emails with "is:important" label

- **FR-S016**: Gmail watcher MUST create task files in vault/Inbox/ with filename: EMAIL_{message_id}.md

- **FR-S017**: Gmail watcher MUST include YAML frontmatter: type="email", from={sender}, subject={subject}, received={timestamp}, priority="high"

- **FR-S018**: Gmail watcher MUST include email snippet (first 200 chars) and suggested actions checklist

- **FR-S019**: Gmail watcher MUST track processed email IDs in vault/Logs/gmail_processed_ids.txt to prevent duplicates

- **FR-S020**: Gmail watcher MUST handle API errors gracefully: 403 → pause; 429 → exponential backoff; 500 → retry

#### WhatsApp Watcher (Silver)

- **FR-S021**: System MUST provide WhatsApp watcher script (scripts/whatsapp_watcher.py) using Playwright to monitor WhatsApp Web for keywords: "urgent", "invoice", "payment", "help", "asap"

- **FR-S022**: WhatsApp watcher MUST create task files: WHATSAPP_{chat_id}_{timestamp}.md

- **FR-S023**: WhatsApp watcher MUST include YAML frontmatter: type="whatsapp", from={contact_name}, keywords={matched_keywords}

- **FR-S024**: WhatsApp watcher MUST handle session expiry: detect login screen, log error, create notification, pause polling

- **FR-S025**: WhatsApp watcher MUST ignore messages without monitored keywords (noise reduction)

#### LinkedIn Integration (Silver)

- **FR-S026**: System MUST provide LinkedIn post generator (scripts/linkedin_generator.py) that drafts posts based on Company_Handbook.md business goals

- **FR-S027**: LinkedIn generator MUST create draft files in vault/Pending_Approval/LinkedIn/: LINKEDIN_POST_{YYYY-MM-DD}.md

- **FR-S028**: LinkedIn generator MUST include YAML frontmatter: type="linkedin_post", scheduled_date, status="pending_approval", character_count

- **FR-S029**: LinkedIn generator MUST use Claude API to draft content aligned with Company_Handbook.md tone and target audience

- **FR-S030**: LinkedIn generator MUST respect posting schedule: max 1 post/day, configurable in Company_Handbook.md

#### Plan.md Generation (Silver)

- **FR-S031**: System MUST detect multi-step tasks in Inbox/ based on keywords: "plan", "campaign", "project", "implement"

- **FR-S032**: System MUST generate Plan.md files in vault/Plans/: PLAN_{task_name}_{date}.md

- **FR-S033**: Plan.md MUST include YAML frontmatter: objective, steps count, approval_required=true, estimated_time, created timestamp

- **FR-S034**: Plan.md MUST include numbered checklist with `[ ]` pending, `[x]` completed

- **FR-S035**: Plan.md MUST include dependency markers: "Step 3 [Blocked by: Step 1, Step 2]"

- **FR-S036**: System MUST update Dashboard.md with plan progress: "Plan: 3/5 steps completed"

- **FR-S037**: System MUST create approval files in vault/Pending_Approval/ for steps requiring approval

#### MCP Server Integration (Silver)

- **FR-S038**: System MUST configure one MCP server in ~/.config/claude-code/mcp.json for email sending

- **FR-S039**: System MUST log all MCP actions to vault/Logs/MCP_Actions/YYYY-MM-DD.md

- **FR-S040**: System MUST implement human-in-the-loop approval for all MCP actions

#### Backward Compatibility (Silver Guarantee)

- **FR-S041**: All Bronze tier functional requirements (FR-B001 through FR-B025) MUST remain functional in Silver tier

- **FR-S042**: When ENABLE_AI_ANALYSIS=false, system MUST operate identically to Bronze tier

- **FR-S043**: Users without CLAUDE_API_KEY MUST receive full Bronze experience

- **FR-S044**: Silver tier MUST maintain Bronze performance targets: Dashboard update <2s, file detection <30s

### Non-Functional Requirements

#### Performance (NFR-S-PERF)

- **NFR-S-PERF-001**: AI priority analysis MUST complete within 5 seconds (including API call)
- **NFR-S-PERF-002**: Gmail watcher MUST process batch of 10 emails within 30 seconds
- **NFR-S-PERF-003**: Dashboard update with AI analysis MUST complete within 5 seconds
- **NFR-S-PERF-004**: System MUST support up to 1000 files (Bronze limit maintained)

#### Reliability (NFR-S-REL)

- **NFR-S-REL-001**: AI analysis failure rate MUST be <5%. If API unavailable, fall back to Bronze
- **NFR-S-REL-002**: Gmail/WhatsApp watchers MUST recover from API errors automatically within 2 minutes
- **NFR-S-REL-003**: System MUST cache API responses for 24 hours. Cache hit rate target: >30%
- **NFR-S-REL-004**: Rate limiting MUST prevent quota exhaustion: max 10 calls/minute, max 100 calls/day

#### Cost Control (NFR-S-COST)

- **NFR-S-COST-001**: Daily API cost MUST stay under $0.10/day under normal usage (100 tasks)
- **NFR-S-COST-002**: System MUST batch API requests when possible
- **NFR-S-COST-003**: System MUST log cost alerts: $0.10 warning, $0.25 error, $0.50 critical
- **NFR-S-COST-004**: API usage log MUST be queryable: generate monthly cost reports

#### Security (NFR-S-SEC)

- **NFR-S-SEC-001**: API key MUST be in .env file (never in code). .env in .gitignore
- **NFR-S-SEC-002**: System MUST sanitize inputs: remove emails, phones, account numbers
- **NFR-S-SEC-003**: System MUST send only task title + first 200 chars to API (no full content)
- **NFR-S-SEC-004**: Gmail/WhatsApp credentials MUST be in ~/.config/ or OS keychain
- **NFR-S-SEC-005**: Human approval MUST be required for all MCP actions

#### Usability (NFR-S-USE)

- **NFR-S-USE-001**: Users upgrade Bronze→Silver by setting ENABLE_AI_ANALYSIS=true and adding CLAUDE_API_KEY. No code changes
- **NFR-S-USE-002**: Error messages actionable: "Claude API key invalid. Check .env. Get key at: https://console.anthropic.com/"
- **NFR-S-USE-003**: Dashboard indicates Silver status: "Silver Tier Active (AI Analysis: ✓, Cost Today: $0.05)"
- **NFR-S-USE-004**: Cost alerts include recommendations

### Key Entities

- **AIAnalysisResult**: Output of Claude API analysis
  - Attributes: task_id, priority ("High"|"Medium"|"Low"), category, reasoning, confidence (0.0-1.0), api_cost (USD)

- **EmailTask**: Extends VaultFile for email-sourced tasks
  - Attributes: email_id, sender_email, subject, snippet, received_timestamp

- **WhatsAppTask**: Extends VaultFile for WhatsApp-sourced tasks
  - Attributes: chat_id, contact_name, matched_keywords, message_preview

- **LinkedInPost**: Drafted LinkedIn post
  - Attributes: scheduled_date, business_goal, post_content, character_count, status

- **Plan**: Multi-step plan file
  - Attributes: plan_id, objective, steps array, total_steps, completed_steps, approval_required, estimated_time

- **PlanStep**: Single step within Plan
  - Attributes: step_number, description, status, dependencies, approval_required

- **APIUsageLog**: Single API call record
  - Attributes: timestamp, request_type, input_tokens, output_tokens, estimated_cost_usd, cache_hit

- **WatcherStatus**: Status of specific watcher
  - Attributes: watcher_type, status ("active"|"paused"|"error"), last_poll_time, error_message


## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-S001**: User can upgrade from Bronze to Silver by adding ENABLE_AI_ANALYSIS=true and CLAUDE_API_KEY to .env, restarting watcher. Upgrade completes in <1 minute

- **SC-S002**: AI analysis assigns priority (High/Medium/Low) to 95% of tasks within 5 seconds. Fallback to "Medium" only when API unavailable

- **SC-S003**: Task categorization (Work/Personal/Urgent) accuracy is 80%+ based on manual review of 100 sample tasks

- **SC-S004**: Gmail watcher detects important emails within 2 minutes and creates task files with correct frontmatter

- **SC-S005**: WhatsApp watcher detects messages with urgent keywords within 30 seconds without duplicates

- **SC-S006**: LinkedIn post generator creates business-aligned drafts on scheduled runs

- **SC-S007**: Plan.md generation creates multi-step plans with 90% accuracy (human review confirms plan is actionable)

- **SC-S008**: Daily API cost stays under $0.10 when processing 100 tasks/day (cost monitoring works)

- **SC-S009**: System operates identically to Bronze when ENABLE_AI_ANALYSIS=false (backward compatibility verified)

- **SC-S010**: All Bronze tier success criteria (SC-B001 through SC-B012) remain met in Silver tier (regression tests pass)

- **SC-S011**: Human-in-the-loop approval workflow functions: approval files created, actions execute only after approval

- **SC-S012**: API usage logs queryable: monthly cost report generated with total_cost, total_requests, cost_by_day

### Definition of Done

Silver Tier is **Done** when:

1. ✅ All 7 user stories have passing acceptance tests
2. ✅ All 44 functional requirements (FR-S001 through FR-S044) are implemented
3. ✅ All 16 non-functional requirements (NFR-S-*) are verified
4. ✅ All 12 success criteria (SC-S001 through SC-S012) are met
5. ✅ All Bronze tier tests still pass (backward compatibility confirmed)
6. ✅ Pytest unit tests achieve 80%+ coverage for new agent_skills modules
7. ✅ Integration test passes: Email arrives → Gmail watcher → AI analyzes → Dashboard updates with priority → Plan.md generated if multi-step
8. ✅ Cost control verified: 100 tasks processed, total cost <$0.10, alert logged if threshold exceeded
9. ✅ Graceful degradation tested: Disconnect network → API unavailable → Falls back to Bronze (Priority="Medium")
10. ✅ MCP server configured: email-mcp in mcp.json, approval workflow tested

## Dependencies

### Python Packages (pyproject.toml)

```toml
[project]
name = "personal-ai-employee-silver"
version = "0.2.0"
requires-python = ">=3.11"

dependencies = [
    # Bronze dependencies (inherited)
    "watchdog>=3.0.0",
    "pyyaml>=6.0",

    # Silver additions
    "anthropic>=0.18.0",                    # Claude API
    "google-auth>=2.16.0",                  # Gmail auth
    "google-api-python-client>=2.80.0",    # Gmail API
    "playwright>=1.40.0",                   # WhatsApp Web
    "aiohttp>=3.9.0",                       # Async HTTP
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "mypy>=1.0",
]
```

### External Tools

- **Obsidian Desktop App**: v1.5+ (same as Bronze)
- **Python**: 3.11+ (same as Bronze)
- **Playwright Browsers**: `playwright install chromium` (for WhatsApp)
- **Gmail API Credentials**: OAuth2 from Google Cloud Console
- **Claude API Key**: From Anthropic Console (https://console.anthropic.com/)

### Configuration Files (.env)

```bash
# Bronze config (inherited)
VAULT_PATH=/path/to/vault

# Silver additions
ENABLE_AI_ANALYSIS=true
CLAUDE_API_KEY=sk-ant-api03-xxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Gmail watcher
GMAIL_CREDENTIALS_PATH=/path/to/gmail_credentials.json
GMAIL_POLL_INTERVAL=120              # Seconds

# WhatsApp watcher
WHATSAPP_SESSION_PATH=/path/to/whatsapp_session
WHATSAPP_KEYWORDS=urgent,invoice,payment,help,asap

# LinkedIn
LINKEDIN_POSTING_FREQUENCY=daily
LINKEDIN_BUSINESS_GOALS_SECTION=Business Goals

# Cost control
API_DAILY_COST_LIMIT=0.10
API_RATE_LIMIT_PER_MIN=10
API_CACHE_DURATION=86400             # 24 hours
```

## Out of Scope (Deferred to Future Tiers)

### Deferred to Gold Tier
- ❌ Multi-step plan execution (Silver creates plans, Gold executes)
- ❌ Odoo accounting integration
- ❌ Facebook/Instagram/Twitter automation
- ❌ Weekly Business Audit & CEO Briefing
- ❌ Cross-domain integration orchestration
- ❌ Multiple MCP servers (Silver has one email MCP)

### Deferred to Platinum Tier
- ❌ Reflection loops and self-correction
- ❌ 24/7 cloud deployment
- ❌ Agent-to-agent communication
- ❌ Automatic failover

### Never in Silver (Safety Boundaries)
- ❌ Autonomous email sending without approval
- ❌ Autonomous LinkedIn posting without approval
- ❌ Autonomous file deletion
- ❌ Code execution from vault files
- ❌ Access to parent directories

## Assumptions

- **Assumption 1**: Users have Gmail accounts with "important" label enabled
- **Assumption 2**: WhatsApp Web accessible, users can maintain active session
- **Assumption 3**: Claude API key is valid with sufficient credits
- **Assumption 4**: Company_Handbook.md contains "Business Goals" section for LinkedIn
- **Assumption 5**: Users understand Silver is "AI-assisted, not autonomous"
- **Assumption 6**: Task content is in English
- **Assumption 7**: Email/WhatsApp monitoring is ethical and legal
- **Assumption 8**: Stable internet for API calls (offline→Bronze fallback)

---

**Next Step**: Proceed to `/sp.clarify 001-silver-tier` to resolve any unclear requirements, or `/sp.plan 001-silver-tier` to design the implementation architecture.
