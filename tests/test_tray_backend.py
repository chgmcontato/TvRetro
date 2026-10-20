"""Remote command construction and parsers; no GUI, network or private settings."""
import importlib.util
from pathlib import Path
import subprocess,unittest
spec=importlib.util.spec_from_file_location('remote_backend',Path(__file__).resolve().parents[1]/'tools/tray/remote_backend.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class BackendTests(unittest.TestCase):
 def test_component_parser_ignores_untrusted_lines_and_deduplicates(self):
  text='2 activities found:\n com.netflix.ninja/.Main\ncom.netflix.ninja/.Other\ncom.example.app/.Launch\ncom.bad.app/.A;reboot\ncom.bad.app/.A$Bad\ncom.bad.app/.A/extra\n'
  apps=b.parse_apps(text);self.assertEqual([x['package'] for x in apps],['com.netflix.ninja','com.example.app']);self.assertEqual(apps[0]['label'],'Netflix')
 def test_app_limit(self):
  self.assertEqual(len(b.parse_apps('\n'.join(f'com.example.a{i}/.Main' for i in range(150)))),100)
 def test_address(self):
  self.assertEqual(b.address('192.0.2.4'),'192.0.2.4:5555')
  for value in ['192.0.2.4;reboot','bad','192.0.2.4:0','192.0.2.4:65536']:
   with self.subTest(value=value),self.assertRaises(ValueError):b.address(value)
 def client(self):
  self.calls=[]
  def run(args,**kwargs):
   self.calls.append((args,kwargs));text=b'device\n' if args[-1]=='get-state' else b''
   return subprocess.CompletedProcess(args,0,stdout=text,stderr=b'')
  return b.ADBClient('/usr/bin/adb','192.0.2.4',5038,run)
 def test_keys_connect_once_and_serialize_argv(self):
  c=self.client();c.key('home');c.key('inputs');self.assertEqual(len(self.calls),4)
  self.assertEqual(self.calls[-1][0],['/usr/bin/adb','-P','5038','-s','192.0.2.4:5555','shell','input','keyevent','178'])
  self.assertTrue(all('shell' not in opts and opts['timeout']<=8 for _,opts in self.calls))
 def test_invalid_actions_do_not_connect(self):
  c=self.client()
  for component in ['com.foo.app/.Main;reboot','com.foo.app/.Main$Inner','bad','com.foo.app/.Main extra']:
   with self.assertRaises(ValueError):c.launch(component)
  with self.assertRaises(KeyError):c.key('reboot')
  self.assertEqual(self.calls,[])
 def test_launch(self):
  c=self.client();c.launch('com.example.app/.Main');self.assertEqual(self.calls[-1][0][-4:],['am','start','-n','com.example.app/.Main'])
 def test_launch_rejected_by_android(self):
  def run(args,**kwargs):return subprocess.CompletedProcess(args,0,stdout=b'Error: Activity not found',stderr=b'')
  c=b.ADBClient('adb','192.0.2.4',runner=run);c.connected=True
  with self.assertRaises(RuntimeError):c.launch('com.example.app/.Main')
 def test_memory_and_disk(self):
  def run(args,**kwargs):
   text=b'MemTotal: 1024 kB\nMemAvailable: 512 kB\n' if args[-1]=='/proc/meminfo' else b'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/x 4096 1024 3072 25% /data\n'
   return subprocess.CompletedProcess(args,0,stdout=text,stderr=b'')
  c=b.ADBClient('adb','192.0.2.4',runner=run);c.connected=True;result=c.overview();self.assertEqual(result['memory']['MemAvailable'],512*1024);self.assertEqual(result['disk_free'],3072*1024)
 def test_unknown_memory_stays_missing(self):
  self.assertEqual(b.parse_memory('MemAvailable: unavailable\nMemFree: 100 kB'),{})
 def test_timeout_propagates_without_retry(self):
  def run(args,**kwargs):raise subprocess.TimeoutExpired('adb',8)
  c=b.ADBClient('adb','192.0.2.4',runner=run)
  with self.assertRaises(subprocess.TimeoutExpired):c.key('home')
if __name__=='__main__':unittest.main(verbosity=2)
