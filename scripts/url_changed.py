# -*- coding: utf-8 -*-
"""3b 动作：URL 变化检查（nav_verified 子动作）。方法：url_changed（对比导航前后 URL）。"""


def url_changed(js, before_url):
    """URL 是否从 before_url 发生变化。返回 bool。"""
    cur = js("location.href")
    return bool(cur and cur != before_url)
