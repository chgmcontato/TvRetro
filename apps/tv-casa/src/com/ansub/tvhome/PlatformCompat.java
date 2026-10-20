package com.ansub.tvhome;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;

/** Runtime permission APIs exist only from Android 6.0; older releases grant at install. */
final class PlatformCompat {
 private PlatformCompat(){}
 static boolean hasPermission(Activity owner,String permission){return (Build.VERSION.SDK_INT>=23?owner.checkSelfPermission(permission):owner.checkCallingOrSelfPermission(permission))==PackageManager.PERMISSION_GRANTED;}
 static void requestPermissions(Activity owner,String[] permissions,int requestCode){if(Build.VERSION.SDK_INT>=23)owner.requestPermissions(permissions,requestCode);}
}
