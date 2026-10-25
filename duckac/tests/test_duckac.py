import unittest
import ctypes
import tempfile
from unittest.mock import patch
import threading
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duckac_engine import (
    AutoClickController, ClickSettings, WindowsBackend, VK_SHIFT, VK_ESCAPE, VK_E,
    parse_hotkey, virtual_key, is_minecraft_target,
)

class FakeBackend:
    def __init__(self):
        self.keys=set()
        self.focused=True
        self.clicks=[]
        self.minecraft=True
    def key_down(self, key):
        return key in self.keys
    def target_focused(self, minecraft_only):
        return self.focused
    def click(self, button):
        self.clicks.append(button)
    def inventory_context(self):
        return self.minecraft

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.backend=FakeBackend()
        self.t=10000.0
        self.controller=AutoClickController(self.backend, ClickSettings(), clock=lambda:self.t)

    def tick(self, offset=0):
        self.t+=offset
        self.controller._tick(self.t)

    def enable(self):
        self.backend.keys={VK_SHIFT,ord('R')}
        self.tick()
        self.backend.keys.clear()
        self.tick(0.06)
        self.assertTrue(self.controller.status().enabled)

    def test_focus_guard_excludes_browser_titles(self):
        self.assertFalse(is_minecraft_target('Minecraft Wiki – Google Chrome','chrome.exe'))
        self.assertTrue(is_minecraft_target('Minecraft 1.21.11','javaw.exe'))
        self.assertTrue(is_minecraft_target('Game','Minecraft.Windows.exe'))
        self.assertFalse(is_minecraft_target('DuckAC','duckac.exe'))

    def test_default_config(self):
        cfg=ClickSettings()
        self.assertEqual(cfg.hotkey,'SHIFT+R')
        self.assertEqual(cfg.inventory_key,'E')
        self.assertEqual(cfg.cps,10)
        self.assertFalse(cfg.minecraft_only)

    def test_shortcut_and_clicks(self):
        self.enable()
        self.tick(0.26)
        self.assertEqual(len(self.backend.clicks),1)
        self.tick(0.2)
        self.assertEqual(len(self.backend.clicks),2)
        self.backend.keys={VK_SHIFT,ord('R')}
        self.tick(0.2)
        self.assertFalse(self.controller.status().enabled)
        clicked=len(self.backend.clicks)
        self.tick(1)
        self.assertEqual(len(self.backend.clicks),clicked)

    def test_inventory_e_and_escape(self):
        self.enable()
        self.tick(0.3)
        self.backend.keys={VK_E}
        self.tick(0.1)
        self.assertTrue(self.controller.status().inventory_open)
        held=len(self.backend.clicks)
        self.tick(1)
        self.assertEqual(held,len(self.backend.clicks))
        self.backend.keys.clear()
        self.tick(.05)
        self.backend.keys={VK_ESCAPE}
        self.tick(.05)
        self.assertFalse(self.controller.status().inventory_open)
        self.tick(.25)
        self.assertGreater(len(self.backend.clicks),held)

    def test_inventory_e_again_resumes(self):
        self.enable()
        self.backend.keys={VK_E}
        self.tick(.25)
        self.assertTrue(self.controller.status().inventory_open)
        self.backend.keys.clear()
        self.tick(.05)
        self.backend.keys={VK_E}
        self.tick(.05)
        self.assertFalse(self.controller.status().inventory_open)

    def test_foreground_focus_blocks_clicks_and_resumes(self):
        self.enable()
        self.backend.focused=False
        self.tick(.5)
        self.assertEqual(len(self.backend.clicks),0)
        self.assertEqual(self.controller.status().label,'PAUSADO · OUTRA JANELA')
        self.backend.focused=True
        self.tick(.05)
        self.tick(.25)
        self.assertGreater(len(self.backend.clicks),0)

    def test_mouse_button_and_rate_adjust(self):
        self.controller.change_settings(cps=21,mouse_button='right')
        self.enable()
        self.tick(.3)
        self.assertEqual(self.backend.clicks[-1],'right')
        self.assertEqual(self.controller.settings.cps,21)

    def test_slow_windows_api_does_not_block_gui_state(self):
        entered=threading.Event()
        release=threading.Event()
        class SlowBackend(FakeBackend):
            def target_focused(self, minecraft_only):
                entered.set()
                release.wait(timeout=2)
                return False
        slow=AutoClickController(SlowBackend(),ClickSettings())
        worker=threading.Thread(target=lambda:slow._tick(11111),daemon=True)
        worker.start()
        try:
            self.assertTrue(entered.wait(timeout=1))
            start=time.perf_counter()
            slow.status()
            slow.change_settings(cps=17)
            slow.toggle()
            self.assertLess(time.perf_counter()-start,0.20,
                            'Win32 lento não pode travar GUI')
        finally:
            release.set()
            worker.join(timeout=1)

    def test_invalid_modifier_gives_clear_error(self):
        with self.assertRaises(ValueError):
            parse_hotkey('META+R')


    def test_clicks_every_foreground_app_when_unrestricted(self):
        self.assertFalse(self.controller.settings.minecraft_only)
        self.enable()
        self.backend.minecraft=False  # Browser, text editor or any app in focus.
        self.tick(.27)
        self.assertEqual(len(self.backend.clicks),1)
        self.assertEqual(self.controller.status().current_cps,1)

    def test_e_reliably_pauses_universal_mode_even_when_launcher_is_unrecognized(self):
        self.enable()
        self.backend.minecraft=False  # Feather/new launcher not recognised by Win32.
        self.backend.keys={VK_E}
        self.tick(.27)
        self.assertTrue(self.controller.status().inventory_open)
        self.assertEqual(len(self.backend.clicks),0)
        self.backend.keys.clear()
        self.tick(.03)
        self.backend.keys={VK_ESCAPE}
        self.tick(.03)
        self.assertFalse(self.controller.status().inventory_open)
        self.backend.keys.clear()
        self.tick(.22)
        self.assertEqual(len(self.backend.clicks),1)

    def test_e_again_resumes_with_unrecognized_launcher(self):
        self.enable()
        self.backend.minecraft=False
        self.backend.keys={VK_E}
        self.tick(.27)
        self.assertTrue(self.controller.status().inventory_open)
        self.backend.keys.clear()
        self.tick(.03)
        self.backend.keys={VK_E}
        self.tick(.04)
        self.assertFalse(self.controller.status().inventory_open)

    def test_optional_minecraft_only_inventory_scope(self):
        self.controller.change_settings(inventory_global=False)
        self.enable()
        self.backend.minecraft=False
        self.backend.keys={VK_E}
        self.tick(.27)
        self.assertFalse(self.controller.status().inventory_open)
        self.assertEqual(len(self.backend.clicks),1)
        self.backend.keys.clear()
        self.tick(.05)
        self.backend.minecraft=True
        self.backend.keys={VK_E}
        self.tick(.05)
        self.assertTrue(self.controller.status().inventory_open)

    def test_inventory_keeps_user_disabled_setting(self):
        self.controller.change_settings(inventory_pause=False)
        self.enable()
        self.backend.keys={VK_E}
        self.tick(.3)
        self.assertFalse(self.controller.status().inventory_open)
        self.assertEqual(len(self.backend.clicks),1)

    def test_optional_game_restriction_mode(self):
        self.assertFalse(self.controller.settings.minecraft_only)
        self.controller.change_settings(minecraft_only=True)
        self.assertTrue(self.controller.settings.minecraft_only)

    def test_live_cps_counter_counts_successful_clicks_only(self):
        self.enable()
        self.tick(.26)
        self.tick(.1)
        self.tick(.1)
        current=self.controller.status()
        self.assertEqual(current.total_clicks,3)
        self.assertEqual(current.current_cps,3)
        self.tick(1.1)
        self.assertEqual(self.controller.status().current_cps,1)
        self.backend.focused=False
        self.tick(.05)
        self.assertEqual(self.controller.status().current_cps,0)


    def test_sendinput_press_and_release_are_separate(self):
        class MouseInput(ctypes.Structure):
            _fields_=[("dwFlags",ctypes.c_uint32)]
        class Input(ctypes.Structure):
            _fields_=[("type",ctypes.c_uint32),("mi",MouseInput)]
        class FakeAPI:
            def __init__(self): self.flags=[]
            def SendInput(self,count,ptr,size):
                self.flags.append(ctypes.cast(ptr,ctypes.POINTER(Input)).contents.mi.dwFlags)
                return count
        backend=WindowsBackend.__new__(WindowsBackend)
        backend._init_input_state()
        backend.u=FakeAPI()
        backend.Input=Input
        with patch.object(backend._cancelled, 'wait') as sleep:
            backend.click('left')
        self.assertEqual(backend.u.flags,[0x0002,0x0004])
        sleep.assert_called_once_with(.020)
        backend.u.flags.clear()
        with patch.object(backend._cancelled, 'wait'):
            backend.click('right')
        self.assertEqual(backend.u.flags,[0x0008,0x0010])

    def test_old_config_migrates_to_universal_mode_and_persists_cps(self):
        import duckac
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            path.write_text('{"cps":18,"minecraft_only":true,"hotkey":"SHIFT+R"}')
            with patch.object(duckac,'SETTINGS_PATH',path):
                cfg=duckac.load_settings()
                self.assertFalse(cfg.minecraft_only)
                self.assertEqual(cfg.cps,18)
                cfg.minecraft_only=True
                duckac.save_settings(cfg)
                restored=duckac.load_settings()
                # The minimal V5 UI always uses the foreground application.
                self.assertFalse(restored.minecraft_only)
                self.assertEqual(restored.cps,18)

    def test_i_hotkey_overrides_shift_r_without_residual_listener(self):
        self.controller.change_settings(hotkey='I')
        self.assertEqual(self.controller.settings.hotkey,'I')
        # Soltar I, se estava pressionado enquanto o atalho era gravado.
        self.backend.keys.clear()
        self.tick(.04)
        self.backend.keys={VK_SHIFT,ord('R')}
        self.tick(.10)
        self.assertFalse(self.controller.status().enabled, 'Shift+R antigo deve ser ignorado')
        self.backend.keys={ord('I')}
        self.tick(.08)
        self.assertTrue(self.controller.status().enabled)
        self.tick(.07)
        self.assertTrue(self.controller.status().enabled, 'Manter I pressionado nao repete toggle')
        self.backend.keys.clear()
        self.tick(.05)
        self.backend.keys={ord('I')}
        self.tick(.08)
        self.assertFalse(self.controller.status().enabled)

    def test_capture_key_is_not_activated_before_release(self):
        self.backend.keys={ord('I')}
        self.controller.change_settings(hotkey='I')
        self.tick(.07)
        self.assertFalse(self.controller.status().enabled)
        self.backend.keys.clear()
        self.tick(.05)
        self.backend.keys={ord('I')}
        self.tick(.05)
        self.assertTrue(self.controller.status().enabled)

    def test_inventory_hotkey_conflict_blocked(self):
        with self.assertRaisesRegex(ValueError,'inventário'):
            self.controller.change_settings(hotkey='E')
        self.assertEqual(self.controller.settings.hotkey,'SHIFT+R')
        self.controller.change_settings(inventory_pause=False,hotkey='E')
        self.assertEqual(self.controller.settings.hotkey,'E')

    def test_25_cps_scheduled_on_simulated_clock(self):
        self.controller.change_settings(cps=25)
        self.enable()
        self.tick(.30)
        for _ in range(24):
            self.tick(.04)
        self.assertGreaterEqual(len(self.backend.clicks),24)
        self.assertLessEqual(len(self.backend.clicks),25)

    def test_25_cps_with_worker_timing(self):
        class SlowWindowsEventBackend(FakeBackend):
            def click(self,button):
                time.sleep(.020)  # simula o pulso de 20 ms usado a 25 CPS
                super().click(button)
        backend=SlowWindowsEventBackend()
        ctrl=AutoClickController(backend, ClickSettings(cps=25))
        ctrl.start()
        try:
            ctrl.toggle()
            time.sleep(1.7)
            speed=ctrl.status().current_cps
            self.assertGreaterEqual(speed,22, f'25 CPS pedidos, mas houve {speed}')
            self.assertLessEqual(speed,26)
        finally:
            ctrl.stop()

    def test_universal_focus_detects_own_hwnd_without_slow_title_lookups(self):
        class FakeUser32:
            hwnd=123
            def GetForegroundWindow(self):return self.hwnd
            def GetWindowTextW(self,*args):
                raise AssertionError('Consulta lenta ao título em modo universal')
        backend=WindowsBackend.__new__(WindowsBackend)
        backend._init_input_state()
        backend.u=FakeUser32()
        backend._app_hwnd=999
        self.assertTrue(backend.target_focused(False))
        backend.u.hwnd=999
        self.assertFalse(backend.target_focused(False))

    def test_plain_i_bind_persists_settings_file(self):
        import duckac
        with tempfile.TemporaryDirectory() as temp:
            fake=Path(temp)/'settings.json'
            with patch.object(duckac,'SETTINGS_PATH',fake):
                duckac.save_settings(ClickSettings(cps=25,hotkey='I'))
                cfg=duckac.load_settings()
            self.assertEqual(cfg.hotkey,'I')
            self.assertEqual(cfg.cps,25)

    def test_hotkey_validation(self):
        self.assertEqual(parse_hotkey('SHIFT+R'),(ord('R'),(VK_SHIFT,)))
        self.assertEqual(parse_hotkey('F6'),(0x75,()))
        self.assertEqual(parse_hotkey('R'),(ord('R'),()))
        self.assertEqual(parse_hotkey('I'),(ord('I'),()))
        with self.assertRaises(ValueError):
            parse_hotkey('SHIFT+SHIFT+R')
        with self.assertRaises(ValueError):
            virtual_key('INVALID')

if __name__=='__main__':
    unittest.main()
