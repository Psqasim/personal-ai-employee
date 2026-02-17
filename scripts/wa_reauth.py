#!/usr/bin/env python3
"""WA Pair v6 - handles all page states: QR, Enter phone, Enter code (get new code)"""
import time, sys, re
from playwright.sync_api import sync_playwright

SESSION = '/home/ubuntu/.whatsapp_session_dir'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')

JS_FILL = '''() => {
    const inp = document.querySelector('[aria-label="Type your phone number to log in to WhatsApp"]');
    if (!inp) return 'not_found';
    inp.focus();
    const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    s.call(inp, '+923460326429');
    inp.dispatchEvent(new InputEvent('input',{bubbles:true}));
    inp.dispatchEvent(new Event('change',{bubbles:true}));
    return inp.value;
}'''

JS_NEXT = '''() => {
    const b=[...document.querySelectorAll("div[role=button],button")].find(x=>x.textContent.trim()==='Next');
    if(b){b.dispatchEvent(new MouseEvent('click',{bubbles:true}));return 'ok';}return 'nf';
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

print('=== WA Pair v6 ===', flush=True)

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
    page.screenshot(path='/tmp/wa6_0.png')

    body = page.locator('body').inner_text()
    print(f'State: {body[:100]}', flush=True)

    # Already logged in?
    if page.locator('div[aria-label="Chat list"],#pane-side').count() > 0:
        print('ALREADY LOGGED IN!', flush=True)
        import subprocess
        subprocess.run(['pm2','start','/opt/personal-ai-employee/ecosystem.config.js',
                        '--only','whatsapp_watcher'], cwd='/opt/personal-ai-employee')
        ctx.close(); sys.exit(0)

    # State: already on Enter code page (from previous attempt)?
    if 'Enter code on phone' in body or 'Get a new code' in body:
        print('On Enter code page. Checking for existing code...', flush=True)
        code, chars, _ = get_code(page)
        if len(code) == 8:
            print(f'Fresh code still there: {code[:4]}-{code[4:]}', flush=True)
        else:
            # Click Get new code / try again
            print('Clicking Get a new code...', flush=True)
            for txt in ['Get a new code', 'Try again', 'Resend']:
                loc = page.get_by_text(txt, exact=False)
                if loc.count() > 0:
                    loc.first.click(force=True)
                    time.sleep(6)
                    code, chars, _ = get_code(page)
                    print(f'After resend - code: {code}', flush=True)
                    break

    # State: on QR page - navigate to phone number
    elif 'Steps to log in' in body or 'Scan the QR' in body:
        print('On QR page. Navigating to phone number...', flush=True)
        page.mouse.click(1225, 595)
        time.sleep(6)
        page.keyboard.press('Escape')
        time.sleep(1)
        page.screenshot(path='/tmp/wa6_1.png')

        n = page.locator('[aria-label="Type your phone number to log in to WhatsApp"]').count()
        print(f'Phone input: {n}', flush=True)

        if n > 0:
            val = page.evaluate(JS_FILL)
            print(f'Fill: {val}', flush=True)
            time.sleep(1)
            nr = page.evaluate(JS_NEXT)
            print(f'Next: {nr}', flush=True)
            time.sleep(12)
            page.screenshot(path='/tmp/wa6_2.png')
            code, chars, _ = get_code(page)
        else:
            print('Phone input not found!', flush=True)
            code = ''

    # State: already on Enter phone page
    elif 'Enter phone number' in body:
        print('Already on Enter phone page.', flush=True)
        page.keyboard.press('Escape')
        time.sleep(1)
        n = page.locator('[aria-label="Type your phone number to log in to WhatsApp"]').count()
        if n > 0:
            val = page.evaluate(JS_FILL)
            print(f'Fill: {val}', flush=True)
            time.sleep(1)
            nr = page.evaluate(JS_NEXT)
            print(f'Next: {nr}', flush=True)
            time.sleep(12)
            code, chars, _ = get_code(page)
        else:
            code = ''
    else:
        print('Unknown state!', flush=True)
        code = ''

    # Display code and wait for auth
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
                page.screenshot(path='/tmp/wa6_success.png')
                import subprocess
                subprocess.run(['pm2','start',
                                '/opt/personal-ai-employee/ecosystem.config.js',
                                '--only','whatsapp_watcher'],
                               cwd='/opt/personal-ai-employee')
                print('whatsapp_watcher started!', flush=True)
                ctx.close(); sys.exit(0)
        print('Timeout.', flush=True)
    else:
        print(f'No 8-char code. chars={code}', flush=True)

    page.screenshot(path='/tmp/wa6_final.png')
    ctx.close()
print('Done.', flush=True)
