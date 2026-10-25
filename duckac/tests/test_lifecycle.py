import ctypes
import threading
import time
import unittest
from duckac_engine import AutoClickController,ClickSettings,WindowsBackend,VK_F12,parse_hotkey
from test_duckac import FakeBackend


def native_backend():
    class Mouse(ctypes.Structure):
        _fields_=[('dwFlags',ctypes.c_uint32)]
    class Input(ctypes.Structure):
        _fields_=[('type',ctypes.c_uint32),('mi',Mouse)]
    class API:
        def __init__(self):self.flags=[];self.down=threading.Event()
        def SendInput(self,count,ptr,size):
            flag=ctypes.cast(ptr,ctypes.POINTER(Input)).contents.mi.dwFlags
            self.flags.append(flag)
            if flag in (2,8,32):self.down.set()
            return 1
    b=WindowsBackend.__new__(WindowsBackend)
    b._init_input_state();b.Input=Input;b.u=API()
    return b


class LifecycleTests(unittest.TestCase):
    def test_close_interrupts_held_middle_button_and_cannot_rearm(self):
        backend=native_backend()
        worker=threading.Thread(target=lambda:backend.click('middle',5))
        worker.start()
        self.assertTrue(backend.u.down.wait(1))
        backend.close();worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(backend.u.flags,[32,64])
        backend.arm();backend.click('left')
        self.assertEqual(backend.u.flags,[32,64])

    def test_stop_during_blocked_query_never_sends_delayed_click(self):
        entered,release=threading.Event(),threading.Event()
        class Slow(FakeBackend):
            def target_focused(self,_):
                entered.set();release.wait(3);return True
        backend=Slow();ctrl=AutoClickController(backend,ClickSettings())
        ctrl.toggle();ctrl._last_focus=True;ctrl._grace_until=0
        worker=threading.Thread(target=lambda:ctrl._tick(time.monotonic()+1))
        worker.start();self.assertTrue(entered.wait(1))
        ctrl.stop();release.set();worker.join(1)
        ctrl.toggle();ctrl._tick(time.monotonic()+5)
        self.assertFalse(ctrl.status().enabled)
        self.assertEqual(backend.clicks,[])

    def test_closed_backend_rejects_click_already_approved_by_controller(self):
        b=native_backend();b.close()
        self.assertFalse(b.click('right'))
        self.assertEqual(b.u.flags,[])

    def test_f12_stops_even_with_inventory_pause_disabled(self):
        b=FakeBackend();c=AutoClickController(b,ClickSettings(inventory_pause=False))
        c.toggle();b.keys={VK_F12};c._tick(time.monotonic()+1)
        self.assertFalse(c.status().enabled);self.assertEqual(b.clicks,[])
        with self.assertRaises(ValueError):parse_hotkey('CTRL+F12')

    def test_ui_heartbeat_loss_disarms_without_automatic_resume(self):
        now=[100.];b=FakeBackend();c=AutoClickController(b,ClickSettings(),lambda:now[0])
        c.heartbeat();c.toggle();now[0]+=2;c._tick(now[0])
        self.assertFalse(c.status().enabled)
        c.heartbeat();now[0]+=.01;c._tick(now[0])
        self.assertFalse(c.status().enabled)

    def test_middle_setting_survives_normalization(self):
        s=ClickSettings(mouse_button='middle');s.normalize()
        self.assertEqual(s.mouse_button,'middle')
