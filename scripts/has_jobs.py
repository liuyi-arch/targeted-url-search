# -*- coding: utf-8 -*-
"""3b 动作：职位列表检查（nav_verified 验证子动作）。方法：has_jobs（页面是否出现职位列表）。"""


def has_jobs(js):
    """页面是否出现职位列表。返回 bool。"""
    n = js("document.querySelectorAll('[class*=job-title],[class*=position],[class*=job-item]').length")
    return int(n or 0) > 0
