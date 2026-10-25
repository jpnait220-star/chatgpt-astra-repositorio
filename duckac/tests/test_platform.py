"""Win32 helper contract tests use fake APIs; not a replacement for Windows testing."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckac_platform


class PlatformTests(unittest.TestCase):
    def test_named_mutex_detects_second_copy_and_closes_handle_once(self):
        kernel = SimpleNamespace(CreateMutexW=Mock(return_value=123), CloseHandle=Mock())
        with patch.object(duckac_platform, 'os', SimpleNamespace(name='nt')), \
             patch.object(duckac_platform.ctypes, 'WinDLL', return_value=kernel, create=True), \
             patch.object(duckac_platform.ctypes, 'get_last_error', return_value=183, create=True):
            guard = duckac_platform.SingleInstance()
            self.assertTrue(guard.already_running)
            self.assertEqual(kernel.CreateMutexW.call_args.args[2], 'Local\\DuckAC.SingleInstance.V8')
            guard.close()
            guard.close()
            kernel.CloseHandle.assert_called_once_with(123)

    def test_first_copy_keeps_guard_until_closed(self):
        kernel = SimpleNamespace(CreateMutexW=Mock(return_value=456), CloseHandle=Mock())
        with patch.object(duckac_platform, 'os', SimpleNamespace(name='nt')), \
             patch.object(duckac_platform.ctypes, 'WinDLL', return_value=kernel, create=True), \
             patch.object(duckac_platform.ctypes, 'get_last_error', return_value=0, create=True):
            guard = duckac_platform.SingleInstance()
            self.assertFalse(guard.already_running)
            kernel.CloseHandle.assert_not_called()
            guard.close()
            kernel.CloseHandle.assert_called_once_with(456)

    def test_non_windows_preview_does_not_call_win32(self):
        with patch.object(duckac_platform, 'os', SimpleNamespace(name='posix')):
            guard = duckac_platform.SingleInstance()
            self.assertFalse(guard.already_running)
            guard.close()


if __name__ == '__main__':
    unittest.main()
