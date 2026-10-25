"""DuckAC: Windows click engine supporting all foreground applications by default.

Python stdlib only. The app does not hook or change Minecraft's memory.
"""
from __future__ import annotations

import ctypes
import os
import threading
import time
from dataclasses import dataclass
from collections import deque
from typing import Optional

# Virtual-key codes used by GetAsyncKeyState.
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_E = 0x45
VK_F12 = 0x7B


class ClickMeter:
    """Count completed events in a trailing one-second window, never requested CPS."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.times = deque()
        self.total = 0

    def record(self, now=None):
        self.times.append(self.clock() if now is None else now)
        self.total += 1

    def rate(self, now=None):
        now = self.clock() if now is None else now
        while self.times and now - self.times[0] >= 1.0 - 1e-9:
            self.times.popleft()
        return len(self.times)

    def clear_window(self):
        self.times.clear()


def virtual_key(name: str) -> int:
    key = str(name).upper().strip()
    if len(key) == 1 and ("A" <= key <= "Z" or "0" <= key <= "9"):
        return ord(key)
    if key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 12:
        return 0x6F + int(key[1:])
    special = {"SPACE": 0x20, "TAB": 0x09, "INSERT": 0x2D, "DELETE": 0x2E,
               "HOME": 0x24, "END": 0x23, "PAGEUP": 0x21, "PAGEDOWN": 0x22}
    if key not in special:
        raise ValueError(f"Tecla não suportada: {key}")
    return special[key]


def parse_hotkey(value: str) -> tuple[int, tuple[int, ...]]:
    parts = [x.strip().upper() for x in str(value).split("+")]
    if not parts or any(not p for p in parts):
        raise ValueError("Atalho inválido")
    key = parts[-1]
    mapping = {"SHIFT": VK_SHIFT, "CTRL": VK_CONTROL, "ALT": VK_MENU}
    if any(p not in mapping for p in parts[:-1]):
        raise ValueError("Use Shift, Ctrl ou Alt com uma tecla")
    modifiers = tuple(mapping[p] for p in parts[:-1])
    if len(set(modifiers)) != len(modifiers):
        raise ValueError("Modificador repetido")
    code = virtual_key(key)
    if code == VK_F12:
        raise ValueError('F12 é reservado para parar o autoclique')
    # Aceitar também uma única letra (ex.: I) ou tecla F. Apenas o atalho
    # configurado fica ativo; mudar a combinação desativa a anterior.
    return code, modifiers


@dataclass
class ClickSettings:
    cps: int = 10
    mouse_button: str = "left"
    hotkey: str = "SHIFT+R"
    inventory_key: str = "E"
    inventory_pause: bool = True
    minecraft_only: bool = False
    inventory_global: bool = True  # V4: E / Esc funcionam em qualquer jogo/app em foco.

    def normalize(self) -> None:
        self.cps = max(1, min(25, int(self.cps)))
        if self.mouse_button not in ("left", "right", "middle"):
            self.mouse_button = "left"
        code, modifiers = parse_hotkey(self.hotkey)
        names = {VK_CONTROL: 'CTRL', VK_MENU: 'ALT', VK_SHIFT: 'SHIFT'}
        self.hotkey = '+'.join([names[m] for m in (VK_CONTROL, VK_MENU, VK_SHIFT)
                                if m in modifiers] + [str(self.hotkey).split('+')[-1].strip().upper()])
        virtual_key(self.inventory_key)
        self.inventory_key = self.inventory_key.strip().upper()
        self.inventory_pause = bool(self.inventory_pause)
        self.minecraft_only = bool(self.minecraft_only)
        self.inventory_global = bool(self.inventory_global)
        if self.inventory_pause and (code, modifiers) == (virtual_key(self.inventory_key), ()):
            raise ValueError('O atalho não pode ser igual à tecla do inventário')


def is_minecraft_target(title: str, exe: str) -> bool:
    """Avoid clicking browser tabs whose titles mention Minecraft."""
    title, exe = title.lower(), exe.lower()
    if exe in ("minecraft.windows.exe", "minecraft.exe"):
        return True
    if exe in ("chrome.exe", "msedge.exe", "firefox.exe", "opera.exe",
               "opera_gx.exe", "brave.exe", "iexplore.exe"):
        return False
    # Minecraft Java and game clients typically render through a Java process.
    if exe in ("javaw.exe", "java.exe"):
        return any(name in title for name in ("minecraft", "feather", "lunar", "badlion", "laby"))
    return "minecraft" in title and any(tag in exe for tag in
        ("feather", "lunarclient", "badlion", "labymod", "multimc"))


class WindowsBackend:
    """All low-level Windows APIs are isolated for easier testing."""

    def __init__(self):
        if os.name != "nt":
            raise OSError("O autoclique do DuckAC funciona no Windows 10 ou 11")
        from ctypes import wintypes as wt

        self.u = ctypes.windll.user32
        self.k = ctypes.windll.kernel32
        self.u.GetAsyncKeyState.argtypes = (ctypes.c_int,)
        self.u.GetAsyncKeyState.restype = ctypes.c_short
        self.u.GetForegroundWindow.restype = wt.HWND
        self.u.GetAncestor.argtypes = (wt.HWND, ctypes.c_uint)
        self.u.GetAncestor.restype = wt.HWND
        self.u.GetCursorPos.argtypes = (ctypes.POINTER(wt.POINT),)
        self.u.GetCursorPos.restype = wt.BOOL
        self.u.WindowFromPoint.argtypes = (wt.POINT,)
        self.u.WindowFromPoint.restype = wt.HWND
        self._app_child_hwnd = None
        self._app_hwnd = None
        self.u.GetWindowTextW.argtypes = (wt.HWND, wt.LPWSTR, ctypes.c_int)
        self.u.GetWindowThreadProcessId.argtypes = (wt.HWND, ctypes.POINTER(wt.DWORD))
        self.k.OpenProcess.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
        self.k.OpenProcess.restype = wt.HANDLE
        self.k.QueryFullProcessImageNameW.argtypes = (wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
        self.k.QueryFullProcessImageNameW.restype = wt.BOOL
        self.k.CloseHandle.argtypes = (wt.HANDLE,)

        class MouseInput(ctypes.Structure):
            _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                        ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        class KeybdInput(ctypes.Structure):
            _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                        ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        class HardwareInput(ctypes.Structure):
            _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]

        class InputUnion(ctypes.Union):
            _fields_ = [("mi", MouseInput), ("ki", KeybdInput), ("hi", HardwareInput)]

        class Input(ctypes.Structure):
            _anonymous_ = ("u",)
            _fields_ = [("type", wt.DWORD), ("u", InputUnion)]

        self.Input = Input
        self._init_input_state()
        # Windows default timer granularity can undershoot 25 CPS noticeably.
        self._timer_granularity_set=False
        try:
            self._winmm=ctypes.WinDLL('winmm')
            self._timer_granularity_set=self._winmm.timeBeginPeriod(1)==0
        except (AttributeError, OSError):
            self._timer_granularity_set=False
        self.u.SendInput.argtypes = (wt.UINT, ctypes.POINTER(Input), ctypes.c_int)
        self.u.SendInput.restype = wt.UINT
        self._cached_pid = None
        self._cached_name = ""
        self._pid_checked_at = 0.0

    def _init_input_state(self):
        self._input_lock = threading.RLock()
        self._cancelled = threading.Event()
        self._closed = False
        self._pressed = None
        self._app_child_hwnd = None

    def close(self):
        self._closed = True
        self.cancel()
        if getattr(self,'_timer_granularity_set',False):
            self._winmm.timeEndPeriod(1)
            self._timer_granularity_set=False

    def arm(self):
        with self._input_lock:
            if not self._closed:
                self._cancelled.clear()

    def _send(self, flag):
        event = self.Input()
        event.type = 0
        event.mi.dwFlags = flag
        return self.u.SendInput(1, ctypes.byref(event), ctypes.sizeof(self.Input)) == 1

    def _release(self):
        if self._pressed is None:
            return True
        for _ in range(3):
            if self._send(self._pressed):
                self._pressed = None
                return True
        return False

    def cancel(self):
        self._cancelled.set()
        with self._input_lock:
            self._release()

    def set_app_window(self, hwnd: int) -> None:
        """Register DuckAC's top-level HWND to exclude only its own window.

        Reading the foreground window title on every tick can be very slow in
        some full-screen games; comparing the handle itself is cheap.
        """
        self._app_child_hwnd = int(hwnd)
        root = self.u.GetAncestor(int(hwnd), 2)  # GA_ROOT
        self._app_hwnd = int(root or hwnd)

    def pointer_over_panel(self):
        """Check current wrapper HWND: Tk can recreate it after minimize/restore.

        Foreground alone is insufficient: moving onto the slider need not focus
        this window. The CPS tester remains an intentional click target.
        """
        child = self._app_child_hwnd
        if child is None:
            return False
        from ctypes import wintypes as wt
        panel = self.u.GetAncestor(child, 2)
        if not panel:
            return True  # Fail closed while the window is being recreated.
        self._app_hwnd = int(panel)
        point = wt.POINT()
        if not self.u.GetCursorPos(ctypes.byref(point)):
            return True
        under_pointer = self.u.WindowFromPoint(point)
        return bool(under_pointer and self.u.GetAncestor(under_pointer, 2) == panel)

    def key_down(self, code: int) -> bool:
        return bool(self.u.GetAsyncKeyState(code) & 0x8000)

    def foreground_info(self) -> tuple[str, str]:
        from ctypes import wintypes as wt
        hwnd = self.u.GetForegroundWindow()
        if not hwnd:
            return "", ""
        buffer = ctypes.create_unicode_buffer(320)
        self.u.GetWindowTextW(hwnd, buffer, len(buffer))
        title = buffer.value.lower()
        pid = wt.DWORD()
        self.u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        now = time.monotonic()
        if pid.value != self._cached_pid or now - self._pid_checked_at > 1.0:
            self._cached_pid = pid.value
            self._pid_checked_at = now
            self._cached_name = ""
            handle = self.k.OpenProcess(0x1000, False, pid.value)
            if handle:
                try:
                    path = ctypes.create_unicode_buffer(1024)
                    size = wt.DWORD(len(path))
                    if self.k.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                        self._cached_name = os.path.basename(path.value).lower()
                finally:
                    self.k.CloseHandle(handle)
        return title, self._cached_name

    def inventory_context(self) -> bool:
        """Inventory key must affect the clicker only while playing Minecraft."""
        return is_minecraft_target(*self.foreground_info())

    def target_focused(self, minecraft_only: bool) -> bool:
        if self.pointer_over_panel():
            return False
        if not minecraft_only:
            # Only a constant-time HWND query on each tick: no title lookup.
            hwnd = self.u.GetForegroundWindow()
            if not hwnd:
                return False
            if self._app_hwnd is not None:
                return int(hwnd) != self._app_hwnd
            # Safety fallback for programmatic use outside the DuckAC GUI.
            title = ctypes.create_unicode_buffer(128)
            self.u.GetWindowTextW(hwnd, title, len(title))
            return not title.value.lower().startswith('duckac')
        title, exe = self.foreground_info()
        if not title and not exe:
            return False
        if title.startswith('duckac'):
            return False
        return is_minecraft_target(title, exe)

    def click(self, mouse_button: str, hold_seconds: float = 0.020) -> None:
        # Some applications poll mouse state once per frame. A DOWN and UP in
        # one batch can occur between frames and be ignored by the game.
        # Send separately with a short hold, in the worker thread (never UI).
        down_flag, up_flag = {'left':(0x0002,0x0004), 'right':(0x0008,0x0010),
                              'middle':(0x0020,0x0040)}[mouse_button]
        with self._input_lock:
            if self._closed or self._cancelled.is_set() or self.pointer_over_panel():
                return False
            if not self._send(down_flag):
                raise OSError("O Windows não aceitou o pressionamento do mouse")
            self._pressed = up_flag
        try:
            # At 25 CPS: 20 ms down + 20 ms released, rather than a 12 ms
            # pulse easily missed by applications polling at 60 frames/s.
            self._cancelled.wait(hold_seconds)
        finally:
            with self._input_lock:
                released = self._release()
        if not released:
            raise OSError("O Windows não aceitou a liberação do botão do mouse")
        return True


@dataclass(frozen=True)
class Status:
    enabled: bool = False
    inventory_open: bool = False
    in_target: bool = False
    total_clicks: int = 0
    error: str = ""
    current_cps: int = 0

    @property
    def label(self) -> str:
        if self.error:
            return "ERRO"
        if not self.enabled:
            return "DESATIVADO"
        if self.inventory_open:
            return "PAUSADO · INVENTÁRIO"
        if not self.in_target:
            return "PAUSADO · OUTRA JANELA"
        return "AUTOCLIQUE ATIVO"


class AutoClickController:
    def __init__(self, backend: WindowsBackend, settings: ClickSettings, clock=time.monotonic):
        self.backend = backend
        self.settings = settings
        self.settings.normalize()
        self._clock = clock
        self._lock = threading.RLock()
        self._enabled = False
        self._inventory_open = False
        self._in_target = False
        self._total_clicks = 0
        self._meter = ClickMeter(clock)
        self._error = ""
        self._grace_until = 0.0
        self._next_click_at = 0.0
        self._last_focus = False
        # Consultas frequentes ao jogo/janela podem bloquear por dezenas de ms.
        # No Windows, reconsultar foco periodicamente, sem atrasar cada clique.
        self._focus_cache_seconds = (0.075 if isinstance(backend, WindowsBackend)
                                     else getattr(backend, 'focus_cache_seconds', 0.0))
        self._focus_checked_at = float('-inf')
        self._focus_cached = False
        self._stop = threading.Event()
        self._hotkey_was_down = False
        self._hotkey_wait_for_release = False
        self._capturing_hotkey = False
        self._inventory_was_down = False
        self._escape_was_down = False
        self._thread: Optional[threading.Thread] = None
        self._heartbeat = None

    def heartbeat(self):
        self._heartbeat = self._clock()

    def deactivate(self):
        with self._lock:
            self._enabled = False
            self._inventory_open = False
            self._meter.clear_window()
        if hasattr(self.backend, 'cancel'):
            try:
                self.backend.cancel()
            except Exception as error:
                self._error = str(error)

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._work, daemon=True, name="DuckAC-Input")
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.deactivate()
        if hasattr(self.backend,'close'):
            try:
                self.backend.close()
            except Exception as error:
                self._error = str(error)
        if self._thread and self._thread.is_alive():
            if self._thread is not threading.current_thread():
                self._thread.join(timeout=1.2)

    def status(self) -> Status:
        with self._lock:
            measured = self._meter.rate()
            current = measured if (self._enabled and self._in_target
                         and not self._inventory_open and not self._error) else 0
            return Status(self._enabled, self._inventory_open, self._in_target,
                          self._total_clicks, self._error, current)

    def toggle(self):
        with self._lock:
            if self._capturing_hotkey or self._stop.is_set():
                return
            self._enabled = not self._enabled
            self._inventory_open = False
            self._error = ""
            self._meter.clear_window()
            self._grace_until = self._clock() + 0.18
            self._next_click_at = 0.0
            if self._enabled and hasattr(self.backend, 'arm'):
                self.backend.arm()
            elif not self._enabled and hasattr(self.backend, 'cancel'):
                self.backend.cancel()

    def change_settings(self, **kwargs):
        with self._lock:
            changed = {**self.settings.__dict__, **kwargs}
            settings = ClickSettings(**changed)
            settings.normalize()
            if settings.inventory_pause and parse_hotkey(settings.hotkey) == (
                    virtual_key(settings.inventory_key), ()):
                raise ValueError('O atalho não pode ser igual à tecla do inventário')
            old_hotkey = self.settings.hotkey
            old_cps = self.settings.cps
            self.settings = settings
            if settings.hotkey != old_hotkey:
                # O clique em I que termina a gravação não deve ativar o bot.
                # Ignore essa tecla até ela ser solta. O atalho antigo sai na hora.
                self._hotkey_wait_for_release = True
                self._hotkey_was_down = False
                self._enabled = False
                self._meter.clear_window()
            if settings.cps != old_cps:
                self._next_click_at = 0.0
                self._meter.clear_window()
            self._inventory_open = False if not settings.inventory_pause else self._inventory_open
            self._grace_until = self._clock() + 0.15

    def set_hotkey_capture(self, capturing: bool):
        self.deactivate()
        with self._lock:
            self._capturing_hotkey = capturing
            self._enabled = False
            self._meter.clear_window()
            self._hotkey_wait_for_release = True
            self._hotkey_was_down = False
            self._next_click_at = 0.0

    def _tick(self, now: float) -> None:
        """Never hold the UI state lock while calling Windows APIs.

        Some drivers can stall a process/window query. Previously _refresh on
        Tk's main thread waited for _lock while GetForegroundWindow/OpenProcess
        was running here, making Windows mark DuckAC as Not Responding.
        """
        if self._stop.is_set():
            return
        if self.backend.key_down(VK_F12) or (self._heartbeat is not None and now-self._heartbeat > 1.5):
            self.deactivate()
            self._hotkey_wait_for_release = True
            return
        with self._lock:
            cfg = self.settings
            self._meter.rate(now)
        key, mods = parse_hotkey(cfg.hotkey)
        # Win32 calls are deliberately outside the state mutex.
        key_pressed = self.backend.key_down(key)
        # Exact modifier match: plain R must not also accept the old Shift+R.
        active = key_pressed and all(self.backend.key_down(k) == (k in mods)
                                    for k in (VK_SHIFT, VK_CONTROL, VK_MENU))
        focus_ttl = self._focus_cache_seconds if cfg.minecraft_only else 0.0
        if now-self._focus_checked_at >= focus_ttl:
            focused = self.backend.target_focused(cfg.minecraft_only)
            self._focus_cached = bool(focused)
            self._focus_checked_at = now
        else:
            focused = self._focus_cached
        inventory_pressed = self.backend.key_down(virtual_key(cfg.inventory_key))
        esc_pressed = self.backend.key_down(VK_ESCAPE)
        # V3 required Minecraft detection even in universal mode. Third-party
        # launchers / mods often don't look like Minecraft in Win32 process data;
        # this prevented E from pausing the clicker entirely. Global inventory
        # handling is now the reliable default, with an optional Minecraft-only
        # scope for people who type in other apps while the clicker is enabled.
        inventory_scope_ok = cfg.inventory_global or (
            bool(self.backend.inventory_context())
            if cfg.inventory_pause and (inventory_pressed or esc_pressed)
            else False
        )

        do_click = False
        with self._lock:
            # The UI may replace settings while a Win32 query is in flight.
            # Never apply input collected for the previous configuration.
            if cfg is not self.settings or self._stop.is_set():
                return
            if self._capturing_hotkey:
                self._in_target = focused
                self._hotkey_was_down = False
                return
            if self._hotkey_wait_for_release:
                if not key_pressed:
                    self._hotkey_wait_for_release = False
                self._hotkey_was_down = active
            else:
                if active and not self._hotkey_was_down:
                    self.toggle()
                    self._grace_until = now + 0.20
                    self._next_click_at = 0
                self._hotkey_was_down = active

            self._in_target = focused
            if self._enabled and cfg.inventory_pause and focused and inventory_scope_ok:
                if inventory_pressed and not self._inventory_was_down and not active:
                    self._inventory_open = not self._inventory_open
                    self._grace_until = now + 0.2
                if esc_pressed and not self._escape_was_down and self._inventory_open:
                    self._inventory_open = False
                    self._grace_until = now + 0.2
            self._inventory_was_down = inventory_pressed
            self._escape_was_down = esc_pressed
            if focused and not self._last_focus:
                self._grace_until = now + 0.18
            self._last_focus = focused

            if not self._enabled or not focused or self._inventory_open or now < self._grace_until:
                if not focused or self._inventory_open:
                    self._meter.clear_window()
                self._next_click_at = now
                return
            if now >= self._next_click_at:
                period = 1.0 / cfg.cps
                # Keep the original click phase to prevent CPS dropping due
                # to accumulating 1-9ms polling jitter at each click.
                if self._next_click_at <= 0 or now-self._next_click_at > period:
                    self._next_click_at = now+period
                else:
                    self._next_click_at += period
                do_click = True

        if not do_click:
            return
        # A queued click must not use a replaced hotkey/configuration.
        with self._lock:
            if cfg is not self.settings or not self._enabled or self._capturing_hotkey or self._stop.is_set():
                return
        try:
            if isinstance(self.backend, WindowsBackend):
                sent = self.backend.click(cfg.mouse_button, min(0.050, 0.5 / cfg.cps))
            else:
                sent = self.backend.click(cfg.mouse_button)
        except Exception as exc:
            with self._lock:
                self._error = str(exc)
                self._enabled = False
            if hasattr(self.backend, 'cancel'):
                self.backend.cancel()
            return
        with self._lock:
            if sent is False or self._stop.is_set():
                return
            self._total_clicks += 1
            self._meter.record(self._clock())

    def _work(self):
        while not self._stop.is_set():
            now = self._clock()
            try:
                self._tick(now)
            except Exception as e:
                with self._lock:
                    self._error = str(e)
                    self._enabled = False
            # Short and adaptive poll helps keep 25 CPS close to target,
            # while the UI remains independent on its own thread.
            with self._lock:
                enabled=self._enabled
                deadline=self._next_click_at
            if enabled:
                remaining=max(0.0,deadline-self._clock())
                self._stop.wait(min(0.001,remaining) if remaining else 0.001)
            else:
                self._stop.wait(0.004)
