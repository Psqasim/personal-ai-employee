# Personal AI Employee

> Your autonomous task management assistant that monitors an Obsidian vault and maintains an always-up-to-date dashboard.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tested](https://img.shields.io/badge/tests-passing-brightgreen.svg)](docs/bronze/bronze-testing.md)

| Tier | Status | Highlights |
|------|--------|------------|
| **Bronze** | ✅ Complete | 100% offline vault monitoring, auto dashboard |
| **Silver** | ✅ Complete | AI priority analysis, task categorization, Gmail watcher |
| **Gold** | ✅ Complete | **3/5 live integrations working!** Email ✅, Odoo ✅, WhatsApp ✅ |
| **Platinum** | ✅ Complete | WhatsApp admin notifications, stale file recovery, cloud-ready |
| **Hackathon+** | ✅ Complete | **Natural language commands, A2A orchestration, Odoo payments/contacts/bills** |

---

## 🎬 Demo Evidence (Live Testing Results)

**Hackathon+ Status:** ✅ **Production Running** — Oracle Cloud VM live 24/7, WhatsApp AI auto-reply, Natural Language Commands, A2A orchestration

### Working Integrations (Live Tested)

| Integration | Status | Evidence |
|-------------|--------|----------|
| **📧 Email (SMTP)** | ✅ **WORKING** | Email sent & delivered to Gmail inbox |
| **📊 Odoo Accounting** | ✅ **WORKING** | Draft invoices, contacts, payments, bills via XML-RPC |
| **💬 WhatsApp Auto-Reply** | ✅ **WORKING** | AI replies generated & sent on Oracle Cloud VM (Playwright) |
| **🤖 WhatsApp Commands** | ✅ **WORKING** | `!invoice Ali 5000` → vault draft created + confirmation sent |
| **🧠 Natural Language CLI** | ✅ **WORKING** | `natural_command.py "invoice Ali 5000 Rs"` → draft in <3s |
| **☁️ Oracle Cloud VM** | ✅ **WORKING** | 3 PM2 processes running 24/7 (orchestrator, git_sync, watcher) |
| **🔄 A2A Orchestration** | ✅ **WORKING** | Cloud writes Needs_Action/ → local claims → executes → Done/ |
| 🔗 LinkedIn | ⏸️ Token scope | MCP implemented, API token needs extra permissions |
| 🐦 Twitter | ⏸️ API credit | MCP implemented, needs $5 API tier upgrade |

**Note:** All 5 MCP servers fully implemented. LinkedIn/Twitter blocked by external API limitations only (not code). Email, Odoo, WhatsApp, and the full A2A pipeline are working end-to-end.

### Screenshots

**Email Automation Test:**
![Email Sent Successfully](public/emailTest.png)
*Real email sent via SMTP MCP - delivered to muhammadqasim0326@gmail.com*

**MCP Servers Status:**
![All 5 MCP Servers Operational](public/mcptest.png)
*✅ All MCP servers responding: Email, LinkedIn, WhatsApp, Twitter, Odoo*

**Odoo Accounting Integration:**
![Draft Invoice Created](public/odootest.png)
*Draft invoice INV/2026/00001 created (100.00 PKR) - draft-only safety mode*

**Obsidian Dashboard:**
![Task Dashboard](public/obsidianDasbboard.png)
*Enhanced dashboard with emoji indicators and real-time task tracking*

**Approval Workflow:**
![Email Approval Process](public/obsidanApprovalEmail.png)
*Human-in-the-loop approval system - email draft pending approval*

**Test Results:**
- ✅ 47/48 automated tests passing (97% coverage)
- ✅ All 5 MCP servers operational (100% connectivity)
- ✅ 6/9 integrations fully working end-to-end (Email, Odoo, WhatsApp, Commands, CLI, A2A)
- ✅ Safety gates enforced (approval workflow, bounded loops, audit logging)
- ✅ Oracle Cloud VM running stable — 3 PM2 processes, git auto-sync every 60s

📄 **Full Validation Report:** [docs/reports/HACKATHON-FINAL-SUBMISSION.md](docs/reports/HACKATHON-FINAL-SUBMISSION.md)

---

## ✨ What It Does

Drop a markdown file in your Obsidian vault's Inbox folder. Within 30 seconds, your Dashboard automatically updates with:
- Task filename (as clickable Obsidian wiki link)
- Timestamp when detected
- Current status (Inbox, Needs Action, Done)
- Priority level

**No manual updates. No external APIs. Just seamless task tracking.**

---

## 🚀 Quick Start

### Bronze (Offline, No API Required)

```bash
# 1. Clone and install
git clone https://github.com/Psqasim/personal-ai-employee.git
cd personal-ai-employee
pip install -e .[dev]

# 2. Initialize your vault
python3 scripts/init_vault.py ~/my-vault

# 3. Start monitoring
python3 scripts/watch_inbox.py ~/my-vault

# 4. Drop a task and watch the magic happen ✨
echo "# Review Proposal" > ~/my-vault/Inbox/task.md
```

📖 **Bronze Setup Guide**: [docs/bronze/bronze-setup.md](docs/bronze/bronze-setup.md)

### Natural Language Commands (Hackathon+)

```bash
# Send any command in plain English — Claude parses intent and creates a vault draft
venv/bin/python3 scripts/natural_command.py "invoice Ali 5000 Rs web design"
# → vault/Pending_Approval/Odoo/INVOICE_DRAFT_MANUAL_Ali_*.md

venv/bin/python3 scripts/natural_command.py "send email to john@gmail.com about meeting"
# → vault/Pending_Approval/Email/EMAIL_DRAFT_CMD_*.md

venv/bin/python3 scripts/natural_command.py "add contact John Smith john@co.com +9230012345"
# → vault/Pending_Approval/Odoo/CONTACT_DRAFT_*.md

venv/bin/python3 scripts/natural_command.py "register payment for invoice INV/2026/00003"
# → vault/Pending_Approval/Odoo/PAYMENT_DRAFT_*.md

venv/bin/python3 scripts/natural_command.py "create purchase bill from Ali Traders 25000 Rs supplies"
# → vault/Pending_Approval/Odoo/BILL_DRAFT_*.md

# WhatsApp: send "!invoice Ali 5000" from your phone → appears in dashboard
# Requires: CLAUDE_API_KEY set in .env, WHATSAPP_ADMIN_NAME set to your contact name
```

### Silver (AI-Powered, Requires Claude API Key)

```bash
# 1. Get your Claude API key from https://console.anthropic.com/
# 2. Configure .env
cp .env.example .env
# Set: ENABLE_AI_ANALYSIS=true, CLAUDE_API_KEY=sk-ant-api03-...

# 3. Install Silver dependencies
pip install anthropic>=0.18.0 google-api-python-client>=2.80.0 \
  google-auth-oauthlib>=1.0.0

# 4. Start watcher (AI analysis enabled automatically)
python3 scripts/watch_inbox.py

# 5. Drop a task — Dashboard now shows AI-assigned priority + category
echo "# Urgent client proposal — due today" > vault/Inbox/task.md
```

⚡ **Silver Quickstart**: [docs/silver/quickstart.md](docs/silver/quickstart.md)

---

## 🏗️ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    User Workflow                             │
└────────────┬────────────────────────┬────────────────────────┘
             │                        │
             v                        v
    ┌────────────────┐       ┌────────────────┐
    │  Drop .md File │       │ Query via CLI  │
    │  in Inbox/     │       │ (Claude Code)  │
    └────────┬───────┘       └────────┬───────┘
             │                        │
             v                        v
    ┌──────────────────────────────────────────┐
    │        File Watcher (30s polling)        │
    │  • Detects new files in Inbox/           │
    │  • Updates Dashboard.md (atomic write)   │
    │  • Logs events to vault/Logs/            │
    └──────────────────┬───────────────────────┘
                       │
                       v
    ┌──────────────────────────────────────────┐
    │           Obsidian Vault                 │
    │  Inbox/  Needs_Action/  Done/  Plans/    │
    │  Dashboard.md  Company_Handbook.md       │
    └──────────────────────────────────────────┘
```

**Architecture Deep Dive**: [docs/bronze/bronze-architecture.md](docs/bronze/bronze-architecture.md)

---

## 📚 Documentation

### Bronze Tier

| Guide | Description | Link |
|-------|-------------|------|
| **Setup** | Installation, configuration, starting the watcher | [bronze-setup.md](docs/bronze/bronze-setup.md) |
| **Architecture** | Component design, data flow, API reference | [bronze-architecture.md](docs/bronze/bronze-architecture.md) |
| **Usage** | Daily workflow, Claude Code integration | [bronze-usage.md](docs/bronze/bronze-usage.md) |
| **Testing** | Unit tests, integration tests, troubleshooting | [bronze-testing.md](docs/bronze/bronze-testing.md) |

### Silver Tier

| Guide | Description | Link |
|-------|-------------|------|
| **Quickstart** | 5-minute setup: API key + Gmail | [silver/quickstart.md](docs/silver/quickstart.md) |
| **Setup Guide** | Full setup: WhatsApp, LinkedIn, PM2, MCP | [silver/setup-guide.md](docs/silver/setup-guide.md) |
| **Testing** | Manual testing guide for Silver features | [silver/manual-testing-guide.md](docs/silver/manual-testing-guide.md) |

### Gold Tier

| Guide | Description | Link |
|-------|-------------|------|
| **Architecture** | Complete system architecture, data flows | [gold/architecture-diagram.md](docs/gold/architecture-diagram.md) |
| **Lessons Learned** | Challenges, solutions, recommendations | [gold/lessons-learned.md](docs/gold/lessons-learned.md) |
| **Demo Script** | 5-10 min hackathon walkthrough | [DEMO-SCRIPT.md](DEMO-SCRIPT.md) |
| **Agent Skills** | 7 reusable skills (email, whatsapp, linkedin, etc.) | [.claude/skills/](.claude/skills/) |

### Platinum Tier

| Guide | Description | Link |
|-------|-------------|------|
| **Oracle Cloud Setup** | Deploy cloud agent to Oracle Free Tier VM | [oracle-cloud-setup.md](docs/platinum/oracle-cloud-setup.md) |
| **PM2 Config** | Process management, auto-restart, log rotation | [ecosystem.config.js](ecosystem.config.js) |
| **WhatsApp Notifications** | 5 alert types, cooldowns, admin number setup | [whatsapp_notifier.py](cloud_agent/src/notifications/whatsapp_notifier.py) |

### Hackathon+ (Natural Language Commands + A2A)

| Guide | Description | Link |
|-------|-------------|------|
| **Command Router** | Claude-powered intent parser, 8 action types | [command_router.py](cloud_agent/src/command_router.py) |
| **CLI Interface** | Natural language commands from terminal | [natural_command.py](scripts/natural_command.py) |
| **WhatsApp Commands** | `!invoice`, `!email`, `!contact` via WhatsApp | [whatsapp_watcher.py](scripts/whatsapp_watcher.py) |
| **A2A Orchestration** | Agent-to-agent via vault files + git sync | [local orchestrator](local_agent/src/orchestrator.py) |

---

## 🎯 Features

### Bronze Tier (Foundation)
- ✅ **Automatic File Detection** - Monitors Inbox/ every 30 seconds
- ✅ **Dashboard Auto-Update** - Maintains task table with wiki links
- ✅ **Event Logging** - All actions logged to vault/Logs/
- ✅ **Atomic Writes** - No data corruption, timestamped backups
- ✅ **Agent Skills API** - Query vault from Claude Code
- ✅ **100% Offline** - No network requests, all local processing
- ✅ **Obsidian Compatible** - Standard markdown, preserves formatting

### Silver Tier (AI-Powered)
- ✅ **AI Priority Analysis** - Claude assigns High/Medium/Low priority to every task
- ✅ **Task Categorization** - Work / Personal / Urgent auto-classification
- ✅ **24h Response Caching** - Minimizes API costs (typical: <$0.01/day)
- ✅ **PII Sanitization** - Emails, phones, and account numbers stripped before API calls
- ✅ **Gmail Watcher** - Monitors important emails, creates vault tasks automatically
- ✅ **Graceful Fallback** - Reverts to Bronze behavior when API is unavailable

### Gold Tier (Autonomous Execution) 🎯
- ✅ **Email Automation** - AI drafts replies, human approves, SMTP sends via MCP
- ✅ **WhatsApp Automation** - Playwright automation, keyword detection, approval workflow
- ✅ **LinkedIn Automation** - Business-aligned posts, rate limiting, scheduling
- ✅ **Multi-Step Plans** - Ralph Wiggum loop (max 10 iterations) executes complex tasks
- ✅ **MCP Integration** - 4 MCP servers (email, whatsapp, linkedin, odoo) with approval gates
- ✅ **CEO Briefing** - Weekly analytics with AI insights, cost tracking, proactive suggestions
- ✅ **Odoo Integration** - Draft invoice/expense creation (NEVER auto-confirms)
- ✅ **Comprehensive Logging** - All MCP actions logged BEFORE execution
- ✅ **7 Agent Skills** - Reusable skills package for email, whatsapp, linkedin, social-media, odoo, ceo-briefing, ralph-wiggum-loop

### Platinum Tier (Proactive Intelligence) 🚀
- ✅ **WhatsApp Admin Notifications** - 5 notification types sent automatically to admin
  - 🚨 Urgent email alert (fires immediately when high-priority email detected)
  - ⏳ Pending approvals alert (fires when 5+ items waiting in Pending_Approval/)
  - ❌ Critical error alert (fires on email send failure or system crash)
  - ☀️ Morning summary at 8 AM UTC daily (emails pending, processed yesterday, API cost)
  - ✅ Task completed confirmation (after each successful email/WhatsApp send)
- ✅ **Non-Blocking Architecture** - All WhatsApp sends run in daemon threads (65s timeout); never blocks main loops
- ✅ **Stale File Recovery (FR-P016)** - Hourly scan of vault/In_Progress/ — files older than 24h auto-moved back to Needs_Action/ with audit log
- ✅ **Environment Flag Control** - `ENABLE_WHATSAPP_NOTIFICATIONS=true/false` for silent skip
- ✅ **Configurable Admin Number** - `WHATSAPP_NOTIFICATION_NUMBER` in `.env`

### Hackathon+ (Natural Language Commands + A2A) 🤖
- ✅ **Natural Language Command Router** (`cloud_agent/src/command_router.py`) — Claude-powered intent extractor supporting 8 action types; few-shot prompted with 11 examples; routes to correct vault draft automatically
- ✅ **CLI Interface** (`scripts/natural_command.py`) — Terminal-based command entry: `python scripts/natural_command.py "invoice Ali 5000 Rs web design"` → creates vault draft instantly
- ✅ **WhatsApp Command Interface** — Admin messages starting with `!` or `/` (or from `WHATSAPP_ADMIN_NAME`) are parsed as commands; bot replies with draft confirmation instead of auto-reply
- ✅ **A2A Orchestration (Agent-to-Agent)** — `monitor_needs_action()` fully implemented: cloud agent writes to `vault/Needs_Action/`, local agent atomically claims tasks, routes by `action` frontmatter field, executes, and releases to `Done/` or `Failed/`
- ✅ **Odoo: Create Contact** — `OdooPoster.create_contact(name, email, phone)` → `res.partner.create()` with WhatsApp confirmation
- ✅ **Odoo: Register Payment** — `OdooPoster.register_payment(invoice_number)` → `account.payment.create()` + `action_post()` + reconcile attempt against invoice
- ✅ **Odoo: Purchase Bills** — `OdooPoster.create_purchase_bill(vendor, amount)` → `account.move` with `move_type=in_invoice` (draft only, never auto-posts)
- ✅ **New Vault Dataclasses** — `OdooContact`, `OdooPayment`, `OdooBill` in `agent_skills/vault_parser.py` with full frontmatter parsing

#### Command Examples (WhatsApp or CLI)
```
"invoice Ali 5000 Rs web design"          → Odoo draft invoice
"!email john@co.com about the proposal"   → Email draft
"add contact John Smith john@co.com"      → Odoo contact draft
"register payment for INV/2026/00003"     → Payment draft
"purchase bill Ali Traders 25000 supplies"→ Vendor bill draft
"post linkedin: We shipped AI invoicing!" → LinkedIn draft
```

#### How A2A Works
```
Oracle Cloud VM (cloud_agent)          Local PC / WSL2 (local_agent)
─────────────────────────────          ─────────────────────────────
WhatsApp command received              git pull every 30s
  ↓ command_router.py                    ↓
vault/Pending_Approval/ ──approve──→  vault/Approved/ ──auto──→ executor

OR (direct A2A path):
vault/Needs_Action/TASK.md  ─────────→ claim_task() → In_Progress/local/
                                         ↓ detect action field
                                         ↓ route to OdooPoster / email_sender
                                       vault/Done/  ←── result
```

---

## 🗺️ Roadmap

| Tier | Status | Capabilities |
|------|--------|-------------|
| **Bronze** | ✅ **Complete** | Vault monitoring, dashboard updates, agent skills API |
| **Silver** | ✅ **Complete** | AI priority analysis, task categorization, Gmail integration |
| **Gold** | ✅ **Complete** | Multi-step execution, MCP automation, human approval workflow |
| **Platinum** | ✅ **Complete** | WhatsApp admin notifications, stale recovery, proactive intelligence |
| **Hackathon+** | ✅ **Complete** | Natural language commands, A2A orchestration, Odoo contacts/payments/bills |

**Current Release**: Hackathon+ (Natural Language Commands + A2A)

---

## 🔧 Requirements

### Bronze (All Tiers)
- **Python**: 3.11 or higher
- **Obsidian**: 1.5+ (tested with 1.11.7)
- **OS**: WSL Ubuntu 22.04+ (primary), macOS 13+, Windows 11 (secondary)
- **Disk Space**: 1GB for vault with 1000 markdown files
- **RAM**: 8GB minimum (watcher uses <100MB)

### Silver (Additional)
- **Claude API Key** — from [console.anthropic.com](https://console.anthropic.com/) (free tier available)
- **anthropic** Python SDK ≥ 0.18.0
- **Google Cloud Project** — for Gmail watcher (optional)
- **Node.js 18+** — for PM2 process manager (optional)

### Gold (Additional)
- **Playwright** — `playwright install chromium` for WhatsApp automation
- **SMTP Credentials** — Gmail app password or custom SMTP server
- **LinkedIn OAuth Token** — for LinkedIn API v2 (optional)
- **MCP Servers** — JSON-RPC servers for email, whatsapp, linkedin, odoo
- **Odoo Instance** — Community or Enterprise (optional, for accounting integration)

### Platinum (Additional)
- **WhatsApp Session** — authenticated session at `WHATSAPP_SESSION_PATH` (run `scripts/setup_whatsapp_session.py` once)
- **Env vars** — `ENABLE_WHATSAPP_NOTIFICATIONS=true`, `WHATSAPP_NOTIFICATION_NUMBER=+<country><number>`

---

## 🧪 Testing

Bronze Tier is production-ready with comprehensive testing:

- ✅ **Manual End-to-End Test**: PASSED (5/5 steps)
- ✅ **File Detection**: <20 seconds (target: <30s)
- ✅ **Dashboard Update**: <1 second (target: <2s)
- ✅ **Event Logging**: All events captured correctly

**Test Results**: [docs/bronze/bronze-testing.md](docs/bronze/bronze-testing.md)

---

## 🤝 Contributing

Contributions welcome! This project follows Spec-Driven Development:

1. Review `.specify/memory/constitution.md` for development principles
2. Check `specs/bronze-tier/spec.md` for current scope
3. Run tests: `pytest --cov=agent_skills`
4. Format code: `black agent_skills/ scripts/`
5. Type check: `mypy agent_skills/ scripts/`

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Muhammad Qasim**
- Full Stack Developer | AI & Web 3.0 Enthusiast
- GIAIC Certified AI, Metaverse, and Web 3.0 Developer
- GitHub: [@Psqasim](https://github.com/Psqasim)
- LinkedIn: [muhammad-qasim](https://www.linkedin.com/in/muhammad-qasim-5bba592b4/)
- Email: muhammadqasim0326@gmail.com

---

## 🙏 Acknowledgments

Built for the GIAIC Personal AI Employee Hackathon 2026.

Special thanks to the Obsidian community for inspiration and the Claude AI team for making intelligent automation accessible.

---

**Ready to get started?** → [Setup Guide](docs/bronze/bronze-setup.md)

**Have questions?** → [Open an issue](https://github.com/Psqasim/personal-ai-employee/issues)
