package com.ansub.tvhome;

import android.app.Activity;
import android.graphics.*;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import java.io.File;
import java.util.concurrent.*;

/** Online covers only in the visible viewport. A named card stays playable offline. */
final class GameCoverView extends FrameLayout implements ViewTreeObserver.OnPreDrawListener {
 private final Activity owner;private final File rom;private final ImageView image;private final TextView placeholder;
 private boolean loading,loaded;private int generation;private long retryAfter;private Future<?> pending;
 GameCoverView(Activity owner,File rom){super(owner);this.owner=owner;this.rom=rom;setBackgroundColor(0xFF161E2B);image=new ImageView(owner);image.setScaleType(ImageView.ScaleType.FIT_CENTER);addView(image,new LayoutParams(-1,-1));placeholder=new TextView(owner);placeholder.setTextColor(Color.WHITE);placeholder.setTypeface(LocalFonts.get(owner,false));placeholder.setTextSize(17);placeholder.setGravity(Gravity.CENTER);placeholder.setPadding(16,12,16,12);showName("Buscando capa…");addView(placeholder,new LayoutParams(-1,-1));}
 private void showName(String detail){placeholder.setText(rom.getName().replaceFirst("(?i)\\.(sfc|smc|chd|cue|pbp|m3u)$","")+"\n\n"+detail);placeholder.setVisibility(VISIBLE);}
 protected void onAttachedToWindow(){super.onAttachedToWindow();getViewTreeObserver().addOnPreDrawListener(this);}
 protected void onDetachedFromWindow(){if(getViewTreeObserver().isAlive())getViewTreeObserver().removeOnPreDrawListener(this);release();super.onDetachedFromWindow();}
 public void release(){generation++;loading=false;loaded=false;image.setImageDrawable(null);placeholder.setVisibility(VISIBLE);if(pending!=null)pending.cancel(false);RemoteCovers.WORKER.purge();}
 public boolean onPreDraw(){Rect visible=new Rect();boolean show=owner.hasWindowFocus()&&getWindowVisibility()==VISIBLE&&isShown()&&getGlobalVisibleRect(visible)&&visible.width()>0;
  if(!show){if(loaded||loading)release();return true;}if(loaded||loading||SystemClock.elapsedRealtime()<retryAfter||getWidth()==0)return true;
  loading=true;final int request=++generation,w=getWidth(),h=getHeight();final android.content.Context context=owner.getApplicationContext();try{pending=RemoteCovers.WORKER.submit(()->{Bitmap result=null;String detail="Capa não encontrada • confira o nome do jogo";try{result=RemoteCovers.load(context,rom,w,h);}catch(Exception e){detail="Sem capa agora • jogo disponível";}final Bitmap cover=result;final String message=detail;post(()->{if(request!=generation||!isAttachedToWindow())return;loading=false;loaded=cover!=null;if(loaded){image.setImageBitmap(cover);placeholder.setVisibility(GONE);}else{retryAfter=SystemClock.elapsedRealtime()+60000;showName(message);}});});}catch(RejectedExecutionException e){loading=false;retryAfter=SystemClock.elapsedRealtime()+3000;}return true;
 }
}
