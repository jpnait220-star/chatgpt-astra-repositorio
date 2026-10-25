"""Regressions for reported CPS, hotkey replacement and real input failure paths."""
import ctypes
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckac
from duckac_engine import AutoClickController, ClickMeter, ClickSettings, WindowsBackend, VK_SHIFT
from test_duckac import FakeBackend


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.backend = FakeBackend()
        self.ctrl = AutoClickController(self.backend, ClickSettings(cps=25), clock=lambda:self.now)

    def tick(self, delta=0.01):
        self.now += delta
        self.ctrl._tick(self.now)

    def test_recording_suspends_old_hotkey_even_if_user_presses_it(self):
        self.ctrl.set_hotkey_capture(True)
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.tick(1)
        self.assertFalse(self.ctrl.status().enabled)
        self.assertEqual(self.backend.clicks, [])
        self.ctrl.change_settings(hotkey='I')
        self.ctrl.set_hotkey_capture(False)
        self.backend.keys.clear()
        self.tick()
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.assertFalse(self.ctrl.status().enabled)
        self.backend.keys = {ord('I')}
        self.tick()
        self.assertTrue(self.ctrl.status().enabled)

    def test_old_shift_r_does_not_match_new_plain_r(self):
        self.ctrl.change_settings(hotkey='R')
        self.tick()
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.assertFalse(self.ctrl.status().enabled)
        self.backend.keys.clear()
        self.tick()
        self.backend.keys = {ord('R')}
        self.tick()
        self.assertTrue(self.ctrl.status().enabled)

    def test_release_of_modifier_alone_does_not_arm_captured_key(self):
        self.ctrl.change_settings(hotkey='SHIFT+R')
        self.ctrl.set_hotkey_capture(False)
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.backend.keys = {ord('R')}
        self.tick()
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.assertFalse(self.ctrl.status().enabled)
        self.backend.keys.clear()
        self.tick()
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.assertTrue(self.ctrl.status().enabled)

    def test_blocked_windows_query_cannot_apply_old_shortcut_after_rebind(self):
        entered, release = threading.Event(), threading.Event()
        class BlockedBackend(FakeBackend):
            def target_focused(self, minecraft_only):
                entered.set()
                release.wait(2)
                return True
        backend = BlockedBackend()
        backend.keys = {VK_SHIFT, ord('R')}
        ctrl = AutoClickController(backend, ClickSettings())
        worker = threading.Thread(target=lambda:ctrl._tick(100.0))
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            ctrl.change_settings(hotkey='I')
        finally:
            release.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertFalse(ctrl.status().enabled, 'Stale Shift+R must not toggle new config')
        self.assertEqual(backend.clicks, [])

    def test_cps_expires_even_when_worker_has_no_new_ticks(self):
        self.backend.keys = {VK_SHIFT, ord('R')}
        self.tick()
        self.backend.keys.clear()
        self.tick(.3)
        self.assertEqual(self.ctrl.status().current_cps, 1)
        self.now += 1.1
        self.assertEqual(self.ctrl.status().current_cps, 0)
        self.assertEqual(self.ctrl.status().total_clicks, 1)

    def test_pause_and_reactivation_do_not_reuse_old_cps_samples(self):
        self.ctrl.toggle()
        self.tick(.3)
        self.tick(.2)
        self.assertGreater(self.ctrl.status().current_cps, 0)
        self.ctrl.toggle()
        self.ctrl.toggle()
        self.assertEqual(self.ctrl.status().current_cps, 0)

    def test_failed_click_is_never_counted(self):
        def rejected(button):
            raise OSError('SendInput rejected')
        self.backend.click = rejected
        self.ctrl.toggle()
        self.tick(.3)
        # First foreground transition also has a grace period.
        self.tick(.3)
        state = self.ctrl.status()
        self.assertFalse(state.enabled)
        self.assertIn('rejected', state.error)
        self.assertEqual((state.total_clicks, state.current_cps), (0, 0))

    def test_real_rate_for_1_10_25_over_virtual_ten_seconds(self):
        for cps in (1, 10, 25):
            with self.subTest(cps=cps):
                now = [50.0]
                backend = FakeBackend()
                ctrl = AutoClickController(backend, ClickSettings(cps=cps), clock=lambda:now[0])
                ctrl.toggle()
                # Simulate a 20 ms DOWN event with 1 ms worker polling jitter.
                for _ in range(500):
                    now[0] += .001
                    ctrl._tick(now[0])
                start = len(backend.clicks)
                end = now[0]+10
                while now[0] < end:
                    n = len(backend.clicks)
                    ctrl._tick(now[0])
                    now[0] += .020 if len(backend.clicks) != n else .001
                sent = len(backend.clicks)-start
                self.assertLessEqual(abs(sent/10-cps), .2)

    def test_completed_click_is_timestamped_after_backend_delay(self):
        self.backend.click = lambda button:setattr(self, 'now', self.now+.05)
        self.ctrl.toggle()
        self.tick(.3)
        self.tick(.3)
        finished = self.now
        self.now = finished+.99
        self.assertEqual(self.ctrl.status().current_cps, 1)
        self.now = finished+1.01
        self.assertEqual(self.ctrl.status().current_cps, 0)

    def test_meter_counts_received_releases_only_and_drops_expired_samples(self):
        clock = [1.0]
        meter = ClickMeter(lambda:clock[0])
        for _ in range(25):
            meter.record()
            clock[0] += .04
        self.assertEqual(meter.rate(), 24)  # Exactly one-second-old release expires.
        self.assertEqual(meter.total, 25)
        clock[0] += 1
        self.assertEqual(meter.rate(), 0)
        self.assertEqual(meter.total, 25)

    def test_invalid_cps_field_does_not_erase_saved_custom_hotkey(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'settings.json'
            p.write_text(json.dumps({'cps':None, 'hotkey':'I'}))
            with patch.object(duckac, 'SETTINGS_PATH', p):
                cfg = duckac.load_settings()
            self.assertEqual(cfg.hotkey, 'I')
            self.assertEqual(cfg.cps, 25)

    def test_hotkey_survives_save_reload_and_is_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'nested'/'settings.json'
            with patch.object(duckac, 'SETTINGS_PATH', p):
                cfg = ClickSettings(hotkey='shift + ctrl + r')
                cfg.normalize()
                duckac.save_settings(cfg)
                loaded = duckac.load_settings()
                self.assertEqual(loaded.hotkey, 'CTRL+SHIFT+R')
                self.assertEqual(json.loads(p.read_text())['config_version'], 9)

    def test_sendinput_failure_during_release_is_reported(self):
        class MouseInput(ctypes.Structure):
            _fields_ = [('dwFlags', ctypes.c_uint32)]
        class Input(ctypes.Structure):
            _fields_ = [('type', ctypes.c_uint32), ('mi', MouseInput)]
        class API:
            def __init__(self):self.flags=[]
            def SendInput(self,count,ptr,size):
                flag=ctypes.cast(ptr,ctypes.POINTER(Input)).contents.mi.dwFlags
                self.flags.append(flag)
                return 0 if flag == 0x0004 else 1
        backend=WindowsBackend.__new__(WindowsBackend)
        backend._init_input_state()
        backend.Input=Input;backend.u=API()
        with patch.object(backend._cancelled, 'wait'):
            with self.assertRaisesRegex(OSError, 'liberação'):
                backend.click('left')
        self.assertEqual(backend.u.flags[0], 0x0002)
        self.assertGreaterEqual(backend.u.flags.count(0x0004), 2)


if __name__ == '__main__':
    unittest.main()
