# -*- coding: utf-8 -*-
"""3a 第一步：goto_url 导航打开页面并取状态。用法：browser-use <<'PY' ... PY 中调用。

职责边界：本文件只负责"导航 + 取页面状态"，成败判定在流程内完成
（意图=页面可进入后续流程：正文 ≥ 200 + 标题无错误特征）；正文 < 200（SPA 慢加载）→ 由 open_page_wait.py 复查。
"""

import time


def open_page(goto_url, page_info, url, sleep_s=3.0):
    """goto_url 在当前标签页导航（站点间不 new_tab，100+ 站点内存爆炸），sleep 后取标题确认。返回 page_info() 结果。"""
    goto_url(url)
    time.sleep(sleep_s)
    info = page_info()
    print(f"Title: {info.get('title', '')}")
    return info
