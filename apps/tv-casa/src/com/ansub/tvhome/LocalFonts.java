package com.ansub.tvhome;
import android.content.Context;
import android.graphics.Typeface;
/** User-provided fonts are optional and are never required to build the source. */
final class LocalFonts {
 static Typeface get(Context c,boolean bold){try{return Typeface.createFromAsset(c.getAssets(),bold?"fonts/Courier_New_Bold.ttf":"fonts/Courier_New.ttf");}catch(RuntimeException e){return Typeface.create(Typeface.MONOSPACE,bold?Typeface.BOLD:Typeface.NORMAL);}}
}
