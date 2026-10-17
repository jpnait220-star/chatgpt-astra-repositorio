"""Browser UI tests with explicitly simulated extension messages; no extension install."""
import functools
import http.server
from pathlib import Path
import tempfile
import threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
fixture='''(() => {
 const now=Date.now();
 const state={settings:{minutes:15,paused:false},cleaned:0,history:[],tabs:[
 {id:1,title:'Inspiração de design — uma coleção de boas ideias',url:'https://www.pinterest.com/inspiration',favorite:true,lastActive:now,protection:'Favorite'},
 {id:2,title:'Uma trilha sonora para se concentrar',url:'https://open.spotify.com/playlist/focus',favorite:false,lastActive:now,protection:'Playing audio'},
 {id:3,title:'A arte de fazer um pouco menos',url:'https://medium.com/ideas',favorite:false,lastActive:now-7*60000,protection:null},
 {id:4,title:'Lugares para conhecer no fim de semana',url:'https://www.notion.so/travel',favorite:false,lastActive:now-3*60000,protection:null},
 {id:5,title:'DuckCleans · notas do projeto',url:'https://github.com/projects',favorite:false,lastActive:now,protection:'Pinned'}
 ]};
 window.__fixture=state;
 window.chrome={runtime:{sendMessage:async message=>{
  if(message.type==='settings') { Object.assign(state.settings,message.settings); }
  if(message.type==='favorite') { const tab=state.tabs.find(tab=>tab.id===message.id); tab.favorite=!tab.favorite;tab.protection=tab.favorite?'Favorite':null; }
  if(message.type==='clearHistory') state.history=[];
  return {ok:true,data:structuredClone(state)};
 }}};
})();'''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
  errors=[]; page.on('pageerror',lambda error:errors.append(str(error)))
  page.add_init_script(fixture)
  page.goto(f'http://127.0.0.1:{server.server_port}/dashboard.html')
  page.wait_for_function("document.querySelector('#openCount').textContent === '5'")
  assert page.title()=='DuckCleans GUI'
  assert page.locator('.tab-row').count()==5
  page.get_by_role('button',name='Pausar limpeza').click()
  assert page.locator('#pauseButton').evaluate('(el)=>el.getAnimations().length > 0')
  assert page.get_by_role('button',name='Retomar limpeza').is_visible()
  assert page.locator('#headerStatus').inner_text()=='Limpeza pausada'
  page.get_by_role('button',name='Retomar limpeza').click()
  page.get_by_role('button',name='Favoritar: A arte de fazer um pouco menos',exact=True).click()
  page.locator('[data-view="favorites"]').click()
  assert page.locator('.tab-row').count()==2
  page.locator('[data-view="settings"]').click()
  assert page.locator('.content').evaluate('(el)=>el.getAnimations().length > 0')
  # Mouse attraction is bounded, returns on leave, and does not move the slider.
  preset=page.locator('[data-minutes="1"]')
  box=preset.bounding_box()
  page.mouse.move(box['x']+box['width']*.8,box['y']+box['height']*.55)
  page.wait_for_function("parseFloat(document.querySelector('[data-minutes=\"1\"]').style.getPropertyValue('--magnet-x')) > 0")
  assert abs(float(preset.evaluate("el=>el.style.getPropertyValue('--magnet-x').replace('px','')"))) <= 5
  page.mouse.move(700,90)
  page.wait_for_function("document.querySelector('[data-minutes=\"1\"]').style.getPropertyValue('--magnet-x') === ''")
  # Exercise the actual native slider via keyboard and dragging its circular thumb.
  slider=page.locator('#timeoutRange')
  slider.focus()
  slider.press('Home')
  page.wait_for_function('__fixture.settings.minutes === 1')
  assert slider.get_attribute('aria-valuetext')=='1 minuto'
  assert page.locator('#heroMinutes').inner_text()=='1 minuto'
  slider.press('ArrowRight')
  page.wait_for_function('__fixture.settings.minutes === 2')
  slider.press('Home')
  page.wait_for_function('__fixture.settings.minutes === 1')
  box=slider.bounding_box()
  page.mouse.move(box['x']+14,box['y']+box['height']/2)
  page.mouse.down()
  page.mouse.move(box['x']+box['width']-14,box['y']+box['height']/2,steps=12)
  page.mouse.up()
  page.wait_for_function('__fixture.settings.minutes === 240')
  assert slider.evaluate("el=>el.style.getPropertyValue('--range-progress')")=='100%'
  page.locator('[data-minutes="1"]').click()
  page.wait_for_function('__fixture.settings.minutes === 1')
  page.locator('[data-minutes="60"]').click()
  page.wait_for_function("document.querySelector('#timeoutDisplay').textContent === '60'")
  page.locator('#customMinutes').fill('0')
  page.locator('#timeoutForm button').click()
  assert not page.locator('#customMinutes').evaluate('(el)=>el.checkValidity()')
  assert page.evaluate('__fixture.settings.minutes')==60
  page.locator('#customMinutes').fill('90')
  page.locator('#timeoutForm button').click()
  page.wait_for_function("document.querySelector('#timeoutDisplay').textContent === '90'")
  page.locator('[data-minutes="15"]').click()
  page.locator('[data-view="activity"]').click()
  assert page.get_by_text('Tudo tranquilo por aqui.').is_visible()
  assert page.locator('#clearHistory').is_disabled()
  page.locator('[data-view="overview"]').click()
  page.locator('#search').fill('nothing-matches')
  assert page.get_by_text('Nenhuma aba encontrada.').is_visible()
  page.locator('#search').fill('notion')
  assert page.locator('.tab-row').count()==1
  page.locator('#search').fill('')
  page.evaluate("__fixture.tabs[2].title='<img src=x onerror=alert(1)>'")
  page.get_by_role('button',name='Pausar limpeza').click()
  assert page.get_by_text('<img src=x onerror=alert(1)>',exact=True).is_visible()
  assert page.locator('#tabList img').count()==0
  page.evaluate("__fixture.tabs[2].title='A arte de fazer um pouco menos'")
  page.get_by_role('button',name='Retomar limpeza').click()
  page.locator('#toast').wait_for(state='hidden')
  artifacts=ROOT/'artifacts'; artifacts.mkdir(exist_ok=True)
  page.wait_for_function('document.getAnimations().length === 0')
  page.screenshot(path=str(artifacts/'duckcleans-overview.png'),full_page=True)
  page.locator('[data-view="settings"]').click()
  page.wait_for_function('document.getAnimations().length === 0')
  page.screenshot(path=str(artifacts/'duckcleans-settings.png'),full_page=True)
  page.set_viewport_size({'width':640,'height':1000})
  page.locator('[data-view="overview"]').click()
  page.wait_for_function('document.getAnimations().length === 0')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  page.screenshot(path=str(artifacts/'duckcleans-compact.png'),full_page=True)
  page.emulate_media(reduced_motion='reduce')
  page.locator('[data-view="settings"]').click()
  assert page.locator('.content').evaluate('(el)=>el.getAnimations().length')==0
  assert page.locator('[data-view="settings"]').evaluate('(el)=>getComputedStyle(el).transform')=='none'
  assert page.locator('[data-view="settings"]').evaluate('(el)=>el.getAnimations().length')==0
  assert not errors,errors
  browser.close()
  print('PASS: browser UI with simulated data: overview, favorites, pause/resume, settings, invalid timeout, search, activity empty state, safe titles, compact layout. Screenshots contain demonstration data.')
finally:
 server.shutdown()
