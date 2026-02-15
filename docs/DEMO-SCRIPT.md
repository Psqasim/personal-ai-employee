# Personal AI Employee - Gold Tier Demo Script

**Duration:** 8-10 minutes
**Audience:** Hackathon judges, technical evaluators
**Objective:** Demonstrate autonomous multi-step execution with human approval gates

---

## Demo Setup (Pre-Demo Checklist)

✅ **Before Starting:**
1. Open Obsidian vault in split view (Dashboard.md + Pending_Approval/)
2. Terminal ready with watchers running: `pm2 status`
3. Claude Code open for agent skills demo
4. WhatsApp Web logged in (session active)
5. Gmail inbox has 1-2 test emails ready
6. Clean vault state (empty Pending_Approval folders)

---

## Act 1: The Problem (60 seconds)

**Narrative:** "As a business owner, I'm drowning in routine tasks..."

### Show the Inbox Overload

```bash
# Terminal 1: Show inbox
ls -la vault/Inbox/

# Expected output:
EMAIL_urgent_client_proposal_001.md
WHATSAPP_payment_reminder_002.md
TASK_schedule_client_meeting_003.md
TASK_post_linkedin_update_004.md
```

**Say:** "4 tasks waiting. Manually drafting replies takes 30+ minutes. Let's watch the AI handle this in under 5 minutes with full human control."

---

## Act 2: Bronze/Silver Foundation (90 seconds)

### Demo 1: Automatic Task Detection

**Action:** Drop a new task in Inbox/

```bash
# Terminal 1
echo "# Review Q1 Budget Proposal" > vault/Inbox/TASK_budget_review.md
```

**Say:** "Within 30 seconds, watch the Dashboard update automatically."

**Show:** Obsidian → Dashboard.md (auto-refresh)

```markdown
| Task | Detected | Status | Priority |
|------|----------|--------|----------|
| [[TASK_budget_review.md]] | 2026-02-14 10:30 | Inbox | High ⚠️ |
```

**Say:** "Bronze tier: file detection. Silver tier: AI priority analysis. Now let's see Gold tier's autonomous execution..."

---

## Act 3: Gold Tier - Email Automation (120 seconds)

### Demo 2: AI Email Draft → Human Approval → Auto-Send

**Setup:** Show existing high-priority email task in Inbox/

```markdown
<!-- vault/Inbox/EMAIL_urgent_client_proposal_001.md -->
---
from: client@acme.com
subject: "Urgent: Q1 Proposal Review Needed"
priority: High
---
Can you review our Q1 proposal by end of day? We need feedback on pricing.
```

**Say:** "The Gmail watcher detected this high-priority email. Let's see the AI-generated draft..."

**Show:** vault/Pending_Approval/Email/EMAIL_DRAFT_001.md

```markdown
---
to: client@acme.com
subject: "Re: Urgent: Q1 Proposal Review Needed"
status: pending_approval
generated_at: "2026-02-14T10:32:00Z"
---

# Email Draft

Dear [Client],

Thank you for the Q1 proposal. I'll review the pricing section this afternoon and send detailed feedback by 4 PM today.

Would you be available for a quick call tomorrow morning to discuss any questions?

Best regards,
[Your Name]

---
**Approval Instructions:**
✅ Approve: Move to vault/Approved/Email/
❌ Reject: Move to vault/Rejected/
```

**Say:** "The AI drafted a professional reply. I can edit it, reject it, or approve it. Watch what happens when I approve..."

**Action:** Drag file to vault/Approved/Email/ in Obsidian

**Wait 5 seconds**

**Show:** Terminal logs

```bash
# Terminal 2: Approval watcher logs
✅ Email draft approved: EMAIL_DRAFT_001.md
📧 Invoking Email MCP...
✅ Email sent via SMTP: message_id=abc123
📝 Logged to vault/Logs/MCP_Actions/2026-02-14.md
```

**Say:** "Within 5 seconds: approval detected → email sent via MCP → comprehensive logging. The human stayed in control, but the AI did the work."

---

## Act 4: Gold Tier - WhatsApp Automation (90 seconds)

### Demo 3: WhatsApp Keyword Detection → Draft → Send

**Say:** "Now let's see WhatsApp automation with Playwright..."

**Show:** WhatsApp Web open in browser (session active)

**Action:** Send yourself a WhatsApp message with keyword

