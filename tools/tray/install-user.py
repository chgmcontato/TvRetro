#!/usr/bin/python3
"""Install tray remote for the current user; no sudo and no changes to the TV."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--tv',help='IPv4 da TV, com porta opcional')
p.add_argument('--adb-port',type=int,default=5037)
p.add_argument('--autostart',action='store_true')
p.add_argument('--typelib',type=Path,help='Pasta opcional com typelib Ayatana oficial')
a=p.parse_args()
if not 1<=a.adb_port<=65535:p.error('Porta ADB inválida')
address=None
if a.tv:
 host,sep,port=a.tv.partition(':');ipaddress.IPv4Address(host);port=int(port) if sep else 5555
 if not 1<=port<=65535:p.error('Porta inválida')
 address=f'{host}:{port}'
source=Path(__file__).resolve().parent
destination=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'tvretro'
config_home=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
destination.mkdir(parents=True,exist_ok=True)
for name in ('tvretro-tray.py','launch.sh','tvretro.svg'):
 shutil.copy2(source/name,destination/name)
(destination/'launch.sh').chmod(0o755)
if a.typelib:
 file=a.typelib/'AyatanaAppIndicator3-0.1.typelib'
 if not file.is_file():p.error('Typelib oficial não encontrado')
 (destination/'typelib').mkdir(exist_ok=True)
 shutil.copy2(file,destination/'typelib'/file.name)
config=config_home/'tvretro/config.json'
if not config.exists() and address:
 config.parent.mkdir(parents=True,exist_ok=True)
 config.write_text(json.dumps({'tv':address,'adb_port':a.adb_port},indent=2)+'\n')
 config.chmod(0o600)
def desktop(background=False):
 return f'[Desktop Entry]\nType=Application\nName=TvRetro Controle\nComment=Controle remoto da TV na bandeja\nExec="{destination / "launch.sh"}"'+(' --background' if background else '')+f'\nIcon={destination / "tvretro.svg"}\nTerminal=false\nCategories=Utility;\nStartupNotify=false\n'
applications=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'applications'
applications.mkdir(parents=True,exist_ok=True)
(applications/'tvretro-controle.desktop').write_text(desktop())
if a.autostart:
 startup=config_home/'autostart';startup.mkdir(parents=True,exist_ok=True)
 (startup/'tvretro-controle.desktop').write_text(desktop(True))
print('Instalado: TvRetro Controle. Abra pelo menu de aplicativos ou execute:')
print(destination/'launch.sh')
