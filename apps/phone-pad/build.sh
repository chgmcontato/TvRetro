#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${ANDROID_HOME:?Defina ANDROID_HOME para o SDK Android}"
: "${JAVA_HOME:?Defina JAVA_HOME para o JDK 17}"
export PATH="$JAVA_HOME/bin:$PATH"
bt="$ANDROID_HOME/build-tools/35.0.0"
jar="$ANDROID_HOME/platforms/android-35/android.jar"
mkdir -p build/classes build/dex
javac -encoding UTF-8 -source 8 -target 8 -classpath "$jar" -d build/classes src/com/carlos/snespad/MainActivity.java
"$bt/d8" --lib "$jar" --min-api 28 --output build/dex build/classes/com/carlos/snespad/*.class
"$bt/aapt2" compile --dir res -o build/resources.zip
"$bt/aapt2" link -o build/unsigned.apk -I "$jar" --manifest AndroidManifest.xml build/resources.zip
(cd build/dex && zip -q ../unsigned.apk classes.dex)
"$bt/zipalign" -f 4 build/unsigned.apk build/aligned.apk
: "${KEYSTORE:?Set KEYSTORE to a private keystore outside this repository}"
: "${KEYSTORE_PASS:?Set KEYSTORE_PASS in the build environment}"
export KEYSTORE_PASS
"$bt/apksigner" sign --ks "$KEYSTORE" --ks-pass env:KEYSTORE_PASS --out build/phone-pad.apk build/aligned.apk
"$bt/apksigner" verify --verbose build/phone-pad.apk
