# -*- coding: utf-8 -*-
"""3c 动作：触发搜索。动作文件内多个方法 = 不同实现方式。
顺序按 3 轮 23 站实测成功率排序：trigger_enter 为**零成本首选**（不依赖 DOM 结构，60% 直接命中，
失败代价低；其余方法均需特定页面元素，前置反而对表单型站点多一次 no-btn 切换）→
click_search_btn（按钮型，实测 6/6=100%）→ click_search_icon（图标型，实测 1/1=100%）→
search_via_url_param（URL 参数型，实测 1/1=100%）→ click_btn_by_selector（需显式 selector，未实测）。"""

import time


def trigger_enter(js, sleep_s=3.0):
    """方法1（零成本首选）：对当前聚焦输入框派发回车，触发搜索。返回 'enter'/'no-input'。
    注意：依赖 activeElement，fill_keyword 填入后若焦点丢失会 no-input（多站点坑），
    失败时依次尝试 click_search_btn / click_search_icon / search_via_url_param。"""
    res = js("""(function(){
        let ae = document.activeElement;
        if (ae && ae.tagName === 'INPUT') {
            ae.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
            ae.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',keyCode:13,bubbles:true}));
            return 'enter';
        }
        return 'no-input';
    })()""")
    time.sleep(sleep_s)
    return res


def click_search_btn(js, sleep_s=3.0):
    """方法2：点击搜索按钮（type=submit 或文本含"搜索"）。返回 'clicked'/'no-btn'。
    实测 6/6=100%（网易 ant-input-search-button、Beisen 系"搜索职位"按钮）。"""
    res = js("""(function(){
        let btns = document.querySelectorAll('button, input[type=submit], [role=button], a');
        for (let el of btns) {
            let t = (el.textContent || el.value || '').trim();
            if (t.includes('搜索') || t.includes('查询') || el.type === 'submit') {
                if (el.offsetParent !== null) {
                    el.click();
                    return 'clicked';
                }
            }
        }
        return 'no-btn';
    })()""")
    time.sleep(sleep_s)
    return res


def click_search_icon(js, icon_selector='.searchBox .icon--search', sleep_s=3.0):
    """方法3：点击搜索图标触发（4399 坑）。实测 1/1=100%。
    适配坑：搜索框 JS fill + 回车无效，但点搜索图标有效（URL 变 `?key={词}`）。
    默认选择器适配 4399 `.searchBox .icon--search`，其他站点可传自定义选择器。
    返回 'clicked'/'no-icon'。"""
    res = js("""(function(){
        let el = document.querySelector(%r);
        if (!el) return 'no-icon';
        el.click();
        return 'clicked';
    })()""" % icon_selector)
    time.sleep(sleep_s)
    return res


def search_via_url_param(js, keyword, param='postKey', sleep_s=4.0):
    """方法4：URL 参数触发搜索（hotjob/北森系：新安能/荣耀）。实测 1/1=100%。
    适配坑：antd-mobile 搜索框（`.am-search-value`）JS fill + 回车均不触发过滤，
    但 **URL 加 `{param}={关键词}` 参数刷新** 立即生效 → 在现 URL 追加参数导航。
    返回 'nav'（已导航）/ 'no-url'。"""
    u = js("location.href")
    if not u or 'about:' in u:
        return 'no-url'
    import urllib.parse
    import re
    kw = urllib.parse.quote(keyword)
    new_u = re.sub(r'([?&]%s=)[^&]*' % re.escape(param), r'\g<1>%s' % kw, u)
    if new_u == u:
        sep = '&' if '?' in u else '?'
        new_u = u + sep + '%s=%s' % (param, kw)
    js("location.href = %r" % new_u)
    time.sleep(sleep_s)
    return 'nav'


def click_btn_by_selector(js, selector, sleep_s=3.0):
    """方法5（最后兜底）：按 CSS 选择器 JS click 指定搜索按钮。返回 'clicked'/'no-btn'。
    需调用方显式传 selector（无默认值），未实测。
    适配坑：美团 `.zp_search_btn` 按钮 getBoundingClientRect 为 0,0（不可真实点击/CDP 点击超时），
    但 **JS click 有效** → 直接 `document.querySelector(selector).click()`。"""
    res = js("""(function(){
        let el = document.querySelector(%r);
        if (!el) return 'no-btn';
        el.click();
        return 'clicked';
    })()""" % selector)
    time.sleep(sleep_s)
    return res
