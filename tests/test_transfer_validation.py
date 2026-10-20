"""HTTP regressions for control characters and bounded header parsing."""
import http.client,os,socket,subprocess,tempfile,unittest
from pathlib import Path
from urllib.parse import quote
repo=Path(__file__).resolve().parents[1]
java=Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java'
class ValidationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='tvretro-validation-');cls.root=Path(cls.tmp.name);cls.classes=cls.root/'classes';cls.classes.mkdir()
  subprocess.run([str(java.with_name('javac')),'-source','1.8','-target','1.8','-d',str(cls.classes),str(repo/'apps/tv-casa/src/com/ansub/tvhome/LocalTransferServer.java'),str(repo/'tests/Harness.java')],check=True)
  cls.p=subprocess.Popen([str(java),'-cp',str(cls.classes),'Harness',str(cls.root/'games'),'0'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
  port,token=cls.p.stdout.readline().split();cls.port=int(port);cls.base='/'+token
 @classmethod
 def tearDownClass(cls):
  cls.p.stdin.write('\n');cls.p.stdin.flush();cls.p.wait(timeout=10);cls.p.stdin.close();cls.p.stdout.close();cls.tmp.cleanup()
 def test_multiline_names_rejected(self):
  for name in ['a\nb\nc.sfc','a\rb\nc.sfc','a\nb\rc.sfc','a\n/escape.sfc','a\n\\escape.sfc','a\x00b.sfc']:
   with self.subTest(name=repr(name)):
    c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
    try:
     c.request('POST',self.base+'/upload?console=SNES&name='+quote(name,safe=''),body=b'test');r=c.getresponse();r.read();self.assertEqual(r.status,400);self.assertFalse((self.root/'games/SNES'/name).exists())
    finally:c.close()
 def test_header_line_too_long_is_bad_request(self):
  with socket.create_connection(('127.0.0.1',self.port),timeout=5) as c:
   c.sendall(('GET '+self.base+' HTTP/1.1\r\nX-Large: '+'a'*8300+'\r\n\r\n').encode());self.assertEqual(c.recv(4096).split(b'\r\n')[0],b'HTTP/1.1 400 Bad Request')
 def test_header_timeout_is_request_timeout(self):
  with socket.create_connection(('127.0.0.1',self.port),timeout=13) as c:
   c.sendall(('GET '+self.base+' HTTP/1.1\r\n').encode());self.assertEqual(c.recv(4096).split(b'\r\n')[0],b'HTTP/1.1 408 Request Timeout')
if __name__=='__main__':unittest.main(verbosity=2)
