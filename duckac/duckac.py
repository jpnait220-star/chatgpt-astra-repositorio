"""DuckAC V9: compact dark UI, replaceable hotkey and honest CPS meters."""
from __future__ import annotations

import json
import logging
import os
import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox
from pathlib import Path

from duckac_engine import (AutoClickController, ClickMeter, ClickSettings, WindowsBackend,
                           virtual_key)
from duckac_platform import SingleInstance, enable_dpi_awareness, show_in_taskbar

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
APPDATA = Path(os.getenv('APPDATA') or Path.home()) / 'DuckAC'
SETTINGS_PATH = APPDATA / 'settings.json'
W, H = 560, 592
BG = '#0B0E14'; TOP = '#111620'; CARD = '#151B26'; LIGHT = '#222B3A'
STROKE = '#303A4C'; INK = '#F4F5F7'; MUTED = '#9BA6B9'; ACCENT = '#FFDB62'
GREEN = '#88E0B1'; RED = '#FF939C'; FONT = 'Segoe UI'


def load_settings():
    # Preserve a valid custom hotkey even if an unrelated setting is damaged.
    cfg = ClickSettings(cps=25)
    try:
        obj = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return cfg
    if not isinstance(obj, dict):
        return cfg
    for key in ('cps', 'mouse_button', 'inventory_key', 'inventory_pause', 'hotkey'):
        if key not in obj:
            continue
        candidate = ClickSettings(**{**vars(cfg), key: obj[key]})
        try:
            candidate.normalize()
        except (ValueError, TypeError, AttributeError):
            continue
        cfg = candidate
    return cfg


def save_settings(cfg):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps({**vars(cfg), 'config_version': 9}, ensure_ascii=False, indent=2),
                   encoding='utf-8')
    tmp.replace(SETTINGS_PATH)


def rounded(c, x, y, w, h, r, fill, outline=None, width=1):
    r = max(2, min(r, w/2, h/2))
    pts = [x+r,y,x+w-r,y,x+w,y,x+w,y+r,x+w,y+h-r,x+w,y+h,
           x+w-r,y+h,x+r,y+h,x,y+h,x,y+h-r,x,y+r,x,y]
    return c.create_polygon(pts, fill=fill, outline=outline or fill, width=width,
                            smooth=True, splinesteps=20, tags='frame')


