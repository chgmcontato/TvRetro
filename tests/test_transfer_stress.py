"""Synthetic local HTTP load. Requires a JDK; Linux additionally reports /proc metrics. No TV or ROMs. Run separately from the quick suite."""
import subprocess,pathlib,tempfile,os,http.client,socket,time,hashlib,concurrent.futures,json,urllib.parse,random
repo=pathlib.Path(__file__).resolve().parents[1];java=str(pathlib.Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java')
results=[]
def check(name,fn):
 start=time.monotonic()
 try: detail=fn();results.append({'test':name,'ok':True,'seconds':round(time.monotonic()-start,2),'detail':detail})
 except Exception as e:results.append({'test':name,'ok':False,'seconds':round(time.monotonic()-start,2),'error':type(e).__name__+': '+str(e)})
 print(json.dumps(results[-1],ensure_ascii=False),flush=True)
with tempfile.TemporaryDirectory(prefix='tvretro-stress-') as tmp:
 tmp=pathlib.Path(tmp);root=tmp/'games';root.mkdir();classes=tmp/'classes';classes.mkdir()
 subprocess.run([java+'c','-source','1.8','-target','1.8','-d',str(classes),str(repo/'apps/tv-casa/src/com/ansub/tvhome/LocalTransferServer.java'),str(repo/'tests/Harness.java')],check=True)
 p=subprocess.Popen([java,'-Xmx64m','-cp',str(classes),'Harness',str(root),'0'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 port,token=p.stdout.readline().split();port=int(port);base='/'+token
 def req(method='GET',path=None,data=None,headers=None):
  c=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
  try:
   c.request(method,path or base,body=data,headers=headers or {});r=c.getresponse();return r.status,r.read()
  finally:c.close()
 def upload(name,data=b'x',headers=None):return req('POST',base+'/upload?console=SNES&name='+urllib.parse.quote(name,safe=''),data,headers)
 def metrics():
  if not pathlib.Path('/proc',str(p.pid),'status').exists():return None
  return {'fds':len(list(pathlib.Path('/proc',str(p.pid),'fd').iterdir())),'threads':len(list(pathlib.Path('/proc',str(p.pid),'task').iterdir())),'rss_kib':int(next(x for x in pathlib.Path('/proc',str(p.pid),'status').read_text().splitlines() if x.startswith('VmRSS:')).split()[1])}
 before=metrics()
 try:
  def sequential():
   for i in range(500): assert req()[0]==200
   return '500 GETs'
  check('500 requisições sequenciais',sequential)
  def batch():
   def one(i):
    payload=bytes([i%256])*65536;status,_=upload('batch%d.sfc'%i,payload);assert status==200;assert (root/'SNES'/('batch%d.sfc'%i)).read_bytes()==payload
   for i in range(80):one(i)
   return '80 arquivos de 64 KiB íntegros'
  check('Envios repetidos e integridade',batch)
  def big():
   chunk=b'payload-test-1234'*4096;n=1024;c=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
   c.putrequest('POST',base+'/upload?console=PSX&name=synthetic.chd');c.putheader('Content-Length',str(len(chunk)*n));c.endheaders()
   h=hashlib.sha256()
   for _ in range(n):c.send(chunk);h.update(chunk)
   r=c.getresponse();assert r.status==200;r.read();c.close()
   target=root/'PSX/synthetic.chd';actual=hashlib.sha256()
   with target.open('rb') as saved:
    for block in iter(lambda:saved.read(65536),b''):actual.update(block)
   assert actual.digest()==h.digest();target.unlink()
   return '64 MiB por streaming; SHA-256 idêntico; JVM limitada a 64 MiB de heap'
  check('Upload grande com heap limitado',big)
  def contention():
   c=socket.create_connection(('127.0.0.1',port));c.settimeout(5)
   c.sendall(('POST '+base+'/upload?console=SNES&name=held.sfc HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4096\r\n\r\na').encode())
   try:
    for _ in range(100):
     if list(root.rglob('*.part')):break
     time.sleep(.01)
    status,body=upload('blocked.sfc');assert status==409
    c.sendall(b'a'*4095);r=http.client.HTTPResponse(c);r.begin();assert r.status==200;r.read()
   finally:c.close()
   assert upload('after-held.sfc')[0]==200
   return 'Segundo upload recebe 409; primeiro conclui; trava liberada'
  check('Concorrência e recuperação da trava',contention)
  def aborts():
   for i in range(30):
    c=socket.create_connection(('127.0.0.1',port));c.sendall(('POST '+base+'/upload?console=SNES&name=abort%d.sfc HTTP/1.1\r\nHost: localhost\r\nContent-Length: 8192\r\n\r\npartial'%i).encode());c.shutdown(socket.SHUT_WR);c.settimeout(5)
    while c.recv(4096):pass
    c.close()
   time.sleep(.1);assert not list(root.rglob('*.part'));assert not list(root.rglob('abort*'));assert upload('after-abort.sfc')[0]==200
   return '30 interrupções; nenhum parcial/arquivo final; próximo envio funciona'
  check('Uploads interrompidos',aborts)
  def invalid_names():
   names=['../escape.sfc','..\\escape.sfc','.hidden.sfc','slash/file.sfc','back\\file.sfc','a\x00b.sfc','a\rb.sfc','a\nb.sfc','a\tb.sfc','a'*181+'.sfc']
   found=[]
   for name in names:
    status,_=upload(name)
    if status!=400:found.append({'name':repr(name),'status':status})
   assert not found,found
   return str(len(names))+' nomes recusados'
  check('Validação de nomes e caracteres de controle',invalid_names)
  def rejection_deadline():
   c=socket.create_connection(('127.0.0.1',port));c.settimeout(5);start=time.monotonic();c.sendall(('POST '+base+'/upload?console=SNES&name=batch0.sfc HTTP/1.1\r\nHost: localhost\r\nContent-Length: 100000\r\n\r\n').encode());r=http.client.HTTPResponse(c);r.begin();assert r.status==409;r.read();response=time.monotonic()-start
   while c.recv(4096):pass
   time.sleep(3.3);assert upload('after-linger.sfc')[0]==200;elapsed=time.monotonic()-start;c.close();assert response<2
   return {'response_s':round(response,2),'recovery_checked_s':round(elapsed,2)}
  check('Limite de 3 segundos no descarte',rejection_deadline)
  def malformed():
   rng=random.Random(42)
   for i in range(80):
    path=base+'/upload?console=SNES&name=fuzz%d.sfc'%i
    samples=[b'GET / HTTP/1.1\r\n\r\n',('POST '+path+' HTTP/1.1\r\nContent-Length: nope\r\n\r\n').encode(),('POST '+path+' HTTP/1.1\r\nContent-Length: -1\r\n\r\n').encode(),b'INVALID\r\n\r\n',b'GET http:// HTTP/1.1\r\n\r\n']
    with socket.create_connection(('127.0.0.1',port)) as c:
     c.settimeout(3);c.sendall(rng.choice(samples));c.shutdown(socket.SHUT_WR)
     try:
      data=c.recv(4096);assert data.startswith(b'HTTP/1.1 ')
     except ConnectionResetError:pass
   assert req()[0]==200
   return '80 requisições malformadas; servidor continua respondendo'
  check('Entradas malformadas e recuperação',malformed)
  def saturation():
   sockets=[]
   try:
    for i in range(20):sockets.append(socket.create_connection(('127.0.0.1',port),timeout=2))
    time.sleep(.2);during=metrics();assert during is None or during['threads']<=before['threads']+5
   finally:
    for c in sockets:c.close()
   time.sleep(1);assert req()[0]==200
   return during
  check('Saturação de conexões e recuperação',saturation)
  time.sleep(.3);after=metrics();results.append({'metrics_before':before,'metrics_after':after});print(json.dumps(results[-1]),flush=True)
 finally:
  start=time.monotonic();p.stdin.write('\n');p.stdin.flush();p.wait(timeout=10);print('Processo encerrado em',round(time.monotonic()-start,2),'s',flush=True)
if any(item.get('ok') is False for item in results):raise SystemExit(1)
