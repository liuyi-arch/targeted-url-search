# -*- coding: utf-8 -*-
"""3a 打开页面：createTarget 新开 tab + 轮询就绪 + switch_tab 设置 active session（方案 A 默认，禁用 goto_url/new_tab 封装）。"""

import time


def open_page_create(cdp, js, url, min_len=40, timeout=15, sleep_s=1.0, switch_tab=None):
    """createTarget 新开 tab + 轮询正文 ≥ min_len。返回 (tid, title, body_len)；处理完须 close_tab_keepalive 释放。
    传 switch_tab（browser-harness 内置）→ 打开后自动激活该 tab（activateTarget+attach+set_session），
    此后裸 js()/cdp() 默认执行在该 tab，根治"js() 落在 about:blank"坑。"""
    tid = cdp("Target.createTarget", url=url)["targetId"]
    if switch_tab:
        try:
            switch_tab(tid)
        except Exception:
            pass  # 激活失败不阻断，仍可用 target_id 定向
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
