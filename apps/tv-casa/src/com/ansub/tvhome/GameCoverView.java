package com.ansub.tvhome;

import android.app.Activity;
import android.graphics.*;
import android.view.*;
import android.widget.ImageView;
import java.util.concurrent.*;

/** Decode only covers intersecting the viewport; release references outside it. */
final class GameCoverView extends ImageView implements ViewTreeObserver.OnPreDrawListener {
 private static final ExecutorService WORKER=new ThreadPoolExecutor(0,1,20,TimeUnit.SECONDS,new LinkedBlockingQueue<Runnable>());
 private final String asset;private final Activity owner;private boolean loading,loaded,failed;private int generation;
 GameCoverView(Activity owner,String id){super(owner);this.owner=owner;asset="covers/"+id+".png";setScaleType(ScaleType.FIT_CENTER);setBackgroundColor(0xFF161820);}
 protected void onAttachedToWindow(){super.onAttachedToWindow();getViewTreeObserver().addOnPreDrawListener(this);}
 protected void onDetachedFromWindow(){if(getViewTreeObserver().isAlive())getViewTreeObserver().removeOnPreDrawListener(this);release();super.onDetachedFromWindow();}
 public void release(){generation++;loading=false;loaded=false;setImageDrawable(null);}
 public boolean onPreDraw(){Rect visible=new Rect();boolean show=owner.hasWindowFocus()&&getWindowVisibility()==VISIBLE&&isShown()&&getGlobalVisibleRect(visible)&&visible.width()>0;
  if(!show){if(loaded||loading)release();return true;}if(loaded||loading||failed||getWidth()==0)return true;
  loading=true;final int request=++generation,w=getWidth(),h=getHeight();WORKER.execute(()->{Bitmap image=null;try{BitmapFactory.Options opts=new BitmapFactory.Options();opts.inJustDecodeBounds=true;try(java.io.InputStream in=getContext().getAssets().open(asset)){BitmapFactory.decodeStream(in,null,opts);}int sample=1;while(opts.outWidth/(sample*2)>=w&&opts.outHeight/(sample*2)>=h)sample*=2;opts.inJustDecodeBounds=false;opts.inSampleSize=sample;opts.inPreferredConfig=Bitmap.Config.RGB_565;try(java.io.InputStream in=getContext().getAssets().open(asset)){image=BitmapFactory.decodeStream(in,null,opts);}}catch(Exception ignored){}final Bitmap result=image;post(()->{if(request!=generation||!isAttachedToWindow()){if(result!=null)result.recycle();return;}loading=false;loaded=result!=null;failed=result==null;setImageBitmap(result);});});return true;
 }
}
