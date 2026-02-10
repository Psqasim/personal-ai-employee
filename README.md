# Personal AI Employee

> Your autonomous task management assistant that monitors an Obsidian vault and maintains an always-up-to-date dashboard.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tested](https://img.shields.io/badge/tests-passing-brightgreen.svg)](docs/bronze/bronze-testing.md)

**Bronze Tier**: Foundation AI Employee - 100% offline, local-first vault monitoring with automatic dashboard updates.

---

## ✨ What It Does

Drop a markdown file in your Obsidian vault's Inbox folder. Within 30 seconds, your Dashboard automatically updates with:
- Task filename (as clickable Obsidian wiki link)
- Timestamp when detected
- Current status (Inbox, Needs Action, Done)
- Priority level

**No manual updates. No external APIs. Just seamless task tracking.**

---

## 🚀 Quick Start (5 Minutes)

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

**That's it!** Your Dashboard.md updates automatically.

📖 **Detailed Setup Guide**: [docs/bronze/bronze-setup.md](docs/bronze/bronze-setup.md)

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

| Guide | Description | Link |
|-------|-------------|------|
| **Setup** | Installation, configuration, starting the watcher | [bronze-setup.md](docs/bronze/bronze-setup.md) |
| **Architecture** | Component design, data flow, API reference | [bronze-architecture.md](docs/bronze/bronze-architecture.md) |
| **Usage** | Daily workflow, Claude Code integration | [bronze-usage.md](docs/bronze/bronze-usage.md) |
| **Testing** | Unit tests, integration tests, troubleshooting | [bronze-testing.md](docs/bronze/bronze-testing.md) |

---

## 🎯 Features (Bronze Tier)

- ✅ **Automatic File Detection** - Monitors Inbox/ every 30 seconds
- ✅ **Dashboard Auto-Update** - Maintains task table with wiki links
- ✅ **Event Logging** - All actions logged to vault/Logs/
- ✅ **Atomic Writes** - No data corruption, timestamped backups
- ✅ **Agent Skills API** - Query vault from Claude Code
- ✅ **100% Offline** - No network requests, all local processing
- ✅ **Obsidian Compatible** - Standard markdown, preserves formatting

---

## 🗺️ Roadmap

| Tier | Status | Capabilities |
|------|--------|-------------|
| **Bronze** | ✅ **Available Now** | Vault monitoring, dashboard updates, agent skills API |
| **Silver** | 🔄 Q2 2026 | AI priority analysis, auto file movement, email integration |
| **Gold** | 📅 Q3 2026 | Multi-step execution, external APIs, task decomposition |
| **Platinum** | 📅 Q4 2026 | Reflection loops, 24/7 cloud deployment, multi-agent coordination |

**Current Release**: Bronze Tier v0.1.0 (Production Ready)

---

## 🔧 Requirements

- **Python**: 3.11 or higher
- **Obsidian**: 1.5+ (tested with 1.11.7)
- **OS**: WSL Ubuntu 22.04+ (primary), macOS 13+, Windows 11 (secondary)
- **Disk Space**: 1GB for vault with 1000 markdown files
- **RAM**: 8GB minimum (watcher uses <100MB)

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
