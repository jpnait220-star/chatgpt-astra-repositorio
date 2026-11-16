"""Camera orbit, bounded visible aim assistance and rendered green terrain regression checks."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
import functools,http.server,threading,json
ROOT=Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=browser.new_page(viewport={'width':1280,'height':800});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('dialog',lambda d:d.dismiss())
  page.goto(f'http://127.0.0.1:{server.server_port}/LAST%20ZONE%20Duo.html?quality=low')
  page.wait_for_function('typeof VERDANT!=="undefined"&&typeof ASSIST!=="undefined"')
  page.evaluate("HTMLCanvasElement.prototype.requestPointerLock=function(){};Object.defineProperty(document,'pointerLockElement',{get:()=>state==='play'?rd.domElement:null,configurable:true});newGame();paused=true;rd.setPixelRatio(.4)")
  print(page.evaluate("""()=>{if(Math.hypot(grassGround.rotation.x,grassGround.rotation.y,grassGround.rotation.z)>.001)throw Error('double rotated ground');const v=new T.Vector3(90,terrainHeight(90,60),60);const ray=new T.Raycaster(new T.Vector3(v.x,20,v.z),new T.Vector3(0,-1,0),0,40),hit=ray.intersectObject(grassGround,false)[0];if(!hit||Math.abs(hit.point.y-v.y)>.15)throw Error('terrain rendering/physics mismatch');if(VERDANT.trees<350||VERDANT.decorationCount<3000)throw Error('vegetation');return {trees:VERDANT.trees,grass:VERDANT.decorationCount,terrainHeight:hit.point.y,health:pl[0].hp}}"""))
  page.evaluate("window.savedObs=obs.splice(0);window.savedSolids=solids.splice(0);pl.forEach(p=>p.alive=p.id<2?1:0);const p=pl[0];p.x=0;p.z=-60;p.y=0;p.yaw=0;p.pit=0;p.st='ground';p.crouched=false;aim=aimK=0;view=0;steadyCamera.ready=false")
  print(page.evaluate("""()=>{const p=pl[0];stableCameraUpdate(p,1/60);const old=cam.position.clone();p.yaw=Math.PI/2;stableCameraUpdate(p,1/60);const direction=cam.getWorldDirection(new T.Vector3());if(direction.distanceTo(new T.Vector3(1,0,0))>.0001)throw Error('rotation lag/roll');if(Math.abs(cam.position.distanceTo(steadyCamera.anchor)-Math.hypot(3.8,.62))>.01)throw Error('third person distance');if(cam.position.distanceTo(old)<4)throw Error('orbit position lag');p.yaw=0;steadyCamera.ready=false;stableCameraUpdate(p,1/60);const y=cam.position.y;p.crouched=true;stableCameraUpdate(p,1/60);if(!(cam.position.y<y&&cam.position.y>p.y+1.25))throw Error('stance smoothing');p.crouched=false;steadyCamera.ready=false;stableCameraUpdate(p,1/60);const wall=new T.Mesh(new T.BoxGeometry(5,5,.25),mt(0x555555));wall.position.set(0,2.5,-62);sc.add(wall);solids.push(wall);sc.updateMatrixWorld(true);stableCameraUpdate(p,1/60);if(cam.position.z<-61.8)throw Error('camera penetrated wall');solids.pop();release(wall);steadyCamera.ready=false;return 'PASS: immediate orbit rotation, stable horizon, modestly wider camera, smooth crouch and wall clipping'}"""))
  print(page.evaluate("""()=>{paused=false;const p=pl[0],b=pl[1];p.yaw=0;p.pit=0;b.x=1.2;b.z=-30;b.y=0;b.st='ground';b.alive=1;b.g.position.set(b.x,b.y,b.z);steadyCamera.ready=false;stableCameraUpdate(p,1/60);const error=()=>{const d=new T.Vector3(b.x,b.y+1.35,b.z).sub(cam.position);return Math.hypot(ang(p.yaw,Math.atan2(d.x,d.z)),Math.atan2(d.y,Math.hypot(d.x,d.z))-p.pit)};const start=error(),idle=p.yaw;fh=0;softAim(p,1/60);if(p.yaw!==idle)throw Error('idle autoaim');fh=1;for(let i=0;i<60;i++){const yaw=p.yaw,pit=p.pit;softAim(p,1/60);if(Math.hypot(ang(yaw,p.yaw),pit-p.pit)>ASSIST.hipSpeed/60+.00001)throw Error('aim snapped')}const after=error();if(after>start*.20||RETICLE.target!==b.id)throw Error('tracking failed '+start+','+after);const wall=new T.Mesh(new T.BoxGeometry(5,5,.3),mt(0x555555));wall.position.set(0,2.5,-45);sc.add(wall);solids.push(wall);sc.updateMatrixWorld(true);const blocked=p.yaw;softAim(p,1/60);if(p.yaw!==blocked||RETICLE.target!==null)throw Error('aim through wall');solids.pop();release(wall);BATTLE.free.held=true;const free=p.yaw;softAim(p,1/60);if(p.yaw!==free||RETICLE.target!==null)throw Error('free look aim');BATTLE.free.held=false;fh=0;paused=true;return {aimErrorBefore:start,aimErrorAfter:after,maxRadiansPerSecond:ASSIST.hipSpeed,lineOfSight:'PASS'}}"""))
  page.evaluate("obs.push(...savedObs);solids.push(...savedSolids);rebuildNav();const p=pl[0];p.x=4;p.z=68;p.y=terrainHeight(4,68);p.yaw=Math.PI;p.pit=-.08;p.st='ground';p.on=1;p.g.position.set(p.x,p.y,p.z);p.g.rotation.y=p.yaw;p.ch.visible=false;zf={x:0,z:0,r:395};zr.scale.set(395,1,395);zr.position.set(0,90,0);pl.slice(1).forEach(p=>{p.alive=0;p.g.visible=false});setQuality(1);rd.setPixelRatio(.8);steadyCamera.ready=false;for(let i=0;i<12;i++)pose(p,1/30);stableCameraUpdate(p,1/30);battleHud();dm(mc,150);rd.render(sc,cam)")
  page.screenshot(path=str(ROOT/'verdant-town.png'))
  # Bird's-eye inspection catches the old vertical-ground defect independently of third-person framing.
  page.evaluate("cam.position.set(110,55,105);cam.lookAt(20,0,10);rd.render(sc,cam)")
  page.screenshot(path=str(ROOT/'verdant-aerial.png'))
  im=Image.open(ROOT/'verdant-aerial.png').convert('RGB');pixels=list(im.crop((80,250,1180,730)).get_flattened_data());green=sum(g>r*1.12 and g>b*1.08 and 30<g<235 for r,g,b in pixels)/len(pixels)
  if green<.10:raise AssertionError(f'green terrain missing from rendered view: {green}')
  print('PASS: green pixel fraction',round(green,3),'no JavaScript/shader errors')
  assert not errors,errors
  browser.close()
finally:server.shutdown()
