# -*- coding: utf-8 -*-
"""3b 第 2 步：探测 Tab 有无下拉。返回 {has_dropdown, menu_id}；true→hover_expand.py，false→click_tab.py。

适配坑（快手）：antd 导航 Tab（class `ant-dropdown-trigger`，如快手"应届招聘/实习招聘"）无 data-menu-id，
仅凭 submenu/menu-id/aria-haspopup 探测会漏判 → 增加 `ant-dropdown-trigger` class 识别。
适配坑（普渡/卓驭 italent 系）：styled-components 导航下拉父菜单（class 为 sc-* 哈希）也无标准下拉特征，
但点击后会展开二级菜单 → 由 find_tab 新方法按坐标点击处理（见 find_tab.py）。"""


def tab_has_dropdown(js, text):
    """按 text 定位可见 Tab，探测下拉特征（ant-dropdown-trigger/submenu/data-menu-id/aria-haspopup/子容器）。返回 {has_dropdown, menu_id}。"""
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
                    let hasDd = cls.includes('submenu') || cls.includes('ant-dropdown-trigger') ||
                                !!mid || el.getAttribute('aria-haspopup') === 'true' ||
                                !!el.querySelector('[role=menu], [class*=dropdown], [class*=popup], [class*=submenu]');
                    return JSON.stringify({has_dropdown: hasDd, menu_id: mid});
                }
            }
        }
        return JSON.stringify({has_dropdown: false, menu_id: ''});
    })()
    """ % text)
