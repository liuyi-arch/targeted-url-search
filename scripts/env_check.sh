#!/usr/bin/env bash
# Step 0：启动独立 Chrome 调试实例（端口 0 自动分配 + 唯一 profile）→ 读端口 → 轮询验证。
# 端口 0 + 唯一 profile：系统自动分配空闲端口、绕开单实例锁，无需清理旧实例（不按端口 kill，防误杀用户 Chrome）。
set -uo pipefail

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE="/tmp/chrome-debug-profile-$(date +%s)"
PORT_FILE="${PROFILE}/DevToolsActivePort"
LOG="/tmp/chrome-debug.log"

# 启动独立 Chrome（端口 0 自动分配；--disable-blink-features 防反自动化站点导航走）
"${CHROME_BIN}" --remote-debugging-port=0 --remote-debugging-address=127.0.0.1 \
  --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-blink-features=AutomationControlled \
  --user-data-dir="${PROFILE}" about:blank > "${LOG}" 2>&1 &

# 轮询读端口并验证就绪（DevToolsActivePort 第一行即端口号，≤15s）
PORT=""
for i in $(seq 1 15); do
    if [ -f "${PORT_FILE}" ] && [ -s "${PORT_FILE}" ]; then
        PORT=$(head -1 "${PORT_FILE}")
        curl -sf "http://127.0.0.1:${PORT}/json/version" | grep -q '"Browser"' && break
        PORT=""
    fi
    sleep 1
done

if [ -z "${PORT}" ]; then
    echo "[FAIL] Chrome 调试实例未就绪" >&2
    tail -5 "${LOG}" 2>/dev/null || true
    exit 1
fi
echo "[ok] Chrome 调试实例就绪，端口 ${PORT}（系统自动分配，独立 profile）"
echo "[hint] browser-use 须带: export BU_CDP_URL=http://127.0.0.1:${PORT}"
