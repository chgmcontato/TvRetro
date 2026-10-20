"""Bounded, on-demand Android TV operations. No scanning, polling or local shell."""
import ipaddress
import re
import subprocess

KEYS = {'up':19,'down':20,'left':21,'right':22,'ok':23,'home':3,'back':4,
        'play':85,'previous':88,'next':87,'rewind':89,'forward':90,
        'volume-up':24,'volume-down':25,'mute':164,'menu':82,'info':165,
        'inputs':178,'sleep':223,'wake':224}
APP_NAMES = {'com.carlos.tvcasa':'TvRetro','com.android.vending':'Play Store',
 'com.retroarch.ra32':'RetroArch','com.crunchyroll.crunchyroid':'Crunchyroll',
 'com.google.android.youtube.tv':'YouTube','com.disney.disneyplus':'Disney+',
 'com.wbd.stream':'Max','com.netflix.ninja':'Netflix',
 'com.amazon.amazonvideo.livingroom':'Prime Video'}
COMPONENT = re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+/[A-Za-z0-9_.$]+\Z')

def address(value):
    host, sep, port = value.strip().partition(':')
    ipaddress.IPv4Address(host)
    number = int(port) if sep else 5555
    if not 1 <= number <= 65535:
        raise ValueError('Porta inválida')
    return f'{host}:{number}'

def parse_apps(text):
    apps = {}
    for line in text.splitlines():
        component = line.strip()
        # Reject shell metacharacters, including inner-class dollar signs.
        if not COMPONENT.fullmatch(component) or '$' in component:
            continue
        package = component.split('/')[0]
        if package not in apps:
            apps[package] = {'package':package,'component':component,
                             'label':APP_NAMES.get(package,package)}
        if len(apps) >= 100:
            break
    return sorted(apps.values(),key=lambda app:(app['package'] not in APP_NAMES,app['label'].casefold()))

def parse_memory(text):
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r'(MemTotal|MemAvailable):\s+(\d+)\s+kB',line.strip())
        if match:
            values[match[1]] = int(match[2])*1024
    return values

class ADBClient:
    def __init__(self, executable, tv, port=5037, runner=subprocess.run):
        self.tv = address(tv)
        self.port = int(port)
        if not 1 <= self.port <= 65535:
            raise ValueError('Porta ADB inválida')
        self.base = [executable,'-P',str(self.port)]
        self.runner = runner
        self.connected = False

    def run(self,*args):
        result = self.runner(self.base+['-s',self.tv]+list(args),check=True,
                             capture_output=True,timeout=8)
        if len(result.stdout) > 2*1024*1024:
            raise RuntimeError('Resposta muito grande')
        return result.stdout.decode('utf-8',errors='replace')

    def connect(self):
        self.runner(self.base+['connect',self.tv],check=True,capture_output=True,timeout=5)
        if self.run('get-state').strip() != 'device':
            raise RuntimeError('Não autorizado')
        self.connected = True

    def ensure_connected(self):
        if not self.connected:
            self.connect()

    def key(self,key):
        code = KEYS[key]
        self.ensure_connected()
        return self.run('shell','input','keyevent',str(code))

    def apps(self):
        self.ensure_connected()
        text = ''
        for category in ['LEANBACK_LAUNCHER','LAUNCHER']:
            text += '\n'+self.run('shell','cmd','package','query-activities','--brief',
                '-a','android.intent.action.MAIN','-c','android.intent.category.'+category)
        return parse_apps(text)

    def launch(self,component):
        if not COMPONENT.fullmatch(component) or '$' in component:
            raise ValueError('Componente inválido')
        self.ensure_connected()
        result = self.run('shell','am','start','-n',component)
        if re.search(r'Error:|Exception|Permission Denial',result):
            raise RuntimeError('O Android não abriu este aplicativo')
        return result

    def settings(self):
        self.ensure_connected()
        result = self.run('shell','am','start','-a','android.settings.SETTINGS')
        if re.search(r'Error:|Exception|Permission Denial',result):
            raise RuntimeError('Configurações indisponíveis')
        return result

    def overview(self):
        self.ensure_connected()
        memory = parse_memory(self.run('shell','cat','/proc/meminfo'))
        disk = self.run('shell','df','-k','/data')
        free = total = None
        for line in disk.splitlines():
            parts = line.split()
            if len(parts)>=6 and all(x.isdigit() for x in parts[1:4]):
                total,free = int(parts[1])*1024,int(parts[3])*1024
        return {'memory':memory,'disk_total':total,'disk_free':free}
