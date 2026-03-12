# Personal AI Employee - Demo Video Script (5-7 minutes)

> **Speaker:** Muhammad Qasim
> **Format:** Screen recording + voiceover (no face cam)
> **Dashboard URL:** http://129.151.151.212:3000/dashboard (cloud — everything works here)
> **Recording:** OBS Studio (laptop screen) + Phone screen recorder (WhatsApp)
> **Editing:** CapCut (free) — cut out waiting time, join clips

---

## My Recording Strategy

**Best approach: Record everything with waiting, then CUT in editor.**

Why this is better:
- No pressure — take your time, make mistakes, redo anything
- Wait 2-3 minutes for WhatsApp/email to process — just wait, cut later
- Record laptop screen AND phone screen separately, combine in editor
- Add voiceover AFTER recording if you want (or talk while recording)

**You need 2 recordings running at same time:**
1. **OBS on laptop** — records browser (dashboard) + terminal
2. **Phone screen recorder** — records WhatsApp messages arriving

After recording, open CapCut, put laptop video as main, and overlay phone video in corner when showing WhatsApp.

---

## BEFORE RECORDING — Setup (30 min before)

### Step 1: Open Cloud Dashboard
Open browser: `http://129.151.151.212:3000`
Login with your admin credentials. Make sure dark mode is on.

### Step 2: Check Cloud VM
```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 list
pm2 logs whatsapp_watcher --lines 5 --nostream
exit
```
All 4 processes should be "online". Watcher should show recent logs.

### Step 3: Clean Up Dashboard
- Go to Approvals tab — approve or reject old items so it looks clean
- Or leave 1-2 items there to show in demo

### Step 4: Open These Tabs
1. `http://129.151.151.212:3000/dashboard` (main dashboard)
2. `http://129.151.151.212:3000/dashboard/status` (MCP status)
3. `http://129.151.151.212:3000/dashboard/briefings` (CEO briefing)
4. `https://personal-ai-employee2.odoo.com` (Odoo — logged in)
5. `https://github.com/Psqasim/personal-ai-employee` (GitHub repo)
6. Terminal (WSL2) ready for SSH

### Step 5: Phone Ready
- Open WhatsApp on phone
- Start phone screen recorder (keep recording the whole time)
- Keep phone next to laptop

### Step 6: Start OBS Recording
- Record full screen at 1080p
- Start recording!

---

## SCENE 1: Introduction (30 seconds)

**Screen:** Terminal

**Do:** Show project folder
```bash
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
ls
```

**Say:**
"Assalam o Alaikum! I am Muhammad Qasim. This is my Personal AI Employee — an autonomous business assistant for the GIAIC Hackathon. It manages emails, WhatsApp, Odoo accounting, and LinkedIn — running 24/7 on Oracle Cloud with human approval. Let me show you."

**Then:** Switch to dashboard browser tab.

---

## SCENE 2: Dashboard Overview (45 seconds)

**Screen:** Browser — `http://129.151.151.212:3000`

**Do:** Show login page (glass design, particles). Login.

**Say:**
"This is the admin dashboard — Next.js 16 with glassmorphism design, dark mode, particle animations."

**Do:** After login, point mouse at stats cards.

**Say:**
"The dashboard shows real-time numbers — pending tasks, in progress, and completed. These tabs show approvals, completed items, API usage, and the vault file browser."

**Do:** Quickly click each tab to show them.

---

## SCENE 3: Send WhatsApp from Dashboard (2-3 min recording, cut to 50 sec)

**Screen:** Browser — Dashboard

> **Wait time:** ~1-2 min for message to arrive on WhatsApp. KEEP RECORDING. Cut the wait in editing.

**Do:** Click "Quick Create" in sidebar. Click "WhatsApp" tab.

**Fill in:**
- Phone: `923460326429` (your own number)
- Message: Click **"AI Generate"** button — let Claude write the message
- OR type: `Assalamu Alaikum! Meeting confirmed for tomorrow 3 PM. See you there InshaAllah!`

**Say:**
"Quick Create lets me send anything — emails, WhatsApp, invoices, LinkedIn posts. Let me send a WhatsApp message. I can type it myself or click AI Generate to let Claude write it."

**Do:** Click Submit.

