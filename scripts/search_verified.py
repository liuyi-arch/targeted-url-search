# -*- coding: utf-8 -*-
"""3c 动作：验证搜索是否生效。动作文件内多个方法 = 不同实现方式：

- url_has_query()   —— 方法1：URL 带 q/query/keyword 参数（如汇川 ?q=前端）
- stats_changed()   —— 方法2：页面出现"共N个/职位列表N个"统计变化（如网易"职位列表 1 个"）
"""

import json
import re


def url_has_query(js):
    """方法1：URL 是否带 q/query/keyword 参数。返回 bool。"""
    u = js("location.href")
    return any(m in u.lower() for m in ['?q=', '&q=', 'query=', 'keyword='])


def stats_changed(js):
    """方法2：页面是否出现搜索统计变化（共N个/职位列表N个/暂无职位）。返回 bool。"""
    t = js("document.body.innerText.slice(0, 2000)")
    return bool(re.search(r'(共\s*\d+\s*(个|条)|职位列表\s*\d+\s*个|全部校招职位\s*\(\d+\)|暂无职位)', t))


def search_verified(js):
    """组合入口：任一方法命中即判定搜索生效。返回 bool。"""
    return url_has_query(js) or stats_changed(js)