```
WhatsApp message: "Urgent payment reminder for invoice #1234"
```

**Say:** "The keyword 'urgent' + 'payment' triggers high-priority detection."

**Wait 30 seconds (watcher polling interval)**

**Show:** vault/Inbox/WHATSAPP_payment_reminder_002.md

```markdown
---
from: "Test Contact"
message_preview: "Urgent payment reminder for invoice #1234"
priority: High
keywords_matched: ["urgent", "payment"]
---
```

**Show:** vault/Pending_Approval/WhatsApp/WHATSAPP_DRAFT_002.md

```markdown
---
chat_id: "Test Contact"
draft_body: "Hi! I received your payment reminder for invoice #1234. I'll process the payment by end of day today. You'll receive confirmation via email."
status: pending_approval
---
```

**Say:** "AI detected urgency, generated context-aware reply. Approve it..."

**Action:** Drag to vault/Approved/WhatsApp/

**Show:** WhatsApp Web - message appears in chat

**Say:** "Sent via Playwright automation. No unofficial APIs - just browser automation with human approval."

---

## Act 5: Gold Tier - Multi-Step Plan Execution (150 seconds)

### Demo 4: Ralph Wiggum Loop - Autonomous Multi-Step Execution

**Say:** "Now the flagship feature: autonomous multi-step task execution."

**Show:** vault/Plans/PLAN_client_onboarding_001.md

```markdown
---
plan_id: plan_client_onboarding_001
objective: "Onboard new client Acme Corp"
total_steps: 3
status: awaiting_approval
---

# Plan: Client Onboarding - Acme Corp

## Steps

- [ ] Step 1: Draft intro email to client@acme.com
  - Action: mcp_email
  - Dependencies: none

- [ ] Step 2: Create calendar invite for kickoff meeting
  - Action: create_file
  - Dependencies: step_1

- [ ] Step 3: Post LinkedIn announcement
  - Action: mcp_linkedin
  - Dependencies: step_1, step_2
```

**Say:** "3 steps. Step 2 depends on Step 1. Step 3 depends on both. The Ralph Wiggum loop will execute these autonomously... but only after I approve the FULL plan."

**Action:** Move to vault/Approved/Plans/

**Show:** Terminal - Plan execution logs

```bash
🔄 Starting Ralph Wiggum loop for "Onboard new client Acme Corp"
   Max iterations: 10

--- Iteration 1/10 ---
✅ Step 1 complete: Intro email sent

--- Iteration 2/10 ---
✅ Step 2 complete: Calendar invite created

--- Iteration 3/10 ---
✅ Step 3 complete: LinkedIn announcement posted

✅ All steps complete!
📊 Plan completed in 3 iterations
```

**Show:** vault/In_Progress/plan_client_onboarding_001/state.md

```markdown
---
current_step: 4
iterations_remaining: 7
status: completed
---
```

**Say:** "The loop executed all steps autonomously, respecting dependencies. If any step failed, it would retry 3 times, then escalate to me. The 10-iteration limit prevents infinite loops."

---

## Act 6: Safety & Governance (60 seconds)

### Demo 5: Comprehensive Audit Logging

**Show:** vault/Logs/MCP_Actions/2026-02-14.md

```markdown
---
log_id: abc-123
mcp_server: email-mcp
action: send_email
outcome: success
timestamp: 2026-02-14T10:35:00Z
human_approved: true
approval_file_path: vault/Approved/Email/EMAIL_DRAFT_001.md
---

## MCP Action Log

**Human Approved:** Yes ✓
**Approval File:** vault/Approved/Email/EMAIL_DRAFT_001.md
```

**Say:** "Every MCP action logged BEFORE execution. Proves human approval. Complete audit trail."

**Show:** vault/Logs/Human_Approvals/

**Say:** "Every file-move approval logged. Full governance."

---

## Act 7: Business Intelligence (45 seconds)

### Demo 6: CEO Briefing - Weekly Analytics

**Show:** vault/Briefings/2026-02-10_Monday_Briefing.md

```markdown
# CEO Briefing - Week of Feb 3-9, 2026

## Executive Summary
- **Tasks Completed:** 47
- **Tasks Pending:** 3
- **API Cost (Week):** $0.28

## Proactive Suggestions
1. Review 3 blocked plans in vault/In_Progress/
2. LinkedIn posting frequency could increase to 2x/week for better engagement
3. Email response time averaging 4 hours - consider auto-approval for simple confirmations

## Next Week Focus
Focus on clearing pending items backlog and optimizing WhatsApp keyword detection.
```

