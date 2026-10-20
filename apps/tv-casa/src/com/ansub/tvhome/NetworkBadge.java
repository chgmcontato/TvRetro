package com.ansub.tvhome;

import android.app.Activity;
import android.content.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.*;
import android.net.wifi.WifiManager;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import java.util.Locale;

/** Activity-local header. TV-wide transfer rate, not an ISP speed test or Wi-Fi-only counter. */
final class NetworkBadge extends LinearLayout {
 private final Activity owner;private final ImageView icon;private final TextView usage;
 private final Handler handler=new Handler(Looper.getMainLooper());private boolean running;
 private long previousTime,previousRx,previousTx;
 private final Runnable tick=new Runnable(){public void run(){if(!running)return;refresh();handler.postDelayed(this,2000);}};
 static NetworkBadge install(Activity owner,View content,int top,int right,float scale){
  FrameLayout host=new FrameLayout(owner);host.addView(content,new FrameLayout.LayoutParams(-1,-1));
  NetworkBadge badge=new NetworkBadge(owner,scale);FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(Math.round(560*scale),Math.round(76*scale),Gravity.TOP|Gravity.RIGHT);p.topMargin=top;p.rightMargin=right;host.addView(badge,p);owner.setContentView(host);return badge;
 }
 private NetworkBadge(Activity owner,float scale){super(owner);this.owner=owner;setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);setPadding(6,4,6,4);setFocusable(true);
  usage=new TextView(owner);usage.setTextColor(Color.WHITE);usage.setTypeface(LocalFonts.get(owner,false));usage.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,Math.max(12,Math.round(26*scale)));usage.setGravity(Gravity.RIGHT|Gravity.CENTER_VERTICAL);usage.setMaxLines(2);addView(usage,new LayoutParams(0,-1,1));
  icon=new ImageView(owner);LayoutParams image=new LayoutParams(Math.round(40*scale),Math.round(40*scale));image.leftMargin=Math.round(16*scale);addView(icon,image);
  setOnFocusChangeListener((v,f)->{GradientDrawable bg=new GradientDrawable();bg.setColor(f?0xCC6D5420:Color.TRANSPARENT);bg.setCornerRadius(12);bg.setStroke(f?3:0,0xFFFFD166);setBackground(bg);});
  setOnClickListener(v->{for(String action:new String[]{Settings.ACTION_WIFI_SETTINGS,Settings.ACTION_WIRELESS_SETTINGS,Settings.ACTION_SETTINGS})try{owner.startActivity(new Intent(action));return;}catch(Exception ignored){}});
 }
 public void start(){if(running)return;running=true;previousTime=0;handler.post(tick);}
 public void stop(){running=false;handler.removeCallbacks(tick);}
 protected void onAttachedToWindow(){super.onAttachedToWindow();start();}
 protected void onDetachedFromWindow(){stop();super.onDetachedFromWindow();}
 private static String rate(long delta,long elapsed){return delta<0||elapsed<=0?"—":String.format(Locale.getDefault(),"%.1f",delta*1000d/elapsed/1024);}
 void refresh(){
  ConnectivityManager cm=(ConnectivityManager)owner.getSystemService(Context.CONNECTIVITY_SERVICE);String connection="Offline";int[] drawing=LineIcon.SLASH;
  try{boolean wifi=false,ethernet=false,connected=false;int signal=Integer.MIN_VALUE;if(Build.VERSION.SDK_INT>=23){NetworkCapabilities caps=cm.getNetworkCapabilities(cm.getActiveNetwork());if(caps!=null){connected=true;wifi=caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI);ethernet=caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET);if(Build.VERSION.SDK_INT>=29)signal=caps.getSignalStrength();}}else{android.net.NetworkInfo info=cm.getActiveNetworkInfo();connected=info!=null&&info.isConnected();if(connected){wifi=info.getType()==ConnectivityManager.TYPE_WIFI;ethernet=info.getType()==ConnectivityManager.TYPE_ETHERNET;}}if(connected){if(wifi){connection="Wi-Fi";if(signal==Integer.MIN_VALUE){WifiManager manager=(WifiManager)owner.getApplicationContext().getSystemService(Context.WIFI_SERVICE);signal=manager.getConnectionInfo().getRssi();}int level=WifiManager.calculateSignalLevel(signal,3);drawing=level==0?LineIcon.WIFI_1:level==1?LineIcon.WIFI_2:LineIcon.WIFI;}else if(ethernet){connection="Ethernet";drawing=LineIcon.ETHERNET;}else{connection="Rede";drawing=LineIcon.WIFI;}}}catch(Exception ignored){}
  icon.setImageDrawable(new LineIcon(drawing));long now=SystemClock.elapsedRealtime(),rx=TrafficStats.getTotalRxBytes(),tx=TrafficStats.getTotalTxBytes();String value=previousTime==0||rx<0||tx<0?"↓ —  ↑ — KiB/s":"↓ "+rate(rx-previousRx,now-previousTime)+"  ↑ "+rate(tx-previousTx,now-previousTime)+" KiB/s";
  usage.setText(value+"\n"+connection+" • tráfego total da TV");setContentDescription(connection+". "+value+". Todas as interfaces da TV. Abrir ajustes de rede.");previousTime=now;previousRx=rx;previousTx=tx;
 }
}
