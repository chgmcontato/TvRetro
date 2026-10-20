"""Exercise the production permission adapter with API 21/22/23/35 JVM doubles.
These tests do not replace execution on Android hardware or an emulator.
"""
import os,subprocess,tempfile,unittest
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
java=Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java'
class PlatformCompatTests(unittest.TestCase):
 def test_permission_dispatch(self):
  sources={
   'android/os/Build.java':'package android.os; public class Build {public static class VERSION {public static int SDK_INT;}}',
   'android/content/pm/PackageManager.java':'package android.content.pm; public class PackageManager {public static final int PERMISSION_GRANTED=0;}',
   'android/app/Activity.java':'''package android.app; import android.os.Build; public class Activity {public int legacy,modern,requests,permission;public int checkCallingOrSelfPermission(String p){legacy++;return permission;}public int checkSelfPermission(String p){if(Build.VERSION.SDK_INT<23)throw new AssertionError("API 23 invoked on old Android");modern++;return permission;}public void requestPermissions(String[] p,int code){if(Build.VERSION.SDK_INT<23)throw new AssertionError("API 23 invoked on old Android");if(code!=20||p.length!=1)throw new AssertionError();requests++;}}''',
   'com/ansub/tvhome/PlatformCompatTests.java':'''package com.ansub.tvhome; import android.app.Activity; import android.os.Build; public class PlatformCompatTests {public static void main(String[] args){for(int api:new int[]{21,22,23,35}){Build.VERSION.SDK_INT=api;Activity a=new Activity();a.permission=0;if(!PlatformCompat.hasPermission(a,"permission"))throw new AssertionError();a.permission=-1;if(PlatformCompat.hasPermission(a,"permission"))throw new AssertionError();PlatformCompat.requestPermissions(a,new String[]{"permission"},20);if(api<23?(a.legacy!=2||a.modern!=0||a.requests!=0):(a.legacy!=0||a.modern!=2||a.requests!=1))throw new AssertionError("Dispatch API "+api);}System.out.println("Permissões: API 21, 22, 23 e 35 aprovadas com doubles JVM.");}}'''
  }
  with tempfile.TemporaryDirectory(prefix='tvretro-platform-') as folder:
   base=Path(folder);files=[]
   for name,content in sources.items():
    p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);files.append(str(p))
   files.append(str(repo/'apps/tv-casa/src/com/ansub/tvhome/PlatformCompat.java'))
   subprocess.run([str(java.with_name('javac')),'-source','1.8','-target','1.8','-d',str(base)]+files,check=True)
   subprocess.run([str(java),'-cp',str(base),'com.ansub.tvhome.PlatformCompatTests'],check=True)
if __name__=='__main__':unittest.main(verbosity=2)
