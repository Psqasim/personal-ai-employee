#!/usr/bin/env python3
"""
WhatsApp Local Setup (WSL2-compatible) — phone pairing code authentication.

Works headlessly on WSL2: headless=True + --no-zygote + --disable-gpu
(headless=False SIGTRAPs; --enable-unsafe-swiftshader + --no-zygote SIGTRAPs)

Usage:
    cd /tmp
    python /path/to/scripts/wa_local_setup.py

Steps:
  1. Script prints an 8-char pairing code
  2. On your phone: WhatsApp → Linked Devices → Link a Device
     → tap "Link with phone number instead" → enter the code
  3. Script detects success and session is saved
"""
import os, sys, re, time

# CRITICAL: change to Linux fs before importing playwright
# (WSL2 Playwright driver hangs indefinitely when CWD is on /mnt/d Windows mount)
os.chdir("/tmp")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load .env
env_file = os.path.join(project_root, ".env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.split("#")[0].strip())

SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", "/home/ps_qasim/.whatsapp_session_dir")
PHONE = os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "+923460326429").replace(" ", "")

# Verified working on WSL2: headless=True + --no-zygote + --disable-gpu (no SwiftShader)
WSL2_ARGS = [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-crash-reporter",
    "--disable-background-networking", "--no-zygote",
    "--disable-gpu", "--disable-setuid-sandbox",
]
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

# JS helpers — all use JS to avoid headless viewport visibility issues
JS_CLICK_LINK_PHONE = """() => {
    const el = [...document.querySelectorAll('div,a,span')]
        .find(e => e.textContent.trim().startsWith('Link with phone number'));
    if (el) { el.click(); return 'ok'; }
    return 'not_found';
}"""

JS_PHONE_INPUT_EXISTS = """() => {
    return document.querySelectorAll('[aria-label="Type your phone number to log in to WhatsApp"]').length;
}"""

JS_FILL_PHONE = f"""() => {{
    const inp = document.querySelector('[aria-label="Type your phone number to log in to WhatsApp"]');
    if (!inp) return 'not_found';
    inp.focus();
    const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    s.call(inp, '{PHONE}');
    inp.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
    inp.dispatchEvent(new Event('change', {{bubbles: true}}));
    return inp.value;
}}"""

JS_CLICK_NEXT = """() => {
    const b = [...document.querySelectorAll("div[role=button],button")]
        .find(x => x.textContent.trim() === 'Next');
    if (b) { b.click(); return 'ok'; }
    return 'not_found';
}"""


def cleanup_locks(session_path):
    import glob, shutil
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = os.path.join(session_path, name)
        if os.path.exists(p) or os.path.islink(p):
            try: os.unlink(p)
            except Exception: pass
    for d in glob.glob("/tmp/org.chromium.Chromium.*"):
        shutil.rmtree(d, ignore_errors=True)


def extract_pairing_code(page):
    """Extract 8-char pairing code from WhatsApp page body."""
    txt = page.locator("body").inner_text()
    lines = txt.split("\n")
    code_chars = []
    in_code = False
    for ln in lines:
        ln = ln.strip()
        if "Enter code on phone" in ln or "Linking WhatsApp" in ln:
            in_code = True
            continue
        if in_code:
            if re.match(r"^[A-Z0-9]$", ln):
                code_chars.append(ln)
            elif len(code_chars) >= 8:
                break
            elif ln and ln != "-" and not re.match(r"^[A-Z0-9]$", ln) and len(code_chars) < 4:
                in_code = False
    return "".join(code_chars[:8])


def navigate_to_phone_pairing(page):
    """Click 'Link with phone number instead', fill phone, get pairing code."""
    clicked = page.evaluate(JS_CLICK_LINK_PHONE)
    print(f"JS click 'Link with phone number': {clicked}", flush=True)
    time.sleep(6)
    page.screenshot(path="/tmp/wa_setup_1.png")

    n = page.evaluate(JS_PHONE_INPUT_EXISTS)
    print(f"Phone input found: {n}", flush=True)
    if not n:
        # Try scrolling to trigger layout
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        n = page.evaluate(JS_PHONE_INPUT_EXISTS)
        print(f"Phone input after scroll: {n}", flush=True)

    if n:
        val = page.evaluate(JS_FILL_PHONE)
        print(f"Phone filled: {val}", flush=True)
        time.sleep(1)
        nr = page.evaluate(JS_CLICK_NEXT)
        print(f"Next clicked: {nr}", flush=True)
        time.sleep(12)
        page.screenshot(path="/tmp/wa_setup_2.png")
        return extract_pairing_code(page)
    else:
        # Print body for debugging
        body_snippet = page.locator("body").inner_text()[:300]
        print(f"Body after click: {body_snippet!r}", flush=True)
        return ""


