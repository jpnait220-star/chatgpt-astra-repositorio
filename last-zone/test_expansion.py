from playwright.sync_api import sync_playwright
from pathlib import Path
import http.server,functools,threading,json
root=Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling'])
 page=browser.new_page(viewport={'width':1280,'height':800});errors=[];closed=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('close',lambda:closed.append(True));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('dialog',lambda d:d.dismiss())
 page.goto(f'http://127.0.0.1:{server.server_port}/LAST%20ZONE%20Duo.html?quality=low');page.wait_for_function('typeof CAMPAIGN!=="undefined"');page.evaluate("rd.setPixelRatio(.4);HTMLCanvasElement.prototype.requestPointerLock=function(){};Object.defineProperty(document,'pointerLockElement',{get:()=>state==='play'&&!paused&&!INPUT.menuOpen?rd.domElement:null,configurable:true})")
 page.click('#settings-open');page.click('[data-action="forward"]');page.keyboard.press('KeyI');assert page.evaluate("INPUT.bindings.forward==='KeyI'")
 page.click('[data-action="reload"]');page.keyboard.press('KeyI');assert 'já está' in page.locator('#settings-note').inner_text()
 page.keyboard.press('Escape');page.click('#settings-close');page.reload();page.wait_for_function('typeof INPUT!=="undefined"');assert page.evaluate("INPUT.bindings.forward==='KeyI'")
 page.evaluate("rd.setPixelRatio(.4);HTMLCanvasElement.prototype.requestPointerLock=function(){};Object.defineProperty(document,'pointerLockElement',{get:()=>state==='play'&&!paused&&!INPUT.menuOpen?rd.domElement:null,configurable:true});newGame();paused=true")
 print(page.evaluate("""()=>{if(pl.length!==32||pl.some(p=>p.hp!==200||p.maxHp!==200))throw Error('HP/player count');if(GAME_WORLD.radius!==400||OUTER_DISTRICTS.length!==8)throw Error('world extent');const sectors=new Set(pl.map(p=>p.spawnPlan.region));if(sectors.size<10)throw Error('spawns clustered');if(new Set(pl.map(p=>[Math.round(p.x/50),Math.round(p.z/50)].join(','))).size<20)throw Error('spawns concentrated');return {players:pl.length,mapDiameter:800,sectors:sectors.size,trees:ISLAND.treeCount,houses:WORLD_HOUSES.length}}"""))
 page.evaluate("pl.forEach(p=>{p.alive=p.id===0?1:0;p.g.visible=!!p.alive});const p=pl[0];p.x=50;p.z=50;p.y=0;p.st='ground';p.on=1;p.vy=0;p.yaw=0;obs.splice(0);paused=false;$('pause').classList.add('h')")
 z=page.evaluate('pl[0].z');page.keyboard.down('KeyI');page.wait_for_function('(z)=>pl[0].z>z+.4',arg=z);page.keyboard.up('KeyI')
 page.keyboard.press('ControlLeft');page.wait_for_function('pl[0].crouched');page.keyboard.press('ControlLeft');page.wait_for_function('!pl[0].crouched')
 page.keyboard.down('KeyC');page.wait_for_function('pl[0].crouched');page.keyboard.up('KeyC');page.wait_for_function('!pl[0].crouched')
 print('PASS: remapping, persistence, duplicate prevention, Ctrl toggle and C hold')
 # Restore defaults using the actual menu.
 page.keyboard.press('KeyO');page.click('#bindings-reset');page.click('#settings-close');page.evaluate("paused=false;$('pause').classList.add('h')")
 print(page.evaluate("""()=>{const p=pl[0];p.hp=100;p.armor=p.helmet=0;p.w=['pistol'];p.cur=0;p.mag.pistol=5;p.ammo.pistol=0;p.rl=p.cd=0;p.g.position.set(p.x,0,p.z);p.g.rotation.y=0;cam.position.set(p.x,1.7,p.z-3.5);cam.lookAt(p.x,1.2,p.z+15);cam.updateMatrixWorld(true);const oldMag=p.mag.pistol;fire(p,new T.Vector3(p.x,1.5,p.z),new T.Vector3(0,0,1));if(p.mag.pistol!==oldMag-1||RETICLE.kick!==1||WP.pistol.sp!==0)throw Error('reticle/straight ray');return 'PASS: dynamic reticle without random bullet spread'}"""))
 # A torso just off the reticle is followed slowly; no input means no auto aiming.
 print(page.evaluate("""()=>{const p=pl[0],target=pl[1];target.alive=1;target.st='ground';target.x=p.x+.1;target.z=p.z+15;target.y=0;target.g.position.set(target.x,0,target.z);p.pit=0;p.yaw=0;cam.position.set(p.x,1.2,p.z);const saved=solids.splice(0);fh=0;const before=p.yaw;softAim(p,.016);if(p.yaw!==before)throw Error('idle assistance');fh=1;softAim(p,.016);fh=0;if(!(p.yaw>before&&p.yaw-before<=ASSIST.hipSpeed*.016+.00001))throw Error('assist too strong/missing');const panel=new T.Mesh(new T.BoxGeometry(4,4,.2),mt(0x123456));panel.position.set(p.x,2,p.z+6);sc.add(panel);solids.push(panel);sc.updateMatrixWorld(true);const blocked=p.yaw;fh=1;softAim(p,.016);fh=0;if(p.yaw!==blocked)throw Error('aim through wall');release(panel);solids.splice(0);solids.push(...saved);target.alive=0;return 'PASS: bounded assistance only while firing and only with line of sight'}"""))
 # Real death must keep the page open and show a clear defeat state.
 page.evaluate("const p=pl[0];p.hp=100;p.armor=p.helmet=0;dmg(p,pl[1],'body',500)");page.wait_for_function("state==='end'");assert page.locator('#end').is_visible();assert not closed
 page.evaluate("newGame();paused=true;pl.forEach(p=>p.g.visible=p.id===0);const p=pl[0];p.armor=p.helmet=0;dmg(p,pl[1],'body',500);newGame();paused=true")
 page.wait_for_timeout(1200);assert page.evaluate("state==='play'&&pl[0].alive&&pl[0].hp===200"), 'old death callback ended new round'
 assert page.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});dispatchEvent(e);return e.defaultPrevented})()")
 print('PASS: death screen, browser remains open, protected exit and no stale defeat after restart')
 # Force effect upload then expiry; GPU geometry count must not grow per batch.
 page.evaluate("pl.forEach(p=>{p.alive=p.id===0?1:0;p.g.visible=!!p.alive});const p=pl[0];p.x=50;p.z=50;p.y=0;p.st='ground';p.on=1;p.yaw=0;p.vy=0;paused=false;$('pause').classList.add('h')")
 page.wait_for_timeout(300)
 stats=page.evaluate("""async()=>{const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await frame();const base=rd.info.memory.geometries,measure=[];for(let b=0;b<4;b++){for(let i=0;i<20;i++)shotLine(new T.Vector3(pl[0].x,1.3,pl[0].z+1),new T.Vector3(pl[0].x,1.3,pl[0].z+8));rd.render(sc,cam);for(const f of fx)f.t=-1;await frame();measure.push(rd.info.memory.geometries)}if(measure.at(-1)>base+12)throw Error('FX GPU leak '+JSON.stringify({base,measure}));return {base,measure,disposed:STABILITY.disposed}}""")
 print('PASS: bounded GPU effects',stats)
 # Bot looting and migration preserve encounters instead of invulnerability or scripted alive counts.
 print(page.evaluate("""()=>{paused=true;const b=pl[2];pl.forEach(p=>p.alive=0);b.alive=1;b.x=80;b.z=45;b.y=0;b.vy=0;b.yaw=0;b.st='ground';b.on=1;b.hp=100;b.w=['pistol'];b.cur=0;b.mag.pistol=5;b.ammo.pistol=15;b.motion={x:0,z:0};b.brain=null;b.spawnPlan={homeX:80,homeZ:45,dropX:80,dropZ:45};const savedObs=obs.splice(0),savedSolids=solids.splice(0),savedItems=items;items=[];const m=itemModel('ump');m.position.set(80,.6,49);sc.add(m);items.push({t:'ump',x:80,y:0,z:49,m,visual:true});zs='wait';zf={x:0,z:0,r:395};for(let n=0;n<160&&!b.w.includes('ump');n++){const input=ai(b,.05);mv(b,.05,input)}if(!b.w.includes('ump'))throw Error('bot cannot loot');zs='shr';z1={x:0,z:0,r:50};b.x=250;b.z=100;b.brain=null;ai(b,.05);if(b.brain.mode!=='migrate')throw Error('safe migration');zs='wait';obs.push(...savedObs);solids.push(...savedSolids);items.forEach(it=>release(it.m));items=savedItems;return 'PASS: bot picks up real items and migrates when safe shrinks'}"""))
 # Audio is activated by a gesture and each action has a bounded sound path.
 page.click('#music-toggle');page.evaluate("MUSIC.enabled=true;startMusic();for(const id of Object.keys(GUN_SOUND))snd(id,pl[0].x,pl[0].z);for(const id of ['step','run','jump','land','loot','heal','ice','clk'])snd(id,pl[0].x,pl[0].z)")
 assert page.evaluate("Object.keys(GUN_SOUND).every(id=>SFX.played[id]>0)&&SFX.voices.size<=32")
 page.wait_for_timeout(1200);assert page.evaluate('SFX.voices.size<=2'), 'voices did not release'
 print('PASS: distinct gun/action profiles, bounded and released audio voices')
 page.evaluate('toMenu()');page.wait_for_timeout(200);page.click('#settings-open');page.screenshot(path=str(root/'controls-menu.png'));page.click('#settings-close')
 page.evaluate("cam.position.set(120,140,160);cam.lookAt(0,0,0);rd.render(sc,cam)");page.screenshot(path=str(root/'expanded-map.png'))
 assert not errors,errors;assert not closed
 print('PASS: no runtime/shader errors')
 browser.close()
server.shutdown()
