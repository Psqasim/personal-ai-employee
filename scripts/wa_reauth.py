#!/usr/bin/env python3
"""WA Pair v9 - use text_content() to avoid layout-reflow timeouts on ARM"""
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
        'input[type="text"]',
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
    if (!b) return 'nf';
    // Try React fiber onClick first
    const allKeys = Object.getOwnPropertyNames(b);
    const fk = allKeys.find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
    if (fk) {
        let fiber = b[fk];
        for (let i = 0; i < 30 && fiber; i++) {
            const props = fiber.memoizedProps || fiber.pendingProps || {};
            if (typeof props.onClick === 'function') {
                try {
                    props.onClick({type:'click',preventDefault:()=>{},stopPropagation:()=>{},nativeEvent:{type:'click'},currentTarget:b,target:b});
                    return 'ok_fiber';
                } catch(e) {}
            }
            fiber = fiber.return;
        }
    }
    b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    return 'ok_native';
}'''


def safe_body_text(page, timeout=30000):
    """Get body text without triggering layout reflow (avoids ARM timeout)."""
    try:
        return page.locator('body').text_content(timeout=timeout) or ''
    except Exception:
        # Fallback: evaluate JS directly
        try:
            return page.evaluate('() => document.body?.innerText || document.body?.textContent || ""') or ''
        except Exception:
            return ''


def get_code(page):
    """Extract 8-char pairing code from page body"""
    txt = safe_body_text(page)
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


def poll_for_code(page, timeout=45):
    """Poll for pairing code up to `timeout` seconds (2s intervals). Returns (code, chars, txt)."""
    for i in range(timeout // 2):
        code, chars, txt = get_code(page)
        if len(code) == 8:
            print(f'Code found after {(i+1)*2}s', flush=True)
            return code, chars, txt
        # Also check if page now shows "Enter code on phone" text as a signal
        body_preview = safe_body_text(page)[:300]
        if 'Enter code on phone' in body_preview or 'Linking WhatsApp' in body_preview:
            print(f'Code page detected at {(i+1)*2}s, raw preview: {body_preview[:150]}', flush=True)
        else:
            print(f'Waiting for code... {(i+1)*2}s (page: {body_preview[:80].strip()})', flush=True)
        time.sleep(2)
    return '', [], ''


JS_CLICK_PHONE = """() => {
    // Strategy 1: Find role=button elements first (more specific), then all divs
    const keywords = ['Log in with phone number', 'Link with phone number'];

    function tryClick(el, label) {
        // Try React fiber — check own property names (not just enumerable)
        const allKeys = Object.getOwnPropertyNames(el);
        const fiberKey = allKeys.find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
        if (fiberKey) {
            let fiber = el[fiberKey];
            for (let i = 0; i < 50 && fiber; i++) {
                const props = fiber.memoizedProps || fiber.pendingProps || {};
                // Try onClick, onMouseDown (WhatsApp uses both)
                for (const handler of ['onClick', 'onMouseDown', 'onPointerDown']) {
                    if (typeof props[handler] === 'function') {
                        try {
                            props[handler]({
                                type: handler === 'onClick' ? 'click' : handler.slice(2).toLowerCase(),
                                preventDefault: () => {},
                                stopPropagation: () => {},
                                nativeEvent: { type: 'click' },
                                currentTarget: el,
                                target: el,
                            });
                            return 'fiber_' + handler + ':' + label;
                        } catch(e) { /* try next handler */ }
                    }
                }
                fiber = fiber.return;
            }
        }
        // Fallback: dispatch full native event sequence (React root listens at document)
        const opts = { bubbles: true, cancelable: true, view: window };
        el.dispatchEvent(new PointerEvent('pointerover',  opts));
        el.dispatchEvent(new PointerEvent('pointerenter', { bubbles: false }));
        el.dispatchEvent(new MouseEvent('mouseover',  opts));
        el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: false }));
        el.dispatchEvent(new PointerEvent('pointerdown', opts));
        el.dispatchEvent(new MouseEvent('mousedown',  opts));
        el.dispatchEvent(new PointerEvent('pointerup',   opts));
        el.dispatchEvent(new MouseEvent('mouseup',    opts));
        el.dispatchEvent(new MouseEvent('click',      opts));
        return 'native:' + label;
    }

    for (const kw of keywords) {
        // Pass 1: role=button and button elements (most specific)
        const buttons = [...document.querySelectorAll('div[role=button], button, a[role=button]')];
        let el = buttons.find(e => e.textContent.trim() === kw || e.textContent.trim().startsWith(kw));
        if (el) return tryClick(el, kw);

        // Pass 2: any element with exact or prefix text match
        const all = [...document.querySelectorAll('div, span, a, button')];
        el = all.find(e => e.textContent.trim() === kw);
        if (!el) el = all.find(e => e.textContent.trim().startsWith(kw) && e.textContent.trim().length < kw.length + 5);
        if (el) return tryClick(el, kw);
    }
    return 'not_found';
}"""


def click_phone_number_link(page):
    """Click 'Log in with phone number': JS fiber + trusted Playwright click."""
    # ── Step 1: React fiber JS (fires React state update) ─────────────────────
    result = page.evaluate(JS_CLICK_PHONE)
    print(f'JS click result: {result}', flush=True)

    # ── Step 2: ALWAYS also fire a real Playwright loc.click() ────────────────
    # loc.click() generates isTrusted=true events (pointerdown+mousedown+click)
    # WhatsApp checks event.isTrusted — programmatic JS events are blocked.
    for selector in [
        ':text("Log in with phone number")',
        ':text("Link with phone number instead")',
        'div[role="button"]:has-text("phone number")',
        'a:has-text("phone number")',
    ]:
        try:
            loc = page.locator(selector).first
            if loc.count() == 0:
                continue
            loc.scroll_into_view_if_needed(timeout=5000)
            time.sleep(0.5)
            loc.click(timeout=8000)   # trusted events: pointerdown→mousedown→click
            print(f'loc.click() via: {selector}', flush=True)
            return True
        except Exception as e:
            print(f'  {selector}: {e}', flush=True)
            continue

    # ── Step 3: page.mouse.click fallback ─────────────────────────────────────
    for selector in [':text("Log in with phone number")', 'div[role="button"]:has-text("phone number")']:
        try:
            loc = page.locator(selector).first
            if loc.count() == 0:
                continue
            box = loc.bounding_box()
            if box:
                cx = box['x'] + box['width'] / 2
                cy = box['y'] + box['height'] / 2
                page.mouse.move(cx, cy)
                time.sleep(0.3)
                page.mouse.click(cx, cy)
                print(f'Mouse click at ({cx:.0f},{cy:.0f})', flush=True)
                return True
        except Exception as e:
            print(f'  mouse {selector}: {e}', flush=True)

    return result != 'not_found'


def find_phone_input(page):
    """Count phone inputs across multiple selectors."""
    selectors = [
        '[aria-label="Type your phone number to log in to WhatsApp"]',
        'input[type="tel"]',
        'input[type="text"]',
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


print('=== WA Pair v9 ===', flush=True)

# Clear stale session so WhatsApp starts clean (avoids cached bad states)
import shutil
if os.path.exists(SESSION):
    shutil.rmtree(SESSION)
    print(f'Cleared session dir: {SESSION}', flush=True)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
window.chrome = {runtime: {}};
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION, headless=True,
        args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
              '--enable-unsafe-swiftshader','--disable-setuid-sandbox',
              '--no-first-run','--mute-audio',
              '--disable-blink-features=AutomationControlled'],
        user_agent=UA, viewport={'width':1920,'height':1080},
    )
    ctx.add_init_script(STEALTH_JS)   # mask navigator.webdriver for all pages
    page = ctx.new_page()
    page.set_default_timeout(90000)   # 90s for all actions (ARM VM is slow)
    print('Loading...', flush=True)
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=90000)
    time.sleep(30)

    body = safe_body_text(page, timeout=45000)
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
        # Poll up to 40s for phone input to appear (ARM VM is slow to render)
        n = 0
        for t in range(14):
            time.sleep(3)
            n = find_phone_input(page)
            if n > 0:
                print(f'Phone input appeared after {(t+1)*3}s', flush=True)
                break
            chk = safe_body_text(page)
            if 'Enter phone' in chk or ('phone number' in chk.lower() and 'Log in with phone' not in chk):
                print(f'Page changed after {(t+1)*3}s, rechecking input...', flush=True)
                n = find_phone_input(page)
                break
        print(f'Phone input count: {n}', flush=True)

        if n > 0:
            val = page.evaluate(JS_FILL)
            print(f'Fill result: {val}', flush=True)
            time.sleep(1)
            nr = page.evaluate(JS_NEXT)
            print(f'Next result: {nr}', flush=True)
            # Also try trusted Playwright click on Next button as fallback
            for next_sel in [':text("Next")', 'div[role="button"]:has-text("Next")', 'button:has-text("Next")']:
                try:
                    loc = page.locator(next_sel).first
                    if loc.count() > 0:
                        loc.click(timeout=5000)
                        print(f'Trusted Next click via: {next_sel}', flush=True)
                        break
                except Exception as e:
                    print(f'  Next click {next_sel}: {e}', flush=True)
            time.sleep(3)  # brief pause before polling
            code, chars, _ = poll_for_code(page, timeout=45)
        else:
            # Take screenshot to debug what we see after clicking
            body2 = safe_body_text(page)
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
            # Also try trusted Playwright click on Next button as fallback
            for next_sel in [':text("Next")', 'div[role="button"]:has-text("Next")', 'button:has-text("Next")']:
                try:
                    loc = page.locator(next_sel).first
                    if loc.count() > 0:
                        loc.click(timeout=5000)
                        print(f'Trusted Next click via: {next_sel}', flush=True)
                        break
                except Exception as e:
                    print(f'  Next click {next_sel}: {e}', flush=True)
            time.sleep(3)  # brief pause before polling
            code, chars, _ = poll_for_code(page, timeout=45)
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
                pass  # screenshot removed (times out on Oracle ARM)
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

    ctx.close()
print('Done.', flush=True)
