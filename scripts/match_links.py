# -*- coding: utf-8 -*-
"""3e 判定 + 编排：按 KEYWORD 判定标题，提取命中职位（或第 1 个）链接。
底层方法（extract_a_links / extract_by_click / extract_via_fiber_onclick）在 extract_links.py。"""

from extract_links import extract_a_links, extract_by_click, extract_via_fiber_onclick


def match_titles(titles, keyword):
    """3e：返回标题中含 KEYWORD（连续子串）的职位标题。"""
    return [t for t in titles if keyword and keyword in t]


def extract_matched_links(js, cdp, titles, keyword, max_click=5, sleep_s=1.5):
    """3e：判定后提取岗位链接。命中 → 命中职位链接；未命中 → 第 1 个职位链接。返回 [{title, link}]。"""
    targets = match_titles(titles, keyword) or titles[:1]
    all_links = {it["title"]: it["link"] for it in extract_a_links(js)}
    results = [{"title": t, "link": all_links[t]} for t in targets if t in all_links]
    missing = [t for t in targets if t not in all_links]
    if missing:
        for item in extract_by_click(js, cdp, missing, max_click=max_click, sleep_s=sleep_s):
            results.append({"title": item["title"], "link": item["url"]})
        still_missing = [t for t in missing if t not in {r["title"] for r in results}]
        if still_missing:
            for item in extract_via_fiber_onclick(js, still_missing, max_click=max_click):
                results.append({"title": item["title"], "link": item["url"]})
    return results
