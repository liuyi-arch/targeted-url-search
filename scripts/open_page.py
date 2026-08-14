# -*- coding: utf-8 -*-
"""3a 打开页面：createTarget 新开 tab + 轮询就绪（方案 A 默认，禁用 goto_url/new_tab 封装）。"""

import time


def open_page_create(cdp, js, url, min_len=40, timeout=15, sleep_s=1.0):
    """createTarget 新开 tab + 轮询正文 ≥ min_len。返回 (tid, title, body_len)；处理完须 close_tab_keepalive 释放。"""
    tid = cdp("Target.createTarget", url=url)["targetId"]
    title, length = "", 0
    for _ in range(int(timeout / sleep_s)):
        try:
            title = js("document.title", target_id=tid)
            length = int(js("(document.body && document.body.innerText.length) || 0", target_id=tid) or 0)
        except Exception:
            title, length = "", 0
        if length >= min_len:
            break
        time.sleep(sleep_s)
    print(f"TID: {tid} | Title: {title} | BodyLen: {length}")
    return tid, title, length
