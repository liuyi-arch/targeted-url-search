# -*- coding: utf-8 -*-
"""3c 动作：触发搜索。动作文件内多个方法 = 不同实现方式：

- trigger_enter()            —— 方法1（默认）：对聚焦输入框派发回车（React 表单 onSubmit）
- click_search_btn()         —— 方法2：点击搜索按钮（button onClick 不触发 onSubmit，按钮兜底）
- click_btn_by_selector()    —— 方法3：按 CSS 选择器 JS click 指定按钮（适配 rect 0,0 不可真实点击的按钮）
"""

import time


def trigger_enter(js, sleep_s=3.0):
    """方法1：对当前聚焦输入框派发回车，触发搜索。返回 'enter'/'no-input'。
    注意：依赖 activeElement，fill_keyword 填入后若焦点丢失会 no-input（多站点坑），
    失败时依次尝试 click_search_btn / click_btn_by_selector。"""
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
    """方法2：点击搜索按钮（type=submit 或文本含"搜索"）。返回 'clicked'/'no-btn'。"""
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


def click_btn_by_selector(js, selector, sleep_s=3.0):
    """**方法3**：按 CSS 选择器 JS click 指定搜索按钮。返回 'clicked'/'no-btn'。
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
