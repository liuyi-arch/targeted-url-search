# -*- coding: utf-8 -*-
"""3b/3d 动作：hover 展开下拉（3b hover；real_click 供 3d 提取兜底）。动作文件内多个方法 = 不同实现方式：

- hover_expand_css()   —— 方法1（默认）：普通 CSS/JS 下拉，JS 派发 mouseenter/mouseover 即可展开
- hover_expand_antd()  —— 方法2：antd 系菜单（JS dispatchEvent 无效，须 CDP 真实鼠标移动）
- click_dropdown_item() —— hover 后在下拉列表点"职位/岗位"项（配合方法1使用）

antd 系辅助函数（ensure_wide_viewport / hover_submenu / get_popup_items / pick_url / real_click）
统一收敛在本文件，由 hover_expand_antd() 入口调度，外部只调入口函数。

通用规则：popup/下拉里找到的菜单项若带 `data-menu-id`/`href` 属性，**直接提取 URL 导航**，
不要模拟点击（React/antd 站点的 JS .click() 常不触发跳转，真实点击可能弹登录框）。
antd 的 data-menu-id 即目标 URL（如 rc-menu-uuid-/app/job/position?id=102），由 pick_url() 提取。
"""

import time
import json


# ============ 方法1：普通 CSS/JS 下拉 ============

def hover_expand_css(js):
    """hover 导航区元素触发下拉（普通 CSS/JS 下拉）。返回 {hovered, text}。"""
    return js("""
    (function() {
        const navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
        const areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
        const isVis = e => e.offsetParent !== null && e.getClientRects().length > 0;
        for (let area of areas) {
            for (let el of area.querySelectorAll('a, button, li, span, div')) {
                let t = (el.textContent||'').trim();
                if (t.length < 20 && isVis(el) && /校招|校园|实习|招聘|职位|岗位|Join|Career/i.test(t)) {
                    ['mouseenter','mouseover','mousemove'].forEach(ev => el.dispatchEvent(new MouseEvent(ev, {bubbles: true})));
                    return JSON.stringify({hovered: true, text: t});
                }
            }
        }
        return JSON.stringify({hovered: false});
    })()
    """)


def click_dropdown_item(js):
    """hover 后 1s，在下拉列表找"职位/岗位"项并点击。返回 {clicked, text}。"""
    time.sleep(1)
    return js("""
    (function() {
        const kws = ['职位','岗位','招聘','全部职位','Jobs','Positions'];
        const isVis = e => e.offsetParent !== null && e.getClientRects().length > 0;
        for (let el of document.querySelectorAll('a, button, li, span, div[role=menuitem]')) {
            let t = (el.textContent||'').trim();
            if (t.length < 20 && isVis(el) && kws.some(k => t.includes(k))) {
                el.click();
                return JSON.stringify({clicked: true, text: t});
            }
        }
        return JSON.stringify({clicked: false});
    })()
    """)


# ============ 方法2：antd 系菜单（CDP 真实鼠标） ============

def hover_expand_antd(cdp, js, menu_id, goto_url=None, keywords=('职位', '招聘', '校园')):
    """antd 系菜单展开入口（如网易 campus.game.163.com）。

    流程：放大视口防折叠 → CDP mouseMoved 展开 submenu → 读 popup 菜单项 →
    从 data-menu-id 提取目标 URL。返回目标 URL 或 None。

    Args:
        cdp: browser-use cdp() 函数
        js: browser-use js() 函数
        menu_id: submenu 的 data-menu-id，如 'rc-menu-uuid-/campus'（应届生）、'/intern'（精英实习生）
        goto_url: browser-use goto_url() 函数；传入则直接导航并返回 True
        keywords: 在 popup 项中筛选目标 URL 的语义关键词
    """
    ensure_wide_viewport(cdp, js)
    if not hover_submenu(cdp, js, menu_id):
        return None
    items = get_popup_items(js)
    url = pick_url(items, keywords)
    if url and goto_url:
        goto_url(url)
        return True
    return url


def ensure_wide_viewport(cdp, js):
    """窗口过窄时 antd 菜单折叠进"更多"，放大视口（若已折叠需 goto_url 刷新）。"""
    cdp("Emulation.setDeviceMetricsOverride", width=1920, height=1000,
        deviceScaleFactor=1, mobile=False)
    time.sleep(2)


def hover_submenu(cdp, js, menu_id):
    """CDP 真实鼠标移动 hover 到 submenu-title，返回是否成功。"""
    rect = js("""
    (function(){
        let el = document.querySelector('[data-menu-id="%s"]');
        if(!el) return 'nf';
        let r = el.getBoundingClientRect();
        if(r.width===0 && r.height===0) return 'nf';
        return JSON.stringify({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
    })()
    """ % menu_id)
    if rect == 'nf':
        return False
    p = json.loads(rect)
    cdp("Input.dispatchMouseEvent", type="mouseMoved", x=100, y=100)  # 先从别处移入
    time.sleep(0.5)
    cdp("Input.dispatchMouseEvent", type="mouseMoved", x=p["x"], y=p["y"])
    time.sleep(2)
    return True


def get_popup_items(js):
    """读取 antd popup 菜单项，返回 [{t: 文本, id: data-menu-id(即URL)}]。"""
    return json.loads(js("""
    JSON.stringify([...document.querySelectorAll('li[role=menuitem]')].filter(e=>e.offsetParent!==null)
      .map(e=>({t:e.textContent.trim().replace(/\\s+/g,' ').slice(0,60), id:e.getAttribute('data-menu-id')||''})))
    """))


def pick_url(items, keywords):
    """从 popup 项中挑出含关键词的项，返回其 data-menu-id（即 URL），无则 None。"""
    for it in items:
        if it.get('id') and it['id'].startswith('rc-menu-uuid-') and it['id'] != 'rc-menu-uuid-rc-menu-more':
            path = it['id'].replace('rc-menu-uuid-', '', 1)
            if any(k in it['t'] for k in keywords):
                return path
    return None


def real_click(cdp, js, selector, retries=2):
    """CDP 真实鼠标点击元素（JS .click() 对 React/antd 常不触发）。返回点击坐标或 None。"""
    for _ in range(retries):
        rect = js("""
        (function(){
            let el = document.querySelector('%s');
            if(!el) return 'nf';
            let r = el.getBoundingClientRect();
            if(r.width===0 && r.height===0) return 'nf';
            return JSON.stringify({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
        })()
        """ % selector)
        if rect == 'nf':
            return None
        p = json.loads(rect)
        try:
            cdp("Input.dispatchMouseEvent", type="mouseMoved", x=p["x"], y=p["y"])
            time.sleep(0.3)
            cdp("Input.dispatchMouseEvent", type="mousePressed", x=p["x"], y=p["y"],
                button="left", clickCount=1)
            cdp("Input.dispatchMouseEvent", type="mouseReleased", x=p["x"], y=p["y"],
                button="left", clickCount=1)
            return p
        except Exception:
            time.sleep(2)  # IPC 偶发超时（点击触发重定向/弹窗时常见），重试
    return None
