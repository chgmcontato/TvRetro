package com.ansub.tvhome;

import android.app.Activity;
import android.os.*;
import android.content.*;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.TextView;

/** Handles RetroArch 1.22.2 exiting on a different-content intent. */
public class GameLaunchActivity extends Activity {
 private NetworkBadge networkBadge;
 private boolean launched=false,left=false,retried=false,switchCandidate=false;
 private long started;private Handler handler=new Handler(Looper.getMainLooper());
 private String path,core,config;
 protected void onCreate(Bundle state){super.onCreate(state);path=getIntent().getStringExtra("ROM");core=getIntent().getStringExtra("LIBRETRO");config=getIntent().getStringExtra("CONFIGFILE");String previous=getSharedPreferences("game_launch",0).getString("last",null);switchCandidate=previous==null||!path.equals(previous);TextView text=new TextView(this);text.setText("Abrindo jogo…");text.setTextSize(24);text.setTextColor(Color.WHITE);text.setBackgroundColor(0xFF151018);text.setGravity(Gravity.CENTER);networkBadge=NetworkBadge.install(this,text,24,32,getResources().getDisplayMetrics().widthPixels/1920f);}
 protected void onResume(){super.onResume();if(networkBadge!=null)networkBadge.start();if(!launched){handler.postDelayed(()->{if(!isFinishing()){launched=true;started=SystemClock.elapsedRealtime();open();handler.postDelayed(()->{if(!isFinishing()){retried=true;open();handler.postDelayed(()->{if(!isFinishing())finish();},600);}},1400);}},150);}}
 private void open(){Intent intent=new Intent();intent.setClassName("com.retroarch.ra32","com.retroarch.browser.retroactivity.RetroActivityFuture");intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);intent.putExtra("ROM",path);intent.putExtra("LIBRETRO",core);intent.putExtra("CONFIGFILE",config);try{getSharedPreferences("game_launch",0).edit().putString("last",path).apply();startActivity(intent);}catch(Exception e){new android.app.AlertDialog.Builder(this).setMessage("Não foi possível abrir o RetroArch.").setPositiveButton("Voltar",(d,w)->finish()).setOnCancelListener(d->finish()).show();}}
 protected void onPause(){if(networkBadge!=null)networkBadge.stop();if(launched)left=true;super.onPause();}
 protected void onDestroy(){handler.removeCallbacksAndMessages(null);super.onDestroy();}
}
