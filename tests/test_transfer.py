import subprocess,os,pathlib,http.client,socket,time,shutil
import tempfile
repo=pathlib.Path(__file__).resolve().parents[1]
sandbox=tempfile.TemporaryDirectory(prefix='tvretro-tests-')
root=pathlib.Path(sandbox.name)/'games';root.mkdir()
classes=pathlib.Path(sandbox.name)/'classes';classes.mkdir()
java=pathlib.Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java'
javac=java.with_name('javac')
subprocess.run([str(javac),'-d',str(classes),str(repo/'apps/tv-casa/src/com/ansub/tvhome/LocalTransferServer.java'),str(repo/'tests/Harness.java')],check=True)
p=subprocess.Popen([str(java),'-cp',str(classes),'Harness',str(root),'0'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
port,token=p.stdout.readline().split();port=int(port);base='/'+token

def req(method,path,data=None,headers=None):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10);c.request(method,path,body=data,headers=headers or {});r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
try:
 assert len(token)==32
 assert req('GET',base)[0]==200
 assert req('GET',base+'/check?console=SNES&name=demo.sfc&size=8')[0]==200
 assert not (root/'SNES/demo.sfc').exists()
 assert req('GET','/invalid')[0]==403
 assert req('POST',base+'/upload?console=SNES&name=demo.sfc',b'TEST-ROM')[0]==200
 assert (root/'SNES/demo.sfc').read_bytes()==b'TEST-ROM'
 assert req('GET',base+'/check?console=SNES&name=demo.sfc&size=8')[0]==409
 assert req('POST',base+'/upload?console=SNES&name=demo.sfc',b'OVERWRITE')[0]==409
 assert (root/'SNES/demo.sfc').read_bytes()==b'TEST-ROM'
 status,body=req('POST',base+'/upload?console=SNES&name=demo.sfc',b'x'*(8*1024*1024));assert status==409 and b'nada foi' in body
 assert req('POST',base+'/upload?console=SNES&name=large.sfc',b'x'*(8*1024*1024),{'Content-Length':str(2**31+1)})[0]==413
 assert req('POST',base+'/upload?console=SNES&name=..%2Fescape.sfc',b'bad')[0]==400
 assert req('POST',base+'/upload?console=SNES&name=game.zip',b'bad')[0]==400
 assert req('POST',base+'/upload?console=PSX&name=demo.chd',b'CHD-TEST')[0]==200
 assert req('POST',base+'/upload?console=PSX&name=demo.bin',b'TRACK')[0]==200
 assert req('POST',base+'/upload?console=PSX&name=evil.chd',b'x',{'Origin':'http://untrusted.example'})[0]==403
 assert req('POST',base+'/upload?console=SNES&name=empty.sfc',b'')[0]==413
 c=socket.create_connection(('127.0.0.1',port));c.sendall(('POST '+base+'/upload?console=SNES&name=partial.sfc HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1000\r\n\r\npartial').encode());c.shutdown(socket.SHUT_WR);c.recv(2048);c.close()
 assert not (root/'SNES/partial.sfc').exists()
 assert not list(root.rglob('*.part'))
 c=socket.create_connection(('127.0.0.1',port));c.sendall(('GET '+base+' HTTP/1.1\r\nHost: localhost\r\n'+''.join('X-%d: '%i+'a'*7000+'\r\n' for i in range(5))+'\r\n').encode());assert b'400' in c.recv(1024);c.close()
 print('Limite de cabeçalhos e token de 128 bits verificados.')
 print('11 cenários HTTP e integridade verificados: envio, PSX, token, duplicidade, caminhos, formato, origem, vazio e interrupção.')
finally:
 p.stdin.write('\n');p.stdin.flush();p.wait(timeout=10)
# Space reservation rejects upload even when a valid file is supplied.
p=subprocess.Popen([str(java),'-cp',str(classes),'Harness',str(root),str(2**62)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
port,token=p.stdout.readline().split();port=int(port);base='/'+token
try:
 assert req('POST',base+'/upload?console=SNES&name=space.sfc',b'ROM')[0]==507
 assert req('POST',base+'/upload?console=SNES&name=space.sfc',b'x'*(8*1024*1024))[0]==507
 assert not (root/'SNES/space.sfc').exists();print('Reserva de espaço verificada.')
finally:
 p.stdin.write('\n');p.stdin.flush();p.wait(timeout=10)

# Short idle threshold exercises monotonic activity tracking without a ten-minute wait.
p=subprocess.Popen([str(java),'-cp',str(classes),'Harness',str(root),'0','2000'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
port,token=p.stdout.readline().split();port=int(port);base='/'+token
try:
 for _ in range(4):
  time.sleep(1);assert req('GET',base)[0]==200
 time.sleep(2.4)
 try:
  c=socket.create_connection(('127.0.0.1',port),timeout=1);c.close()
  raise AssertionError('Servidor continuou aceitando conexões após inatividade')
 except ConnectionRefusedError: pass
 print('Atividade mantém a sessão; inatividade fecha o socket (limite de teste: 2 s).')
finally:
 p.stdin.write('\n');p.stdin.flush();p.wait(timeout=10)
sandbox.cleanup()
