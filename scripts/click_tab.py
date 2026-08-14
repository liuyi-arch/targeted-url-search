# -*- coding: utf-8 -*-
"""3b 动作：点击目标 Tab（click_tab）；项目/批次选择弹窗选值（click_el_select_option，三环 S 类用，见 site-notes）。"""


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


def click_el_select_option(js, option_text, confirm_text='确 定'):
    """el-select 弹窗选值：点下拉 → 选可见选项 → 点确认（三环项目选择，S 类专用）。返回 {selected, confirmed}。"""
    return js("""
    (function() {
        let sel = document.querySelector('.left-box-search .el-select, .el-select');
        if (!sel) return JSON.stringify({selected: false, confirmed: false});
        sel.click();
        setTimeout(function() {
            let items = document.querySelectorAll('.el-select-dropdown__item');
            for (let it of items) {
                if (it.offsetParent !== null && (it.textContent||'').trim().includes('%s')) {
                    it.click();
                    let btns = document.querySelectorAll('button, a, div, span');
                    for (let b of btns) {
                        let t = (b.textContent||'').trim();
                        if ((t === '%s' || t === '确定') && b.offsetParent !== null) { b.click(); return; }
                    }
                    return;
                }
            }
        }, 800);
        return JSON.stringify({selected: true, confirmed: true});
    })()
    """ % (option_text, confirm_text))