**Say:**
"It creates a draft in the vault. Now I approve it..."

**Do:** Go to Approvals tab. Find the WhatsApp draft. Click "Approve & Send".

**Say:**
"I click Approve and Send. The cloud watcher picks it up and sends via Playwright browser automation."

**Do:** Wait for message to arrive on phone (1-2 min). Keep recording. When it arrives:

**Say:**
"And there it is — message received on WhatsApp! Sent from the cloud through browser automation."

> **In editing:** Cut the 1-2 min waiting to ~5 seconds with a fade/cut.

---

## SCENE 4: Send Email from Dashboard (2-3 min recording, cut to 45 sec)

**Screen:** Browser — Dashboard

> **Wait time:** ~30-60 sec for email to send. Cut in editing.

**Do:** Click "Quick Create". Click "Email" tab.

**Fill in:**
- To: `muhammadqasim0326@gmail.com` (your own email)
- Subject: `Project Update - AI Employee Demo`
- Click **"AI Generate"** to let Claude write the body

**Say:**
"Now an email. I type the address and subject, then click AI Generate — Claude writes a professional email body."

**Do:** Click Submit. Go to Approvals tab. Click "Approve & Send".

**Say:**
"Same approval flow — the AI drafts, I review, I approve. The email goes out via SMTP. No email ever sends without my approval."

**Do:** Show email arrived in Gmail (open Gmail tab or show on phone).

> **In editing:** Cut waiting time.

---

## SCENE 5: Create Odoo Invoice (50 seconds)

**Screen:** Browser — Dashboard + Odoo tab

**Do:** Click "Quick Create". Click "Invoice" tab.

**Fill in:**
- Customer: Ali
- Amount: 5000
- Description: Web design project

**Do:** Click Submit.

**Say:**
"Odoo accounting integration — I create invoices, contacts, payments, and bills. This creates a DRAFT invoice in Odoo. The system never auto-confirms financial transactions — that is a safety rule."

**Do:** Switch to Odoo browser tab. Show the draft invoice.

**Say:**
"See? Draft state in Odoo. I have to manually confirm it. The AI employee cannot spend my money."

---

## SCENE 6: WhatsApp Auto-Reply from Mobile (2-3 min recording, cut to 50 sec)

**Screen:** Phone screen recording (WhatsApp)

> **This is the big demo moment.** You send a command from WhatsApp, the AI processes it and replies.
> **Wait time:** 2-5 min for AI to reply. KEEP PHONE RECORDING. Cut in editing.

**Do on phone:** Open WhatsApp. Send message to your own number (the bot reads it):
```
Hey send a WhatsApp message with Salam and Quran verse to 923011496677
```

**Say (voiceover, add later):**
"Now the coolest part — I can give commands directly from WhatsApp. I tell the AI to send a message with a Quran verse to a friend."

**Do:** Wait for the bot to reply with confirmation (1-3 min).

**Say:**
"The cloud agent reads my WhatsApp command, uses Claude AI to generate the message, and sends it. All from my phone — no dashboard needed."

**Do:** Show the AI's confirmation reply and the delivered message.

> **In editing:** Cut waiting time. Show command sent, then quick cut to reply received.

---

## SCENE 7: Oracle Cloud — SSH & PM2 Logs (50 seconds)

**Screen:** Terminal

**Do:**
```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 list
```

**Say:**
"The cloud side — Oracle Cloud VM running 24/7 for free. Four PM2 processes: orchestrator watches Gmail, git sync pulls code every 60 seconds, WhatsApp watcher sends approved messages, and auto-reply handles WhatsApp with AI."

**Do:** Run `pm2 logs --lines 20`

**Say:**
"Live logs — you can see it actively checking emails, processing WhatsApp messages, sending notifications."

**Do:** Ctrl+C, then `exit`.

---

## SCENE 8: CEO Briefing + MCP Status (40 seconds)

**Screen:** Browser — Dashboard

**Do:** Click "Briefings" in sidebar. Click on latest briefing.

**Say:**
"Every week, the AI generates a CEO Briefing — task summary, API costs, and business suggestions. It tells me what was done, how much it cost, and what to focus on next week."

**Do:** Scroll through briefing briefly. Then click "Server Status" in sidebar.

