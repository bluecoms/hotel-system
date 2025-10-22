#!/bin/sh
set -e
echo "PID: $(cat /tmp/vite.pid 2>/dev/null || echo '-')"
busybox netstat -ltn 2>/dev/null | grep ':5176' || echo "port 5176: no listener"
curl -Is http://127.0.0.1:5176/ | head -n1 || true
tail -n 40 /tmp/vite.out || true
