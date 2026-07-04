#!/usr/bin/env bash
# 桌面 Cursor 终端一键启动晶合688249 监控
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

INTERVAL="${1:-300}"
echo "晶合688249 监控 · 每 ${INTERVAL} 秒刷新 (Ctrl+C 退出)"
exec python3 tracker.py --watch "$INTERVAL"
