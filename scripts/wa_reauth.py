#!/usr/bin/env python3
"""WA Pair v7 - robust phone-number pairing, no hardcoded coordinates"""
import time, sys, re, os
from playwright.sync_api import sync_playwright

SESSION = '/home/ubuntu/.whatsapp_session_dir'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')

# Phone number to authenticate with (loaded from env or fallback)
PHONE = os.getenv('WHATSAPP_PHONE_NUMBER', '+923460326429')

JS_FILL = f'''() => {{
    const selectors = [
        '[aria-label="Type your phone number to log in to WhatsApp"]',
        'input[type="tel"]',
        'input[inputmode="tel"]',
        'input[inputmode="numeric"]',
        'input[placeholder*="phone"]',
        'input[placeholder*="Phone"]',
        'input[class*="phone"]',
    ];
    let inp = null;
    for (const sel of selectors) {{
        inp = document.querySelector(sel);
        if (inp) break;
    }}
    if (!inp) return 'not_found';
    inp.focus();
    const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    s.call(inp, '{PHONE}');
    inp.dispatchEvent(new InputEvent('input',{{bubbles:true}}));
    inp.dispatchEvent(new Event('change',{{bubbles:true}}));
    return inp.value;
}}'''

JS_NEXT = '''() => {
    const candidates = [...document.querySelectorAll("div[role=button],button,[role=link]")];
    const b = candidates.find(x => /^next$/i.test(x.textContent.trim()));
    if (b) { b.dispatchEvent(new MouseEvent('click',{bubbles:true})); return 'ok'; }
    return 'nf';
}'''


def get_code(page):
    """Extract 8-char pairing code from page body"""
    txt = page.locator('body').inner_text()
    lines = txt.split('\n')
    code_chars = []
    in_code = False
    for ln in lines:
        ln = ln.strip()
        if 'Enter code on phone' in ln or 'Linking WhatsApp' in ln:
            in_code = True; continue
        if in_code:
            if re.match(r'^[A-Z0-9]$', ln):
                code_chars.append(ln)
            elif len(code_chars) >= 8:
                break
            elif ln and ln != '-' and not re.match(r'^[A-Z0-9]$', ln) and len(code_chars) < 4:
                in_code = False
    return ''.join(code_chars[:8]), code_chars, txt


def click_phone_number_link(page):
    """Click 'Log in with phone number' using text or aria selectors."""
    # Try multiple selectors for the phone-number login button
    for selector in [
        'text="Log in with phone number"',
        'text="Link with phone number instead"',
        '[data-testid="link-device-qr-code-companion-phone-number-entry"]',
        'a:has-text("phone number")',
        'button:has-text("phone number")',
        'div[role="button"]:has-text("phone number")',
        'span:has-text("Log in with phone number")',
    ]:
        try:
            loc = page.locator(selector)
            if loc.count() > 0:
                loc.first.click(force=True)
                print(f'Clicked phone link via: {selector}', flush=True)
                return True
        except Exception:
            continue
    # Fallback: look for any element containing "phone number" text
    try:
        page.get_by_text('phone number', exact=False).first.click(force=True)
        print('Clicked phone link via get_by_text fallback', flush=True)
        return True
    except Exception as e:
        print(f'Could not click phone link: {e}', flush=True)
        return False


def find_phone_input(page):
    """Count phone inputs across multiple selectors."""
    selectors = [
        '[aria-label="Type your phone number to log in to WhatsApp"]',
        'input[type="tel"]',
        'input[inputmode="tel"]',
        'input[inputmode="numeric"]',
        'input[placeholder*="phone"]',
        'input[placeholder*="Phone"]',
    ]
    for sel in selectors:
        n = page.locator(sel).count()
        if n > 0:
            print(f'Found phone input via: {sel} ({n})', flush=True)
            return n
    return 0


