# -*- coding: utf-8 -*-
"""3a 第一步：导航 + 轮询等待页面就绪并取状态。用法：browser-use <<'PY' ... PY 中调用。

职责边界：本文件只负责"导航 + 轮询就绪 + 取状态"；成败判定在流程内完成（正文 ≥ 40 + 标题无错误特征）。
默认 min_len=40：适配轻量页面（内推绑定页/登录页等正文 <200 但正常加载的场景，如招商 bindInvited 正文 45）；
轮询超时正文仍 < 40（SPA 极慢加载）→ 由 open_page_wait.py 兜底。
注意：阈值调低后，正文 40-200 的页面会通过 3a，是否可进入流程由 3b nav_verified（URL 变化 + 搜索框/职位列表）二次把关。"""

import time


def open_page(goto_url, js, url, min_len=40, timeout=15, sleep_s=1.0):
    """goto_url 导航（不 new_tab），轮询正文 ≥ min_len（每 sleep_s 查一次，最多 timeout s）。返回 (title, body_len)。"""
    goto_url(url)
    title, length = "", 0
    for _ in range(int(timeout / sleep_s)):
        title = js("document.title")
        length = int(js("(document.body && document.body.innerText.length) || 0") or 0)
        if length >= min_len:
            break
        time.sleep(sleep_s)
    print(f"Title: {title} | BodyLen: {length}")
    return title, length
