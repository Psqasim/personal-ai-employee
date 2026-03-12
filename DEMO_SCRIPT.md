# Personal AI Employee - Demo Video Script

> **Speaker:** Muhammad Qasim
> **Dashboard:** http://129.151.151.212:3000 (cloud — use this, not localhost)
> **Recording:** OBS on laptop only — everything is on laptop screen!
> **Editing:** CapCut (free) — cut the waiting parts, join all clips
> **Final video:** 5-7 minutes after cuts

---

## How to Record

**Record everything on laptop with OBS, then cut waiting parts in CapCut.**

Only 1 recording needed — OBS on laptop records everything:
- Browser (dashboard, Gmail, Odoo, GitHub)
- Terminal (SSH, PM2 logs)
- WhatsApp Desktop app (main number — shows messages arriving)
- WhatsApp Web in browser tab (2nd number — for sending commands to the bot)

No phone recording needed! Everything is on your laptop screen.

---

## Before You Start (30 min before)

### Browser Tabs (open all):
- Tab 1: `http://129.151.151.212:3000` — Dashboard (login, dark mode ON)
- Tab 2: `https://web.whatsapp.com` — Login with your **2nd number** (for sending commands)
- Tab 3: `https://personal-ai-employee2.odoo.com` (Odoo, logged in)
- Tab 4: `https://www.linkedin.com` (LinkedIn, logged in)
- Tab 5: `https://github.com/Psqasim/personal-ai-employee`
- Tab 6: `https://mail.google.com` (Gmail)

