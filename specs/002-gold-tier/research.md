# Research: Gold Tier Technical Discovery

**Feature**: 002-gold-tier | **Date**: 2026-02-13 | **Phase**: 0

## Summary

This document resolves all NEEDS CLARIFICATION markers from the plan and researches best practices for Gold tier's key technologies: Playwright WhatsApp automation, MCP server architecture, Ralph Wiggum loop patterns, and AI draft generation.

---

## 1. Playwright WhatsApp Web Automation Patterns

**Decision**: Use Playwright with persistent browser context for WhatsApp Web automation

**Rationale**:
- WhatsApp Web is a React SPA that requires stable CSS selectors and session persistence
- Playwright's `browser_context.storage_state()` persists authentication across restarts (avoids re-scanning QR code)
- Headless mode works for message sending; headed mode only needed for QR code scan
- Playwright auto-waits for elements (more stable than Selenium explicit waits)

**Key Selectors** (WhatsApp Web as of 2026-01):
```python
# Chat list search box
SEARCH_BOX = 'div[contenteditable="true"][data-tab="3"]'

# Message input field (in active chat)
MESSAGE_INPUT = 'div[contenteditable="true"][data-tab="10"]'

# Send button
SEND_BUTTON = 'button[data-tab="11"]'

# QR code canvas (for initial auth)
QR_CODE = 'canvas[aria-label="Scan this QR code to link a device!"]'

# Chat items in left panel
CHAT_ITEM = 'div[role="listitem"]'

# Last message in active chat
LAST_MESSAGE = 'div[data-pre-plain-text]'
```

**Session Persistence Pattern**:
```python
from playwright.sync_api import sync_playwright

def authenticate_whatsapp_qr(session_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headed for QR scan
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://web.whatsapp.com')

        # Wait for QR code
        qr_canvas = page.wait_for_selector(QR_CODE, timeout=10000)
        print("Scan QR code with WhatsApp mobile app...")

        # Wait for auth (QR disappears)
        page.wait_for_selector('div[data-testid="conversation-panel-wrapper"]', timeout=60000)
        print("Authenticated!")

        # Save session
        context.storage_state(path=session_path)
        browser.close()

def send_whatsapp_message(session_path, contact_name, message):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless for automated sends
        context = browser.new_context(storage_state=session_path)  # Load saved session
        page = context.new_page()
        page.goto('https://web.whatsapp.com')

        # Wait for chat panel (confirms session valid)
        page.wait_for_selector('div[data-testid="conversation-panel-wrapper"]')

        # Search for contact
        search_box = page.wait_for_selector(SEARCH_BOX)
        search_box.fill(contact_name)
        page.keyboard.press('Enter')

        # Type and send message
        message_input = page.wait_for_selector(MESSAGE_INPUT)
        message_input.fill(message)
        page.click(SEND_BUTTON)

        # Confirm sent (wait for message to appear in chat)
        page.wait_for_selector(f'span[dir="ltr"]:has-text("{message[:20]}")')

        browser.close()
```

**Session Expiry Detection**:
- If session expired, `page.goto('https://web.whatsapp.com')` redirects to QR code page
- Detect by checking for QR_CODE selector within 5 seconds
- If present → session expired → pause watcher, create `vault/Needs_Action/whatsapp_session_expired.md`

**Error Recovery**:
- Network timeout → retry 3 times (5s, 10s, 20s backoff)
- Element not found → check if logged out (QR code present), if not → log selector change, notify human
- Message send confirmation timeout → assume sent (idempotent), log warning

**Alternatives Considered**:
- whatsapp-web.js (unofficial library): Frequently broken by WhatsApp updates, uses legacy Puppeteer
- Selenium: Less stable auto-waiting, more verbose code than Playwright
- Official WhatsApp Business API: Requires business verification, paid tier, overkill for personal use

---

## 2. MCP Server Architecture & JSON-RPC over stdio

**Decision**: Implement MCP servers as standalone Python processes using JSON-RPC 2.0 over stdin/stdout

**Rationale**:
- MCP protocol is language-agnostic (stdin/stdout), allows future servers in Go/Rust/Node.js
- Isolated processes = isolated permissions (email-mcp holds SMTP password, whatsapp-mcp holds Playwright session, no shared secrets)
- Claude Code natively supports MCP via `~/.config/claude-code/mcp.json` configuration
- JSON-RPC 2.0 is well-specified, tooling exists (Python: `jsonrpcserver`)

