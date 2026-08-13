# -*- coding: utf-8 -*-
"""3a 兜底：SPA 极慢加载复查（仅 open_page.py 轮询超时正文仍 < 40 时调用）。用法：browser-use <<'PY' ... PY 中调用。

职责边界：wait_for_load + 再等复查；成败判定在流程内完成（正文 ≥ 40 + 标题无错误特征）。"""

import time


def open_page_wait(js, wait_for_load, min_len=40, wait_s=5):
    """wait_for_load + 再等 wait_s 复查。返回 bool 是否达标（正文 ≥ min_len）。"""
    wait_for_load()
    time.sleep(wait_s)
    wait_for_load()
    length = int(js("(document.body && document.body.innerText.length) || 0") or 0)
    print(f"BodyLen after wait: {length}")
    return length >= min_len
