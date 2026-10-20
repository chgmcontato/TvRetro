#!/usr/bin/python3
"""TvRetro Controle: GTK tray remote. No web server, video or background polling."""
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, Gio, GLib, AyatanaAppIndicator3 as Indicator

APP_ID = 'org.tvretro.Remote'
HERE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'tvretro/config.json'
AUTOSTART = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'autostart/tvretro-controle.desktop'
KEYS = {'up': 19, 'down': 20, 'left': 21, 'right': 22, 'ok': 23,
        'home': 3, 'back': 4, 'play': 85, 'volume-up': 24, 'volume-down': 25, 'mute': 164}

def address(value):
    host, sep, port = value.strip().partition(':')
    ipaddress.IPv4Address(host)
    number = int(port) if sep else 5555
    if not 1 <= number <= 65535:
        raise ValueError('Porta inválida')
    return f'{host}:{number}'

class Remote(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='tvretro-adb')
        self.busy = False
        self.connected = False
        self.settings = {'tv': '', 'adb_port': 5037}
        try:
            saved = json.loads(CONFIG.read_text())
            tv = address(saved['tv'])
            adb_port = int(saved.get('adb_port', 5037))
            if not 1 <= adb_port <= 65535:
                raise ValueError('Porta ADB inválida')
            self.settings = {'tv': tv, 'adb_port': adb_port}
        except (OSError, ValueError, KeyError, TypeError):
            pass
        self.adb = shutil.which('adb')
        self.status_message = 'Pronto. A conexão acontece ao enviar um comando.'

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.hold()
        self.status_action = Gio.SimpleAction.new_stateful('status', None, GLib.Variant('s', self.status_message))
        self.add_action(self.status_action)
        for name, callback in [('show', self.show_control), ('quit', self.quit)]:
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', lambda a, p, cb=callback: cb())
            self.add_action(action)
        send = Gio.SimpleAction.new('send', GLib.VariantType.new('s'))
        send.connect('activate', lambda a, p: self.send(p.get_string()))
        self.add_action(send)
        self.indicator = Indicator.Indicator.new('tvretro-controle', str(HERE/'tvretro.svg'), Indicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_title('TvRetro Controle')
        menu = Gtk.Menu()
        def item(label, callback):
            row = Gtk.MenuItem(label=label)
            row.connect('activate', lambda *_: callback())
            menu.append(row)
            return row
        opening = item('Abrir controle', self.show_control)
        menu.append(Gtk.SeparatorMenuItem())
        item('Home da TV', lambda: self.send('home'))
        item('Voltar', lambda: self.send('back'))
        item('Volume +', lambda: self.send('volume-up'))
        item('Volume −', lambda: self.send('volume-down'))
        item('Mudo', lambda: self.send('mute'))
        menu.append(Gtk.SeparatorMenuItem())
        item('Sair', self.quit)
        menu.show_all()
        self.indicator.set_menu(menu)
        self.indicator.set_secondary_activate_target(opening)
        self.indicator.set_status(Indicator.IndicatorStatus.ACTIVE)

    def do_command_line(self, command_line):
        arguments = command_line.get_arguments()[1:]
        if '--quit' in arguments:
            self.quit()
        elif '--background' not in arguments:
            self.activate()
        return 0

    def do_activate(self):
        self.show_control()

    def show_control(self):
        if self.window is None:
            self.build_window()
        self.window.show_all()
        self.window.present()

    def build_window(self):
        self.window = Gtk.ApplicationWindow(application=self, title='TvRetro Controle')
        self.window.set_default_size(350, 505)
        self.window.set_resizable(False)
        self.window.set_icon_from_file(str(HERE/'tvretro.svg'))
        self.window.connect('delete-event', lambda window, event: (window.hide() or True))
        self.window.connect('key-press-event', self.keyboard)
        css = Gtk.CssProvider()
        css.load_from_data(b'''window {background:#111923;color:#edf3fa;} button {background:#263446;color:#f5f8fc;border:1px solid #42536a;border-radius:12px;min-height:42px;font-size:16px;} button:hover,button:focus {background:#4c432d;border-color:#ffd166;} button:active {background:#716034;} .pad {font-size:25px;min-width:76px;min-height:66px;} .title {font-size:24px;font-weight:bold;} .muted {color:#b4c1d1;font-size:12px;} entry {color:#fff;background:#263446;}''')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=18)
        self.window.add(box)
        title = Gtk.Label(label='TvRetro')
        title.get_style_context().add_class('title')
        box.pack_start(title, False, False, 0)
        self.status_label = Gtk.Label(label=self.status_message, wrap=True, max_width_chars=38)
        self.status_label.get_style_context().add_class('muted')
        box.pack_start(self.status_label, False, False, 0)
        pad = Gtk.Grid(row_spacing=7, column_spacing=7, halign=Gtk.Align.CENTER)
        box.pack_start(pad, False, False, 0)
        def button(label, key, grid, x, y, style=None):
            b = Gtk.Button(label=label)
            if style:
                b.get_style_context().add_class(style)
            b.connect('clicked', lambda *_: self.send(key))
            grid.attach(b, x, y, 1, 1)
        for label, key, x, y in [('▲','up',1,0),('◀','left',0,1),('OK','ok',1,1),('▶','right',2,1),('▼','down',1,2)]:
            button(label, key, pad, x, y, 'pad')
        actions = Gtk.Grid(row_spacing=7, column_spacing=7, column_homogeneous=True)
        box.pack_start(actions, False, False, 0)
        for label, key, x, y in [('Home','home',0,0),('Voltar','back',1,0),('▶ / Ⅱ','play',2,0),('Vol −','volume-down',0,1),('Mudo','mute',1,1),('Vol +','volume-up',2,1)]:
            button(label,key,actions,x,y)
        hint = Gtk.Label(label='Setas + Enter para navegar • Esc para voltar\nFechar a janela mantém o ícone na bandeja.', wrap=True)
        hint.get_style_context().add_class('muted')
        box.pack_start(hint, False, False, 0)
        expander = Gtk.Expander(label='Configurações')
        box.pack_start(expander, False, False, 0)
        settings = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7, margin_top=8)
        expander.add(settings)
        self.tv_entry = Gtk.Entry(text=self.settings['tv'], placeholder_text='IP da TV, por exemplo 192.168.1.10')
        settings.pack_start(self.tv_entry, False, False, 0)
        self.startup_check = Gtk.CheckButton(label='Iniciar na bandeja ao entrar no computador')
        self.startup_check.set_active(AUTOSTART.exists())
        settings.pack_start(self.startup_check, False, False, 0)
        save = Gtk.Button(label='Salvar e reconectar')
        save.connect('clicked', self.save_settings)
        settings.pack_start(save, False, False, 0)
        if not self.settings['tv']:
            expander.set_expanded(True)

    def keyboard(self, window, event):
        if isinstance(window.get_focus(), Gtk.Entry):
            return False
        key = {Gdk.KEY_Up:'up',Gdk.KEY_Down:'down',Gdk.KEY_Left:'left',Gdk.KEY_Right:'right',Gdk.KEY_Return:'ok',Gdk.KEY_KP_Enter:'ok',Gdk.KEY_Escape:'back',Gdk.KEY_BackSpace:'back'}.get(event.keyval)
        if key:
            self.send(key)
            return True
        return False

    def set_status(self, message):
        self.status_message = message
        if hasattr(self, 'status_action'):
            self.status_action.set_state(GLib.Variant('s', message))
        if self.window is not None:
            self.status_label.set_text(message)
        return False

    def save_settings(self, button):
        if self.busy:
            self.set_status('Aguarde o comando atual terminar antes de salvar.')
            return
        try:
            self.settings['tv'] = address(self.tv_entry.get_text())
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            temporary = CONFIG.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.settings, indent=2)+'\n')
            temporary.chmod(0o600)
            temporary.replace(CONFIG)
            if self.startup_check.get_active():
                AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
                AUTOSTART.write_text(self.desktop_entry(background=True))
            else:
                AUTOSTART.unlink(missing_ok=True)
            self.connected = False
            self.connect_only()
        except (ValueError, OSError) as e:
            self.set_status('Não foi possível salvar. Confira o IPv4 e a pasta de configuração.')

    @staticmethod
    def desktop_entry(background=False):
        script = str(HERE/'tvretro-tray.py')
        args = ' --background' if background else ''
        return f'[Desktop Entry]\nType=Application\nName=TvRetro Controle\nComment=Controle remoto da TV na bandeja\nExec="{HERE / "launch.sh"}"{args}\nIcon={HERE / "tvretro.svg"}\nTerminal=false\nCategories=Utility;\nStartupNotify=false\n'

    def connect_only(self):
        self.send(None)

    def send(self, key):
        if key is not None and key not in KEYS:
            return
        if self.busy:
            return
        if not self.adb:
            self.set_status('ADB não encontrado. Instale Android Platform Tools.')
            self.show_control()
            return
        try:
            tv = address(self.settings['tv'])
        except (ValueError, TypeError):
            self.set_status('Informe o IP da TV em Configurações.')
            self.show_control()
            return
        self.busy = True
        self.set_status('Enviando…' if key else 'Conectando…')
        base = [self.adb, '-P', str(self.settings['adb_port'])]
        connect_first = not self.connected
        def operation():
            try:
                if connect_first:
                    subprocess.run(base+['connect',tv], check=True, capture_output=True, timeout=5)
                    state = subprocess.run(base+['-s',tv,'get-state'], check=True, capture_output=True, timeout=3)
                    if state.stdout.strip()!=b'device':
                        raise RuntimeError('Não autorizado')
                if key is not None:
                    subprocess.run(base+['-s',tv,'shell','input','keyevent',str(KEYS[key])], check=True, capture_output=True, timeout=4)
                GLib.idle_add(self.finished, True, 'Conectado à TV • pronto para usar.')
            except (OSError, subprocess.SubprocessError, RuntimeError):
                GLib.idle_add(self.finished, False, 'TV indisponível. Confira Wi-Fi, IP e autorização ADB na TV; tente novamente.')
        self.worker.submit(operation)

    def finished(self, success, message):
        self.busy = False
        self.connected = success
        self.set_status(message)
        return False

    def do_shutdown(self):
        self.indicator.set_status(Indicator.IndicatorStatus.PASSIVE)
        self.worker.shutdown(wait=False, cancel_futures=True)
        Gtk.Application.do_shutdown(self)

if __name__=='__main__':
    app=Remote()
    sys.exit(app.run(sys.argv))