**MCP Server Template** (Python):
```python
#!/usr/bin/env python3
import sys
import json
import smtplib  # Example: email MCP
from jsonrpcserver import method, Success, Error, dispatch

@method
def send_email(to: str, subject: str, body: str) -> dict:
    try:
        # SMTP send logic
        smtp = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
        smtp.starttls()
        smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))

        msg = f"Subject: {subject}\n\n{body}"
        smtp.sendmail(os.getenv('SMTP_USER'), to, msg)
        smtp.quit()

        return Success({"message_id": f"msg_{int(time.time())}", "sent_at": datetime.now().isoformat()})
    except Exception as e:
        return Error(code=-32000, message=f"SMTP_SEND_FAILED: {str(e)}")

def main():
    # Read JSON-RPC requests from stdin, write responses to stdout
    for line in sys.stdin:
        request = json.loads(line)
        response = dispatch(request)
        print(json.dumps(response), flush=True)

if __name__ == '__main__':
    main()
```

**MCP Configuration** (`~/.config/claude-code/mcp.json`):
```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["/path/to/mcp_servers/email_mcp/server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-app-password"
      }
    },
    "whatsapp-mcp": {
      "command": "python",
      "args": ["/path/to/mcp_servers/whatsapp_mcp/server.py"],
      "env": {
        "WHATSAPP_SESSION_PATH": "/home/user/.whatsapp_session"
      }
    },
    "linkedin-mcp": {
      "command": "python",
      "args": ["/path/to/mcp_servers/linkedin_mcp/server.py"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "your-oauth2-token",
        "LINKEDIN_AUTHOR_URN": "urn:li:person:xxxxx"
      }
    }
  }
}
```

**Tool Registration** (server advertises available tools):
```python
@method
def tools_list() -> list:
    return Success({
        "tools": [
            {
                "name": "send_email",
                "description": "Send an email via SMTP",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        ]
    })
```

**Error Handling**:
- Invalid JSON → return JSON-RPC parse error (-32700)
- Method not found → return method not found error (-32601)
- Server exception → return server error (-32000 to -32099 custom codes)
- Timeout (no response after 30s) → client logs timeout, creates escalation

**Alternatives Considered**:
- REST API (HTTP server): Requires port management, auth tokens, overkill for localhost communication
- Direct Python imports (no MCP): Violates separation of concerns, all secrets in one process, no future multi-language support
- gRPC: Heavier protocol, less human-readable than JSON-RPC

---

## 3. Ralph Wiggum Loop Implementation Pattern

**Decision**: Implement as Python async function with state persistence and max iteration guard

**Rationale**:
- Async allows concurrent plan execution (multiple plans in progress)
- State persistence (`vault/In_Progress/{plan_id}/state.md`) enables restart recovery
- Max 10 iterations prevents infinite loops while allowing reasonable retries (3 retries/step × 3 steps = 9 iterations)
- File-based state (markdown) maintains local-first architecture (no database)

