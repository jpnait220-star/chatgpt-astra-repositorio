"""End-to-end checks using the real unpacked extension and disposable browser state."""
import http.server
import os
from pathlib import Path
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = f'<html><head><title>Test {self.path}</title></head><body>DuckCleans test page</body></html>'.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'
try:
    with tempfile.TemporaryDirectory(prefix='duckcleans-test-') as profile, sync_playwright() as p:
        context = p.chromium.launch_persistent_context(profile, executable_path=os.environ.get('DUCKCLEANS_BROWSER', '/usr/lib/chromium/chromium'), headless=True, ignore_default_args=['--disable-extensions'],
            args=['--no-sandbox', f'--disable-extensions-except={ROOT}', f'--load-extension={ROOT}'],
            viewport={'width': 1440, 'height': 1100})
        worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker')
        extension_id = worker.url.split('/')[2]
        gui = context.new_page()
        gui.goto(f'chrome-extension://{extension_id}/dashboard.html')
        errors=[]
        gui.on('pageerror', lambda error: errors.append(str(error)))
        gui.wait_for_function("document.querySelector('#headerStatus').textContent === 'Limpeza ativada'")
        assert gui.title() == 'DuckCleans GUI'
        test_pages=[]
        for path in ('/favorite', '/expired', '/recent', '/pinned'):
            page = context.new_page()
            page.goto(base + path)
            test_pages.append(page)
        gui.bring_to_front()
        def rpc(message):
            result = gui.evaluate('(message) => chrome.runtime.sendMessage(message)', message)
            assert result['ok'], result
            return result['data']
        state = rpc({'type':'getState'})
        ids={tab['url'].split('/')[-1]:tab['id'] for tab in state['tabs'] if tab['url'].startswith(base)}
        gui.reload()
        gui.get_by_role('button', name='Favoritar: Test /favorite', exact=True).click()
        gui.get_by_role('button', name='Remover dos favoritos: Test /favorite', exact=True).wait_for()
        assert next(t for t in rpc({'type':'getState'})['tabs'] if t['id']==ids['favorite'])['favorite']
        gui.locator('[data-view="favorites"]').click()
        assert gui.locator('.tab-row').count()==1
        test_pages[0].goto(base+'/navigated')
        assert next(t for t in rpc({'type':'getState'})['tabs'] if t['id']==ids['favorite'])['favorite']
        gui.locator('[data-view="settings"]').click()
        gui.locator('[data-minutes="30"]').click()
        gui.wait_for_function("document.querySelector('#timeoutDisplay').textContent === '30'")
        assert rpc({'type':'getState'})['settings']['minutes']==30
        # Validate the background independently from input constraints.
        assert rpc({'type':'settings','settings':{'minutes':1}})['settings']['minutes']==15
        gui.evaluate('(id) => chrome.tabs.update(id, {pinned:true})',ids['pinned'])
        rpc({'type':'getState'})
        def expire():
            gui.evaluate('''async (ids) => {
              const {records}=await chrome.storage.session.get('records');
              for (const id of ids) records[id].lastActive=Date.now()-16*60000;
              await chrome.storage.session.set({records});
            }''',[ids['favorite'],ids['expired'],ids['pinned']])
        expire()
        rpc({'type':'settings','settings':{'paused':True}})
        def trigger_sweep():
            gui.evaluate("() => chrome.alarms.create('duckcleans-sweep',{when:Date.now()+100,periodInMinutes:1})")
        trigger_sweep()
        gui.wait_for_timeout(1200)
        assert not test_pages[1].is_closed(), 'Paused cleaner closed a tab'
        rpc({'type':'settings','settings':{'paused':False}})
        expire()
        trigger_sweep()
        test_pages[1].wait_for_event('close', timeout=15000)
        state=rpc({'type':'getState'})
        assert state['cleaned']==1
        assert len(state['history'])==1 and state['history'][0]['title']=='Test /expired'
        for index in (0,2,3): assert not test_pages[index].is_closed()
        # A worker restart must retain session favorites and local settings.
        cdp=context.new_cdp_session(gui)
        cdp.send('ServiceWorker.enable')
        cdp.send('ServiceWorker.stopAllWorkers')
        state=rpc({'type':'getState'})
        assert next(t for t in state['tabs'] if t['id']==ids['favorite'])['favorite']
        assert state['cleaned']==1
        gui.locator('[data-view="overview"]').click()
        gui.reload()
        gui.get_by_role('button',name='Remover dos favoritos: Test /navigated',exact=True).wait_for()
        gui.locator('#search').fill('no-such-tab')
        assert gui.locator('.tab-row').count()==0
        assert gui.get_by_text('Nenhuma aba encontrada.').is_visible()
        gui.locator('#search').fill('')
        # Text from web pages must never become executable markup.
        test_pages[2].evaluate("document.title='<img src=x onerror=alert(1)>'")
        gui.reload()
        gui.get_by_text('<img src=x onerror=alert(1)>',exact=True).wait_for()
        assert gui.locator('#tabList img').count()==0
        test_pages[2].evaluate("document.title='Um espaço para sua próxima ideia'")
        gui.reload()
        gui.wait_for_function("document.querySelector('#headerStatus').textContent === 'Limpeza ativada'")
        out=ROOT/'artifacts'
        out.mkdir(exist_ok=True)
        gui.screenshot(path=str(out/'duckcleans-overview.png'),full_page=True)
        gui.locator('[data-view="settings"]').click()
        gui.screenshot(path=str(out/'duckcleans-settings.png'),full_page=True)
        gui.set_viewport_size({'width':640,'height':1000})
        gui.locator('[data-view="overview"]').click()
        assert gui.evaluate('document.documentElement.scrollWidth <= innerWidth')
        gui.screenshot(path=str(out/'duckcleans-compact.png'),full_page=True)
        assert not errors, errors
        context.close()
        print('PASS: real extension startup, GUI, favorites, navigation, settings, minimum timeout, pause/resume, automatic closing, pinned/active/recent protection, history, worker restart, search, safe title rendering, responsive layout.')
finally:
    server.shutdown()
