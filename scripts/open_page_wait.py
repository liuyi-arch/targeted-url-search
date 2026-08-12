# -*- coding: utf-8 -*-
"""3a 第二步：SPA 慢加载复查（仅 open_page.py 打开后正文 < 200 时调用）。用法：browser-use <<'PY' ... PY 中调用。

职责边界：wait_for_load 等待加载，正文仍不足 → 再等 5s 复查；成败判定在流程内完成（正文 ≥ 200 + 标题无错误特征）。
"""

import time
import json


def open_page_wait(js, wait_for_load, min_len=200):
    """wait_for_load() 等待加载，正文长度 < min_len（可能只渲染出骨架屏/加载动画）→ 再等 5s 复查。返回 True。"""
    wait_for_load()
    chk = js("JSON.stringify({len: document.body.innerText.length})")
    try:
        length = json.loads(chk).get("len", 0)
    except (ValueError, TypeError):
        length = 0
    if length < min_len:
        time.sleep(5)
        wait_for_load()
    return True
