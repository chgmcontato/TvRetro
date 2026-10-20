package com.ansub.tvhome;

import android.app.*;
import android.app.usage.NetworkStats;
import android.app.usage.NetworkStatsManager;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.net.*;
import android.net.wifi.*;
import android.os.*;
import android.os.storage.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import java.io.File;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** Visible-only local telemetry. No root or forced process termination. */
public final class MonitorPanel extends LinearLayout {
 private final Activity owner;private final Runnable releaseCache;private final float scale;private final Typeface regular,bold;
 private final TextView wifi,traffic,memory,disk,status;private final Handler handler=new Handler(Looper.getMainLooper());
 private final ExecutorService statsWorker=Executors.newSingleThreadExecutor();
 private boolean active,disposed,querying;private long lastRx=-1,lastTx=-1,lastTime,queryTime,dayRx=-1,dayTx=-1;private String statsMessage="Autorize acesso ao uso para ver o consumo Wi-Fi de hoje.";
 private final Runnable tick=new Runnable(){public void run(){if(!active)return;update();handler.postDelayed(this,2000);}};
 public MonitorPanel(Activity owner,float scale,Runnable releaseCache){super(owner);this.owner=owner;this.scale=scale;this.releaseCache=releaseCache;regular=LocalFonts.get(owner,false);bold=LocalFonts.get(owner,true);setOrientation(VERTICAL);
  LinearLayout a=row(),b=row();wifi=card(a,"REDE");traffic=card(a,"TRÁFEGO");memory=card(b,"RAM");disk=card(b,"ARMAZENAMENTO");
  LinearLayout buttons=new LinearLayout(owner);addView(buttons,new LayoutParams(-1,px(66)));
  button(buttons,"Liberar RAM",()->confirmRelease());button(buttons,"Nome do Wi-Fi",()->wifiPermission());button(buttons,"Consumo Wi-Fi",()->usageSettings());button(buttons,"Configurações",()->{try{owner.startActivity(new Intent(Settings.ACTION_SETTINGS));}catch(Exception e){message("Configurações indisponíveis.");}});
  status=text(px(20));status.setText("Métricas locais • atualização a cada 2 s • consumo Wi-Fi pode ter atraso no Android.");addView(status,new LayoutParams(-1,px(50)));
 }
 private int px(int n){return Math.max(1,Math.round(n*scale));}
 private LinearLayout row(){LinearLayout r=new LinearLayout(owner);addView(r,new LayoutParams(-1,0,1));return r;}
 private TextView text(int size){TextView t=new TextView(owner);t.setTextColor(Color.WHITE);t.setTypeface(regular);t.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,size);return t;}
 private TextView card(LinearLayout row,String title){TextView t=text(px(24));t.setText(title);t.setPadding(px(22),px(16),px(22),px(12));GradientDrawable bg=new GradientDrawable();bg.setColor(0xE6151B24);bg.setCornerRadius(px(18));bg.setStroke(px(2),0xFF364653);t.setBackground(bg);LayoutParams p=new LayoutParams(0,-1,1);p.setMargins(px(5),px(5),px(5),px(8));row.addView(t,p);return t;}
 private void button(LinearLayout row,String label,Runnable action){Button b=new Button(owner);b.setText(label);b.setTypeface(bold);b.setAllCaps(false);b.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,px(21));b.setTextColor(Color.WHITE);b.setPadding(px(4),0,px(4),0);style(b,false);b.setOnFocusChangeListener((v,f)->style(b,f));b.setOnClickListener(v->action.run());LayoutParams p=new LayoutParams(0,-1,1);p.setMargins(px(4),px(4),px(4),px(4));row.addView(b,p);}
 private void style(Button b,boolean focus){GradientDrawable bg=new GradientDrawable();bg.setCornerRadius(px(13));bg.setColor(focus?0xFF6D5420:0xFF293343);bg.setStroke(focus?px(5):px(1),focus?0xFFFFD166:0xFF455366);b.setBackground(bg);}
 public void start(){if(disposed||active)return;active=true;lastTime=0;handler.post(tick);}
 public void stop(){active=false;handler.removeCallbacks(tick);}
 protected void onAttachedToWindow(){super.onAttachedToWindow();start();}
 protected void onDetachedFromWindow(){stop();disposed=true;statsWorker.shutdownNow();super.onDetachedFromWindow();}
 public void permissionsChanged(){if(disposed)return;queryTime=0;if(active)update();}
 private static String size(long bytes){if(bytes<0)return "indisponível";if(bytes>=1024L*1024*1024)return String.format(Locale.getDefault(),"%.2f GiB",bytes/(1024d*1024*1024));return String.format(Locale.getDefault(),"%.1f MiB",bytes/(1024d*1024));}
 private static String rate(long bytes,long ms){if(ms<=0||bytes<0)return "—";return String.format(Locale.getDefault(),"%.1f KiB/s",bytes*1000d/ms/1024);}
 private void update(){
  if(disposed||!active)return;
  ActivityManager.MemoryInfo m=new ActivityManager.MemoryInfo();((ActivityManager)owner.getSystemService(Context.ACTIVITY_SERVICE)).getMemoryInfo(m);
  memory.setText("RAM\nDisponível: "+size(m.availMem)+" / "+size(m.totalMem)+"\nEm uso: "+size(m.totalMem-m.availMem)+"\nPressão: "+(m.lowMemory?"alta":"normal"));
  StatFs fs=new StatFs("/data");StringBuilder storage=new StringBuilder("INTERNO\nLivre: "+size(fs.getAvailableBytes())+" / "+size(fs.getTotalBytes()));
  if(Build.VERSION.SDK_INT>=30){StorageManager sm=(StorageManager)owner.getSystemService(Context.STORAGE_SERVICE);for(StorageVolume v:sm.getStorageVolumes())if(v.isRemovable()){File f=v.getDirectory();if(f!=null&&f.canRead()){storage.append("\nUSB: ").append(size(f.getUsableSpace())).append(" / ").append(size(f.getTotalSpace()));}else storage.append("\nUSB detectado, mas não pode ser lido.");}}
  disk.setText(storage.toString());
  StringBuilder net=new StringBuilder("REDE\n");try{ConnectivityManager cm=(ConnectivityManager)owner.getSystemService(Context.CONNECTIVITY_SERVICE);Network n=Build.VERSION.SDK_INT>=23?cm.getActiveNetwork():null;NetworkCapabilities caps=n==null?null:cm.getNetworkCapabilities(n);if(Build.VERSION.SDK_INT<23){NetworkInfo info=cm.getActiveNetworkInfo();if(info==null||!info.isConnected())net.append("Desconectada");else{net.append(info.getType()==ConnectivityManager.TYPE_WIFI?"Wi-Fi":info.getType()==ConnectivityManager.TYPE_ETHERNET?"Ethernet":"Outra conexão");if(info.getType()==ConnectivityManager.TYPE_WIFI){WifiInfo legacy=((WifiManager)owner.getApplicationContext().getSystemService(Context.WIFI_SERVICE)).getConnectionInfo();if(legacy!=null)net.append(" • ").append(legacy.getSSID()).append("\nSinal: ").append(legacy.getRssi()).append(" dBm");}}}else if(caps==null)net.append("Desconectada");else{net.append(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"Wi-Fi":caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?"Ethernet":"Outra conexão");if(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)){WifiInfo info=((WifiManager)owner.getApplicationContext().getSystemService(Context.WIFI_SERVICE)).getConnectionInfo();String ssid=info==null?null:info.getSSID();net.append(" • ").append(ssid==null||ssid.equals("<unknown ssid>")?"nome protegido pelo Android":ssid.replace("\"",""));if(info!=null)net.append("\nSinal: ").append(info.getRssi()).append(" dBm • link: ").append(info.getLinkSpeed()).append(" Mbps");}LinkProperties lp=cm.getLinkProperties(n);if(lp!=null)for(LinkAddress la:lp.getLinkAddresses())if(la.getAddress() instanceof Inet4Address){net.append("\nIP: ").append(la.getAddress().getHostAddress());break;}}}catch(Exception e){net.append("Detalhes indisponíveis");}wifi.setText(net.toString());
  long now=SystemClock.elapsedRealtime(),rx=TrafficStats.getTotalRxBytes(),tx=TrafficStats.getTotalTxBytes();String live=rx<0||tx<0?"Taxa de tráfego indisponível":lastTime==0?"Aguardando amostra…":"TV agora ↓ "+rate(rx-lastRx,now-lastTime)+" ↑ "+rate(tx-lastTx,now-lastTime);lastTime=now;lastRx=rx;lastTx=tx;
  traffic.setText("TRÁFEGO\n"+live+"\n(todas as interfaces da TV)\nWi-Fi hoje ↓ "+size(dayRx)+" ↑ "+size(dayTx)+"\n"+statsMessage);
  if(!querying&&now-queryTime>15000){queryTime=now;queryWifi();}
 }
 private void queryWifi(){if(disposed||!active||statsWorker.isShutdown())return;if(Build.VERSION.SDK_INT<23){dayRx=dayTx=-1;statsMessage="Consumo diário indisponível no Android 5; taxa atual disponível acima.";return;}AppOpsManager ops=(AppOpsManager)owner.getSystemService(Context.APP_OPS_SERVICE);if(ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS,android.os.Process.myUid(),owner.getPackageName())!=AppOpsManager.MODE_ALLOWED){dayRx=dayTx=-1;statsMessage="Autorize em Consumo Wi-Fi.";return;}querying=true;statsWorker.execute(()->{long rx=-1,tx=-1;String msg;try{Calendar c=Calendar.getInstance();c.set(Calendar.HOUR_OF_DAY,0);c.set(Calendar.MINUTE,0);c.set(Calendar.SECOND,0);c.set(Calendar.MILLISECOND,0);NetworkStatsManager mgr=(NetworkStatsManager)owner.getSystemService(Context.NETWORK_STATS_SERVICE);NetworkStats.Bucket bucket=mgr.querySummaryForDevice(ConnectivityManager.TYPE_WIFI,null,c.getTimeInMillis(),System.currentTimeMillis());rx=bucket.getRxBytes();tx=bucket.getTxBytes();msg="Wi-Fi desde 00h • dados podem atrasar.";}catch(Exception e){msg="Consumo Wi-Fi indisponível neste sistema.";}final long resultRx=rx,resultTx=tx;final String text=msg;handler.post(()->{querying=false;if(!disposed){dayRx=resultRx;dayTx=resultTx;statsMessage=text;}});});}
 private void wifiPermission(){if(!PlatformCompat.hasPermission(owner,android.Manifest.permission.ACCESS_FINE_LOCATION)){new AlertDialog.Builder(owner).setTitle("Identificar a rede Wi-Fi").setMessage("O Android exige permissão de localização para revelar o nome do Wi-Fi. A TvRetro consulta somente a rede conectada; não solicita posição GPS.").setPositiveButton("Permitir",(d,w)->PlatformCompat.requestPermissions(owner,new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION},40)).setNegativeButton("Cancelar",null).show();return;}android.location.LocationManager lm=(android.location.LocationManager)owner.getSystemService(Context.LOCATION_SERVICE);if(Build.VERSION.SDK_INT>=28&&!lm.isLocationEnabled()){new AlertDialog.Builder(owner).setTitle("Nome da rede protegido").setMessage("O Android também exige Localização ativada na TV para mostrar o nome da rede. Você pode ativá-la nos ajustes ou continuar usando o painel sem o nome do Wi-Fi.").setPositiveButton("Abrir ajustes",(d,w)->{try{owner.startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));}catch(Exception e){message("Abra Preferências do dispositivo → Localização nas configurações da TV.");}}).setNegativeButton("Manter como está",null).show();}else{message("Identificação do Wi-Fi atualizada.");update();}}
 private void usageSettings(){try{Intent i=new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS);i.setData(Uri.parse("package:"+owner.getPackageName()));owner.startActivity(i);}catch(Exception e){try{owner.startActivity(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS));}catch(Exception e2){message("A TV não oferece a tela de acesso ao uso.");}}}
 private void confirmRelease(){new AlertDialog.Builder(owner).setTitle("Liberar RAM").setMessage("O Android administra a RAM. Posso liberar o cache de capas da home e solicitar o encerramento dos apps de streaming em segundo plano. Isso pode parar reprodução. RetroArch, saves e serviços da TV são preservados. O ganho é temporário e não é garantido.").setNeutralButton("Só cache da home",(d,w)->{releaseCache.run();message("Cache da home liberado. RAM disponível é atualizada no painel.");}).setPositiveButton("Cache + streamings",(d,w)->{releaseCache.run();if(Build.VERSION.SDK_INT<34){ActivityManager am=(ActivityManager)owner.getSystemService(Context.ACTIVITY_SERVICE);for(String pkg:new String[]{"com.crunchyroll.crunchyroid","com.google.android.youtube.tv","com.disney.disneyplus","com.wbd.stream","com.netflix.ninja","com.amazon.amazonvideo.livingroom"})try{am.killBackgroundProcesses(pkg);}catch(Exception ignored){}message("Cache liberado; encerramento de streamings solicitado ao Android.");}else message("Cache liberado. Este Android restringe encerramento de outros apps.");}).setNegativeButton("Cancelar",null).show();}
 private void message(String s){status.setText(s);}
}
