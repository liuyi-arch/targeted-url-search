# -*- coding: utf-8 -*-
"""3d 取搜索结果标题（最多 5 个）。判空后供 3e 判定 KEYWORD 是否命中。"""

import json

from extract_links import extract_a_links, JOB_CONTAINER_SELECTOR


NAV_EXCLUDE = "header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab], [class*=footer]"
MAX_TITLES = 5  # 3d 上限


def extract_container_titles(js):
    """岗位标题容器文本提取（去重限长，排除导航区/菜单误命中）。返回 [str]。"""
    titles = json.loads(js("""
    JSON.stringify([...document.querySelectorAll('%s')]
      .filter(e => e.offsetParent !== null)
      .filter(e => !e.closest('%s'))
      .map(e => e.textContent.trim())
      .filter(t => t.length > 2 && t.length < 60))
    """ % (JOB_CONTAINER_SELECTOR, NAV_EXCLUDE)))
    seen, out = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def get_job_titles(js, limit=MAX_TITLES):
    """3d：判空并取最多 limit 个职位标题。返回 [str]；空结果返回 []。"""
    titles = extract_container_titles(js)
    if not titles:
        titles = [it["title"] for it in extract_a_links(js)]
    return titles[:limit]
