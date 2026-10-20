package com.ansub.tvhome;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.text.Normalizer;
import java.util.*;
import java.util.regex.*;

/** Pure Java catalogue parser/matcher: never guesses between different ambiguous titles. */
public final class ThumbnailCatalog {
 public static final String SNES="Nintendo - Super Nintendo Entertainment System",PSX="Sony - PlayStation";
 private final Map<String,List<String>> titles=new HashMap<>();
 public static String normalize(String value){return Normalizer.normalize(value.replaceFirst("(?i)\\.(sfc|smc|chd|cue|bin|pbp|m3u|png)$","").replaceAll("\\([^)]*\\)|\\[[^]]*\\]"," "),Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]+"," ").trim().replaceFirst(" gold cartridge$","");}
 public static String encode(String value){try{return URLEncoder.encode(value,"UTF-8").replace("+","%20");}catch(Exception e){throw new IllegalArgumentException(e);}}
 public static String base(String system){if(!SNES.equals(system)&&!PSX.equals(system))throw new IllegalArgumentException("Console não suportado");return "https://thumbnails.libretro.com/"+encode(system)+"/Named_Boxarts/";}
 public static ThumbnailCatalog parse(InputStream stream)throws IOException{
  ThumbnailCatalog catalog=new ThumbnailCatalog();BufferedReader reader=new BufferedReader(new InputStreamReader(stream,StandardCharsets.UTF_8));Pattern href=Pattern.compile("href=\"([^\"]+)\"",Pattern.CASE_INSENSITIVE);String line;int total=0,count=0;
  while((line=reader.readLine())!=null){total+=line.length();if(total>4*1024*1024||line.length()>32768)throw new IOException("Catálogo excedeu limite");Matcher m=href.matcher(line);while(m.find()){String raw=m.group(1);if(!raw.toLowerCase(Locale.ROOT).endsWith(".png"))continue;String filename;try{filename=URLDecoder.decode(raw.replace("+","%2B"),"UTF-8");}catch(IllegalArgumentException e){continue;}if(filename.length()>512||filename.indexOf('/')>=0||filename.indexOf('\\')>=0||filename.indexOf(':')>=0||filename.matches(".*[\\p{Cntrl}].*"))continue;String title=normalize(filename);if(title.isEmpty())continue;if(++count>16000)throw new IOException("Catálogo excedeu limite");List<String> versions=catalog.titles.get(title);if(versions==null){versions=new ArrayList<>();catalog.titles.put(title,versions);}versions.add(filename);}}
  if(catalog.titles.isEmpty())throw new IOException("Catálogo sem títulos");return catalog;
 }
 public String find(String romName){String wanted=normalize(romName);if(wanted.isEmpty())return null;List<String> versions=titles.get(wanted);
  if(versions==null){String match=null;for(String title:titles.keySet())if(title.startsWith(wanted+" - ")||title.startsWith(wanted+" ")){if(match!=null)return null;match=title;}if(match!=null)versions=titles.get(match);}
  if(versions==null)return null;String best=null;int bestScore=Integer.MIN_VALUE;for(String f:versions){String n=f.toLowerCase(Locale.ROOT),request=romName.toLowerCase(Locale.ROOT);int score=n.contains("(usa")?50:n.contains("(world")?40:n.contains("(europe")?30:0;for(String region:new String[]{"japan","europe","usa","brazil"})if(request.contains("("+region+")")&&n.contains("("+region))score+=100;if(request.contains("(j)")&&n.contains("(japan"))score+=100;if(n.contains("sample")||n.contains("beta")||n.contains("proto")||n.contains("demo"))score-=100;if(n.contains("disc 1"))score+=5;if(best==null||score>bestScore||score==bestScore&&f.compareTo(best)<0){best=f;bestScore=score;}}return best;
 }
 public static String candidate(String romName){String name=romName.replaceFirst("(?i)\\.(sfc|smc|chd|cue|bin|pbp|m3u)$","").replaceAll("\\([^)]*\\)|\\[[^]]*\\]"," ").replace('_',' ').replaceAll("\\s+"," ").trim().replaceFirst("(?i) gold cartridge$","");if(name.isEmpty())return null;String n=romName.toLowerCase(Locale.ROOT),region="USA";if(n.contains("(j)")||n.contains("(japan"))region="Japan";else if(n.contains("(e)")||n.contains("(europe"))region="Europe";else if(n.contains("(world"))region="World";else if(n.contains("(brazil"))region="Brazil";return name+" ("+region+").png";}
 public int size(){return titles.size();}
}
