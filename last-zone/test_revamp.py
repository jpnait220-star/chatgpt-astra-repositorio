from pathlib import Path
from playwright.sync_api import sync_playwright
import http.server,functools,threading,json
root=Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1280,'height':800});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('dialog',lambda d:d.dismiss())
 page.goto(f'http://127.0.0.1:{server.server_port}/LAST%20ZONE%20Duo.html?quality=low');page.wait_for_function('typeof sampleProfiles!=="undefined"');page.evaluate("rd.setPixelRatio(.45);HTMLCanvasElement.prototype.requestPointerLock=function(){};newGame();paused=true")
 print(page.evaluate("""()=>{if(items.filter(i=>i.t==='k25'||i.t==='k100').length<48)throw Error('medicine count');if(items.filter(i=>i.medMarker).length<48)throw Error('medicine markers');if(ZP[0].w!==35||zr.geometry.parameters.height!==180||zr.material.fog!==false)throw Error('storm setup');paused=false;REVAMP.zoneRound=ROUND_ID;REVAMP.preview=false;REVAMP.zoneAt=performance.now()-1000;zt=0;zone(.001);if(zt<.95||zt>1.1)throw Error('storm slowed by physics '+zt);zt=34.9;REVAMP.zoneAt=performance.now()-200;zone(.001);if(zs!=='shr'||zf.r>=395)throw Error('storm transition');paused=true;return {meds:items.filter(i=>i.t==='k25'||i.t==='k100').length,firstWait:ZP[0].w,zonePhase:zs,radius:zf.r,stormHeight:zr.geometry.parameters.height}}"""))
 # Flat, isolated arena for deterministic movement; the actual world is restored afterwards.
 page.evaluate("window.originalObs=obs.splice(0);window.originalSolids=solids.splice(0);window.realTerrain=terrainHeight;terrainHeight=()=>0;pl.forEach(p=>p.alive=p.id===0?1:0)")
 print(page.evaluate("""()=>{const p=pl[0];const reset=()=>{p.x=50;p.z=50;p.y=0;p.vy=0;p.st='ground';p.on=1;p.sl=0;p.vault=null;p.motion={x:0,z:0};p.yaw=0};reset();obs.push({x0:-100,x1:100,z0:52,z1:52.2,y0:0,y1:4});for(let i=0;i<90;i++)mv(p,1/60,{f:1,r:1});if(p.z>51.601||p.x>47)throw Error('wall sliding '+p.x+','+p.z);obs.length=0;reset();p.y=.1;p.vy=-1;p.on=0;p.motion.coyote=.08;mv(p,.016,{j:1});if(p.vy<=0)throw Error('coyote jump');reset();p.y=.20;p.vy=-2;p.on=0;p.motion.coyote=0;mv(p,.016,{j:1});for(let i=0;i<7;i++)mv(p,.016,{});if(p.vy<=0)throw Error('jump buffer');reset();p.st='chute';p.y=50;p.on=0;for(let i=0;i<60;i++)mv(p,1/60,{f:1});const held=p.z;for(let i=0;i<90;i++)mv(p,1/60,{});const stopped=p.z;for(let i=0;i<30;i++)mv(p,1/60,{});if(Math.abs(p.z-stopped)>.01||stopped<=held)throw Error('canopy momentum release');return 'PASS: wall sliding, coyote time, buffered landing jump and controlled canopy inertia'}"""))
 # A real doorway approached from the side must be navigated around, not walked through.
 page.evaluate('obs.push(...originalObs);solids.push(...originalSolids);terrainHeight=realTerrain')
 print(page.evaluate("""()=>{pl.forEach(p=>p.alive=0);const b=pl[2],h=WORLD_HOUSES.find(h=>h.x===24&&h.z===22);b.alive=1;b.x=h.x+13;b.z=h.z;b.y=0;b.vy=0;b.on=1;b.st='ground';b.yaw=-Math.PI/2;b.hp=100;b.k25=b.k100=0;b.w=['pistol'];b.cur=0;b.mag.pistol=5;b.ammo.pistol=15;b.brain=null;b.motion={x:0,z:0};b.spawnPlan={homeX:h.x,homeZ:h.z,dropX:b.x,dropZ:b.z};const oldItems=items;items=[];const model=itemModel('ump');model.position.set(h.x,.6,h.z);sc.add(model);items.push({t:'ump',m:model,x:h.x,z:h.z,y:0,visual:true});zf={x:0,z:0,r:395};zs='wait';for(let step=0;step<500&&!b.w.includes('ump');step++){BATTLE.clock+=.04;const input=ai(b,.04);mv(b,.04,input);b.g.position.set(b.x,b.y,b.z)}if(!b.w.includes('ump'))throw Error('door path failed '+JSON.stringify({x:b.x,z:b.z,mode:b.brain?.mode,path:b.brain?.nav?.path}));b.hp=35;b.k25=1;b.hl=0;b.brain.target=null;b.brain.think=1;ai(b,.04);if(b.hl<=0||b.k25!==0)throw Error('bot healing');items.forEach(i=>release(i.m));items=oldItems;return {doorLoot:'PASS',healing:'PASS',pathPlans:NAV.plans,recoveries:NAV.recoveries}}"""))
 # Let the actual game loop finish a bot's kit, rather than only checking the AI request.
 page.evaluate("pl[0].alive=1;pl[0].st='ground';pl[0].x=0;pl[0].z=0;pl[0].y=0;const b=pl[2];b.x=200;b.z=100;b.y=terrainHeight(200,100);b.hp=35;b.hl=0;b.k25=1;b.k100=0;b.brain=null;b.spawnPlan={homeX:200,homeZ:100};zf={x:0,z:0,r:395};z1={...zf};zs='wait';zt=0;zph=0;REVAMP.zoneRound=-1;paused=false")
 page.wait_for_function('pl[2].hp>=59&&pl[2].hl<=0',timeout=30000)
 assert page.evaluate('Math.abs(pl[2].hp-60)<.001&&pl[2].k25===0')
 print(page.evaluate("paused=true;({botHealth:pl[2].hp,smallKitsLeft:pl[2].k25})"))
 page.click('#music-toggle');page.evaluate('MUSIC.enabled=true;startMusic()');page.wait_for_function('SAMPLES.ready');page.wait_for_timeout(500)
 print(page.evaluate("""()=>{if(Object.keys(SAMPLES.buffers).length!==7)throw Error('audio assets');if(MUSIC.volume<.79)throw Error('music migration');for(const id in sampleProfiles)snd(id,pl[0].x,pl[0].z);snd('step',pl[0].x,pl[0].z);snd('land',pl[0].x,pl[0].z);if(SAMPLES.played<7||SFX.voices.size>32)throw Error('sample playback');for(const buffer of Object.values(SAMPLES.buffers)){const data=buffer.getChannelData(0);let energy=0;for(let i=0;i<data.length;i++){if(!Number.isFinite(data[i])||Math.abs(data[i])>1.001)throw Error('invalid audio');energy+=data[i]*data[i]}if(energy<.001)throw Error('silent sample')}return {sampleBuffers:Object.keys(SAMPLES.buffers).length,played:SAMPLES.played,musicVolume:MUSIC.volume,musicGain:musicBus.gain.value}}"""))
 page.wait_for_timeout(1400);assert page.evaluate('SFX.voices.size===0')
 # Render the storm close enough to verify its actual output, not just a material property.
 page.evaluate("pl[0].alive=1;pl[0].x=0;pl[0].z=-60;pl[0].y=0;pl[0].on=1;pl[0].st='ground';pl[0].g.position.set(0,0,-60);zf={x:0,z:0,r:45};z1={x:5,z:5,r:30};zph=4;zs='shr';cam.position.set(0,3,-68);cam.lookAt(0,7,-30);zr.position.set(0,90,0);zr.scale.set(45,1,45);setQuality(1);rd.setPixelRatio(1);dm(mc,150);battleHud();rd.render(sc,cam)")
 page.screenshot(path=str(root/'revamp-storm.png'))
 page.evaluate("cam.position.set(65,3,52);cam.lookAt(24,2,22);rd.render(sc,cam)");page.screenshot(path=str(root/'revamp-town.png'))
 assert not errors,errors;print('PASS: no JavaScript or shader errors')
 browser.close()
server.shutdown()
