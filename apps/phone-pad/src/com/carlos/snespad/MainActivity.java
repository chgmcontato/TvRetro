package com.carlos.snespad;

import android.app.*;
import android.os.*;
import android.Manifest;
import android.bluetooth.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;
import java.util.*;

public class MainActivity extends Activity {
 BluetoothAdapter adapter; BluetoothHidDevice hid; BluetoothDevice host;
 boolean autoConnect=true,requesting=false,visible=false; TextView status; LinearLayout root; boolean registered=false; int buttons=0; int directions=0;
 // Gamepad: eight buttons, followed by signed X/Y axes. No report ID.
 static final byte[] DESCRIPTOR=new byte[]{
  0x05,0x01,0x09,0x05,(byte)0xA1,0x01,
  0x05,0x09,0x19,0x01,0x29,0x08,0x15,0x00,0x25,0x01,0x75,0x01,(byte)0x95,0x08,(byte)0x81,0x02,
  0x05,0x01,0x09,0x30,0x09,0x31,0x15,(byte)0x81,0x25,0x7F,0x75,0x08,(byte)0x95,0x02,(byte)0x81,0x02,(byte)0xC0};
 void log(String s){runOnUiThread(()->status.setText(s));}
 public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
 root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(12),dp(8),dp(12),dp(8));root.setBackgroundColor(Color.rgb(18,22,32));ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(root);setContentView(scroll);
 scroll.setOnApplyWindowInsetsListener((v,insets)->{if(Build.VERSION.SDK_INT>=30){android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);}else{v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());}return insets;});scroll.requestApplyInsets();
 TextView title=new TextView(this);title.setText("SNES • PHONE PAD");title.setTextSize(18);title.setTextColor(Color.WHITE);root.addView(title);
 status=new TextView(this);status.setTextColor(Color.rgb(111,224,185));status.setTextSize(14);status.setMinHeight(dp(34));root.addView(status);log("Pronto para conectar. Toque em Conectar / Retomar.");
 LinearLayout actions=row();action(actions,"Conectar / Retomar",()->{autoConnect=true;startHid();});action(actions,"Escolher TV",()->{if(registered)choose();else{startHid();log("Ative o perfil primeiro; depois escolha a TV.");}});action(actions,"Parear",()->discover());action(actions,"Desconectar",()->{autoConnect=false;release();if(hid!=null&&host!=null)hid.disconnect(host);});
 LinearLayout shoulders=row();key(shoulders,"L",16,0);key(shoulders,"R",32,0);
 LinearLayout pad=row();pad.setGravity(Gravity.CENTER);pad.setPadding(dp(12),0,dp(12),0);
 View dpad=new DirectionPad();LinearLayout.LayoutParams dparams=new LinearLayout.LayoutParams(0,dp(156),1);pad.addView(dpad,dparams);
 LinearLayout middle=new LinearLayout(this);middle.setOrientation(1);middle.setGravity(Gravity.CENTER);pad.addView(middle,new LinearLayout.LayoutParams(0,dp(156),1));
 LinearLayout centerButtons=new LinearLayout(this);middle.addView(centerButtons);key(centerButtons,"SELECT",64,0);key(centerButtons,"START",128,0);
 TextView hint=new TextView(this);hint.setText("Segure vários botões ao mesmo tempo.\nAo voltar de outro app, aguarde reconectar.");hint.setTextSize(12);hint.setTextColor(Color.LTGRAY);hint.setGravity(Gravity.CENTER);middle.addView(hint);
 LinearLayout right=new LinearLayout(this);right.setOrientation(1);pad.addView(right,new LinearLayout.LayoutParams(0,dp(156),1));
 LinearLayout top=new LinearLayout(this);right.addView(top);spacer(top);key(top,"X",8,0);spacer(top);
 LinearLayout mid=new LinearLayout(this);right.addView(mid);key(mid,"Y",4,0);spacer(mid);key(mid,"A",2,0);
 LinearLayout bottom=new LinearLayout(this);right.addView(bottom);spacer(bottom);key(bottom,"B",1,0);spacer(bottom);
 adapter=((BluetoothManager)getSystemService(BLUETOOTH_SERVICE)).getAdapter(); }
 int dp(float value){return Math.round(value*getResources().getDisplayMetrics().density);}
 Button button(String text){Button b=new Button(this);b.setText(text);b.setTextSize(14);b.setTextColor(Color.WHITE);b.setAllCaps(false);b.setGravity(Gravity.CENTER);b.setPadding(dp(4),0,dp(4),0);b.setMinHeight(0);b.setMinimumHeight(0);b.setMinWidth(0);b.setMinimumWidth(0);android.content.res.ColorStateList colors=new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_pressed},new int[]{}},new int[]{Color.rgb(80,109,135),Color.rgb(43,53,72)});b.setBackgroundTintList(colors);return b;}
 LinearLayout.LayoutParams buttonParams(int height){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(height),1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}
 LinearLayout row(){LinearLayout l=new LinearLayout(this);root.addView(l);return l;}
 void action(LinearLayout l,String text,Runnable r){Button b=button(text);l.addView(b,buttonParams(48));b.setOnClickListener(v->{try{r.run();}catch(Exception e){log(e.toString());}});}
 void key(LinearLayout l,String text,int mask,int dir){Button b=button(text);l.addView(b,buttonParams(text.length()>1?46:46));
 if(mask==1||mask==2||mask==4||mask==8){int c=mask==1?Color.rgb(194,161,49):mask==2?Color.rgb(188,70,90):mask==4?Color.rgb(54,142,110):Color.rgb(65,113,190);b.setBackgroundTintList(new android.content.res.ColorStateList(new int[][]{new int[]{android.R.attr.state_pressed},new int[]{}},new int[]{Color.rgb(105,120,140),c}));}
b.setOnTouchListener((v,e)->{int a=e.getActionMasked();if(a==MotionEvent.ACTION_DOWN){v.getParent().requestDisallowInterceptTouchEvent(true);buttons|=mask;directions|=dir;b.setPressed(true);send();}else if(a==MotionEvent.ACTION_UP||a==MotionEvent.ACTION_CANCEL){buttons&=~mask;directions&=~dir;b.setPressed(false);send();if(a==MotionEvent.ACTION_UP)v.performClick();}return true;});}
 boolean permissions(){if(Build.VERSION.SDK_INT>=31&&(checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)!=PackageManager.PERMISSION_GRANTED||checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE)!=PackageManager.PERMISSION_GRANTED)){requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT,Manifest.permission.BLUETOOTH_ADVERTISE},10);return false;}return true;}
 void startHid(){if(!permissions())return;if(adapter==null){log("Bluetooth indisponível.");return;}if(!adapter.isEnabled()){startActivity(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE));return;}if(hid!=null){register();return;}if(requesting)return;requesting=true;boolean ok=adapter.getProfileProxy(this,new BluetoothProfile.ServiceListener(){public void onServiceConnected(int p,BluetoothProfile proxy){requesting=false;hid=(BluetoothHidDevice)proxy;register();}public void onServiceDisconnected(int p){hid=null;registered=false;host=null;log("Serviço HID desconectado. Ative novamente.");}},BluetoothProfile.HID_DEVICE);if(!ok)requesting=false;log(ok?"Aguardando serviço HID…":"Perfil HID indisponível neste celular.");}
 void register(){if(registered){reconnect();return;}hid.registerApp(new BluetoothHidDeviceAppSdpSettings("SNES Phone Pad","Controle experimental SNES","Carlos",BluetoothHidDevice.SUBCLASS2_GAMEPAD,DESCRIPTOR),null,null,getMainExecutor(),new BluetoothHidDevice.Callback(){
 public void onAppStatusChanged(BluetoothDevice d,boolean r){registered=r;if(!r){host=null;log("Perfil pausado. Ao voltar, toque em Conectar / Retomar.");}else{log("Perfil ativo. Escolha a TV ou faça o pareamento pelo Bluetooth do celular.");if(visible&&autoConnect)reconnect();}}
 public void onConnectionStateChanged(BluetoothDevice d,int state){if(state==BluetoothProfile.STATE_CONNECTED){host=d;getPreferences(0).edit().putString("lastTv",d.getAddress()).apply();release();log("● Conectado a "+d.getName());}else if(state==BluetoothProfile.STATE_DISCONNECTED){host=null;buttons=0;directions=0;log("○ Desconectado. Toque em Conectar / Retomar.");}}
 public void onGetReport(BluetoothDevice d,byte type,byte id,int size){if(type==BluetoothHidDevice.REPORT_TYPE_INPUT)hid.replyReport(d,type,id,report());else hid.reportError(d,BluetoothHidDevice.ERROR_RSP_UNSUPPORTED_REQ);}
 });}
 void discover(){if(!permissions())return;if(!registered){log("Ative o perfil primeiro.");return;}Intent i=new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);i.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION,120);startActivity(i);}
 void choose(){if(!permissions())return;if(!registered){log("Ative o perfil primeiro.");return;}ArrayList<BluetoothDevice> ds=new ArrayList<>(adapter.getBondedDevices());String[] names=new String[ds.size()];for(int i=0;i<names.length;i++)names[i]=ds.get(i).getName()+"\n"+ds.get(i).getAddress();if(ds.isEmpty()){log("Nenhum pareamento. Procure o celular pela TV primeiro.");return;}new AlertDialog.Builder(this).setTitle("Escolha a TV").setItems(names,(d,n)->{autoConnect=true;getPreferences(0).edit().putString("lastTv",ds.get(n).getAddress()).apply();boolean ok=hid.connect(ds.get(n));log(ok?"Conexão solicitada. Se não funcionar, conecte pela TV.":"Solicitação recusada. Tente conectar pela TV.");}).show();}
 void spacer(LinearLayout l){l.addView(new View(this),new LinearLayout.LayoutParams(0,dp(46),1));}
 void reconnect(){if(hid==null||!registered||!visible)return;try{List<BluetoothDevice> connected=hid.getConnectedDevices();if(!connected.isEmpty()){host=connected.get(0);getPreferences(0).edit().putString("lastTv",host.getAddress()).apply();release();log("● Conectado a "+host.getName());return;}String address=getPreferences(0).getString("lastTv",null);if(address==null){log("Perfil ativo. Toque em Escolher TV para selecionar TV do quarto.");return;}BluetoothDevice d=adapter.getRemoteDevice(address);log(hid.connect(d)?"Reconectando a "+d.getName()+"…":"Não foi possível reconectar. Tente pelo Bluetooth do celular.");}catch(Exception e){log("Reconexão indisponível. Tente pelo Bluetooth do celular.");}}
 protected void onResume(){super.onResume();visible=true;if(adapter!=null&&autoConnect&&getPreferences(0).contains("lastTv")){new Handler(getMainLooper()).postDelayed(()->{if(visible)try{startHid();}catch(Exception e){log("Toque em Conectar / Retomar.");}},500);}}
 public void onRequestPermissionsResult(int r,String[] p,int[] g){super.onRequestPermissionsResult(r,p,g);if(r==10&&g.length>0){boolean granted=true;for(int v:g)granted&=v==PackageManager.PERMISSION_GRANTED;if(granted)startHid();else log("Autorize Dispositivos próximos para conectar.");}}
 class DirectionPad extends View {
  Paint paint=new Paint(3);int pointer=-1;
  DirectionPad(){super(MainActivity.this);setContentDescription("Direcional: deslize para mudar de direção, incluindo diagonais");}
  protected void onDraw(Canvas c){super.onDraw(c);float unit=Math.min(getWidth(),getHeight())/3f,cx=getWidth()/2f,cy=getHeight()/2f;paint.setColor(Color.rgb(43,53,72));c.drawRoundRect(cx-unit/2,cy-unit*1.45f,cx+unit/2,cy+unit*1.45f,dp(12),dp(12),paint);c.drawRoundRect(cx-unit*1.45f,cy-unit/2,cx+unit*1.45f,cy+unit/2,dp(12),dp(12),paint);paint.setColor(Color.WHITE);paint.setTextAlign(Paint.Align.CENTER);paint.setTextSize(dp(20));c.drawText("▲",cx,cy-unit*.8f+dp(7),paint);c.drawText("▼",cx,cy+unit*.8f+dp(7),paint);c.drawText("◀",cx-unit*.85f,cy+dp(7),paint);c.drawText("▶",cx+unit*.85f,cy+dp(7),paint);paint.setColor(directions==0?Color.rgb(79,93,115):Color.rgb(111,224,185));c.drawCircle(cx,cy,dp(8),paint);}
  public boolean onTouchEvent(MotionEvent e){int a=e.getActionMasked();if(a==MotionEvent.ACTION_DOWN){pointer=e.getPointerId(0);getParent().requestDisallowInterceptTouchEvent(true);}if(a==MotionEvent.ACTION_UP||a==MotionEvent.ACTION_CANCEL){pointer=-1;directions=0;send();invalidate();if(a==MotionEvent.ACTION_UP)performClick();return true;}int index=e.findPointerIndex(pointer);if(index>=0){float unit=Math.min(getWidth(),getHeight())/3f;float dx=(e.getX(index)-getWidth()/2f)/unit,dy=(e.getY(index)-getHeight()/2f)/unit;directions=(dx<-.35f?4:dx>.35f?8:0)|(dy<-.35f?1:dy>.35f?2:0);send();invalidate();}return true;}
  public boolean performClick(){super.performClick();return true;}
 }
 byte[] report(){int x=((directions&8)!=0?127:0)-((directions&4)!=0?127:0);int y=((directions&2)!=0?127:0)-((directions&1)!=0?127:0);return new byte[]{(byte)buttons,(byte)x,(byte)y};}
 void send(){if(hid!=null&&host!=null)try{if(!hid.sendReport(host,0,report()))log("Falha ao enviar. Verifique a conexão.");}catch(SecurityException e){log("Permissão Bluetooth necessária.");}}
 void release(){buttons=0;directions=0;send();}
 protected void onPause(){visible=false;release();super.onPause();}
 protected void onDestroy(){release();if(hid!=null){try{hid.unregisterApp();adapter.closeProfileProxy(BluetoothProfile.HID_DEVICE,hid);}catch(Exception ignored){}}super.onDestroy();}
}
