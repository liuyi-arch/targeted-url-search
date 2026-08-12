# -*- coding: utf-8 -*-
"""3b 动作：点击目标 Tab。方法：click_tab（按文本点击可见 Tab）。"""


def click_tab(js, text):
    """用 find_tab 返回的 text 点击可见的语义 Tab。返回 {clicked, text}。"""
    return js("""
    (function() {
        let navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
        let areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
        for (let area of areas) {
            for (let el of area.querySelectorAll('a, button, li, span, div[role=tab]')) {
                let t = el.textContent.trim();
                if (t === '%s' && t.length < 20 && el.offsetParent !== null) {
                    el.click();
                    return JSON.stringify({clicked: true, text: t});
                }
            }
        }
        return JSON.stringify({clicked: false});
    })()
    """ % text)
