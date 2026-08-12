# -*- coding: utf-8 -*-
"""3b 动作：验证导航结果（组合动作）。方法：

- nav_verified()          —— 成功判定（意图充分条件）：URL 变化 且（搜索框 或 职位列表）
- has_type_evidence()     —— M 类归因证据：页面是否含目标类型关键词（校招/实习/职位字样）

子动作各自独立成文件（url_changed / has_search_input / has_jobs），便于单独复用。
"""

from url_changed import url_changed
from has_search_input import has_search_input
from has_jobs import has_jobs


def nav_verified(js, before_url=None):
    """成功判定：URL 变化（传入 before_url 时校验，否则仅非空）且 页面出现搜索框或职位列表。返回 bool。"""
    if before_url and not url_changed(js, before_url):
        return False
    return has_search_input(js) or has_jobs(js)


def has_type_evidence(js, mode):
    """M 类归因证据：页面文本是否含目标类型关键词（说明目标类型职位视图存在，只是方法未命中）。返回 bool。"""
    kw_map = {1: ['校园招聘', '校招', '应届', '校招职位', '校招岗位'],
              2: ['实习招聘', '实习生', '实习'],
              3: ['职位', '招聘职位', '职位列表', '岗位', '岗位投递']}
    kws = kw_map.get(mode, kw_map[1])
    txt = js("document.body.innerText.slice(0, 3000)")
    return any(k in txt for k in kws)
