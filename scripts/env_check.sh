#!/usr/bin/env bash
# -*- coding: utf-8 -*-
"""环境检查 + Chrome 调试实例启动（Step 0）。
用法：bash scripts/env_check.sh

要点：
- pkill 只精确匹配调试端口参数，避免误杀用户日常 Chrome。
- open -a 在 Chrome 已运行时 --args 会被忽略（端口不监听）→ 用二进制直接启动兜底。
"""

set -e

# 1) 清理旧调试实例（只匹配调试端口，不误杀日常 Chrome）
pkill -9 -f "remote-debugging-port=9222" 2>/dev/null || true
sleep 1

# 2) 优先用 open -a（macOS 常规方案）
if ! open -a "Google Chrome" --args --remote-debugging-port=9222 2>/dev/null; then
    echo "open -a 失败，改用二进制直接启动"
fi

# 3) 验证端口是否监听；未监听则二进制启动（Chrome 已运行时 open 的 --args 被忽略）
if ! lsof -i :9222 -sTCP:LISTEN >/dev/null 2>&1; then
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      --remote-debugging-port=9222 \
      --no-sandbox --disable-gpu --disable-dev-shm-usage \
      --user-data-dir=/tmp/chrome-debug-profile \
      about:blank > /tmp/chrome-debug.log 2>&1 &
    sleep 2
fi

# 4) 验证 browser-use 连接
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor
