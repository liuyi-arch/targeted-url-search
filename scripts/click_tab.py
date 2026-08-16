# -*- coding: utf-8 -*-
"""3b 动作：点击目标 Tab（click_tab）；React fiber onClick 触发（click_tab_fiber，CVTE 用）；项目/批次选择弹窗选值（click_el_select_option，三环 S 类用，见 site-notes）。"""


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


def click_tab_fiber(js, text, container_sel='button, a, div, span'):
    """**方法2**：React fiber onClick 触发 Tab/按钮（JS click 无效时用，CVTE 坑）。
    适配坑：CVTE 首页"查看全部岗位"为 BUTTON（无 href），JS click 不触发路由，
    须触发 React fiber 属性上的 onClick 才跳转。返回 'fiber-clicked'/'js-clicked'/'nf'。"""
    return js("""
    (function() {
        let els = [...document.querySelectorAll(%r)];
        let el = els.find(e => (e.textContent||'').trim().includes('%s') && e.offsetParent !== null);
        if (!el) return 'nf';
        let keys = Object.keys(el).filter(k => k.startsWith('__reactProps'));
        for (let k of keys) {
            try {
                if (el[k] && el[k].onClick) { el[k].onClick({}); return 'fiber-clicked'; }
            } catch(e) {}
        }
        el.click();
        return 'js-clicked';
    })()
    """ % (container_sel, text))


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
