#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Step 0 环境检查：清端口占用 → 二进制启动 Chrome(9222, IPv4) → 轮询验证端口。
# 注意：不用 open -a（Chrome 已运行时 --args 被忽略）；成功判定仅以 9222 /json/version 为准（pipe 模式自动连接）。

set -uo pipefail

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT=9222
PROFILE="/tmp/chrome-debug-profile"
LOG="/tmp/chrome-debug.log"

# 1) 清空 9222 占用（按端口杀，彻底清理任何残留实例；9222 为调试专用端口，无日常 Chrome 误杀风险）
lsof -ti :${PORT} | xargs kill -9 2>/dev/null || true
sleep 1

# 2) 二进制启动：独立 profile 防冲突；--no-sandbox 必需（否则沙箱初始化失败）；强制 IPv4（否则只监听 [::1] 验证连不上）
"${CHROME_BIN}" \
  --remote-debugging-port=${PORT} \
  --remote-debugging-address=127.0.0.1 \
  --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --user-data-dir="${PROFILE}" \
  about:blank > "${LOG}" 2>&1 &

# 3) 轮询验证端口（冷启动可能 >2s，最多 15s）
PORT_OK=0
for i in $(seq 1 15); do
    if curl -sf "http://127.0.0.1:${PORT}/json/version" | grep -q '"Browser"'; then
        PORT_OK=1
        break
    fi
    sleep 1
done

if [ "${PORT_OK}" != "1" ]; then
    echo "[FAIL] Chrome 调试端口 ${PORT} 未监听" >&2
    echo "--- ${LOG} 尾部日志 ---" >&2
    tail -5 "${LOG}" 2>/dev/null || true
    exit 1
fi
echo "[ok] Chrome 调试端口 ${PORT} 已监听"
