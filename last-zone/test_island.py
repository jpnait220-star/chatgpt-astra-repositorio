"""Deterministic movement, map/tree consistency and user-gesture audio tests."""
from playwright.sync_api import sync_playwright
import http.server,threading,functools,json
from pathlib import Path
root=Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':900});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
 page.goto(f'http://127.0.0.1:{server.server_port}/LAST%20ZONE%20Island%202.html');page.wait_for_function('typeof ISLAND!=="undefined"');page.wait_for_timeout(300)
 assert page.evaluate('!MUSIC.started'), 'audio must wait for user interaction'
 page.click('#music-toggle');page.click('#music-toggle');page.wait_for_function('MUSIC.scheduled>0');page.wait_for_timeout(300)
 print(page.evaluate("""()=>{if(AC.state!=='running'||!MUSIC.started||MUSIC.scheduled===0)throw Error('audio startup');const timer=MUSIC.timer;startMusic();startMusic();if(timer!==MUSIC.timer)throw Error('duplicate timer');if(MUSIC.active>24)throw Error('unbounded voices');return {audio:AC.state,notesScheduled:MUSIC.scheduled,voices:MUSIC.active}}"""))
 page.locator('#music-volume').fill('30');assert page.evaluate('Math.abs(MUSIC.volume-.3)<.001')
 page.click('#music-toggle');page.wait_for_timeout(500);assert page.evaluate('musicBus.gain.value<.002'), 'mute must silence scheduled voices'
 page.evaluate("HTMLCanvasElement.prototype.requestPointerLock=function(){};newGame();paused=true;pl.forEach(p=>{p.st='ground';p.y=0;p.ch.visible=false});window.savedTerrain=terrainHeight;terrainHeight=()=>0;window.testObs=obs.splice(0);")
 print(page.evaluate("""()=>{const assert=(ok,msg)=>{if(!ok)throw Error(msg)};assert(ISLAND.treeCount===240,'tree count');assert(artGroups.crowns.length===ISLAND.treeCount*5,'crowns');assert(!oldTreeCrowns.visible,'old crowns hidden');const trunk=testObs.filter(o=>o.y1===2.8);assert(trunk.length===ISLAND.treeCount,'trunk collider heights');
 const p=pl[0];FRONTIER.autoLoot=false;const reset=()=>{p.x=60;p.z=45;p.y=0;p.vy=0;p.on=1;p.st='ground';p.vault=null;p.sl=0;p.stamina=100;p.motion={x:0,z:0,exhausted:false};p.yaw=0};
 reset();for(let n=0;n<120;n++)mv(p,1/60,{f:1});const forward=Math.hypot(p.x-60,p.z-45);assert(forward>9&&forward<10.5,'walking distance '+forward);for(let n=0;n<30;n++)mv(p,1/60,{});assert(Math.hypot(p.motion.x,p.motion.z)<.001,'braking');
 reset();for(let n=0;n<120;n++)mv(p,1/60,{f:1,r:1});const diagonal=Math.hypot(p.x-60,p.z-45);assert(Math.abs(diagonal-forward)<.03,'diagonal speed');
 reset();for(let n=0;n<60;n++)mv(p,1/30,{f:1});const coarse=Math.hypot(p.x-60,p.z-45);assert(Math.abs(coarse-forward)<.1,'frame dependence');
 reset();obs.push({x0:58,x1:62,z0:47,z1:47.05,y0:0,y1:4});for(let n=0;n<60;n++)mv(p,1/30,{f:1,run:1});assert(p.z<=46.601,'thin wall tunneling '+p.z);obs.length=0;
 reset();p.st='chute';p.x=24;p.z=0;p.y=7.25;mv(p,.05,{});assert(p.st==='ground'&&Math.abs(p.y-7.2)<.01,'roof landing '+p.y);
 reset();obs.push({x0:59,x1:61,z0:44,z1:46,y0:1.3,y1:2.3});mv(p,.016,{});pose(p,.016);if(!p.crouched||p.rig.crouch<=0)throw Error('forced crouch under ceiling');obs.length=0;reset();p.armor=0;setQuality(0);assert(!RN.visible&&!canopy.castShadow,'light setting');setQuality(2);assert(!RN.visible&&canopy.castShadow,'high setting');terrainHeight=window.savedTerrain;obs.push(...testObs);return {trees:ISLAND.treeCount,forward,diagonal,coarse,checks:'audio, tree bounds, acceleration, braking, diagonal normalization, thin-wall collision, roof landing, quality'} }"""))
 # Draw static real-world views without advancing AI; input/physics tested separately above.
 page.evaluate("pl[0].x=4;pl[0].z=40;pl[0].y=0;pl[0].st='ground';pl[0].on=1;pl[0].yaw=Math.PI;pl[0].pit=-.04;pl[0].g.position.set(4,0,40);sun.position.set(-56,90,0);sun.target.position.set(4,0,40);sun.target.updateMatrixWorld();dm(mc,150);$('top').textContent='ISLAND 2 · TESTE DE CENÁRIO';cam.position.set(5,2.1,44);cam.lookAt(0,2,-6);pl[0].g.rotation.y=Math.PI;rd.render(sc,cam)")
 page.screenshot(path=str(root/'island-town.png'))
 page.evaluate("cam.position.set(-44,3,34);cam.lookAt(-62,3,-20);rd.render(sc,cam)");page.screenshot(path=str(root/'island-trees.png'))
 page.evaluate("cam.position.set(12,38,52);cam.lookAt(0,0,0);rd.render(sc,cam)");page.screenshot(path=str(root/'island-aerial.png'))
 page.evaluate('toMenu()');page.wait_for_timeout(250);page.screenshot(path=str(root/'island-lobby.png'))
 print(page.evaluate("()=>{const q=lp;pose(q,.016,true);q.g.updateMatrixWorld(true);for(const arm of q.rig.hands){const wrist=new T.Vector3();arm.hand.getWorldPosition(wrist);const target=q.rig.avatar.localToWorld(arm.lastTarget.clone());if(wrist.distanceTo(target)>.0001)throw Error('IK hand detached');const upper=arm.shoulder.children.find(m=>m.isMesh&&m.geometry.type==='SphereGeometry');if(!upper)throw Error('missing joint volume')}return 'PASS: wrists reach weapon targets and shoulder joints have connected volume'}"));assert not errors,errors
 print('PASS: no JavaScript or shader errors; screenshots captured')
 browser.close()
server.shutdown()
