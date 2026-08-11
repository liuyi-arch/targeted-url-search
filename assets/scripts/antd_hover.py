# -*- coding: utf-8 -*-
"""antd 菜单展开 + 提取目标 URL。
适用：antd Menu 站点（P1，如网易 campus.game.163.com）。
用法：在 browser-use <<'PY' ... PY 中 import 本文件函数，或复制关键步骤。

关键点：
- JS dispatchEvent 无法触发 antd submenu（rc-trigger 只认可信事件流）→ 必须 CDP 真实 mouseMoved。
- popup 的 li[role=menuitem] 的 data-menu-id 属性直接携带目标 URL → 提取后 goto_url。
"""

import time
import json


def ensure_wide_viewport(cdp, js):
    """窗口过窄时 antd 菜单折叠进'更多'，放大视口（若已折叠需 goto_url 刷新）。"""
    cdp("Emulation.setDeviceMetricsOverride", width=1920, height=1000,
        deviceScaleFactor=1, mobile=False)
    time.sleep(2)


def hover_submenu(cdp, js, menu_id):
    """CDP 真实鼠标移动 hover 到 submenu-title，返回是否成功。

    Args:
        menu_id: data-menu-id 值，如 'rc-menu-uuid-/campus'（应届生）、'/intern'（精英实习生）。
    """
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
    """从 popup 项中挑出含关键词（如 '职位'、'招聘'、'校园'）的项，返回其 data-menu-id（即 URL），无则 None。"""
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