def main():
    from playwright.sync_api import sync_playwright

    print(f"\n{'='*55}")
    print("  WhatsApp Local Setup (WSL2 Headless)")
    print(f"{'='*55}")
    print(f"Session path : {SESSION_PATH}")
    print(f"Phone number : {PHONE}")
    print()

    if not os.path.isdir(SESSION_PATH):
        os.makedirs(SESSION_PATH, exist_ok=True)

    cleanup_locks(SESSION_PATH)
    print("Starting Playwright (20-25s on WSL2)...", flush=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=True,
            args=WSL2_ARGS,
            user_agent=UA,
            viewport={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        print("Browser launched. Loading WhatsApp Web...", flush=True)
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=40000)
        print("Waiting 25s for page to initialize...", flush=True)
        time.sleep(25)
        page.screenshot(path="/tmp/wa_setup_0.png")

        body = page.locator("body").inner_text()
        print(f"Page state: {body[:150]!r}", flush=True)

        code = ""

        # Already logged in?
        logged_in_js = page.evaluate("""() => {
            return document.querySelectorAll('div[aria-label="Chat list"],#pane-side').length;
        }""")
        if logged_in_js > 0:
            print("\n✅ Already logged in! Session is valid.")
            print("   Run: pm2 restart local_approval_handler")
            ctx.close()
            return True

        # On "Enter code on phone" page (leftover from previous attempt)
        if "Enter code on phone" in body or "Get a new code" in body:
            print("On pairing code page (from previous attempt)...", flush=True)
            code = extract_pairing_code(page)
            if len(code) == 8:
                print(f"Code still valid: {code[:4]}-{code[4:]}", flush=True)
            else:
                resend = page.evaluate("""() => {
                    const b = [...document.querySelectorAll('div,span,button')]
                        .find(e => ['Get a new code','Try again','Resend'].some(t => e.textContent.trim().startsWith(t)));
                    if (b) { b.click(); return 'ok'; }
                    return 'nf';
                }""")
                print(f"Resend clicked: {resend}", flush=True)
                time.sleep(6)
                code = extract_pairing_code(page)

        # On QR page
        elif "Steps to log in" in body or "Scan" in body:
            code = navigate_to_phone_pairing(page)

        # Already on phone number entry page
        elif "Enter phone number" in body:
            print("On Enter phone page.", flush=True)
            n = page.evaluate(JS_PHONE_INPUT_EXISTS)
            if n:
                val = page.evaluate(JS_FILL_PHONE)
                print(f"Phone filled: {val}", flush=True)
                time.sleep(1)
                page.evaluate(JS_CLICK_NEXT)
                time.sleep(12)
                code = extract_pairing_code(page)
            else:
                code = navigate_to_phone_pairing(page)
        else:
            print(f"Unknown state. Trying phone pairing anyway...", flush=True)
            code = navigate_to_phone_pairing(page)

        # Display pairing code and wait for user to enter on phone
        if len(code) == 8:
            display = f"{code[:4]}-{code[4:]}"
            print(f"\n{'='*55}")
            print(f"  PAIRING CODE: {display}")
            print(f"{'='*55}")
            print("On your phone:")
            print("  WhatsApp → Linked Devices → Link a Device")
            print("  Tap: 'Link with phone number instead'")
            print(f"  Enter: {display}")
            print(f"{'='*55}")
            print("Waiting 3 minutes for you to enter the code...", flush=True)

            for i in range(90):
                time.sleep(2)
                li = page.evaluate("""() => {
                    return document.querySelectorAll('div[aria-label="Chat list"],#pane-side').length;
                }""")
                if li > 0:
                    print(f"\n✅ AUTH SUCCESS after {(i+1)*2}s!", flush=True)
                    page.screenshot(path="/tmp/wa_setup_success.png")
                    print(f"Session saved: {SESSION_PATH}")
                    print("\nNow restart local services:")
                    print("  pm2 restart local_approval_handler")
                    ctx.close()
                    return True
            print("\n❌ Timeout (3 min). Code likely expired. Run again.", flush=True)
        else:
            print(f"\n❌ Could not get pairing code.")
            print("Screenshots: /tmp/wa_setup_0.png  /tmp/wa_setup_1.png  /tmp/wa_setup_2.png")

        page.screenshot(path="/tmp/wa_setup_final.png")
        ctx.close()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
