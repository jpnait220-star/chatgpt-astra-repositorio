"""Verify health capacity, real healing and HUD values in the live game loop."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import http.server, functools, threading

ROOT = Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
            args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':960, 'height':640})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: d.dismiss())
        page.goto(f'http://127.0.0.1:{server.server_port}/LAST%20ZONE%20Duo.html?quality=low')
        page.wait_for_function('typeof GAME_WORLD!=="undefined"&&typeof healthLabel!=="undefined"')
        page.evaluate("HTMLCanvasElement.prototype.requestPointerLock=function(){};rd.setPixelRatio(.3);newGame();paused=true")
        assert page.evaluate('GAME_WORLD.maxHealth===200&&pl.length===32&&pl.every(p=>p.hp===200&&p.maxHp===200)')
        assert page.locator('#health-number').inner_text() == '200 / 200 HP'
        assert page.evaluate("(()=>{const p=pl[0];p.k25=p.k100=1;heal(p,'k25');heal(p,'k100');return p.k25===1&&p.k100===1&&p.hl===0})()")
        # Two living actors prevent automatic victory while the actual update loop heals.
        page.evaluate("pl.forEach(p=>p.alive=p.id<2?1:0);const p=pl[0],b=pl[1];p.x=50;p.z=50;p.y=terrainHeight(50,50);p.st='ground';p.on=1;p.vy=0;p.hp=185;p.armor=p.helmet=0;b.x=250;b.z=200;b.y=terrainHeight(250,200);b.st='ground';b.on=1;b.hp=200;b.brain=null;zf={x:0,z:0,r:395};z1={...zf};zs='wait';zt=0;zph=0;heal(p,'k25');paused=false")
        page.wait_for_function('pl[0].hl<=0&&pl[0].hp>=199.999', timeout=30000)
        assert page.evaluate('Math.abs(pl[0].hp-200)<.001&&pl[0].k25===0')
        assert page.locator('#health-number').inner_text() == '200 / 200 HP'
        page.evaluate("paused=true;const p=pl[0];p.hp=150;p.hl=0;heal(p,'k100');paused=false")
        page.wait_for_function('pl[0].hl<=0&&pl[0].hp>=199.999', timeout=30000)
        assert page.evaluate('Math.abs(pl[0].hp-200)<.001&&pl[0].k100===0')
        page.evaluate("paused=true;pl[0].hp=100;rd.render(sc,cam)")
        assert page.locator('#health-number').inner_text() == '100 / 200 HP'
        assert page.evaluate("$('hf').style.width==='50%'")
        assert not errors, errors
        print('PASS: 32 actors start at 200 HP, full-health kits are retained, both kits cap at 200 in the real loop, half-health HUD is 50%, no runtime errors')
        browser.close()
finally:
    server.shutdown()
