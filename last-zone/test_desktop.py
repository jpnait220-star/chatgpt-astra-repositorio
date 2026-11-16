"""Launch the packaged Electron app (Linux test build), exercise its real IPC/proxy and Ctrl+W."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,socket,os,time,tempfile,json,urllib.request
root=Path(__file__).resolve().parent
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with socket.socket() as s:s.bind(('127.0.0.1',0));debug=s.getsockname()[1]
remote=subprocess.Popen(['node','server.mjs'],cwd=root,env={**os.environ,'PORT':str(port),'HOST':'127.0.0.1'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
app=None
try:
 for i in range(50):
  try:urllib.request.urlopen(f'http://127.0.0.1:{port}/health');break
  except Exception:time.sleep(.1)
 with tempfile.TemporaryDirectory(prefix='lz-native-test-') as folder:
  log=open(Path(folder)/'electron.log','w')
  app=subprocess.Popen([str(root/'desktop-dist/LAST ZONE-linux-x64/LAST ZONE'),'--no-sandbox','--ozone-platform=headless','--headless','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',f'--remote-debugging-port={debug}'],env={**os.environ,'XDG_CONFIG_HOME':folder+'/config','XDG_CACHE_HOME':folder+'/cache'},stdout=log,stderr=log)
  for i in range(100):
   if app.poll() is not None:raise RuntimeError('Electron exited: '+Path(folder,'electron.log').read_text()[-2000:])
   try:urllib.request.urlopen(f'http://127.0.0.1:{debug}/json/version',timeout=1);break
   except Exception:time.sleep(.1)
  with sync_playwright() as pw:
   browser=pw.chromium.connect_over_cdp(f'http://127.0.0.1:{debug}');page=browser.contexts[0].pages[0];errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.dismiss())
   page.wait_for_function('typeof INPUT!=="undefined"&&!!window.lastZoneDesktop')
   page.evaluate('setQuality(0);rd.setPixelRatio(.4)')
   assert page.evaluate('GAME_WORLD.radius===400&&GAME_WORLD.players===32')
   assert page.evaluate('window.lastZoneDesktop.getConfig()')=={'serverURL':''}
   target=f'http://127.0.0.1:{port}'
   result=page.evaluate('(url)=>window.lastZoneDesktop.connectServer(url)',target);assert result['ok']
   try:page.evaluate("window.lastZoneDesktop.connectServer('file:///tmp/invalid')");raise AssertionError('unsafe URL accepted')
   except Exception as e:assert 'Endereço inválido' in str(e) or 'Use somente' in str(e)
   assert page.evaluate('enterDuo(true)');code=page.evaluate('NET.id')
   req=urllib.request.Request(target+'/api/rooms/'+code+'/join',data=b'{}',headers={'Content-Type':'application/json'});guest=json.load(urllib.request.urlopen(req))
   page.wait_for_function('NET.connected&&state==="play"')
   stream=urllib.request.urlopen(target+'/api/rooms/'+code+'/events?token='+guest['token'],timeout=10)
   state=None
   for i in range(30):
    line=stream.readline().decode().strip()
    if line=='event: state':state=json.loads(stream.readline().decode()[6:]);break
   stream.close();assert state and len(state['players'])==32
   print('PASS: packaged Electron, native bridge, validated server URL and native-to-public room/state streaming')
   page.evaluate("leaveDuo();HTMLCanvasElement.prototype.requestPointerLock=function(){};Object.defineProperty(document,'pointerLockElement',{get:()=>state==='play'&&!paused?rd.domElement:null,configurable:true});newGame();pl.slice(1).forEach(p=>{p.alive=0;p.g.visible=false});paused=false;$('pause').classList.add('h')")
   page.keyboard.down('ControlLeft');page.keyboard.press('KeyW');page.keyboard.up('ControlLeft');page.wait_for_timeout(250);assert not page.is_closed();assert app.poll() is None
   page.keyboard.press('ControlLeft');page.evaluate("openSettings();INPUT.listening='forward';assignBinding('KeyI');closeSettings();toMenu()")
   page.wait_for_timeout(1800)
   assert any('KeyI' in p.read_text() for p in Path(folder).rglob('settings.json'))
   page.screenshot(path=str(root/'desktop-final.png'))
   assert not errors,errors
   print('PASS: Ctrl+W does not close native app; remapped controls persisted to native profile; no renderer exceptions')
  app.terminate();app.wait(timeout=10);app=None;log.close()
finally:
 if app and app.poll() is None:app.terminate();app.wait(timeout=10)
 remote.terminate();remote.wait(timeout=5)
