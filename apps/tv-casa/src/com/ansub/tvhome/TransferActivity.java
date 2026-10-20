package com.ansub.tvhome;
import android.app.*;
import android.os.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import java.io.File;
import java.net.*;
import java.util.*;
public class TransferActivity extends Activity {
 private NetworkBadge networkBadge;
 private long sessionStarted;
 private final Runnable sessionCheck=new Runnable(){public void run(){if(server==null)return;if(server.idleMillis()>10*60*1000L){stop();address.setText("Sessão encerrada por inatividade. Inicie outra se precisar.");}else if(SystemClock.elapsedRealtime()-sessionStarted>=60*60*1000L){stop();address.setText("Sessão encerrada após 60 minutos. Inicie outra se precisar.");}else handler.postDelayed(this,10000);}};
 private Typeface font; private LocalTransferServer server;private TextView address,status;private Handler handler=new Handler(Looper.getMainLooper());
 protected void onCreate(Bundle b){super.onCreate(b);font=LocalFonts.get(this,false);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(48,32,48,32);root.setBackgroundColor(0xFF10151C);networkBadge=NetworkBadge.install(this,root,16,32,getResources().getDisplayMetrics().widthPixels/1920f);text(root,"ENVIAR JOGOS PARA A TV",26);text(root,"1. Inicie o recebimento. 2. Abra o endereço abaixo no navegador do celular ou computador, na mesma rede Wi-Fi.\n3. Escolha SNES ou PSX e envie os arquivos. Ao voltar, a biblioteca será atualizada.",19);address=text(root,"A sessão só fica disponível enquanto esta tela estiver aberta.",23);address.setTextColor(0xFF6FE0B9);status=text(root,"Sem sessão ativa.",18);Button start=new Button(this);start.setText("Iniciar recebimento");styleButton(start);root.addView(start);start.setOnClickListener(v->{if(!PlatformCompat.hasPermission(this,android.Manifest.permission.WRITE_EXTERNAL_STORAGE)){PlatformCompat.requestPermissions(this,new String[]{android.Manifest.permission.WRITE_EXTERNAL_STORAGE},30);return;}startServer();});Button stop=new Button(this);stop.setText("Encerrar e voltar aos jogos");styleButton(stop);root.addView(stop);stop.setOnClickListener(v->finish());text(root,"Sessão local com endereço temporário. Não compartilhe o endereço. Encerra ao sair desta tela ou após 10 minutos sem atividade (máximo de 60 minutos).\nNão substitui arquivos e preserva pelo menos 550 MiB livres. ZIP e RAR precisam ser extraídos antes.",16);start.requestFocus();}
 private TextView text(LinearLayout root,String s,int size){TextView t=new TextView(this);t.setText(s);t.setTypeface(font);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(0,8,0,8);root.addView(t);return t;}
 private void styleButton(Button b){b.setTypeface(font);b.setTextColor(Color.WHITE);b.setAllCaps(false);b.setOnFocusChangeListener((v,focused)->{GradientDrawable bg=new GradientDrawable();bg.setCornerRadius(12);bg.setColor(focused?0xFF6D5420:0xFF293343);bg.setStroke(focused?5:1,focused?0xFFFFD166:0xFF455366);b.setBackground(bg);});}
 private String ip()throws Exception{for(NetworkInterface net:Collections.list(NetworkInterface.getNetworkInterfaces())){if(!net.isUp()||net.isLoopback())continue;for(InetAddress a:Collections.list(net.getInetAddresses()))if(a instanceof Inet4Address&&!a.isLoopbackAddress()&&a.isSiteLocalAddress())return a.getHostAddress();}throw new Exception("Conecte a TV à rede Wi-Fi ou Ethernet.");}
 private void startServer(){if(server!=null)return;try{String ip=ip();server=new LocalTransferServer(new File("/storage/emulated/0/Games"),550L*1024*1024,s->runOnUiThread(()->status.setText(s)));address.setText("http://"+ip+":"+server.port()+"/"+server.token);status.setText("Aguardando arquivos. Use o endereço completo no navegador.");sessionStarted=SystemClock.elapsedRealtime();handler.postDelayed(sessionCheck,10000);}catch(Exception e){stop();status.setText(e.getMessage());}}
 private void stop(){handler.removeCallbacksAndMessages(null);if(server!=null){server.close();server=null;}status.setText("Recebimento encerrado.");}
 public void onRequestPermissionsResult(int r,String[] p,int[] g){super.onRequestPermissionsResult(r,p,g);if(r==30&&g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)startServer();}
 protected void onResume(){super.onResume();if(networkBadge!=null)networkBadge.start();}
 protected void onPause(){if(networkBadge!=null)networkBadge.stop();super.onPause();}
 protected void onStop(){stop();super.onStop();}protected void onDestroy(){stop();super.onDestroy();}
}