**Loop Pseudocode**:
```python
async def execute_plan_ralph_wiggum_loop(plan_id: str):
    """
    Ralph Wiggum loop: autonomously execute plan steps with max 10 iterations.
    Exit conditions: all steps complete, max iterations reached, step blocked, plan rejected.
    """
    plan = load_plan(f"vault/Plans/PLAN_{plan_id}.md")

    # Initialize or load state
    state_file = f"vault/In_Progress/{plan_id}/state.md"
    if os.path.exists(state_file):
        state = load_state(state_file)  # Resume from last step
    else:
        state = ExecutionState(plan_id=plan_id, current_step=1, iterations_remaining=10)

    while state.iterations_remaining > 0:
        # Exit condition 1: All steps complete
        if all(step.status == "completed" for step in plan.steps):
            finalize_plan(plan, status="completed")
            move_to_done(plan)
            update_dashboard(f"Plan: {plan.objective} — COMPLETED ✓")
            return

        # Get current step
        step = plan.steps[state.current_step - 1]

        # Exit condition 2: Step blocked by dependencies
        if not dependencies_met(step, plan.steps):
            mark_step_blocked(step)
            create_escalation(f"vault/Needs_Action/plan_blocked_{plan_id}.md", step)
            return

        # Execute step
        try:
            result = await execute_step(step, plan)
            mark_step_completed(step)
            log_mcp_action(result)

            # Move to next step
            state.current_step += 1
            if state.current_step > len(plan.steps):
                state.current_step = 1  # Loop back to check completion

        except Exception as e:
            # Retry step (up to 3 times)
            if step.retry_count < 3:
                step.retry_count += 1
                await asyncio.sleep(5 * (2 ** step.retry_count))  # Exponential backoff
            else:
                # Step failed after 3 retries
                mark_step_blocked(step)
                create_escalation(f"vault/Needs_Action/plan_blocked_{plan_id}.md", step)
                return

        # Update state and decrement iterations
        state.iterations_remaining -= 1
        state.last_action = step.description
        state.last_action_timestamp = datetime.now().isoformat()
        save_state(state, state_file)
        update_dashboard(f"Plan: {plan.objective} — Step {state.current_step}/{len(plan.steps)} executing")

    # Exit condition 3: Max iterations reached
    create_escalation(f"vault/Needs_Action/plan_escalated_{plan_id}.md", "Max iterations (10) reached")
    finalize_plan(plan, status="escalated")

async def execute_step(step: PlanStep, plan: Plan):
    """Execute a single plan step (may involve MCP invocation)"""
    if step.action_type == "mcp_email":
        # Invoke email MCP
        return await mcp_client.call("email-mcp", "send_email", step.action_params)
    elif step.action_type == "mcp_whatsapp":
        return await mcp_client.call("whatsapp-mcp", "send_message", step.action_params)
    elif step.action_type == "mcp_linkedin":
        return await mcp_client.call("linkedin-mcp", "create_post", step.action_params)
    elif step.action_type == "create_file":
        # Create file in vault (e.g., summary document)
        create_vault_file(step.file_path, step.content)
        return {"status": "file_created"}
    elif step.action_type == "notify_human":
        # Create notification in vault/Needs_Action/
        create_notification(f"vault/Needs_Action/{step.notification_file}.md")
        return {"status": "human_notified"}
```

**State Persistence Format** (`vault/In_Progress/{plan_id}/state.md`):
```yaml
---
plan_id: PLAN_onboarding_2026-02-13
current_step: 2
iterations_remaining: 8
last_action: "Send intro email to client"
last_action_timestamp: 2026-02-13T14:32:10
loop_start_time: 2026-02-13T14:30:00
---

# Execution State

Current step: 2/5
Iterations used: 2 of 10
Last action: Send intro email to client (completed)
Next action: Create calendar invite for kick-off meeting
```

**Edge Cases**:
- **Mid-loop restart**: Load state from file, resume from `current_step`, iterations_remaining preserved
- **Circular dependencies**: Detect during plan validation (before loop starts), mark plan as "invalid_cycle"
- **Step requires human input**: `action_type=notify_human` creates file in `vault/Needs_Action/`, step remains pending until human completes, next iteration checks completion
- **MCP server down**: execute_step raises exception → retry 3 times → mark blocked → escalate

**Alternatives Considered**:
- Synchronous loop: Blocks other plans from executing, no concurrent plan support
- No max iterations: Risk of infinite loops on logic errors
- Database state (SQLite): Violates local-first architecture, vault corruption risk if DB and markdown out of sync

---

## 4. Email Draft Generation Best Practices

**Decision**: Use Claude API with few-shot examples and Company_Handbook.md context

**Rationale**:
- Claude excels at context-aware professional writing
- Few-shot examples (acknowledge, decline, request info) guide tone and structure
- Company_Handbook.md provides sender name, business context, tone preferences
- Prompt engineering more flexible than template-based generation

