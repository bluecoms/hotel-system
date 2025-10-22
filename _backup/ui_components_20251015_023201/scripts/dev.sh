#!/bin/sh
set -e
cd "$(dirname "$0")/.."
pkill -f "node.*vite.js" >/dev/null 2>&1 || true
: > /tmp/vite.out
nohup node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5176 --strictPort \
  </dev/null >/tmp/vite.out 2>&1 & echo $! > /tmp/vite.pid
sleep 0.7
tail -n 60 /tmp/vite.out || true
