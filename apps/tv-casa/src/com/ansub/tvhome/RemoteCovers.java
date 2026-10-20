package com.ansub.tvhome;

import android.content.Context;
import android.graphics.*;
import android.util.LruCache;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** HTTPS-only thumbnails. No ROM upload, no API key, no persistent image files. */
final class RemoteCovers {
 static final ThreadPoolExecutor WORKER=new ThreadPoolExecutor(0,1,20,TimeUnit.SECONDS,new ArrayBlockingQueue<Runnable>(16));
 private static final LruCache<String,Bitmap> IMAGES=new LruCache<String,Bitmap>(3*1024*1024){protected int sizeOf(String k,Bitmap b){return b.getByteCount();}};
 private static volatile int epoch;
 private static final Map<String,ThumbnailCatalog> CATALOGS=new HashMap<>();private static final Map<String,Long> FAILED=new HashMap<>();
 static void clearMemory(){epoch++;IMAGES.evictAll();WORKER.purge();}
 private static HttpURLConnection connect(String path,int limit)throws IOException{URL url=new URL(path);if(!url.getProtocol().equals("https")||!url.getHost().equals("thumbnails.libretro.com"))throw new IOException("Fonte de capa inválida");HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setConnectTimeout(6000);c.setReadTimeout(5000);c.setInstanceFollowRedirects(false);c.setRequestProperty("User-Agent","TvRetro/0.9 (cover thumbnails)");int status=c.getResponseCode();if(status!=200||c.getContentLength()>limit){c.disconnect();if(status==404)throw new FileNotFoundException("Capa não encontrada");throw new IOException("Capa ou catálogo indisponível");}return c;}
 private static class Limited extends FilterInputStream {private int remaining;private final long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);Limited(InputStream in,int max){super(in);remaining=max;}public int read()throws IOException{if(remaining<=0||System.nanoTime()>deadline)throw new IOException("Resposta excedeu limite");int n=super.read();if(n>=0)remaining--;return n;}public int read(byte[] b,int off,int len)throws IOException{if(remaining<=0||System.nanoTime()>deadline)throw new IOException("Resposta excedeu limite");int n=in.read(b,off,Math.min(len,remaining));if(n>=0)remaining-=n;return n;}}
 private static ThumbnailCatalog catalog(String system)throws IOException{ThumbnailCatalog existing=CATALOGS.get(system);if(existing!=null)return existing;Long failed=FAILED.get(system);if(failed!=null&&System.currentTimeMillis()-failed<60000)throw new IOException("Catálogo temporariamente indisponível");HttpURLConnection c=null;try{c=connect(ThumbnailCatalog.base(system),4*1024*1024);try(InputStream in=new Limited(c.getInputStream(),4*1024*1024)){ThumbnailCatalog result=ThumbnailCatalog.parse(in);CATALOGS.put(system,result);FAILED.remove(system);return result;}}catch(IOException e){FAILED.put(system,System.currentTimeMillis());throw e;}finally{if(c!=null)c.disconnect();}}
 static String system(File rom){return rom.getName().toLowerCase(Locale.ROOT).matches(".*\\.(sfc|smc)$")?ThumbnailCatalog.SNES:ThumbnailCatalog.PSX;}
 static Bitmap load(Context context,File rom,int width,int height)throws IOException{
  final int requestEpoch=epoch;String console=system(rom),requested=rom.getName();Properties hints=new Properties();try(InputStream in=context.getAssets().open("cover-hints.properties")){hints.load(in);String hint=hints.getProperty((console.equals(ThumbnailCatalog.SNES)?"SNES/":"PSX/")+rom.getName());if(hint!=null)requested=hint;}catch(IOException ignored){}
  String direct=ThumbnailCatalog.candidate(requested);if(direct!=null)try{return image(ThumbnailCatalog.base(console)+ThumbnailCatalog.encode(direct),width,height,requestEpoch);}catch(FileNotFoundException missing){}
  String title=catalog(console).find(requested);if(title==null)return null;if(requestEpoch!=epoch)throw new IOException("Busca de capa encerrada");return image(ThumbnailCatalog.base(console)+ThumbnailCatalog.encode(title),width,height,requestEpoch);
 }
 private static Bitmap image(String url,int width,int height,int requestEpoch)throws IOException{
  String key=url+"@"+width+"x"+height;Bitmap cached=IMAGES.get(key);if(cached!=null)return cached;
  HttpURLConnection c=connect(url,2*1024*1024);byte[] bytes;try(InputStream in=new Limited(c.getInputStream(),2*1024*1024);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] block=new byte[16384];int n;while((n=in.read(block))!=-1)out.write(block,0,n);bytes=out.toByteArray();}finally{c.disconnect();}
  BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);if(options.outWidth<=0||options.outHeight<=0||options.outWidth>4096||options.outHeight>4096)throw new IOException("Dimensões de capa inválidas");int sample=1;while(options.outWidth/(sample*2)>=width&&options.outHeight/(sample*2)>=height)sample*=2;options.inJustDecodeBounds=false;options.inSampleSize=sample;options.inPreferredConfig=Bitmap.Config.RGB_565;Bitmap image=BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);if(image==null)throw new IOException("Imagem inválida");if(requestEpoch==epoch)IMAGES.put(key,image);return image;
 }
}