### WhatsApp Desktop App:
- Open WhatsApp Desktop (already installed on laptop)
- Link it to your **main number** (923460326429) — scan QR from phone
- This shows messages arriving from the bot
- (Cloud bot is a separate linked device — it won't conflict)

### Other:
- Open terminal (WSL2)
- Start OBS recording (full screen, 1080p)
- Bismillah, start!

---

## SCENE 1: Introduction (30 sec)

**Show:** Terminal

**Do:** Type:
```bash
cd "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
ls
```

**Say:**
"Assalam o Alaikum! My name is Muhammad Qasim. This is my project — Personal AI Employee. I built it for the GIAIC Hackathon. It handles my emails, WhatsApp messages, Odoo invoices, and LinkedIn posts. It runs 24/7 on Oracle Cloud — free tier, only 1 GB RAM. Some things take 1-2 minutes because of the small server. And every action needs my approval first. Let me show you how it works."

**Do:** Switch to browser (dashboard tab).

---

## SCENE 2: Dashboard Login (45 sec)

**Show:** Browser — login page

**Say:**
"This is the dashboard. I built it with Next.js 16. You can see the glass design, dark mode, particle animation in background."

**Do:** Type email and password. Click Login.

**Say:**
"After login, you see the main page. These three cards show how many tasks are pending, in progress, and completed."

**Do:** Point mouse at each card slowly.

**Say:**
"Down here we have four tabs — Approvals, Completed, API Usage, and Vault Browser. Let me show you the Approvals tab."

**Do:** Click Approvals tab. Show the items.

---

## SCENE 3: Send WhatsApp from Dashboard (record 3 min, cut to 1 min)

**Show:** Browser — Dashboard

**Do:** Click "Quick Create" button in sidebar.

**Say:**
"This is Quick Create. From here I can send emails, WhatsApp messages, invoices, or LinkedIn posts. Let me send a WhatsApp message."

**Do:** Click "WhatsApp" tab. Fill in:
- Phone: `923460326429`
- Message: Click **"AI Generate"** button

**Say:**
"I type the phone number. And I click AI Generate — Claude AI writes the message for me. I can also type it myself."

**Do:** Wait for AI to generate (5-10 sec). Then click Submit.

**Say:**
"I click Submit. WhatsApp messages go directly — no approval needed. The cloud server picks it up and sends it using Playwright browser automation."

**Say (while waiting — fill the gap):**
"My cloud server is Oracle Always Free tier — only 1 GB RAM. So it takes 1-2 minutes to process. It opens WhatsApp Web, finds the chat, types the message, and clicks send. All automatic."

**Do:** Keep recording. Switch to WhatsApp Desktop app. Wait 1-2 min for message to arrive.

> **While waiting:** Stay quiet or say: "Let me check if the message arrived..." — then switch to WhatsApp Desktop.

**Say (when it arrives):**
"And there — message received on my WhatsApp! Sent from the cloud."

**Do:** Now switch to terminal. SSH into cloud and show logs:
```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 logs whatsapp_watcher --lines 5 --nostream
```

**Say:**
"And in the cloud logs — you can see it found the chat, typed the message, and sent it. Everything is logged."

**Do:** Type `exit` to leave SSH.

> **In editing:** Cut the 1-2 min wait to 3-5 seconds. Keep the logs part.

---

## SCENE 4: Send Email + Show in Gmail + Show Logs (record 3 min, cut to 1 min)

**Show:** Browser — Dashboard

**Do:** Click "Quick Create". Click "Email" tab. Fill in:
- To: `muhammadqasim0326@gmail.com`
- Subject: `Project Update - AI Employee Demo`
- Click **"AI Generate"**

**Say:**
"Now let me send an email. I type my email address and subject. Then I click AI Generate — Claude writes a professional email."

**Do:** Wait for AI to generate (5-10 sec). Then click Submit.

> **While AI generates:** Stay quiet — just wait 2-3 seconds.

**Say:**
"Emails are different from WhatsApp — emails need my approval first. This is a safety rule. Let me go to Approvals."

**Do:** Click Approvals tab. Find the email draft. Click "Approve & Send".

**Say:**
"I can see the full email here. Subject, body, everything. If it looks good, I click Approve and Send."

**Do:** Click Approve. Wait 10-30 sec.

> **While waiting:** Stay quiet for 2-3 seconds. No need to talk.

**Say:**
"Now let me show you — the email is already in my Gmail."

**Do:** Switch to Gmail tab. Show the received email.

**Say:**
"See? Here it is in Gmail. Same subject, same body. Sent by the AI, approved by me."

**Do:** Now switch to terminal. SSH into cloud:
```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 logs --lines 10 --nostream
```

**Say:**
"And if I check the cloud logs — you can see it here. The email was approved, sent via SMTP, logged. Everything is tracked."

**Do:** Type `exit` to leave SSH.

> **In editing:** Cut the waiting parts.

---

## SCENE 5: Odoo Invoice (50 sec)

**Show:** Browser — Dashboard

**Do:** Click "Quick Create". Click "Invoice" tab. Fill in:
- Customer: Ali
- Amount: 5000
- Description: Web design project

**Say:**
"Now Odoo accounting. I can create invoices, contacts, payments, and bills from here. Let me create an invoice for my client Ali — 5000 rupees for web design."

**Do:** Click Submit.

**Say:**
"It creates a DRAFT invoice in Odoo. Very important — the system never confirms any money transaction. Only draft. I have to confirm it myself in Odoo."

**Do:** Switch to Odoo browser tab. Show the draft invoice.

**Say:**
"See? Here in Odoo — draft state. 5000 rupees, customer Ali. The AI employee cannot spend my money. I have to click Confirm myself."

---

## SCENE 6: LinkedIn Post (record 1 min, cut to 40 sec)

**Show:** Browser — Dashboard

**Do:** Click "Quick Create" in sidebar. Click "LinkedIn" tab.

**Say:**
"Now LinkedIn. I can post on LinkedIn from here. Let me create a post."

**Do:** Click **"AI Generate"** button. Wait 5-10 sec for AI to write the post.

> **While AI generates:** Stay quiet — just wait 2-3 seconds. It's fast.

**Say:**
"Claude AI wrote a professional LinkedIn post for me. I can edit it if I want. But this looks good."

**Do:** Click Submit.

**Say:**
"I click Submit. The system posts it on my LinkedIn using the LinkedIn API. Let me show you."

**Do:** Switch to browser. Open LinkedIn tab. Go to your profile. Show the post.

> **While LinkedIn loads:** Stay quiet — just wait for the page.

**Say:**
"And here it is on my LinkedIn profile. Posted by the AI, from the dashboard. I did not open LinkedIn — the system did everything."

> **In editing:** Cut any wait time.

---

## SCENE 7: WhatsApp Command + Auto-Reply (record 5 min, cut to 1 min)

**Show:** Browser — WhatsApp Web tab (2nd number) + WhatsApp Desktop app (main number)

> Everything on laptop! WhatsApp Web = 2nd number (sends commands). WhatsApp Desktop = main number (sees replies).

### Part A: Send Command

**Do:** Switch to WhatsApp Web tab (2nd number). Send this message to your main number:
```
Hey send a WhatsApp message with Salam and Quran verse to 923011496677
```

**Say:**
"Now the best part. I can give commands from WhatsApp. Watch — I send a message from my second number telling the AI to send a Quran verse to my friend."

**Do:** Switch to WhatsApp Desktop app (main number). Wait 1-3 min for bot reply.

**Say (while waiting — fill the gap):**
"The cloud is 1 GB RAM — Oracle Free tier. So it takes 1-2 minutes. The bot reads my command, uses Claude AI to write the message, opens WhatsApp Web, finds the contact, and sends. All automatic."

> **While waiting:** If still no reply after saying above, stay quiet. Just keep WhatsApp Desktop open on screen.

**Say (when reply comes):**
"There it is! The AI read my command, wrote the message, and sent it. You can see the confirmation here."

### Part B: Auto-Reply

**Do:** Switch to WhatsApp Web tab (2nd number). Send a message to your main number:
```
Hi Qasim, are you free tomorrow for a meeting?
```

**Say:**
"Now I send a normal message — like someone asking me a question. The AI will auto-reply on my behalf."

**Do:** Switch to WhatsApp Desktop app (main number). Wait 2-5 min for AI auto-reply.

> **While waiting:** Stay quiet. Just show the WhatsApp Desktop screen.

**Say (when AI replies):**
"And here is the AI auto-reply. It gave a natural answer with my schedule. And at the end it says 'Qasim's AI Assistant' — so people know it is AI, not me."

> **In editing:** Cut all waiting parts. Show: command sent → cut → reply. Question sent → cut → AI answer.

---

## SCENE 8: Cloud Server — PM2 Status (40 sec)

**Show:** Terminal

**Do:**
```bash
ssh -i ~/.ssh/ssh-key-2026-02-17.key ubuntu@129.151.151.212
pm2 list
```

**Say:**
"This is my Oracle Cloud server. It runs 24/7 for free — Oracle Always Free tier. You can see four processes always running."

**Do:** Point at each row.

**Say:**
"Cloud orchestrator watches my Gmail. Git sync pulls code from GitHub every 60 seconds. The dashboard is this website. And WhatsApp watcher handles all the messaging and AI replies."

**Do:** Type `exit`.

---

## SCENE 9: CEO Briefing + MCP Status (40 sec)

**Show:** Browser — Dashboard

**Do:** Click "Briefings" in sidebar. Click on the latest briefing. Scroll slowly.

**Say:**
"Every week, the AI makes a CEO Briefing. It counts how many tasks I completed, how much API cost I spent, and gives me suggestions for next week. Like a weekly report from my AI employee."

**Do:** Click "Server Status" in sidebar.

**Say:**
"And this is the MCP server status. All my services are online — Email, Gmail, WhatsApp, Odoo, LinkedIn, Twitter. Each one is a separate MCP server that Claude AI can use."

---

## SCENE 10: Vault Browser (30 sec)

**Show:** Browser — Dashboard

**Do:** Click "Vault Browser" tab. Expand a Done/WhatsApp file.

**Say:**
"The Vault Browser shows every file in the system. Done items, failed items, pending items. Each file has full details — who sent it, when, what happened. Complete audit trail."

**Do:** Click to expand one file. Show the YAML metadata.

**Say:**
"In the earlier Silver tier, I used Obsidian with manual file moves. Now the dashboard does everything — one click."

---

## SCENE 11: GitHub (20 sec)

**Show:** Browser — GitHub tab

**Do:** Show the repo. Scroll to README.

**Say:**
"Full source code is on GitHub. Cloud agent, dashboard, five MCP servers, all scripts, vault system. Everything is documented."

---

## SCENE 12: Closing (30 sec)

**Show:** Browser — Dashboard (main page)

**Say:**
"So this is my Personal AI Employee. All five hackathon tiers complete — Bronze, Silver, Gold, Platinum, and Hackathon Plus. It runs 24/7 on Oracle Cloud. Handles email, WhatsApp, LinkedIn, Odoo. And every action needs my approval."

**Do:** Pause 2 seconds.

**Say:**
"I built this solo using Python, Next.js, Claude AI, Playwright, PM2, and Oracle Cloud. Claude Code was my pair programmer. Thank you for watching! Assalam o Alaikum!"

---

## Timing After Editing

| Scene | What | Time |
|-------|------|------|
| 1 | Introduction | 0:30 |
| 2 | Dashboard Login | 0:45 |
| 3 | WhatsApp from Dashboard | 0:50 |
| 4 | Email + Gmail + Logs | 1:00 |
| 5 | Odoo Invoice | 0:50 |
| 6 | LinkedIn Post | 0:40 |
| 7 | WhatsApp Phone (command + auto-reply) | 1:00 |
| 8 | PM2 Cloud Status | 0:40 |
| 9 | CEO Briefing + MCP | 0:40 |
| 10 | Vault Browser | 0:30 |
| 11 | GitHub | 0:20 |
| 12 | Closing | 0:30 |
| **Total after cuts** | | **~7:55** |

**Raw recording time:** ~22 minutes (because of WhatsApp/email wait)
**After cutting waits in CapCut:** ~8 minutes

---

## Wait Times (So You Know When to Be Patient)

| Action | How Long to Wait |
|--------|-----------------|
| AI Generate button | 5-10 seconds |
| WhatsApp message delivery | 1-2 minutes |
| Email send after approve | 10-30 seconds |
| Odoo invoice create | 5-10 seconds |
| LinkedIn post publish | 5-15 seconds |
| WhatsApp command reply | 1-3 minutes |
| WhatsApp auto-reply | 2-5 minutes |

---

## CapCut Editing (After Recording)

1. Put laptop OBS video on main timeline
2. Find waiting parts (1-3 min gaps where nothing happens) — cut them, add fade transition
3. No phone overlay needed — everything is already on laptop screen!
4. Add title text at start: "Personal AI Employee — GIAIC Hackathon 2026"
5. Add background music (optional, low volume) — YouTube Audio Library, search "tech background"
6. Export at 1080p
7. Upload to YouTube or Google Drive
