# WhatsApp Re-Authentication (Local WSL2)

When the WhatsApp session expires on your **local machine**, messages from the
admin dashboard and PM2 will fail. Fix it in under 2 minutes with the steps below.

---

## Signs the session has expired

- Admin dashboard send returns an error
- PM2 logs show `SESSION_EXPIRED` or `LOGGED_IN selector timeout`
- `vault/Needs_Action/` fills up with failed WhatsApp drafts

---

## How to re-authenticate

```bash
# 1. Open a terminal and go to /tmp (IMPORTANT — do NOT run from /mnt/d/)
cd /tmp

# 2. Run the setup script
python /mnt/d/gov\ ai\ code/QUATER\ 4\ part\ 2/hacakthon/personal-ai-employee/scripts/wa_local_setup.py
```

The script will print an **8-character pairing code**, e.g.:

```
=======================================================
  PAIRING CODE: X2XQ-DYJ8
=======================================================
On your phone:
  WhatsApp → Linked Devices → Link a Device
  Tap: 'Link with phone number instead'
  Enter: X2XQ-DYJ8
=======================================================
```

**On your phone:**
1. Open WhatsApp
2. Tap **Settings** → **Linked Devices** → **Link a Device**
3. Tap **"Link with phone number instead"**
4. Enter the code shown in the terminal

The script detects success automatically (`✅ AUTH SUCCESS`).

```bash
# 3. Restart local PM2 services
pm2 restart local_approval_handler
```

Done. Dashboard sends and PM2 approval watcher will work again.

---

## Why cd /tmp first?

On WSL2, the Playwright Node.js driver hangs indefinitely when the working
directory is on the Windows NTFS mount (`/mnt/d/`). Running from `/tmp`
(Linux tmpfs) avoids this. The script itself does `os.chdir('/tmp')` too,
but running from `/tmp` to begin with is safer.

---

## Why not QR code?

WhatsApp QR auth requires `headless=False` (a visible browser window). On WSL2,
`headless=False` causes a Chrome SIGTRAP crash. The phone pairing code approach
works fully headless with the safe arg set:
`headless=True + --no-zygote + --disable-gpu`.

---

## Session lifetime

WhatsApp linked device sessions typically last **several weeks to months**.
You only need to re-authenticate when you see send failures.

---

## Quick reference

| Step | Command |
|------|---------|
| Go to safe dir | `cd /tmp` |
| Run re-auth | `python .../scripts/wa_local_setup.py` |
| Enter code on phone | WhatsApp → Linked Devices → Link with phone number |
| Restart PM2 | `pm2 restart local_approval_handler` |
