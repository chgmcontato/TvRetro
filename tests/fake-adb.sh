#!/usr/bin/env bash
# adb falso para testar tools/debloat sem uma TV. Estado em $FAKE_ADB_DIR.
D="${FAKE_ADB_DIR:?}"
echo "adb $*" >> "$D/calls.log"
[ "${1:-}" = -s ] && shift 2
cmd="${1:-}"; shift || true
touch "$D/packages" "$D/disabled" "$D/persistent" "$D/tvlist" "$D/home_extra"
case "$cmd" in
  connect) echo "connected to ${1:-}"; exit 0 ;;
  devices) printf 'List of devices attached\n127.0.0.1:5555\tdevice\n'; exit 0 ;;
  get-state) echo device; exit 0 ;;
  reboot) touch "$D/rebooted"; exit 0 ;;
  shell) ;;
  *) exit 1 ;;
esac
c="$*"
set -- $c
case "$c" in
  "pm list packages -d "*) grep -Fx -- "$5" "$D/disabled" | sed 's/^/package:/'; exit 0 ;;
  "pm list packages -d") sed 's/^/package:/' "$D/disabled"; exit 0 ;;
  "pm list packages -s -f"|"pm list packages -f") while read -r p; do [ -n "$p" ] && echo "package:/system/priv-app/$p/$p.apk=$p"; done < "$D/packages"; exit 0 ;;
  "pm list packages") sed 's/^/package:/' "$D/packages"; exit 0 ;;
  "pm disable-user --user 0 "*)
    p="$5"
    if grep -Fxq -- "$p" "$D/packages"; then
      echo "$p" >> "$D/disabled"
      if [ -f "$D/steal" ] && grep -Fxq -- "$p" "$D/steal"; then echo "com.google.android.tungsten.setupwraith/.Home" > "$D/home"; fi
      echo "Package $p new state: disabled-user"
    fi; exit 0 ;;
  "pm enable "*) grep -Fxv -- "$3" "$D/disabled" > "$D/disabled.tmp"; mv "$D/disabled.tmp" "$D/disabled"; echo "Package $3 new state: enabled"; exit 0 ;;
  "getprop ro.product.model") echo FakeTV; exit 0 ;;
  "getprop ro.product.brand") echo Fake; exit 0 ;;
  "getprop ro.build.version.release") echo 11; exit 0 ;;
  "cmd package resolve-activity --brief"*) echo "priority=0 preferredOrder=0 match=0x0 specificIndex=-1 isDefault=true"; cat "$D/home"; exit 0 ;;
  "cmd package query-activities --brief"*) echo "2 activities found:"; echo "  priority=0 isDefault=false"; echo "  $(cat "$D/home")"; sed 's/^/  /' "$D/home_extra"; exit 0 ;;
  "cmd package set-home-activity "*) echo "$4" > "$D/home"; echo "Success"; exit 0 ;;
  "dumpsys package "*)
    p="$3"
    if grep -Fxq -- "$p" "$D/packages"; then
      if grep -Fxq -- "$p" "$D/persistent"; then echo "    pkgFlags=[ SYSTEM HAS_CODE PERSISTENT ]"; else echo "    pkgFlags=[ SYSTEM HAS_CODE ALLOW_CLEAR_USER_DATA ]"; fi
    fi; exit 0 ;;
  "settings get "*) f="$D/set_${3}_${4}"; if [ -f "$f" ]; then cat "$f"; else echo null; fi; exit 0 ;;
  "settings put "*) echo "$5" > "$D/set_${3}_${4}"; exit 0 ;;
  "settings delete "*) rm -f "$D/set_${3}_${4}"; exit 0 ;;
  "echo "*">> /data/local/tmp/tvretro-disabled.txt") echo "$2" >> "$D/tvlist"; exit 0 ;;
  "if [ -e /data/local/tmp/tvretro-disabled.txt ]"*) cat "$D/tvlist"; exit 0 ;;
  "rm -f /data/local/tmp/tvretro-disabled.txt") : > "$D/tvlist"; exit 0 ;;
esac
echo "fake-adb: comando não tratado: $c" >&2
exit 1
