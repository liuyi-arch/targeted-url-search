# -*- coding: utf-8 -*-
"""3e 判定 + 编排：按 KEYWORD 判定标题，提取命中职位（或第 1 个）链接。
底层方法（extract_a_links / extract_by_click / extract_via_window_open_click /
extract_via_api / extract_via_fiber_onclick）在 extract_links.py。
兜底顺序按 3 轮 23 站实测成功率排序（均 100%，按成本从低到高）：
a_links（零成本）→ by_click（点击跳转）→ window_open_click（点击+window.open 捕获）→
via_api（点击+监听资源）→ fiber_onclick（触发 fiber onClick，未实测）。"""

from extract_links import (
    extract_a_links,
    extract_by_click,
    extract_via_window_open_click,
    extract_via_api,
    extract_via_fiber_onclick,
)


def match_titles(titles, keyword):
    """3e：返回标题中含 KEYWORD（连续子串）的职位标题。"""
    return [t for t in titles if keyword and keyword in t]


def extract_matched_links(js, cdp, titles, keyword, max_click=5, sleep_s=1.5):
    """3e：判定后提取岗位链接。命中 → 命中职位链接；未命中 → 第 1 个职位链接。返回 [{title, link}]。
    兜底顺序：a_links → by_click → window_open_click → via_api → fiber_onclick（成功率优先 + 成本从低到高）。"""
    targets = match_titles(titles, keyword) or titles[:1]
    all_links = {it["title"]: it["link"] for it in extract_a_links(js)}
    results = [{"title": t, "link": all_links[t]} for t in targets if t in all_links]
    missing = [t for t in targets if t not in all_links]

    # 方法2：点击卡片 SPA 跳转取 URL（欣旺达/新安能 100%）
    if missing:
        for item in extract_by_click(js, cdp, missing, max_click=max_click, sleep_s=sleep_s):
            results.append({"title": item["title"], "link": item["url"]})
        missing = [t for t in missing if t not in {r["title"] for r in results}]

    # 方法3：点击卡片 window.open 新标签捕获（联想/百度/美团 100%，不依赖 __reactProps）
    if missing:
        for item in extract_via_window_open_click(js, missing, max_click=max_click, sleep_s=sleep_s):
            results.append({"title": item["title"], "link": item["url"]})
        missing = [t for t in missing if t not in {r["title"] for r in results}]

    # 方法4：点击卡片触发 API，performance 资源抓 uuid（Beisen 系 100%）
    if missing:
        for item in extract_via_api(js, cdp, missing, max_click=max_click, sleep_s=sleep_s):
            results.append({"title": item["title"], "link": item["url"]})
        missing = [t for t in missing if t not in {r["title"] for r in results}]

    # 方法5：触发 fiber onClick 捕获（未实测，最后尝试）
    if missing:
        for item in extract_via_fiber_onclick(js, missing, max_click=max_click):
            results.append({"title": item["title"], "link": item["url"]})
    return results
