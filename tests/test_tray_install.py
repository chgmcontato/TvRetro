"""Check per-user installation and configuration preservation without a GUI/TV."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

INSTALLER=Path(__file__).resolve().parents[1]/'tools/tray/install-user.py'
class InstallTests(unittest.TestCase):
 def test_preserve_settings_and_autostart(self):
  with tempfile.TemporaryDirectory(prefix='tvretro-install-test-') as folder:
   root=Path(folder)
   env=dict(os.environ,XDG_DATA_HOME=str(root/'data'),XDG_CONFIG_HOME=str(root/'config'))
   run=lambda *args: subprocess.run([sys.executable,str(INSTALLER),*args],env=env,capture_output=True,text=True)
   self.assertEqual(run('--tv','192.0.2.42','--autostart').returncode,0)
   self.assertTrue((root/'data/tvretro/remote_backend.py').is_file())
   config=root/'config/tvretro/config.json'
   self.assertEqual(json.loads(config.read_text())['tv'],'192.0.2.42:5555')
   self.assertEqual(config.stat().st_mode & 0o777,0o600)
   self.assertTrue((root/'config/autostart/tvretro-controle.desktop').exists())
   self.assertIn('--background',(root/'config/autostart/tvretro-controle.desktop').read_text())
   self.assertNotIn('192.0.2.42',(root/'data/applications/tvretro-controle.desktop').read_text())
   self.assertEqual(run('--tv','192.0.2.99').returncode,0)
   self.assertEqual(json.loads(config.read_text())['tv'],'192.0.2.42:5555')
 def test_reject_invalid_address_before_writes(self):
  with tempfile.TemporaryDirectory(prefix='tvretro-install-test-') as folder:
   root=Path(folder)
   env=dict(os.environ,XDG_DATA_HOME=str(root/'data'),XDG_CONFIG_HOME=str(root/'config'))
   p=subprocess.run([sys.executable,str(INSTALLER),'--tv','127.0.0.1;echo invalid'],env=env,capture_output=True)
   self.assertNotEqual(p.returncode,0)
   self.assertFalse((root/'data').exists())
if __name__=='__main__':unittest.main()
