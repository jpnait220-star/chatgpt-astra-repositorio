"""Cursor/window routing regressions; all Win32 input is simulated."""
import ctypes
import unittest
from ctypes import wintypes as wt
from test_lifecycle import native_backend


class PanelGuardTests(unittest.TestCase):
    def make_backend(self):
        backend = native_backend()
        backend._app_child_hwnd = 10
        backend._app_hwnd = 100
        backend.u.panel = 100
        backend.u.under = 11
        backend.u.foreground = 200
        backend.u.GetAncestor = lambda hwnd, _: backend.u.panel if hwnd in (10, 11) else hwnd
        backend.u.GetForegroundWindow = lambda: backend.u.foreground
        backend.u.WindowFromPoint = lambda point: backend.u.under
        def cursor(ptr):
            point = ctypes.cast(ptr, ctypes.POINTER(wt.POINT)).contents
            point.x, point.y = 200, 247
            return True
        backend.u.GetCursorPos = cursor
        return backend

    def test_panel_blocks_input_even_when_other_app_has_focus(self):
        b = self.make_backend()
        self.assertFalse(b.target_focused(False))
        self.assertFalse(b.click('left', 0))
        self.assertEqual(b.u.flags, [])

    def test_pointer_enters_panel_after_focus_query(self):
        b = self.make_backend()
        b.u.under = 200
        self.assertTrue(b.target_focused(False))
        b.u.under = 11
        self.assertFalse(b.click('middle', 0))
        self.assertEqual(b.u.flags, [])

    def test_recreated_wrapper_and_missing_wrapper_fail_closed(self):
        b = self.make_backend()
        b.u.panel = 300
        self.assertTrue(b.pointer_over_panel())
        self.assertEqual(b._app_hwnd, 300)
        b.u.panel = 0
        self.assertFalse(b.click('left', 0))
        self.assertEqual(b.u.flags, [])

    def test_external_window_and_cps_tester_still_receive_input(self):
        b = self.make_backend()
        for target in (200, 400):
            b.u.under = target
            self.assertTrue(b.target_focused(False))
            self.assertTrue(b.click('middle', 0))
        self.assertEqual(b.u.flags, [32, 64, 32, 64])

    def test_failed_cursor_query_does_not_send_input(self):
        b = self.make_backend()
        b.u.GetCursorPos = lambda _: False
        self.assertFalse(b.click('left', 0))
        self.assertEqual(b.u.flags, [])
