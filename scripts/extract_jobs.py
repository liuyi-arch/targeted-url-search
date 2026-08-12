# -*- coding: utf-8 -*-
"""3d/3e 取搜索结果标题并按 KEYWORD 连续子串筛选提取岗位链接。用法：browser-use <<'PY' ... PY 中调用。
3d：get_job_titles 判空并取最多 5 个职位标题；3e：extract_matched_links 判定后提取命中职位（或第一个职位）的链接。"""

import time
import json


JOB_CONTAINER_SELECTOR = (
    "[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],"
    "[class*=post],[class*=position-name],[class*=jobName],[class*=job-name]"
)

MAX_TITLES = 5  # 3d 上限：最多取 5 个职位标题


def extract_a_links(js):
    """`<a>` 链接提取（href 含 position/job/detail/recruit 或位于岗位容器内）。返回 [{title, link}]。"""
    return json.loads(js("""
    JSON.stringify([...document.querySelectorAll('a')].filter(a => {
        const t = a.textContent.trim();
        const h = a.href || '';
        return t.length > 2 && t.length < 200 &&
               (h.includes('position')||h.includes('job')||h.includes('detail')||h.includes('recruit') ||
                a.closest('[class*=JobTitle],[class*=job-title],[class*=position],[class*=job-item]'));
    }).map(a => ({title: a.textContent.trim(), link: a.href})))
    """))


def extract_container_titles(js):
    """岗位标题容器文本提取（去重限长）。返回 [str]。"""
    titles = json.loads(js("""
    JSON.stringify([...document.querySelectorAll('%s')]
      .filter(e => e.offsetParent !== null)
      .map(e => e.textContent.trim())
      .filter(t => t.length > 2 && t.length < 60))
    """ % JOB_CONTAINER_SELECTOR))
    seen, out = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def extract_by_click(js, cdp, titles, max_click=5, sleep_s=1.5):
    """点击岗位容器触发 SPA 跳转取详情 URL（<a> 取不到时补，最多前 max_click 个）。
    点击 → URL 变化则记录 → history.back() 回退；React 卡片 JS .click() 不触发 → real_click。返回 [{title, url}]。"""
    results = []
    for title in titles[:max_click]:
        before = js("location.href")
        clicked = js("""
        (function(){
            let els = [...document.querySelectorAll('%s')];
            let el = els.find(e => e.textContent.trim() === %r && e.offsetParent !== null);
            if(!el) return 'nf';
            el.click();
            return 'clicked';
        })()
        """ % (JOB_CONTAINER_SELECTOR, title))
        time.sleep(sleep_s)
        after = js("location.href")
        if after != before and after and 'about:' not in after:
            results.append({"title": title, "url": after})
        if clicked == 'clicked' and after != before:
            js("history.back()")
            time.sleep(sleep_s)
    return results


def get_job_titles(js, limit=MAX_TITLES):
    """3d：判空并取最多 limit 个职位标题。返回 [str]；空结果返回 []。"""
    titles = extract_container_titles(js)
    if not titles:
        titles = [it["title"] for it in extract_a_links(js)]
    return titles[:limit]


def match_titles(titles, keyword):
    """3e：返回标题中含 KEYWORD（连续子串）的职位标题。"""
    return [t for t in titles if keyword and keyword in t]


def extract_matched_links(js, cdp, titles, keyword, max_click=5, sleep_s=1.5):
    """3e：按 KEYWORD 连续子串判定后提取岗位链接。
    命中 → 提取命中职位的链接；未命中 → 提取第一个职位的链接。返回 [{title, link}]。"""
    targets = match_titles(titles, keyword) or titles[:1]
    all_links = {it["title"]: it["link"] for it in extract_a_links(js)}
    results = [{"title": t, "link": all_links[t]} for t in targets if t in all_links]
    missing = [t for t in targets if t not in all_links]
    if missing:
        for item in extract_by_click(js, cdp, missing, max_click=max_click, sleep_s=sleep_s):
            results.append({"title": item["title"], "link": item["url"]})
    return results
