#!/usr/bin/python3
"""TvRetro Controle: GTK tray remote. No web server, video or background polling."""
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
from gi.repository import Gtk, Gdk, Gio, GLib, Pango, AyatanaAppIndicator3 as Indicator

APP_ID = 'org.tvretro.Remote'
HERE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'tvretro/config.json'
AUTOSTART = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'autostart/tvretro-controle.desktop'
from remote_backend import ADBClient, KEYS, address

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
        self.client = None
        self.app_inventory = []
        self.command_widgets = []
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
        item('Entradas HDMI', lambda: self.send('inputs'))
        item('Aplicativos', lambda: self.show_page('apps'))
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

    def show_page(self, name):
        self.show_control()
        self.pages.set_visible_child_name(name)

    def build_window(self):
        self.window = Gtk.ApplicationWindow(application=self, title='TvRetro Controle')
        self.window.set_default_size(410, 650)
        self.window.set_resizable(True)
        self.window.set_icon_from_file(str(HERE/'tvretro.svg'))
        self.window.connect('delete-event', lambda window, event: (window.hide() or True))
        self.window.connect('key-press-event', self.keyboard)
        css = Gtk.CssProvider()
        css.load_from_data(b'''window {background:#11141c;color:#edf3fa;} button {background:#242b3b;color:#f5f8fc;border:1px solid #3b465e;border-radius:12px;min-height:38px;padding:5px 8px;font-size:14px;} button:hover,button:focus {background:#42405d;border-color:#a999ff;} button:active {background:#60527d;} button:disabled {opacity:0.5;} .pad {font-size:24px;min-width:70px;min-height:58px;} .title {font-size:25px;font-weight:bold;} .muted {color:#bbc3d3;font-size:12px;} entry {color:#fff;background:#242b3b;} stacksidebar,stackswitcher {background:transparent;}''')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=16)
        self.window.add(outer)
        header = Gtk.Box(spacing=8)
        title = Gtk.Label(label='TvRetro', xalign=0)
        title.get_style_context().add_class('title')
        header.pack_start(title, True, True, 0)
        connect = Gtk.Button(label='Conectar')
        connect.connect('clicked', lambda *_: self.connect_only())
        header.pack_start(connect, False, False, 0)
        outer.pack_start(header, False, False, 0)
        self.status_label = Gtk.Label(label=self.status_message, wrap=True, max_width_chars=44, xalign=0)
        self.status_label.get_style_context().add_class('muted')
        outer.pack_start(self.status_label, False, False, 0)
        self.pages = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(stack=self.pages, halign=Gtk.Align.CENTER)
        outer.pack_start(switcher, False, False, 0)
        outer.pack_start(self.pages, True, True, 0)
        control = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pages.add_titled(control, 'control', 'Controle')
        pad = Gtk.Grid(row_spacing=7, column_spacing=7, halign=Gtk.Align.CENTER)
        control.pack_start(pad, False, False, 0)
        for label, key, x, y in [('▲','up',1,0),('◀','left',0,1),('OK','ok',1,1),('▶','right',2,1),('▼','down',1,2)]:
            self.key_button(pad,label,key,x,y,'pad')
        actions = Gtk.Grid(row_spacing=7,column_spacing=7,column_homogeneous=True)
        control.pack_start(actions,False,False,0)
        for label,key,x,y in [('Home','home',0,0),('Voltar','back',1,0),('Menu','menu',2,0),('Vol −','volume-down',0,1),('Mudo','mute',1,1),('Vol +','volume-up',2,1),('Anterior','previous',0,2),('▶ / Ⅱ','play',1,2),('Próximo','next',2,2),('⏪','rewind',0,3),('Informações','info',1,3),('⏩','forward',2,3)]:
            self.key_button(actions,label,key,x,y)
        apps = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        self.pages.add_titled(apps,'apps','Aplicativos')
        load = Gtk.Button(label='Carregar apps da TV')
        load.connect('clicked',lambda *_:self.load_apps())
        self.command_widgets.append(load)
        apps.pack_start(load,False,False,0)
        self.apps_box = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, row_spacing=8,column_spacing=8)
        self.apps_box.set_min_children_per_line(2)
        self.apps_box.set_max_children_per_line(2)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(260)
        scroll.add(self.apps_box)
        apps.pack_start(scroll,True,True,0)
        apps.pack_start(Gtk.Label(label='Lista consultada só quando você pedir.\nNomes desconhecidos aparecem pelo pacote.',wrap=True),False,False,0)
        tv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        self.pages.add_titled(tv,'tv','TV')
        for label,callback in [('HDMI / Entradas',lambda:self.send('inputs')),('Configurações da TV',self.open_settings),('Atualizar RAM e armazenamento',self.load_overview),('Acordar tela (se ADB responder)',lambda:self.send('wake')),('Suspender TV',self.confirm_sleep)]:
            button=Gtk.Button(label=label)
            button.connect('clicked',lambda _,cb=callback:cb())
            self.command_widgets.append(button)
            tv.pack_start(button,False,False,0)
        self.overview_label=Gtk.Label(label='Sem leitura recente. Atualize quando precisar.',wrap=True,xalign=0)
        tv.pack_start(self.overview_label,False,False,0)
        tv.pack_start(Gtk.Label(label='HDMI abre o seletor da TV; escolha com as setas.\nAcordar depende do firmware e não liga TV sem rede.\nReprodução e Info dependem do aplicativo aberto.',wrap=True),False,False,0)
        hint=Gtk.Label(label='Na aba Controle: setas + Enter • Esc para voltar\nFechar mantém o ícone na bandeja.',wrap=True)
        hint.get_style_context().add_class('muted')
        outer.pack_start(hint,False,False,0)
        expander=Gtk.Expander(label='Conexão e inicialização')
        self.settings_expander=expander
        outer.pack_start(expander,False,False,0)
        settings=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=7,margin_top=8)
        expander.add(settings)
        self.tv_entry=Gtk.Entry(text=self.settings['tv'],placeholder_text='IPv4 da TV')
        settings.pack_start(self.tv_entry,False,False,0)
        self.startup_check=Gtk.CheckButton(label='Iniciar na bandeja ao entrar no computador')
        self.startup_check.set_active(AUTOSTART.exists())
        settings.pack_start(self.startup_check,False,False,0)
        save=Gtk.Button(label='Salvar e reconectar')
        save.connect('clicked',self.save_settings)
        settings.pack_start(save,False,False,0)
        if not self.settings['tv']:
            expander.set_expanded(True)

    def key_button(self,grid,label,key,x,y,style=None):
        button=Gtk.Button(label=label)
        if style:
            button.get_style_context().add_class(style)
        button.remote_key=key
        button.connect('clicked',lambda *_:self.send(key))
        self.command_widgets.append(button)
        grid.attach(button,x,y,1,1)

    def confirm_sleep(self):
        dialog=Gtk.MessageDialog(transient_for=self.window,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.OK_CANCEL,text='Suspender a TV agora?')
        dialog.format_secondary_text('Isso interrompe o uso da tela. Acordar pela rede depende da TV; mantenha o controle físico por perto.')
        response=dialog.run()
        dialog.destroy()
        if response==Gtk.ResponseType.OK:
            self.send('sleep')

    @staticmethod
    def size(value):
        return 'indisponível' if value is None else f'{value/1024/1024:.0f} MiB'

    def load_apps(self):
        def show(apps):
            self.app_inventory=apps
            for child in self.apps_box.get_children():
                self.apps_box.remove(child)
            for app in apps:
                button=Gtk.Button(label=app['label'])
                label=button.get_child()
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                label.set_max_width_chars(18)
                label.set_lines(2)
                label.set_ellipsize(Pango.EllipsizeMode.END)
                button.set_tooltip_text(app['package'])
                button.connect('clicked',lambda _,component=app['component']:self.launch_app(component))
                self.apps_box.add(button)
            self.apps_box.show_all()
            self.set_status(f'{len(apps)} aplicativos encontrados.' if apps else 'Nenhum app disponível nesta consulta.')
        self.perform(lambda client:client.apps(),show)

    def launch_app(self,component):
        self.perform(lambda client:client.launch(component))

    def open_settings(self):
        self.perform(lambda client:client.settings())

    def load_overview(self):
        def show(info):
            memory=info['memory']
            self.overview_label.set_text('RAM disponível: '+self.size(memory.get('MemAvailable'))+' / '+self.size(memory.get('MemTotal'))+'\nArmazenamento livre: '+self.size(info['disk_free'])+' / '+self.size(info['disk_total'])+'\nLeitura sob demanda; pode variar após esta consulta.')
        self.perform(lambda client:client.overview(),show)

    def keyboard(self, window, event):
        focus=window.get_focus()
        if isinstance(focus,Gtk.Entry) or self.settings_expander.get_expanded() or self.pages.get_visible_child_name()!='control':
            return False
        if event.keyval in (Gdk.KEY_Return,Gdk.KEY_KP_Enter) and isinstance(focus,Gtk.Button) and not hasattr(focus,'remote_key'):
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
            self.client = None
            self.app_inventory = []
            for child in self.apps_box.get_children():
                self.apps_box.remove(child)
            self.overview_label.set_text('Sem leitura recente. Atualize quando precisar.')
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
        self.perform(lambda client:client.key(key) if key else client.connect())

    def perform(self,operation,on_success=None):
        if self.busy:
            return
        if not self.adb:
            self.set_status('ADB não encontrado. Instale Android Platform Tools.')
            self.show_control()
            return
        try:
            tv=address(self.settings['tv'])
            if self.client is None:
                self.client=ADBClient(self.adb,tv,self.settings['adb_port'])
        except (ValueError,TypeError):
            self.set_status('Informe o IP da TV em Configurações.')
            self.show_control()
            return
        self.busy=True
        self.set_status('Enviando…')
        for widget in self.command_widgets:
            widget.set_sensitive(False)
        def work():
            try:
                result=operation(self.client)
                GLib.idle_add(self.finished,True,result,on_success)
            except (OSError,subprocess.SubprocessError,RuntimeError,ValueError,KeyError):
                self.client.connected=False
                GLib.idle_add(self.finished,False,None,None)
        self.worker.submit(work)

    def finished(self,success,result=None,on_success=None):
        self.busy=False
        self.connected=success
        for widget in self.command_widgets:
            widget.set_sensitive(True)
        self.set_status('Conectado à TV • comando enviado pelo ADB.' if success else 'TV ou função indisponível. Confira rede, IP e autorização ADB; tente novamente.')
        if success and on_success:
            on_success(result)
        return False

    def do_shutdown(self):
        self.indicator.set_status(Indicator.IndicatorStatus.PASSIVE)
        self.worker.shutdown(wait=False, cancel_futures=True)
        Gtk.Application.do_shutdown(self)

if __name__=='__main__':
    app=Remote()
    sys.exit(app.run(sys.argv))