class DuckApp:
    def __init__(self, root, engine):
        self.root, self.engine = root, engine
        self.hover = None
        self.actions = []
        self.dragging = False
        self.window_drag = None
        self.capture = False
        self.toast = ''
        self.save_timer = None
        self.refresh_timer = None
        self.last_state = None
        self.tester = None
        self.closed = False
        self.minimized = False
        families = {name.casefold():name for name in tkfont.families(root)}
        self.font = next((families[name.casefold()] for name in
                          (FONT, 'Arial', 'DejaVu Sans', 'Helvetica', 'Nimbus Sans L')
                          if name.casefold() in families), 'TkDefaultFont')
        root.title('DuckAC V9')
        root.geometry(f'{W}x{H}')
        root.resizable(False, False)
        root.configure(bg=BG)
        root.overrideredirect(True)  # Custom title bar on Windows 10 and 11.
        try:
            self.icon_image = tk.PhotoImage(file=str(BASE/'assets'/'duckac.png'))
            root.iconphoto(True, self.icon_image)
            if os.name == 'nt':
                root.iconbitmap(str(BASE/'assets'/'duckac.ico'))
        except (OSError, tk.TclError):
            pass
        self.canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Motion>', self.mouse_motion)
        self.canvas.bind('<Leave>', self.mouse_leave)
        self.canvas.bind('<Button-1>', self.mouse_click)
        self.canvas.bind('<B1-Motion>', self.mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_release)
        root.bind_all('<KeyPress>', self.capture_key, add='+')
        root.bind('<Map>', self.restore_window, add='+')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<Destroy>', self.on_destroy, add='+')
        root.bind('<Alt-F4>', lambda event: self.close(), add='+')
        root.report_callback_exception = self.callback_error
        self.mouse_images = {(key, bool(active)):tk.PhotoImage(file=str(BASE/'assets'/f'mouse-{key}-{active}.png'))
                             for key in ('left','right','middle') for active in (0,1)}
        self.render()
        root.update_idletasks()
        self.register_window()
        self.engine.heartbeat()
        self.engine.start()
        self.refresh_timer = root.after(100, self.refresh)

    def register_window(self):
        show_in_taskbar(self.root)
        if hasattr(self.engine.backend, 'set_app_window'):
            self.engine.backend.set_app_window(self.root.winfo_id())

    def minimize(self):
        if self.capture:
            self.cancel_capture()
        self.minimized = True
        self.root.overrideredirect(False)
        self.root.iconify()

    def restore_window(self, event):
        if event.widget is self.root and self.minimized and self.root.state() == 'normal':
            self.minimized = False
            self.root.overrideredirect(True)
            self.root.after_idle(self.register_window)

    def txt(self, x, y, text, size=14, bold=False, color=INK, anchor='nw'):
        # Pixel fonts share the same coordinate system as canvas icons/controls.
        return self.canvas.create_text(x, y, text=str(text),
            font=(self.font, -size, 'bold' if bold else 'normal'), fill=color, anchor=anchor,
            tags='frame')

    def action(self, name, x, y, w, h, callback):
        self.actions.append((name, (x, y, x+w, y+h), callback))

    def card(self, x, y, w, h):
        rounded(self.canvas, x, y, w, h, 16, CARD, STROKE)

    def button(self, name, x, y, w, h, label, fn, primary=False, disabled=False):
        color = '#181E29' if disabled else ACCENT if primary else LIGHT
        if self.hover == name and not disabled:
            color = '#FFE791' if primary else '#303C50'
        rounded(self.canvas, x, y, w, h, 11, color, STROKE)
        if label in ('+', '−'):
            cx, cy = x+w/2, y+h/2
            self.canvas.create_line(cx-6, cy, cx+6, cy, fill=INK, width=2, tags='frame')
            if label == '+':
                self.canvas.create_line(cx, cy-6, cx, cy+6, fill=INK, width=2, tags='frame')
        else:
            self.txt(x+w/2, y+h/2, label, 15, True, MUTED if disabled else '#171A22' if primary else INK, 'center')
        if not disabled:
            self.action(name, x, y, w, h, fn)

    def draw_mouse(self, x, y, selected, active=False):
        self.canvas.create_image(x, y, image=self.mouse_images[(selected, active)], tags='frame')
        name = {'left':'ESQUERDO', 'right':'DIREITO', 'middle':'BOTÃO DO MEIO'}[selected]
        self.txt(x, y+89, name, 10, True, ACCENT, 'center')

    def render(self):
        c = self.canvas
        c.delete('frame')
        self.actions = []
        cfg, stat = self.engine.settings, self.engine.status()
        c.create_rectangle(0, 0, W-1, H-1, fill=BG, outline=STROKE, tags='frame')
        c.create_rectangle(1, 1, W-2, 45, fill=TOP, outline='', tags='frame')
        rounded(c, 17, 13, 21, 21, 6, ACCENT)
        self.txt(27, 23, 'D', 14, True, '#151922', 'center')
        self.txt(48, 23, 'DuckAC', 18, True, INK, 'w')
        self.txt(131, 24, 'V9', 11, True, MUTED, 'w')
        if self.hover == 'close':
            rounded(c, 514, 6, 39, 33, 7, '#70303D')
        elif self.hover == 'minimize':
            rounded(c, 470, 6, 39, 33, 7, '#303B50')
        c.create_line(484, 25, 496, 25, fill=INK, width=2, tags='frame')
        c.create_line(528, 17, 540, 29, fill=INK, width=2, tags='frame')
        c.create_line(540, 17, 528, 29, fill=INK, width=2, tags='frame')
        self.action('minimize', 470, 5, 40, 35, self.minimize)
        self.action('close', 514, 5, 40, 35, self.close)

        self.txt(22, 63, 'Um clique. No seu ritmo.', 20, True)
        self.txt(22, 92, 'Esquerdo, direito ou meio. Controle total pelo teclado.', 12, color=MUTED)
        self.card(18, 121, 524, 212)
        self.txt(36, 141, 'VELOCIDADE', 11, True, MUTED)
        self.button('cps_down', 36, 174, 40, 43, '−', lambda:self.cps_change(-1))
        self.txt(151, 196, cfg.cps, 42, True, ACCENT, 'center')
        self.button('cps_up', 230, 174, 40, 43, '+', lambda:self.cps_change(1))
        self.txt(291, 197, 'CPS', 15, True, MUTED, 'w')
        start, end, y = 40, 335, 247
        c.create_line(start, y, end, y, fill='#303B50', width=8, capstyle='round', tags='frame')
        selected = start+(end-start)*(cfg.cps-1)/24
        c.create_line(start, y, selected, y, fill=ACCENT, width=8, capstyle='round', tags='frame')
        c.create_oval(selected-9, y-9, selected+9, y+9, fill=LIGHT, outline='#FFEBAB', width=2, tags='frame')
        self.action('slider', start-9, y-18, end-start+18, 36, self.cps_slide)
        self.txt(start, 264, '1 CPS', 10, color=MUTED)
        self.txt(end, 264, '25 CPS', 10, color=MUTED, anchor='ne')
        self.txt(36, 305, f'Enviados: {stat.current_cps} CPS', 13, True, GREEN if stat.enabled else MUTED, 'w')
        self.txt(337, 305, f'Total: {stat.total_clicks:,}'.replace(',', '.'), 12, color=MUTED, anchor='e')
        c.create_line(364, 141, 364, 312, fill=STROKE, tags='frame')
        self.draw_mouse(451, 213, cfg.mouse_button, stat.enabled and stat.in_target and not stat.inventory_open)

        self.card(18, 345, 252, 85)
        self.txt(36, 361, 'BOTÃO DO MOUSE', 11, True, MUTED)
        for name, label, x in [('left','Esq.',32), ('middle','Meio',110), ('right','Dir.',188)]:
            on = cfg.mouse_button == name
            rounded(c, x, 385, 70, 31, 8, ACCENT if on else LIGHT, STROKE)
            self.txt(x+35, 400.5, label, 12, on, '#171A22' if on else INK, 'center')
            self.action('btn_'+name, x, 385, 70, 31, lambda k=name:self.set_button(k))
        self.card(282, 345, 260, 85)
        self.txt(300, 361, 'ATALHO DE ATIVAÇÃO', 11, True, MUTED)
        rounded(c, 296, 383, 232, 34, 8, '#51462A' if self.capture else LIGHT, STROKE)
        label = 'Pressione uma tecla…' if self.capture else cfg.hotkey.replace('+', ' + ')
        self.txt(412, 400, label, 14, True, INK, 'center')
        self.action('bind', 296, 383, 232, 34, self.start_capture)

        self.card(18, 442, 524, 49)
        on = cfg.inventory_pause
        rounded(c, 34, 455, 21, 21, 5, ACCENT if on else LIGHT, '#69768B')
        if on:
            c.create_line(39, 465, 43, 469, 50, 461, fill=INK, width=2, tags='frame')
        self.txt(66, 466, f'Pausar com {cfg.inventory_key} / Esc', 13, True, INK, 'w')
        self.action('inventory', 27, 448, 304, 36, self.toggle_inventory)
        self.button('test', 359, 452, 169, 29, 'Testar CPS', self.open_tester)

        if stat.error:
            status, color = 'Erro: '+stat.error[:65], RED
        elif self.capture:
            status, color = 'Autoclique parado durante a troca do atalho. Esc cancela.', MUTED
        elif not stat.enabled:
            status, color = 'Parado · pressione '+cfg.hotkey.replace('+', ' + ')+' para ativar', MUTED
        elif stat.inventory_open:
            status, color = 'Pausado · inventário aberto', MUTED
        elif not stat.in_target:
            status, color = 'Ativado · volte à janela em que deseja clicar', MUTED
        else:
            status, color = 'Clicando · '+str(cfg.cps)+' CPS configurados', GREEN
        rounded(c, 18, 495, 524, 29, 12, '#111721', STROKE)
        c.create_oval(30,506,36,512, fill=RED if stat.error else GREEN if stat.enabled else ACCENT,
                      outline='', tags='frame')
        self.txt(280, 509, self.toast or status, 12, True, RED if self.toast else color, 'center')
        self.button('start', 18, 528, 252, 43, 'Iniciar', self.start, True,
                    disabled=stat.enabled or self.capture)
        self.button('stop', 282, 528, 260, 43, 'Parar', self.stop, disabled=not stat.enabled)
        self.txt(280, 582, 'F12 para parar imediatamente · Fechar encerra todos os cliques', 10,
                 color=MUTED, anchor='center')
        self.last_state = (repr(cfg), repr(stat), self.capture, self.hover, self.toast)

    def cps_change(self, delta):
        self.update(cps=max(1, min(25, self.engine.settings.cps+delta)))

    def cps_slide(self, event):
        self.update(cps=round(1+(max(40, min(335, event.x))-40)/295*24))

    def update(self, **values):
        try:
            self.engine.change_settings(**values)
            self.toast = ''
            self.schedule_save()
        except (ValueError, TypeError) as err:
            self.toast = str(err)
        self.render()

    def set_button(self, button): self.update(mouse_button=button)
    def toggle_inventory(self): self.update(inventory_pause=not self.engine.settings.inventory_pause)

    def start(self):
        self.toast = ''
        if not self.engine.status().enabled:
            self.engine.toggle()
        self.render()

    def stop(self):
        self.engine.deactivate()
        if not self.closed:
            self.render()

    def start_capture(self):
        self.capture = True
        self.toast = ''
        self.engine.set_hotkey_capture(True)
        self.canvas.focus_set()
        self.render()

    def cancel_capture(self):
        self.capture = False
        self.engine.set_hotkey_capture(False)
        self.toast = ''
        self.render()

    def capture_key(self, event):
        if not self.capture:
            return
        key = event.keysym.upper()
        if key in ('SHIFT_L','SHIFT_R','CONTROL_L','CONTROL_R','ALT_L','ALT_R','META_L','META_R'):
            return 'break'
        if key == 'ESCAPE':
            self.cancel_capture()
            return 'break'
        key = {'PRIOR':'PAGEUP', 'NEXT':'PAGEDOWN'}.get(key, key)
        try:
            virtual_key(key)
            # Tk on Windows uses Mod5 (0x20000) for Alt; X11 uses Mod1 (0x8).
            alt_mask = 0x20000 if os.name == 'nt' else 0x0008
            mods = []
            for name, mask in [('CTRL', 0x0004), ('ALT', alt_mask), ('SHIFT', 0x0001)]:
                if event.state & mask:
                    mods.append(name)
            bind = '+'.join(mods+[key])
            self.engine.change_settings(hotkey=bind)
            self.capture = False
            self.engine.set_hotkey_capture(False)
            # Persist immediately: closing/minimizing right away cannot lose this binding.
            if self.save_timer:
                self.root.after_cancel(self.save_timer)
                self.save_timer = None
            self.toast = ''
            self.save()
        except ValueError as err:
            self.toast = str(err)
        self.render()
        return 'break'

    def hit(self, x, y):
        for name, (x0,y0,x1,y1), callback in reversed(self.actions):
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name, callback
        return None, None

    def mouse_motion(self, event):
        if self.dragging or self.window_drag:
            return
        name, callback = self.hit(event.x, event.y)
        if name != self.hover:
            self.hover = name
            self.canvas.configure(cursor='hand2' if callback else '')
            self.render()

    def mouse_leave(self, event):
        if self.hover:
            self.hover = None
            self.canvas.configure(cursor='')
            self.render()

    def mouse_click(self, event):
        name, callback = self.hit(event.x, event.y)
        if callback:
            self.dragging = name == 'slider'
            if self.dragging: callback(event)
            else: callback()
        elif event.y < 45:
            self.window_drag = (event.x_root-self.root.winfo_x(), event.y_root-self.root.winfo_y())

    def mouse_drag(self, event):
        if self.dragging:
            self.cps_slide(event)
        elif self.window_drag:
            x, y = event.x_root-self.window_drag[0], event.y_root-self.window_drag[1]
            self.root.geometry(f'+{max(0,x)}+{max(0,y)}')

    def mouse_release(self, event):
        self.dragging = False
        self.window_drag = None

    def schedule_save(self):
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(300, self.save)

    def save(self):
        self.save_timer = None
        try:
            save_settings(self.engine.settings)
        except OSError:
            self.toast = 'Atalho/configuração não salvo: confira a permissão da pasta.'

    def refresh(self):
        if self.closed:
            return
        self.engine.heartbeat()
        current = (repr(self.engine.settings), repr(self.engine.status()), self.capture, self.hover, self.toast)
        if current != self.last_state:
            self.render()
        self.refresh_timer = self.root.after(100, self.refresh)

    def open_tester(self):
        self.stop()
        if self.capture:
            self.cancel_capture()
        if self.tester and self.tester.window.winfo_exists():
            self.tester.window.lift()
        else:
            self.tester = CPSTester(self)

    def close(self):
        if self.closed:
            return
        self.closed = True
        # Stop before touching a child window, timers or the configuration file.
        # A Tcl/save error must never leave the input worker armed.
        try:
            self.engine.stop()
        finally:
            for owner, timer in ((self.root, self.save_timer), (self.root, self.refresh_timer),
                                 (getattr(self.tester, 'window', self.root), getattr(self.tester, 'timer', None))):
                if timer:
                    try:
                        owner.after_cancel(timer)
                    except tk.TclError:
                        pass
            try:
                self.save()
            except Exception:
                logging.exception('Não foi possível salvar ao fechar')
            finally:
                try:
                    self.root.destroy()  # Also destroys the CPS tester.
                except tk.TclError:
                    pass

    def on_destroy(self, event):
        if event.widget is self.root:
            self.closed = True
            self.engine.stop()
            for owner, timer in ((self.root, self.save_timer), (self.root, self.refresh_timer),
                                 (getattr(self.tester, 'window', self.root), getattr(self.tester, 'timer', None))):
                if timer:
                    try:
                        owner.after_cancel(timer)
                    except tk.TclError:
                        pass

    def callback_error(self, kind, value, traceback):
        self.engine.deactivate()
        logging.error('Falha na interface; autoclique desativado', exc_info=(kind,value,traceback))
        self.toast = 'Autoclique parado após erro na interface. Feche e abra novamente.'