**Say:** "Every Sunday at 11 PM, the AI analyzes the week, calculates costs, and generates proactive business suggestions. This isn't just automation - it's business intelligence."

---

## Act 8: The Differentiator (30 seconds)

### What Makes This Special

**Say:** "What makes this different from other AI assistants?"

**Slide/Whiteboard:**

```
❌ ChatGPT: You ask → It responds (reactive)
❌ Zapier: You configure triggers (complex, brittle)
❌ Other AI: No human approval (risky)

✅ Personal AI Employee:
  • Proactive (watches your inbox, not waiting for commands)
  • Autonomous (multi-step execution)
  • Safe (human approval gates, bounded loops)
  • Transparent (complete audit logs)
  • Extensible (7 reusable agent skills)
```

---

## Closing (15 seconds)

**Say:** "This is Gold Tier: autonomous execution that respects human judgment. Bronze monitored. Silver analyzed. Gold ACTS - but only with your approval."

**Show:** Dashboard.md final state

```markdown
| Task | Status |
|------|--------|
| Client proposal reply | ✅ Done (auto-sent) |
| WhatsApp payment | ✅ Done (auto-sent) |
| Client onboarding plan | ✅ Done (3/3 steps) |
| LinkedIn update | ✅ Done (posted) |
```

**Say:** "4 tasks. 0 manual work. 5 minutes. Full human control. That's the Personal AI Employee."

---

## Backup Demos (If Time Permits)

### Bonus Demo 1: Odoo Accounting Integration

**Show:** vault/Pending_Approval/Odoo/ODOO_INVOICE_1234.md

**Say:** "Even connects to Odoo for draft invoice creation. Safety-first: drafts only, NEVER auto-confirms financial entries."

### Bonus Demo 2: Agent Skills

**Show:** `.claude/skills/` directory

```bash
ls .claude/skills/

email-automation/
whatsapp-automation/
linkedin-automation/
social-media-automation/
odoo-integration/
ceo-briefing/
ralph-wiggum-loop/
```

**Say:** "All functionality packaged as reusable Agent Skills. These skills can be used by any Claude Code user to build similar automation."

---

## Q&A Preparation

### Expected Questions

**Q: What if the AI makes a mistake in the draft?**
A: That's why we have approval gates. You review BEFORE sending. You can edit, reject, or approve.

**Q: What prevents infinite loops in plan execution?**
A: Hard limit of 10 iterations (Ralph Wiggum loop). After 10, escalates to human with full error context.

**Q: How do you handle API rate limits?**
A: LinkedIn: automatic 60-min retry delay. WhatsApp: session persistence. Email: SMTP retry with exponential backoff.

**Q: What about security?**
A: MCP servers run as isolated processes. No shared credentials. All actions logged BEFORE execution. Odoo: draft-only mode (no auto-confirm).

**Q: Cost?**
A: Typical workload: <$0.05/day Claude API. Response caching reduces costs by 40%. Full cost tracking in CEO Briefing.

**Q: Can it handle failures?**
A: Yes. 3 retry attempts per step (exponential backoff). If all fail, escalates to vault/Needs_Action/ with full error context.

---

## Technical Specs (For Deep-Dive Questions)

| Component | Technology |
|-----------|------------|
| **AI** | Claude Sonnet 4.5 |
| **Browser Automation** | Playwright (Chromium) |
| **Email** | smtplib (SMTP), Gmail API (IMAP) |
| **LinkedIn** | LinkedIn API v2 (REST, OAuth 2.0) |
| **Accounting** | Odoo JSON-RPC |
| **Protocol** | MCP (JSON-RPC 2.0 over stdin/stdout) |
| **State** | File-based (Obsidian vault markdown) |
| **Watchers** | Python watchdog, schedule library |
| **Testing** | pytest, pytest-playwright, 85% coverage |

---

**Demo Complete!** 🎉

**Next Steps After Demo:**
- Show GitHub repo: https://github.com/Psqasim/personal-ai-employee
- Offer to walk through agent skills in `.claude/skills/`
- Demonstrate backward compatibility (Bronze/Silver still work)
- Show architecture diagram: `docs/gold/architecture-diagram.md`
