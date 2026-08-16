# -*- coding: utf-8 -*-
"""3e 底层方法：提取岗位链接。按命中率排序（<a> → 祖先a → data属性 → 点击跳转 → SPA详情按钮 → API抓取 → fiber onClick）。
判定与编排（match_titles / extract_matched_links）在 match_links.py。"""

import time
import json


JOB_CONTAINER_SELECTOR = (
    "[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],"
    "[class*=post],[class*=position-name],[class*=jobName],[class*=job-name],"
    "[class*=STJobTitle],[class*=positionItem-title],[class*=STListItemContent]"
)


def extract_a_links(js):
    """方法1（最稳）：`<a>` 链接提取（href 含 position/job/detail/recruit 或位于岗位容器内）。返回 [{title, link}]。"""
    return json.loads(js("""
    JSON.stringify([...document.querySelectorAll('a')].filter(a => {
        const t = a.textContent.trim();
        const h = a.href || '';
        return t.length > 2 && t.length < 200 &&
               (h.includes('position')||h.includes('job')||h.includes('detail')||h.includes('recruit') ||
                a.closest('[class*=JobTitle],[class*=job-title],[class*=position],[class*=job-item]'));
    }).map(a => ({title: a.textContent.trim(), link: a.href})))
    """))


def extract_ancestor_a(js, selector='[data-test=positionItem]', titles=None):
    """方法2：卡片本身无 `<a>`，取**祖先 `<a>` 的 href**（metaAPP positionItem → /position/{id}/detail）。返回 [{title, link}]。"""
    results = []
    data = js("""
    (function(){
        let out = [];
        let cards = document.querySelectorAll(%r);
        for (let c of cards) {
            if (c.offsetParent === null) continue;
            let a = c.closest('a');
            let nameEl = c.querySelector('.positionItem-title-text') || c.querySelector('[class*=title]') || c;
            out.push({name: (nameEl.textContent || '').trim().slice(0, 60), href: a ? a.href : ''});
        }
        return JSON.stringify(out);
    })()
    """ % selector)
    try:
        for it in json.loads(data):
            if it["href"] and (not titles or any(t in it["name"] for t in titles)):
                results.append({"title": it["name"], "link": it["href"]})
    except (ValueError, TypeError):
        pass
    return results


def extract_via_attr(js, selector='.position_list_item', attr='data-jobunionid', url_tpl='{scheme}://{host}/web/position/detail?jobUnionId={id}'):
    """方法3：卡片为 div 带 data-* 属性（美团 data-jobunionid）→ 读属性 + URL 模板拼接。返回 [{title, link}]。"""
    results = []
    data = js("""
    (function(){
        let out = [];
        let cards = document.querySelectorAll(%r);
        for (let c of cards) {
            if (c.offsetParent === null) continue;
            let id = c.getAttribute(%r);
            if (!id) continue;
            let nameEl = c.querySelector('[class*=title]') || c;
            out.push({name: (nameEl.textContent || '').trim().split(/\\s+/)[0].slice(0, 60), id: id});
        }
        return JSON.stringify(out);
    })()
    """ % (selector, attr))
    try:
        loc = json.loads(js("JSON.stringify({scheme: location.protocol.replace(':',''), host: location.host})"))
        for it in json.loads(data):
            results.append({"title": it["name"], "link": url_tpl.format(scheme=loc["scheme"], host=loc["host"], id=it["id"])})
    except (ValueError, TypeError, KeyError):
        pass
    return results


def extract_by_click(js, cdp, titles, max_click=5, sleep_s=1.5):
    """方法4：点击岗位容器触发 SPA 跳转取详情 URL（<a> 取不到时补）。URL 变化则记录并 history.back() 回退。返回 [{title, url}]。"""
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


def extract_via_detail_btn(js, cdp, titles, card_selector='[class*=STListItemContent]',
                          btn_text='查看详情', max_click=3, sleep_s=4.0):
    """方法5：SPA 内嵌详情面板（italent 系普渡/卓驭）：点卡片展开面板 → 点"查看详情" → 重写 window.open 捕获
    `/campus/detail?jobAdId={uuid}`。返回 [{title, url}]（相对路径由调用方补全）。"""
    results = []
    for title in titles[:max_click]:
        js("window.__cap=[]; window.open=function(u){window.__cap.push(u); return null;};")
        js("""
        (function(){
            let cards = document.querySelectorAll(%r);
            for (let c of cards) {
                if (c.offsetParent === null) continue;
                if ((c.textContent||'').includes(%r)) { c.click(); return 'card-clicked'; }
            }
            return 'nf';
        })()
        """ % (card_selector, title))
        time.sleep(2.5)
        js("""
        (function(){
            let footers = document.querySelectorAll('[class*=STDetailFooter]');
            for (let f of footers) {
                if (f.offsetParent === null) continue;
                let els = f.querySelectorAll('*');
                for (let el of els) {
                    if (el.offsetParent === null) continue;
                    if ((el.textContent||'').trim() === %r) { el.click(); return 'btn-clicked'; }
                }
            }
            return 'nf';
        })()
        """ % btn_text)
        time.sleep(sleep_s)
        try:
            for u in json.loads(js("JSON.stringify(window.__cap)")):
                if u:
                    results.append({"title": title, "url": u})
        except (ValueError, TypeError):
            pass
    return results


def extract_via_api(js, cdp, titles, card_selector='[class*=STListItemContent]',
                    api_marker='GetSubmitLimit', max_click=5, sleep_s=4.0):
    """方法6：点击卡片触发 API（360 GetSubmitLimit?jobAdId={uuid}）→ 从 performance 资源请求抓 uuid。返回 [{title, url}]。"""
    results = []
    for title in titles[:max_click]:
        js("performance.clearResourceTimings()")
        js("""
        (function(){
            let cards = document.querySelectorAll(%r);
            for (let c of cards) {
                if (c.offsetParent === null) continue;
                if ((c.textContent||'').includes(%r)) { c.click(); return 'clicked'; }
            }
            return 'nf';
        })()
        """ % (card_selector, title))
        time.sleep(sleep_s)
        apis = js("JSON.stringify(performance.getEntriesByType('resource').map(function(e){return e.name;}).filter(function(u){return u.indexOf(%r)>=0;}))" % api_marker)
        try:
            for u in json.loads(apis):
                if 'jobAdId=' in u:
                    results.append({"title": title, "url": u.split('jobAdId=')[-1].split('&')[0]})
        except (ValueError, TypeError):
            pass
    return results


def extract_via_fiber_onclick(js, titles, max_click=5):
    """方法7：React/antd 卡片无 <a> 且 click 不跳转（实际 window.open 新标签页，网易）→ 重写 window.open + 触发
    fiber onClick 捕获 `/app/detail/index?id={id}&projectId={pid}`。返回 [{title, url}]。"""
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