**Say:**
"MCP server status — all services online. Email, Gmail, WhatsApp, Odoo, LinkedIn, Twitter. Each is a separate MCP server."

---

## SCENE 9: Vault Browser + Obsidian Comparison (40 seconds)

**Screen:** Browser — Dashboard

**Do:** Click "Vault Browser" tab on main dashboard. Expand a Done/WhatsApp file.

**Say:**
"The Vault Browser shows every file — completed items, failed, pending. Each file has YAML metadata with full audit trail."

**Do:** Open Obsidian briefly (if installed) OR just say:

**Say:**
"In Silver tier, we used Obsidian vault with manual file moves for approvals. Now in Platinum tier, the dashboard does everything — one click to approve, reject, or create. Same vault system underneath, but much easier to use."

---

## SCENE 10: GitHub Repo (20 seconds)

**Screen:** Browser — GitHub

**Do:** Switch to GitHub tab. Show the repo page. Scroll to README.

**Say:**
"Full source code is open source on GitHub. Cloud agent, dashboard, 5 MCP servers, scripts, vault system — everything documented in the README."

---

## SCENE 11: Closing (30 seconds)

**Screen:** Browser — Dashboard

**Do:** Show dashboard one last time.

**Say:**
"That is my Personal AI Employee. All five hackathon tiers complete — Bronze through Hackathon Plus. Running 24/7 on Oracle Cloud. Handles email, WhatsApp, LinkedIn, Odoo accounting — all with human approval at every step."

**Pause.**

**Say:**
"Tech stack: Python, Next.js, Claude AI, Playwright, PM2, Oracle Cloud. Built solo with Claude Code. Thank you for watching! Assalam o Alaikum!"

---

## Timing (After Editing)

| Scene | Topic | Final Duration |
|-------|-------|---------------|
| 1 | Introduction | 0:30 |
| 2 | Dashboard Overview | 0:45 |
| 3 | WhatsApp from Dashboard | 0:50 |
| 4 | Email from Dashboard | 0:45 |
| 5 | Odoo Invoice | 0:50 |
| 6 | WhatsApp Auto-Reply (mobile) | 0:50 |
| 7 | SSH & PM2 Logs | 0:50 |
| 8 | CEO Briefing + MCP Status | 0:40 |
| 9 | Vault Browser | 0:40 |
| 10 | GitHub | 0:20 |
| 11 | Closing | 0:30 |
| **TOTAL (after cuts)** | | **~6:30** |

**Raw recording time (before cuts):** ~15-20 minutes (because of waiting for WhatsApp/email)

---

## Editing Guide (CapCut)

### Step 1: Import All Clips
- Import OBS laptop recording
- Import phone WhatsApp screen recording

### Step 2: Main Timeline
Put laptop recording as the main video on timeline.

### Step 3: Cut Waiting Time
Find the parts where you waited 1-3 minutes for messages to send. Cut them:
- Keep the "I click Approve" part
- Cut to "And it arrived!" part
- Add a quick fade transition between

### Step 4: Add Phone Overlay
When showing WhatsApp messages on phone:
- Put phone recording as small overlay in bottom-right corner
- Or split screen — laptop left, phone right

### Step 5: Add Voiceover (Optional)
If you didn't talk during recording:
- Record voiceover separately
- Match it to the video

### Step 6: Final Touches
- Add low background music (YouTube Audio Library — search "tech background")
- Add text title at start: "Personal AI Employee — GIAIC Hackathon 2026"
- Export at 1080p

---

## What Takes Time (Plan Your Patience)

| Action | Wait Time | What Happens |
|--------|-----------|--------------|
| Quick Create WhatsApp → Approve | 1-2 min | Cloud watcher picks up file, opens Chrome, sends |
| Quick Create Email → Approve | 30-60 sec | SMTP sends immediately after approval |
| AI Generate (any type) | 5-10 sec | Claude API generates content |
| WhatsApp command from phone | 2-5 min | Cloud reads message, generates reply, sends |
| Odoo invoice create | 5-10 sec | Direct API call, fast |
| CEO Briefing generation | 10-20 sec | Python script, local processing |

**Total waiting across all scenes: ~8-10 minutes**
**After editing cuts: video is 5-7 minutes**
