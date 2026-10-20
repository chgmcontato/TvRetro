#!/usr/bin/env python3
"""Controle local, sem serviço persistente na TV. Python 3 + ADB."""
import argparse, http.server, ipaddress, json, os, secrets, shutil, subprocess, threading, webbrowser
from pathlib import Path

KEYS={'cima':19,'baixo':20,'esquerda':21,'direita':22,'ok':23,'home':3,'voltar':4,'play':85,'volume+':24,'volume-':25,'mudo':164}
PAGE='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Controle TV Casa</title><style>body{background:#10151c;color:#fff;font:18px system-ui;max-width:850px;margin:30px auto;padding:16px}button{font:inherit;padding:16px;margin:5px;background:#293343;color:white;border:2px solid #ffd166;border-radius:12px}img{width:100%;background:black}#pad{display:grid;grid-template-columns:repeat(3,1fr);max-width:440px}#status{min-height:2em}</style><h1>Controle TV Casa</h1><p>Use as setas, Enter e Escape com esta página em foco. Home retorna à TV Casa.</p><div id="pad"><span></span><button data-key="cima">▲</button><span></span><button data-key="esquerda">◀</button><button data-key="ok">OK</button><button data-key="direita">▶</button><span></span><button data-key="baixo">▼</button><span></span></div><div id="actions"></div><p id="status">Pronto.</p><button id="shot">Atualizar imagem</button><button id="mirror">Abrir espelhamento ao vivo</button><button onclick="action('mirror-stop')">Encerrar espelhamento</button><p>A imagem abaixo é atualizada apenas quando solicitado. Para encerrar o controle e o servidor local, use Ctrl+C no terminal.</p><img id="screen" alt="Imagem da TV — clique em Atualizar imagem"><script>let busy=false;const status=document.getElementById('status');async function action(key){if(busy)return;busy=true;try{let r=await fetch(location.pathname+'/'+key,{method:'POST'});status.textContent=await r.text();}catch(e){status.textContent='Conexão encerrada';}finally{busy=false;}}document.querySelectorAll('[data-key]').forEach(b=>b.onclick=()=>action(b.dataset.key));for(const k of ['home','voltar','play','volume+','volume-','mudo']){let b=document.createElement('button');b.textContent=k;b.onclick=()=>action(k);document.getElementById('actions').append(b);}document.addEventListener('keydown',e=>{let k={ArrowUp:'cima',ArrowDown:'baixo',ArrowLeft:'esquerda',ArrowRight:'direita',Enter:'ok',Escape:'voltar'}[e.key];if(k){e.preventDefault();if(!e.repeat)action(k);}});document.getElementById('shot').onclick=()=>{document.getElementById('screen').src=location.pathname+'/screen?'+Date.now();};document.getElementById('mirror').onclick=()=>action('mirror');</script></html>'''

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tv',required=True,help='IPv4 da TV, com porta opcional');p.add_argument('--adb-port',type=int,default=5037);p.add_argument('--scrcpy',default=shutil.which('scrcpy'));p.add_argument('--no-browser',action='store_true');a=p.parse_args()
 host,sep,port=a.tv.partition(':');ipaddress.IPv4Address(host);port=int(port) if sep else 5555
 if not 1<=port<=65535:p.error('Porta inválida')
 address=f'{host}:{port}';adb=shutil.which('adb')
 if not adb:p.error('Instale Android Platform Tools (adb)')
 command=[adb,'-P',str(a.adb_port)]
 subprocess.run(command+['connect',address],check=True,timeout=15)
 token=secrets.token_hex(16);lock=threading.Lock();mirrors=[]
 def run(args):
  with lock:return subprocess.run(command+['-s',address]+args,check=True,timeout=20,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def respond(self,status,data,mime='text/plain; charset=utf-8'):
   self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");self.end_headers();self.wfile.write(data)
  def valid(self):return self.headers.get('Host')==f'127.0.0.1:{server.server_port}'
  def do_GET(self):
   path=self.path.split('?',1)[0]
   if not self.valid():return self.respond(403,b'Host invalido')
   try:
    if path=='/'+token:return self.respond(200,PAGE.encode(),'text/html; charset=utf-8')
    if path=='/'+token+'/screen':
     image=run(['exec-out','screencap','-p']);start=image.find(b'\x89PNG\r\n\x1a\n')
     if start<0:return self.respond(502,b'Imagem indisponivel')
     return self.respond(200,image[start:],'image/png')
    self.respond(404,b'Nao encontrado')
   except (subprocess.SubprocessError,OSError):self.respond(502,b'Nao foi possivel consultar a TV')
  def do_POST(self):
   if not self.valid() or self.headers.get('Origin') not in (None,f'http://127.0.0.1:{server.server_port}'):return self.respond(403,b'Origem invalida')
   prefix='/'+token+'/'
   if not self.path.startswith(prefix):return self.respond(403,b'Sessao invalida')
   key=self.path[len(prefix):]
   try:
    if key in KEYS:run(['shell','input','keyevent',str(KEYS[key])]);return self.respond(200,b'Comando enviado.')
    if key=='mirror-stop':
     for m in mirrors:
      if m.poll() is None:m.terminate()
     return self.respond(200,b'Espelhamento encerrado.')
    if key=='mirror':
     if not a.scrcpy:return self.respond(503,'scrcpy não instalado. Consulte docs/NOTEBOOK.md.'.encode())
     if any(m.poll() is None for m in mirrors):return self.respond(409,b'Espelhamento ja aberto.')
     env=dict(os.environ,ADB_SERVER_SOCKET=f'tcp:127.0.0.1:{a.adb_port}',ADB=adb)
     if env.get('WAYLAND_DISPLAY'):env['SDL_VIDEODRIVER']='wayland'
     mirrors.append(subprocess.Popen([a.scrcpy,'-s',address,'--no-audio','--max-size=1024','--max-fps=15','--video-bit-rate=2M','--render-driver=software','--window-title=TV Casa'],env=env))
     return self.respond(200,'Espelhamento solicitado. Confira a janela e o terminal.'.encode())
    self.respond(404,b'Comando desconhecido')
   except (subprocess.SubprocessError,OSError):self.respond(502,b'Falha de comunicacao; verifique a TV e o terminal.')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
 url=f'http://127.0.0.1:{server.server_port}/{token}';print(url,flush=True)
 if not a.no_browser:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:
  server.server_close()
  for m in mirrors:
   if m.poll() is None:m.terminate()
if __name__=='__main__':main()