**Prompt Template**:
```python
def generate_email_draft(original_email: dict, company_handbook: str) -> str:
    prompt = f"""You are a professional email assistant. Draft a reply to the email below.

Context from Company Handbook:
{company_handbook[:500]}  # Include sender name, business context

Original Email:
From: {original_email['from']}
Subject: {original_email['subject']}
Body: {original_email['body'][:200]}

Draft a professional email reply that:
1. Starts with appropriate greeting (Hi/Dear [Name])
2. Acknowledges the email content
3. Provides a clear response or action
4. Includes call-to-action if needed
5. Ends with professional signature ({get_sender_name(company_handbook)})

Keep the reply concise (2-4 paragraphs). Use a professional but friendly tone.

Examples:
- Acknowledging: "Thank you for reaching out. I've reviewed your request and..."
- Declining politely: "I appreciate your interest. Unfortunately, we're unable to..."
- Requesting info: "Could you please provide additional details about..."

Draft Reply:"""

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

**Validation**:
- Max 500 tokens (prevents rambling)
- Includes sender name from Company_Handbook.md
- No placeholder fields like [YOUR_NAME] (all filled)

**Alternatives Considered**:
- Template-based (Jinja2): Less flexible, requires many templates for different scenarios
- GPT-4: More expensive, Claude comparable quality for business writing
- No AI (manual only): Defeats Gold tier's automation goal

---

## 5. WhatsApp Draft Generation Best Practices

**Decision**: Use Claude API with brevity constraints and keyword context

**Rationale**:
- WhatsApp requires short, conversational replies (max 500 chars per spec)
- Keyword context (urgent, meeting, payment) guides urgency and tone
- Professional but casual tone appropriate for business WhatsApp
- No emojis unless user explicitly uses them (maintain professionalism)

**Prompt Template**:
```python
def generate_whatsapp_draft(original_message: dict) -> str:
    keywords_str = ", ".join(original_message['keywords_matched'])

    prompt = f"""You are drafting a WhatsApp reply for a business conversation.

Original Message:
From: {original_message['contact_name']}
Message: {original_message['message_preview'][:200]}
Keywords detected: {keywords_str}

Draft a professional but conversational WhatsApp reply that:
1. Is BRIEF (max 3-4 sentences, 500 characters)
2. Addresses the urgency indicated by keywords ({keywords_str})
3. Uses business-casual tone (professional but not formal)
4. Ends with your name: {get_sender_name()}
5. No emojis unless original message used them

Examples:
- Urgent payment: "Got it, will process payment today. Expect confirmation by 5 PM. - John"
- Meeting request: "Sure, I'm available tomorrow 2 PM. Send calendar invite? - John"
- General inquiry: "Thanks for reaching out! Let me check and get back to you shortly. - John"

Draft Reply:"""

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,  # Enforce brevity
        messages=[{"role": "user", "content": prompt}]
    )
    draft = response.content[0].text

    # Enforce 500 char limit
    if len(draft) > 500:
        draft = draft[:497] + "..."

    return draft
```

**Validation**:
- ≤500 characters (truncate if needed)
- Includes sender name
- Addresses keywords (urgent → immediate action, meeting → availability)

**Alternatives Considered**:
- Same prompt as email: Too formal for WhatsApp
- No brevity constraint: Produces verbose replies inappropriate for messaging
- Template-based: Inflexible for diverse message types

---

## 6. LinkedIn Post Generation Best Practices

**Decision**: Use Claude API with Company_Handbook.md business goals and LinkedIn best practices

**Rationale**:
- LinkedIn posts require specific structure: hook (first line), value (body), CTA (call-to-action)
- Company_Handbook.md "Business Goals" section provides content direction
- Claude can align tone with brand voice
- 3000 char limit per LinkedIn spec

**Prompt Template**:
```python
def generate_linkedin_post(business_goals: str, posting_date: str) -> str:
    prompt = f"""You are drafting a LinkedIn post to promote a business.

Business Goals (from Company Handbook):
{business_goals[:500]}

Posting Date: {posting_date}

Draft a LinkedIn post that:
1. Starts with a HOOK (engaging first line, <100 chars)
2. Provides VALUE (insight, tip, or story related to business goals)
3. Ends with CLEAR CTA (call-to-action: comment, visit website, DM)
4. Uses 2-3 short paragraphs (not wall of text)
5. Professional tone aligned with business goals
6. Max 3000 characters

Examples:
- Hook: "Most people overlook this when building X..."
- Value: "Here's what I learned after 5 years in the industry..."
- CTA: "What's your experience? Share in comments below."

Draft Post:"""

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    draft = response.content[0].text

    # Enforce 3000 char limit
    if len(draft) > 3000:
        # Truncate at last complete sentence
        draft = draft[:2997]
        last_period = draft.rfind('.')
        if last_period > 2500:  # Reasonable truncation point
            draft = draft[:last_period+1] + " […]"

    return draft
