package com.ansub.tvhome;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Ephemeral, token-protected streaming upload receiver. No file download endpoint. */
public final class LocalTransferServer implements Closeable {
 public interface Observer {void update(String message);}
 private final File root; private final long reserve;
 private final Observer observer; private final ServerSocket server;
 private final Set<Socket> sockets=Collections.synchronizedSet(new HashSet<Socket>());
 private final ThreadPoolExecutor workers=new ThreadPoolExecutor(2,2,0,TimeUnit.SECONDS,new ArrayBlockingQueue<Runnable>(4));
 private final AtomicBoolean uploading=new AtomicBoolean();private volatile boolean closed;
 private volatile long lastActivity=System.nanoTime();
 public final String token;
 public LocalTransferServer(File root,long reserve,Observer observer)throws IOException{
  this.root=root;this.reserve=reserve;this.observer=observer;
  if(!root.isDirectory()&&!root.mkdirs())throw new IOException("Não foi possível criar a pasta Games.");
  byte[] random=new byte[16];new SecureRandom().nextBytes(random);StringBuilder t=new StringBuilder();for(byte b:random)t.append(String.format(Locale.ROOT,"%02x",b&255));token=t.toString();
  server=new ServerSocket(0);Thread accept=new Thread(()->{while(!closed)try{Socket s=server.accept();lastActivity=System.nanoTime();s.setSoTimeout(30000);sockets.add(s);try{workers.execute(()->handle(s));}catch(RejectedExecutionException e){sockets.remove(s);s.close();}}catch(IOException e){if(!closed)observer.update("Recebimento interrompido: "+e.getMessage());}},"TvRetro-transfer");accept.setDaemon(true);accept.start();
 }
 public long idleMillis(){return TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-lastActivity);}
 public int port(){return server.getLocalPort();}
 private String line(InputStream in,long deadline)throws IOException{ByteArrayOutputStream b=new ByteArrayOutputStream();for(int n=0;n<8192;n++){if(System.nanoTime()>deadline)throw new IOException("Prazo de cabeçalho excedido");int c=in.read();if(c<0)throw new EOFException();if(c==10)return new String(b.toByteArray(),StandardCharsets.US_ASCII).replace("\r","");b.write(c);}throw new IOException("Cabeçalho muito longo");}
 private void handle(Socket socket){File temporary=null;boolean locked=false;try{
  InputStream in=socket.getInputStream();OutputStream out=socket.getOutputStream();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(10);socket.setSoTimeout(10000);String[] first=line(in,deadline).split(" ");if(first.length!=3){reply(out,400,"Requisição inválida");return;}
  int headerBytes=first[0].length()+first[1].length();Map<String,String> headers=new HashMap<>();for(int n=0;;n++){String l=line(in,deadline);headerBytes+=l.length();if(headerBytes>32768){reply(out,400,"Cabeçalho muito longo");return;}if(l.isEmpty())break;if(n>=48){reply(out,400,"Cabeçalhos demais");return;}int colon=l.indexOf(':');if(colon>0)headers.put(l.substring(0,colon).toLowerCase(Locale.ROOT),l.substring(colon+1).trim());}
  URI uri=new URI(first[1]);String route=uri.getPath();String prefix="/"+token;
  if(!route.equals(prefix)&&!route.equals(prefix+"/upload")&&!route.equals(prefix+"/check")){reply(out,403,"Sessão inválida");return;}
  if("GET".equals(first[0])&&route.equals(prefix)){respond(out,200,"text/html; charset=utf-8",page().getBytes(StandardCharsets.UTF_8));return;}
  boolean checking="GET".equals(first[0])&&route.equals(prefix+"/check");
  if(!checking&&(!"POST".equals(first[0])||!route.equals(prefix+"/upload"))){reply(out,405,"Método não permitido");return;}
  if(headers.containsKey("transfer-encoding")){reply(out,400,"Envie um arquivo com tamanho conhecido");return;}
  String origin=headers.get("origin"),host=headers.get("host");if(origin!=null&&(host==null||!origin.equals("http://"+host))){reply(out,403,"Origem inválida");return;}
  Map<String,String> query=new HashMap<>();if(uri.getRawQuery()!=null)for(String part:uri.getRawQuery().split("&")){String[] kv=part.split("=",2);if(kv.length==2)query.put(kv[0],URLDecoder.decode(kv[1],"UTF-8"));}
  String console=query.get("console"),name=query.get("name");if(!"SNES".equals(console)&&!"PSX".equals(console)){reply(out,400,"Escolha SNES ou PSX");return;}
  if(name==null||name.length()>180||name.startsWith(".")||name.matches(".*[\\\\/\\p{Cntrl}].*")){reply(out,400,"Nome de arquivo inválido");return;}
  String lower=name.toLowerCase(Locale.ROOT);boolean allowed="SNES".equals(console)?lower.endsWith(".sfc")||lower.endsWith(".smc"):lower.endsWith(".chd")||lower.endsWith(".pbp")||lower.endsWith(".cue")||lower.endsWith(".bin")||lower.endsWith(".m3u");if(!allowed){reply(out,400,"Formato não aceito. Extraia ZIP/RAR antes de enviar.");return;}
  long length;try{length=Long.parseLong(checking?query.get("size"):headers.get("content-length"));}catch(Exception e){reply(out,411,"Tamanho do arquivo necessário");return;}
  if(length<=0||length>2L*1024*1024*1024){reply(out,413,"Tamanho não permitido");return;}
  if(!uploading.compareAndSet(false,true)){reply(out,409,"Outro envio está em andamento");return;}locked=true;
  if(length>root.getUsableSpace()-reserve){reply(out,507,"Espaço insuficiente: a TV reserva 550 MiB livres.");return;}
  File dir=new File(root,console);if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Não foi possível criar a pasta do console");File target=new File(dir,name);if(target.exists()){reply(out,409,"Já existe um arquivo com esse nome; nada foi substituído.");return;}
  if(checking){reply(out,200,"Pronto para receber");return;}
  temporary=File.createTempFile("incoming-",".part",dir);observer.update("Recebendo: "+name);
  socket.setSoTimeout(30000);long uploadDeadline=System.nanoTime()+TimeUnit.MINUTES.toNanos(8);long received=0,lastUpdate=0;try(FileOutputStream file=new FileOutputStream(temporary)){byte[] buffer=new byte[65536];while(received<length){if(System.nanoTime()>uploadDeadline)throw new IOException("Prazo do envio excedido");int read=in.read(buffer,0,(int)Math.min(buffer.length,length-received));if(read<0)throw new EOFException("Envio interrompido");lastActivity=System.nanoTime();file.write(buffer,0,read);received+=read;if(received-lastUpdate>=4*1024*1024){if(root.getUsableSpace()<reserve)throw new IOException("A reserva de espaço livre foi atingida");observer.update("Recebendo "+name+": "+(received*100/length)+"%");lastUpdate=received;}}file.getFD().sync();}
  if(closed)throw new IOException("Sessão encerrada");if(target.exists()||!temporary.renameTo(target))throw new IOException("Não foi possível concluir o arquivo");temporary=null;
  observer.update("Recebido: "+name+". Pode enviar outro arquivo ou voltar à biblioteca.");reply(out,200,"Recebido: "+name);
 }catch(Exception e){if(!closed)observer.update("Envio não concluído: "+e.getMessage());try{reply(socket.getOutputStream(),400,"Envio interrompido ou inválido; tente novamente.");}catch(Exception ignored){}}
 finally{if(temporary!=null)temporary.delete();if(locked)uploading.set(false);sockets.remove(socket);try{socket.close();}catch(Exception ignored){}}}
 private void reply(OutputStream out,int status,String text)throws IOException{respond(out,status,"text/plain; charset=utf-8",text.getBytes(StandardCharsets.UTF_8));}
 private void respond(OutputStream out,int status,String type,byte[] bytes)throws IOException{String h="HTTP/1.1 "+status+" Result\r\nContent-Type: "+type+"\r\nContent-Length: "+bytes.length+"\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nContent-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'\r\n\r\n";out.write(h.getBytes(StandardCharsets.US_ASCII));out.write(bytes);out.flush();}
 private String page(){return "<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Enviar jogos · TvRetro</title><style>body{background:#10151c;color:#eef5f2;font:18px system-ui;max-width:650px;margin:40px auto;padding:20px}button,select,input{font:inherit;padding:14px;margin:12px 0;max-width:100%;box-sizing:border-box}button{background:#6fe0b9;border:0;border-radius:10px}pre{white-space:pre-wrap;font:16px system-ui}</style><h1>Enviar jogos</h1><p>Escolha o console e os arquivos. Mantenha a tela de recebimento aberta na TV.</p><label>Console <select id='console'><option>SNES</option><option>PSX</option></select></label><br><input id='files' type='file' multiple accept='.sfc,.smc,.chd,.pbp,.cue,.bin,.m3u'><br><button id='send'>Enviar para a TV</button><p>Extraia ZIP/RAR antes. Para PSX, prefira CHD ou envie o CUE e todos os BIN correspondentes. Não substitui arquivos existentes.</p><pre id='status' role='status'>Aguardando arquivos.</pre><script>const button=document.getElementById('send'),status=document.getElementById('status');button.onclick=async()=>{const files=document.getElementById('files').files,consoleName=document.getElementById('console').value;if(!files.length){status.textContent='Escolha pelo menos um arquivo.';return;}button.disabled=true;try{for(const file of files){status.textContent='Enviando '+file.name+'…';const check=await fetch(location.pathname+'/check?console='+encodeURIComponent(consoleName)+'&name='+encodeURIComponent(file.name)+'&size='+file.size);if(!check.ok)throw new Error(await check.text());const response=await fetch(location.pathname+'/upload?console='+encodeURIComponent(consoleName)+'&name='+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});const message=await response.text();if(!response.ok)throw new Error(message);status.textContent=message;}status.textContent='Todos os arquivos foram enviados. Volte à biblioteca na TV.';}catch(error){status.textContent=error.message;}finally{button.disabled=false;}};</script></html>";}
 public void close(){closed=true;try{server.close();}catch(Exception ignored){}synchronized(sockets){for(Socket s:sockets)try{s.close();}catch(Exception ignored){}}workers.shutdownNow();}
}
