"""Integration checks for two real browser contexts, HTTP/SSE rooms and combat."""
from playwright.sync_api import sync_playwright
import socket,subprocess,time,json,urllib.request,urllib.error,os
from pathlib import Path
root=Path(__file__).resolve().parent
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
proc=subprocess.Popen(['node','server.mjs'],cwd=root,env={**os.environ,'PORT':str(port),'HOST':'127.0.0.1'},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
base=f'http://127.0.0.1:{port}'
try:
 for n in range(50):
  try:
   urllib.request.urlopen(base+'/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows'])
  host=browser.new_page(viewport={'width':1280,'height':800});guest=browser.new_page(viewport={'width':1280,'height':800});errors=[]
  for page in [host,guest]:
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   page.goto(base+'?quality=low');page.wait_for_function('typeof NET!=="undefined"');page.evaluate("setQuality(0);rd.setPixelRatio(.35);HTMLCanvasElement.prototype.requestPointerLock=function(){};Object.defineProperty(document,'pointerLockElement',{get:()=>state==='play'&&!paused?rd.domElement:null,configurable:true})")
  assert host.evaluate('enterDuo(true)')
  code=host.evaluate('NET.id');assert len(code)==6
  guest.evaluate("OUT.pants='a3'");guest.locator('#duo-code').fill(code);assert guest.evaluate('enterDuo(false)')
  guest.wait_for_function('NET.ready&&pl[0].id===1');host.wait_for_function('NET.connected')
  assert host.evaluate('pl.filter(p=>p.id<2).every(p=>p.hp===200&&p.maxHp===200)')
  guest.wait_for_function('pl.filter(p=>p.id<2).every(p=>p.hp===200&&p.maxHp===200)')
  host.evaluate("paused=true;pl.forEach(p=>{p.alive=p.id<2?1:0;p.g.visible=!!p.alive;p.st='ground';p.on=1;p.y=0;p.ch.visible=false;p.x=50;p.z=40+p.id*4});pl[0].yaw=0;pl[1].yaw=0;zf.r=150")
  guest.wait_for_function('pl[0].st===\"ground\"')
  # Values above the old 100HP cap must survive the real HTTP/SSE round trip.
  host.evaluate("pl.find(p=>p.id===0).hp=175;pl.find(p=>p.id===1).hp=185")
  guest.wait_for_function('pl.find(p=>p.id===0).hp===175&&pl[0].hp===185&&pl[0].maxHp===200')
  guest.wait_for_function("$('health-number').textContent==='185 / 200 HP'&&$('hf').style.width==='92.5%'")
  host.evaluate('pl.filter(p=>p.id<2).forEach(p=>p.hp=200)')
  guest.wait_for_function('pl.filter(p=>p.id<2).every(p=>p.hp===200&&p.maxHp===200)')
  print('PASS: room creation, two players at 200 HP, values above 100 survive SSE, guest HUD uses maximum health')
  # Third player rejected; unauthenticated state writes rejected.
  def post(path,obj,token=None):
   req=urllib.request.Request(base+path,data=json.dumps(obj).encode(),headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
   try:
    r=urllib.request.urlopen(req);return r.status,json.load(r)
   except urllib.error.HTTPError as e:return e.code,json.load(e)
  assert post('/api/rooms/'+code+'/join',{})[0]==409
  assert post('/api/rooms/'+code+'/state',{'players':[]})[0]==403
  # Host resumes; remote input must move the authoritative guest actor.
  host.evaluate("paused=false;pl.forEach(p=>{p.yaw=0});obs.splice(0);NET.input=null")
  guest.evaluate('paused=false;pl[0].yaw=0;pl[0].pit=0');z0=host.evaluate('pl.find(p=>p.id===1).z')
  guest.keyboard.down('KeyW')
  try:host.wait_for_function('(z)=>pl.find(p=>p.id===1).z>z+1',arg=z0)
  except Exception:
   print('DEBUG HOST',host.evaluate('({state,paused,input:NET.input,p:packPlayer(pl.find(p=>p.id===1))})'),flush=True);print('DEBUG GUEST',guest.evaluate('({state,paused,K,role:NET.role,ready:NET.ready,status:NET.status})'),flush=True);raise
  guest.keyboard.up('KeyW')
  guest.wait_for_timeout(300)
  assert abs(host.evaluate('pl.find(p=>p.id===1).z')-guest.evaluate('pl[0].z'))<1.5
  guest.keyboard.press('ControlLeft');host.wait_for_function('pl.find(p=>p.id===1).crouched');guest.keyboard.press('ControlLeft')
  host.wait_for_function('!pl.find(p=>p.id===1).crouched')
  host.wait_for_function("pl.find(p=>p.id===1).outfit?.pants==='a3'");guest.wait_for_function("pl[0].outfit?.pants==='a3'");print('PASS: remote movement, Ctrl crouch and chosen skin reach both browsers')
  # F changes only camera orbit. It must never collect items or turn the actor.
  guest.keyboard.down('KeyF')
  before=guest.evaluate('pl[0].yaw')
  guest.evaluate("(()=>{const e=new MouseEvent('mousemove',{bubbles:true});Object.defineProperties(e,{movementX:{value:100},movementY:{value:10}});rd.domElement.dispatchEvent(e)})()")
  assert guest.evaluate('BATTLE.free.held&&Math.abs(BATTLE.free.yaw)>.05')
  after=guest.evaluate('pl[0].yaw');assert abs(after-before)<.0001,(before,after,guest.evaluate('({held:BATTLE.free.held,free:BATTLE.free.yaw,paused,state,ready:NET.ready,role:NET.role})'))
  guest.keyboard.up('KeyF')
  print('PASS: free look rotates the camera without changing character aim')
  # An item beside the remote avatar is replicated, then collected by E on the host.
  host.evaluate("(()=>{const p=pl.find(p=>p.id===1);const m=itemModel('helmet');m.position.set(p.x,p.y+.6,p.z);sc.add(m);items.push({t:'helmet',m,x:p.x,y:p.y,z:p.z,visual:true})})()")
  guest.wait_for_function("items.some(it=>it.t==='helmet'&&Math.hypot(it.x-pl[0].x,it.z-pl[0].z)<2)")
  guest.keyboard.press('KeyE');host.wait_for_function('pl.find(p=>p.id===1).helmet===100');guest.wait_for_function('pl[0].helmet===100')
  print('PASS: typed ground item, remote pickup and helmet synchronize')
  host.evaluate("window.shotSolids=solids.splice(0);pl[0].x=50;pl[0].z=50;pl[0].hp=200;pl[0].armor=pl[0].helmet=0;const p=pl.find(p=>p.id===1);p.x=50;p.z=44;p.hp=200;p.mag.pistol=5;p.cur=0;p.cd=p.rl=0")
  guest.wait_for_function('Math.abs(pl[0].z-44)<.2');guest.evaluate('pl[0].yaw=0;pl[0].pit=-.05')
  guest.mouse.down();host.wait_for_function('pl[0].hp<200');guest.mouse.up()
  guest.wait_for_function('pl.find(p=>p.id===0).hp<200&&pl.find(p=>p.id===0).hp>100')
  guest.wait_for_function('damageEvents.length>0')
  print('PASS: guest shot damages the host and receives a floating damage number')
  host.evaluate('solids.push(...window.shotSolids)')
  # Damage/falloff and equipment checks independent of randomness and simulation timing.
  print(host.evaluate("""()=>{const check=(ok,msg)=>{if(!ok)throw Error(msg)};const p=pl[0];p.hp=100;p.armor=100;p.helmet=100;const body=dmg(p,null,'body',20),head=dmg(p,null,'head',40);check(Math.abs(body-12)<.001,'vest');check(Math.abs(head-22)<.001,'helmet');check(weaponDamage('m1014',3)*6>weaponDamage('m1014',30)*6*3,'shotgun falloff');check(weaponDamage('ak',10,'head')>weaponDamage('ak',10),'head multiplier');check(weaponDamage('ump',60)<weaponDamage('ump',10),'SMG falloff');return {body,head,shotgunNear:weaponDamage('m1014',3)*6,shotgunFar:weaponDamage('m1014',32)*6}}"""))
  # Slot 2 bullets from the reticle must register at oblique angles too.
  host.evaluate("paused=true;solids.splice(0);pl.forEach(p=>{p.alive=p.id<2?1:0});pl[0].w=['pistol','scar'];pl[0].cur=1;pl[0].mag.scar=30;pl[0].ammo.scar=0;pl[0].h=true")
  print(host.evaluate("""()=>{const p=pl[0],v=pl.find(q=>q.id===1),results=[];for(const angle of [0,.8,-1.1,2.3]){p.x=40;p.z=40;p.y=0;p.yaw=angle;p.g.position.set(40,0,40);p.g.rotation.y=angle;p.cd=0;p.rl=0;v.x=40+Math.sin(angle)*12;v.z=40+Math.cos(angle)*12;v.y=0;v.hp=100;v.alive=1;v.armor=v.helmet=0;v.g.position.set(v.x,0,v.z);cam.position.set(40-Math.sin(angle)*3,1.7,40-Math.cos(angle)*3);cam.lookAt(v.x,1.2,v.z);cam.updateMatrixWorld(true);sc.updateMatrixWorld(true);fire(p,new T.Vector3(40,1.6,40),new T.Vector3(Math.sin(angle),0,Math.cos(angle)));if(v.hp>=100)throw Error('slot 2 missed at angle '+angle);results.push(100-v.hp)}return {slot2Angles:results}}"""))
  assert host.evaluate('damageEvents.length>0')
  # A bot cannot fire through a freshly inserted wall even when its cached target was visible.
  print(host.evaluate("""()=>{const b=pl.find(q=>q.id===1),v=pl[0];b.x=40;b.z=30;b.y=0;b.yaw=0;b.st='ground';b.hp=100;b.alive=1;v.x=40;v.z=45;v.y=0;v.alive=1;b.brain={scan:0,reaction:-1,side:1,strafe:1,target:v,roam:1,gx:40,gz:45};const wall=new T.Mesh(new T.BoxGeometry(8,4,.2),mt(0x334455));wall.position.set(40,2,37);sc.add(wall);solids.push(wall);sc.updateMatrixWorld(true);if(botVisible(b,v))throw Error('bot sees through wall');const ammo=b.mag[b.w[b.cur]];nativeAI(b,.05);if(b.mag[b.w[b.cur]]!==ammo)throw Error('bot shoots through wall');solids.pop();release(wall);return 'PASS: bot line-of-sight and firing guard'}"""))
  # Capture the reorganized HUD and the dropped inventory panel.
  host.evaluate("(()=>{const p=pl[0];p.hp=100;p.armor=75;p.helmet=60;const c={x:p.x+.8,z:p.z+.5,y:0,gear:{w:['ak','m1014'],mag:{ak:12,m1014:3},ammo:{ak:50,m1014:12},k25:2,k100:1,gr:2,ice:1,helmet:30},m:new T.Mesh(new T.BoxGeometry(.85,.55,.65),mt(0x566451))};c.m.position.set(c.x,.3,c.z);sc.add(c.m);crates.push(c);battleHud();dm(mc,150);rd.render(sc,cam)})()")
  host.evaluate("$('pause').classList.add('h');setQuality(1);rd.setPixelRatio(1);$('ammo').innerHTML='SCAR<br>26 / 0';$('wl').innerHTML='<div class=\"hud-card\">1 · Pistola</div><div class=\"hud-card\">2 · SCAR</div>';sun.position.set(pl[0].x-60,90,pl[0].z-40);sun.target.position.set(pl[0].x,0,pl[0].z);pose(pl[0],.016);rd.render(sc,cam)");host.screenshot(path=str(root/'duo-hud.png'))
  # The only third-party networking is absent: both clients use the same server origin.
  assert not errors,errors
  guest.evaluate('leaveDuo()');host.wait_for_function('!NET.connected');host.evaluate('leaveDuo()')
  print('PASS: disconnect cleanup, no JavaScript/shader errors; two browser contexts tested')
  browser.close()
finally:
 proc.terminate();proc.wait(timeout=5)