```

**Validation**:
- ≤3000 characters (truncate at sentence boundary if needed)
- References business goals from Company_Handbook.md
- Includes hook, value, CTA structure

**Alternatives Considered**:
- Manual post writing: Time-consuming, inconsistent quality
- Scheduled template rotation: Repetitive, lacks current context
- GPT-4: More expensive, Claude comparable for business content

---

## 7. File-based Approval Workflow Implementation

**Decision**: Use `watchdog` to monitor `vault/Approved/` folder for file-move events, with file locking to prevent race conditions

**Rationale**:
- Obsidian users drag-and-drop files naturally (no CLI required)
- `watchdog` library (used in Bronze/Silver) is stable and cross-platform
- File locking (`filelock` library) prevents duplicate sends if multiple watchers process same file
- Approval log (`vault/Logs/Human_Approvals/`) provides audit trail

**Approval Watcher Pattern**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from filelock import FileLock
import os

class ApprovalHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Triggered when file moved/created in vault/Approved/"""
        if event.is_directory:
            return

        file_path = event.src_path

        # Determine action type from folder
        if '/Email/' in file_path:
            self.process_email_approval(file_path)
        elif '/WhatsApp/' in file_path:
            self.process_whatsapp_approval(file_path)
        elif '/LinkedIn/' in file_path:
            self.process_linkedin_approval(file_path)
        elif '/Plans/' in file_path:
            self.process_plan_approval(file_path)

    def process_email_approval(self, file_path):
        lock_path = file_path + '.lock'

        try:
            with FileLock(lock_path, timeout=5):  # Acquire lock (5s timeout)
                # Check if already processed (idempotency)
                if self.is_processed(file_path):
                    return

                # Load draft
                draft = load_draft(file_path)

                # Invoke email MCP
                result = mcp_client.call('email-mcp', 'send_email', {
                    'to': draft.to,
                    'subject': draft.subject,
                    'body': draft.draft_body
                })

                # Log MCP action
                log_mcp_action('email-mcp', 'send_email', result, file_path)

                # Log human approval
                log_approval(file_path, 'email', approved=True)

                # Move to Done
                move_to_done(file_path, status='sent')

                # Mark processed
                self.mark_processed(file_path)

        except Timeout:
            # Another process is handling this file
            return
        except Exception as e:
            # Log error, create escalation
            log_error(e)
            create_escalation(f"vault/Needs_Action/retry_send_{draft.id}.md", e)

def start_approval_watcher():
    observer = Observer()
    handler = ApprovalHandler()

    # Watch all approval folders
    observer.schedule(handler, 'vault/Approved/Email/', recursive=False)
    observer.schedule(handler, 'vault/Approved/WhatsApp/', recursive=False)
    observer.schedule(handler, 'vault/Approved/LinkedIn/', recursive=False)
    observer.schedule(handler, 'vault/Approved/Plans/', recursive=False)

    observer.start()
    observer.join()
```

**Deduplication Strategy**:
- Track processed files in `vault/Logs/processed_approvals.json` (append-only)
- Before executing MCP action, check if `file_path` already processed
- If processed, skip (prevents duplicate sends on watcher restart)

**Race Condition Handling**:
- `FileLock` ensures only one watcher process executes MCP action per approval file
- Timeout (5s) prevents deadlock if lock held indefinitely
- If lock timeout, assume another watcher is processing, skip silently

**Alternatives Considered**:
- Polling (check folder every N seconds): Less responsive than event-driven watchdog
- Database queue (SQLite): Violates local-first, adds complexity
- Manual CLI (`approve-draft.sh`): Requires terminal access, less user-friendly than file-move

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| WhatsApp Automation | Playwright with persistent context | Stable selectors, session persistence, headless mode |
| MCP Architecture | JSON-RPC over stdio, isolated processes | Language-agnostic, isolated permissions, Claude Code native support |
| Ralph Wiggum Loop | Async function with max 10 iterations + state persistence | Concurrent plans, restart recovery, infinite loop prevention |
| Email Drafts | Claude API with few-shot examples | Context-aware professional writing, flexible |
| WhatsApp Drafts | Claude API with brevity constraints | Short conversational replies, urgency-aware |
| LinkedIn Posts | Claude API with business goals + hook/value/CTA structure | Engaging posts aligned with brand |
| Approval Workflow | `watchdog` + `filelock` for file-move detection | Event-driven, race condition safe, user-friendly |

All NEEDS CLARIFICATION markers from plan.md are now resolved.

**Next Phase**: Generate data-model.md, contracts/, quickstart.md