class CPSTester:
    """Counts actual Tk button releases received by its target area, not engine ticks."""
    def __init__(self, app):
        self.app = app
        self.window = w = tk.Toplevel(app.root)
        w.title('DuckAC · Teste de CPS')
        w.geometry('480x370')
        w.configure(bg=BG)
        w.resizable(False, False)
        w.overrideredirect(True)
        self.meter = ClickMeter()
        self.drag = None
        header = tk.Frame(w, bg=TOP, height=40)
        header.pack(fill='x')
        label = tk.Label(header, text='DuckAC · Teste de CPS', bg=TOP, fg=INK,
                         font=(app.font, -15, 'bold'), padx=14, pady=10)
        label.pack(side='left')
        tk.Button(header, text='Fechar', command=self.close, bg=TOP, fg=INK,
                  relief='flat', font=(app.font, -13)).pack(side='right', padx=8)
        for widget in (header, label):
            widget.bind('<Button-1>', self.drag_start)
            widget.bind('<B1-Motion>', self.drag_move)
        self.instruction = tk.Label(w, text='Mova o mouse para a área abaixo.\nAtive e pare com '+app.engine.settings.hotkey.replace('+',' + '),
            bg=BG, fg=INK, font=(app.font,-14), pady=12)
        self.instruction.pack()
        self.area = tk.Canvas(w, bg='#27261F', highlightthickness=0, height=190)
        self.area.pack(fill='x', padx=18)
        self.rate_text = self.area.create_text(222, 70, text='0 CPS', fill=ACCENT,
                                               font=(app.font,-42,'bold'))
        self.total_text = self.area.create_text(222, 115, text='Recebidos aqui: 0', fill='#FFF7CC',
                                                font=(app.font,-14))
        self.area.create_text(222, 154, text='Esquerdo, direito ou meio · janela de 1 segundo',
                              fill='#CBC4AC', font=(app.font,-11))
        self.area.bind('<ButtonRelease-1>', self.receive)
        self.area.bind('<ButtonRelease-3>', self.receive)
        self.area.bind('<ButtonRelease-2>', self.receive)
        tk.Button(w, text='Zerar contagem', command=self.reset, bg=LIGHT, fg=INK,
                  relief='flat', font=(app.font,-13), padx=18).pack(pady=9)
        w.protocol('WM_DELETE_WINDOW', self.close)
        self.timer = w.after(100, self.refresh)
        w.lift()

    def drag_start(self, event):
        self.drag = (event.x_root-self.window.winfo_x(), event.y_root-self.window.winfo_y())

    def drag_move(self, event):
        if self.drag:
            self.window.geometry(f'+{max(0,event.x_root-self.drag[0])}+{max(0,event.y_root-self.drag[1])}')

    def receive(self, event):
        self.meter.record()
        return 'break'

    def reset(self):
        self.meter = ClickMeter()

    def refresh(self):
        self.instruction.configure(text='Mova o mouse para a área abaixo.\nAtive e pare com '+
                                   self.app.engine.settings.hotkey.replace('+', ' + '))
        self.area.itemconfigure(self.rate_text, text=f'{self.meter.rate()} CPS')
        self.area.itemconfigure(self.total_text, text=f'Recebidos aqui: {self.meter.total}')
        self.timer = self.window.after(100, self.refresh)

    def close(self):
        self.app.stop()
        try:
            if self.window.winfo_exists():
                self.window.after_cancel(self.timer)
                self.window.destroy()
        except tk.TclError:
            pass
        finally:
            self.app.tester = None


