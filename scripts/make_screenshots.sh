#!/bin/sh
# Renders the screenshots in docs/images with a headless Chromium browser (Brave or Chrome) from frontend/demo.
# Needs the built bundle (cd frontend && npm run build). No Home Assistant and no switch involved: sample data only.
cd "$(dirname "$0")/.." || exit 1
BROWSER="${BROWSER:-/Applications/Brave Browser.app/Contents/MacOS/Brave Browser}"
python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER=$!
sleep 1
shot() { # name width height query
  "$BROWSER" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size="$2,$3" --virtual-time-budget=6000 --screenshot="docs/images/$1.png" \
    "http://127.0.0.1:8765/frontend/demo/index.html?$4" >/dev/null 2>&1
  echo "docs/images/$1.png"
}
shot panel-overview 1100 520 "view=overview&scheme=reactor&mode=dark&ha=dark"
shot panel-device 1100 900 "view=device&port=1&scheme=reactor&mode=dark&ha=dark&devices=1"
shot panel-device-light 1100 900 "view=device&port=2&scheme=cockpit&mode=light&ha=light&devices=1"
shot panel-settings 1100 700 "view=settings&scheme=plasma&mode=dark&ha=dark&devices=1"
shot card-dark 600 760 "kind=card&ha=dark"
shot card-light 600 760 "kind=card&ha=light"
kill $SERVER
