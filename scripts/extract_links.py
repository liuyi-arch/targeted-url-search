# -*- coding: utf-8 -*-
"""3e 底层方法：提取岗位链接的三种实现。
- extract_a_links：<a> 链接提取
- extract_by_click：JS .click() 跳转取 URL
- extract_via_fiber_onclick：React fiber onClick 捕获 URL
判定与编排（match_titles / extract_matched_links）在 match_links.py。"""

import time
import json


JOB_CONTAINER_SELECTOR = (
    "[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],"
    "[class*=post],[class*=position-name],[class*=jobName],[class*=job-name]"
)


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


def extract_by_click(js, cdp, titles, max_click=5, sleep_s=1.5):
    """点击岗位容器触发 SPA 跳转取详情 URL（<a> 取不到时补）。URL 变化则记录并 history.back() 回退。返回 [{title, url}]。"""
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


def extract_via_fiber_onclick(js, titles, max_click=5):
    """React/antd 卡片无 <a> 且 click 不跳转（实际 window.open 新标签页）时：
    重写 window.open 捕获参数 + 触发卡片 fiber onClick，从 URL 模板提取详情链接（如网易 /app/detail/index?id={id}&projectId={pid}）。
    返回 [{title, url}]；相对路径由调用方拼接域名。"""
    results = []
    for title in titles[:max_click]:
        captured = js("""
        (function(){
            window.__captured = [];
            window.open = function(url){ window.__captured.push(url); return null; };
            let el = [...document.querySelectorAll('%s')]
                .find(e => e.textContent.trim().includes(%r) && e.offsetParent !== null);
            if(!el) return 'nf';
            let keys = Object.keys(el).filter(k => k.startsWith('__reactProps'));
            for (let k of keys) {
                try {
                    let props = el[k];
                    if (props.onClick) { props.onClick({}); break; }
                } catch(e) {}
            }
            return JSON.stringify(window.__captured);
        })()
        """ % (JOB_CONTAINER_SELECTOR, title))
        if captured != 'nf':
            try:
                for u in json.loads(captured):
                    results.append({"title": title, "url": u})
            except (ValueError, TypeError):
                pass
    return results
