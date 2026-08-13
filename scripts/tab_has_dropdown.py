# -*- coding: utf-8 -*-
"""3b 第 2 步：探测 Tab 有无下拉。返回 {has_dropdown, menu_id}；true→hover_expand.py，false→click_tab.py。"""


def tab_has_dropdown(js, text):
    """按 text 定位可见 Tab，探测下拉特征（submenu/data-menu-id/aria-haspopup/子容器）。返回 {has_dropdown, menu_id}。"""
    return js("""
    (function() {
        const navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
        const areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
        for (let area of areas) {
            for (let el of area.querySelectorAll('a, button, li, span, div[role=tab], div[role=menuitem]')) {
                let t = el.textContent.trim();
                if (t === '%s' && t.length < 20 && el.offsetParent !== null) {
                    let cls = (el.className || '').toString();
                    // antd 的 data-menu-id 可能在子/父元素（LI > DIV[data-menu-id]），就近查找
                    let mid = (el.getAttribute('data-menu-id') ||
                              el.closest('[data-menu-id]')?.getAttribute('data-menu-id') ||
                              el.querySelector('[data-menu-id]')?.getAttribute('data-menu-id')) || '';
                    let hasDd = cls.includes('submenu') || !!mid || el.getAttribute('aria-haspopup') === 'true' ||
                                !!el.querySelector('[role=menu], [class*=dropdown], [class*=popup], [class*=submenu]');
                    return JSON.stringify({has_dropdown: hasDd, menu_id: mid});
                }
            }
        }
        return JSON.stringify({has_dropdown: false, menu_id: ''});
    })()
    """ % text)