def main():
    if '--check-installation' in sys.argv:
        from duckac_diagnostics import check_installation
        return check_installation(sys.argv[sys.argv.index('--check-installation') + 1])
    preview = '--preview' in sys.argv
    if os.name != 'nt' and not preview:
        print('DuckAC é compatível com Windows 10/11.')
        return 1
    guard = SingleInstance() if not preview else None
    engine = root = None
    try:
        if guard and guard.already_running:
            messagebox.showinfo('DuckAC já está aberto', 'Já existe uma versão do DuckAC aberta.\nFeche a anterior. Se ela ficou oculta, encerre DuckAC_V8.exe no Gerenciador de Tarefas.')
            return 0
        enable_dpi_awareness()
        if preview:
            class Preview:
                def key_down(self, code): return False
                def target_focused(self, mc): return False
                def inventory_context(self): return False
                def click(self, button): raise AssertionError('Preview não envia cliques')
            backend = Preview()
        else:
            backend = WindowsBackend()
        root = tk.Tk()
        engine = AutoClickController(backend, load_settings())
        DuckApp(root, engine)
        root.mainloop()
        return 0
    finally:
        try:
            if engine:
                engine.stop()
        finally:
            if root:
                try:
                    root.destroy()
                except tk.TclError:
                    pass
            if guard:
                guard.close()


if __name__ == '__main__':
    raise SystemExit(main())
