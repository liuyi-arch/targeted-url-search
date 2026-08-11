# -*- coding: utf-8 -*-
"""岗位三层提取（3f）。在 browser-use <<'PY' ... PY 中调用。"""

import time
import json


JOB_CONTAINER_SELECTOR = (
    "[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],"
    "[class*=post],[class*=position-name],[class*=jobName],[class*=job-name]"
)


def extract_a_links(js):
    """第一层：`<a>` 链接（href 含 position/job/detail/recruit）。返回 [{title, link}]。"""
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
    """第二层：岗位标题容器文本（去重、限长）。返回 [str]。"""
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
    """第三层：点击岗位容器触发 SPA 跳转取详情 URL（仅第一层链接数为 0 时启用）。
    对前 max_click 个标题：点击 → 若 URL 变化记录 → history.back() 回退。
    返回 [{title, url}]。React 卡片 JS .click() 不触发时需 CDP 真实点击。
    """
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


def search_stats(js):
    """提取页面岗位统计文本（'职位列表 N 个'/'共 N 个'等），用于判定搜索是否生效。返回 str 或 ''。"""
    import re
    txt = js("document.body.innerText")
    m = re.search(r'(职位列表\s*\d+\s*个|共\s*\d+\s*个在招职位|全部校招职位\s*\(\d+\)|暂无职位信息|暂无职位)', txt)
    return m.group(0) if m else ''