print('=== WA Pair v7 ===', flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION, headless=True,
        args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
              '--enable-unsafe-swiftshader','--disable-setuid-sandbox',
              '--no-first-run','--mute-audio'],
        user_agent=UA, viewport={'width':1920,'height':1080},
    )
    page = ctx.new_page()
    print('Loading...', flush=True)
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=40000)
    time.sleep(25)
    page.screenshot(path='/tmp/wa7_0.png')

    body = page.locator('body').inner_text()
    print(f'State: {body[:120]}', flush=True)

    # ── Already logged in ─────────────────────────────────────────────────────
    if page.locator('div[aria-label="Chat list"],#pane-side').count() > 0:
        print('ALREADY LOGGED IN!', flush=True)
        import subprocess
        subprocess.run(['pm2','start','/opt/personal-ai-employee/ecosystem.config.js',
                        '--only','whatsapp_watcher'], cwd='/opt/personal-ai-employee')
        ctx.close(); sys.exit(0)

    # ── Already on Enter code page ────────────────────────────────────────────
    if 'Enter code on phone' in body or 'Get a new code' in body:
        print('On Enter code page. Checking for existing code...', flush=True)
        code, chars, _ = get_code(page)
        if len(code) == 8:
            print(f'Fresh code: {code[:4]}-{code[4:]}', flush=True)
        else:
            for txt in ['Get a new code', 'Try again', 'Resend']:
                loc = page.get_by_text(txt, exact=False)
                if loc.count() > 0:
                    loc.first.click(force=True)
                    time.sleep(6)
                    code, chars, _ = get_code(page)
                    print(f'After resend: {code}', flush=True)
                    break

    # ── QR page / "Steps to log in" ──────────────────────────────────────────
    elif 'Steps to log in' in body or 'Scan the QR' in body or 'Scan this QR' in body:
        print('On QR page. Clicking "Log in with phone number"...', flush=True)
        clicked = click_phone_number_link(page)
        time.sleep(6)
        page.screenshot(path='/tmp/wa7_1.png')

        n = find_phone_input(page)
        print(f'Phone input count: {n}', flush=True)

        if n > 0:
            val = page.evaluate(JS_FILL)
            print(f'Fill result: {val}', flush=True)
            time.sleep(1)
            nr = page.evaluate(JS_NEXT)
            print(f'Next result: {nr}', flush=True)
            time.sleep(12)
            page.screenshot(path='/tmp/wa7_2.png')
            code, chars, _ = get_code(page)
        else:
            # Take screenshot to debug what we see after clicking
            page.screenshot(path='/tmp/wa7_phone_fail.png')
            body2 = page.locator('body').inner_text()
            print(f'Page after click: {body2[:200]}', flush=True)
            print('All inputs on page:', flush=True)
            for inp in page.locator('input').all():
                try:
                    print(f'  input type={inp.get_attribute("type")} '
                          f'placeholder={inp.get_attribute("placeholder")} '
                          f'aria={inp.get_attribute("aria-label")}', flush=True)
                except Exception:
                    pass
            code = ''

    # ── Already on phone entry page ───────────────────────────────────────────
    elif 'Enter phone number' in body or 'phone number' in body.lower():
        print('On phone entry page.', flush=True)
        n = find_phone_input(page)
        if n > 0:
            val = page.evaluate(JS_FILL)
            print(f'Fill result: {val}', flush=True)
            time.sleep(1)
            nr = page.evaluate(JS_NEXT)
            print(f'Next result: {nr}', flush=True)
            time.sleep(12)
            code, chars, _ = get_code(page)
        else:
            code = ''

    else:
        print('Unknown state!', flush=True)
        code = ''

    # ── Show pairing code and wait ────────────────────────────────────────────
    if len(code) == 8:
        display = code[:4] + '-' + code[4:]
        print('', flush=True)
        print('='*50, flush=True)
        print(f'  PAIRING CODE: {display}', flush=True)
        print('='*50, flush=True)
        print('On phone:', flush=True)
        print('  WhatsApp > Linked Devices > Link a Device', flush=True)
        print('  Tap: Link with phone number instead', flush=True)
        print(f'  Enter: {display}', flush=True)
        print('='*50, flush=True)
        print('Waiting 3 min for auth...', flush=True)
        for i in range(90):
            time.sleep(2)
            if page.locator('div[aria-label="Chat list"],#pane-side').count() > 0:
                print(f'AUTH SUCCESS after {(i+1)*2}s!', flush=True)
                page.screenshot(path='/tmp/wa7_success.png')
                import subprocess
                subprocess.run(['pm2','start',
                                '/opt/personal-ai-employee/ecosystem.config.js',
                                '--only','whatsapp_watcher'],
                               cwd='/opt/personal-ai-employee')
                print('whatsapp_watcher started!', flush=True)
                ctx.close(); sys.exit(0)
        print('Timeout - code may have expired.', flush=True)
    else:
        print(f'No 8-char code found. code="{code}"', flush=True)

    page.screenshot(path='/tmp/wa7_final.png')
    ctx.close()
print('Done.', flush=True)
