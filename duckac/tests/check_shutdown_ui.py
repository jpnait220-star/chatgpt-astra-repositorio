"""Actual Tk lifecycle; input backend only records in memory, never sends OS clicks."""
import sys,time,tempfile,threading,subprocess,tkinter as tk
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duckac
from duckac_engine import AutoClickController,ClickSettings

class Backend:
    def __init__(self):self.clicks=[]
    def key_down(self,key):return False
    def target_focused(self,_):return True
    def click(self,button):self.clicks.append(button)

def pump(root,seconds):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        root.update();time.sleep(.01)

if len(sys.argv)==1:
    for route in ('close','save-error','destroy','tester-gone','callback-error','quit'):
        subprocess.run([sys.executable,__file__,route],check=True,timeout=60)
    print('All shutdown subprocesses exited cleanly')
    raise SystemExit(0)

with tempfile.TemporaryDirectory() as temp,patch.object(duckac,'SETTINGS_PATH',Path(temp)/'settings.json'):
    for route in ([sys.argv[1]] if sys.argv[1]!='quit' else []):
        root=tk.Tk();b=Backend();engine=AutoClickController(b,ClickSettings(cps=25))
        app=duckac.DuckApp(root,engine)
        app.start();pump(root,.35)
        assert b.clicks,route
        if route=='tester-gone':
            app.open_tester();app.tester.window.destroy();app.start();pump(root,.3)
        if route=='save-error':
            with patch.object(app,'save',side_effect=OSError('simulated disk failure')):app.close()
        elif route=='destroy':root.destroy()
        elif route=='callback-error':
            app.callback_error(ValueError,ValueError('simulated callback failure'),None)
            count=len(b.clicks);pump(root,.15)
            assert len(b.clicks)==count and not engine.status().enabled
            app.close()
        else:app.close()
        count=len(b.clicks);time.sleep(.08)
        assert len(b.clicks)==count and not engine._thread.is_alive(),route
        assert not engine.status().enabled,route
    if sys.argv[1]!='quit':
        print('Shutdown GUI OK:',sys.argv[1])
        raise SystemExit(0)
    created=[]
    original=duckac.DuckApp
    class QuitApp(original):
        def __init__(self,root,engine):
            super().__init__(root,engine);created.append(engine);root.after(80,root.quit)
    with patch.object(duckac,'DuckApp',QuitApp),patch.object(sys,'argv',['duckac.py','--preview']):
        assert duckac.main()==0
    assert not created[0]._thread.is_alive()
    assert not any(t.name=='DuckAC-Input' and t.is_alive() for t in threading.enumerate())
print('Shutdown GUI OK: close, save failure, destroyed root/tester, callback failure and mainloop quit')
