#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$APP_DIR/typelib" ]; then
    export GI_TYPELIB_PATH="$APP_DIR/typelib${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
fi
exec /usr/bin/python3 "$APP_DIR/tvretro-tray.py" "$@"
