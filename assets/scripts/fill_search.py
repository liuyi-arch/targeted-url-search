# -*- coding: utf-8 -*-
"""搜索框填入关键词 + 触发搜索 + 验证生效。
适用：通用（3d）。在 browser-use <<'PY' ... PY 中调用。

返回 'filled'/'no-input'；调用后需 sleep(3) 再验证。
"""

import time


def fill_and_search(js, keyword, fill_sleep=1.0, trigger_sleep=3.0):
    """定位搜索框 → native setter 填入 → 触发回车。返回状态。"""
    filled = js("""
    (function(){
        let inputs = document.querySelectorAll('input');
        for (let inp of inputs) {
            let ph = (inp.placeholder || '').toLowerCase();
            if (ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search')||ph.includes('keyword')) {
                let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                setter.call(inp, '%s');
                inp.dispatchEvent(new InputEvent('input',{bubbles:true, inputType:'insertText', data:'%s'}));
                inp.dispatchEvent(new Event('change',{bubbles:true}));
                inp.focus();
                return 'filled';
            }
        }
        return 'no-input';
    })()
    """ % (keyword, keyword))
    if filled == 'no-input':
        return 'no-input'
    time.sleep(fill_sleep)
    js("""(function(){
        let ae = document.activeElement;
        if (ae && ae.tagName === 'INPUT') {
            ae.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
            ae.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',keyCode:13,bubbles:true}));
            return 'enter';
        }
        return 'no-input';
    })()""")
    time.sleep(trigger_sleep)
    return 'filled'


def search_effective(js):
    """验证搜索是否生效：URL 带 q/query/keyword 参数，或页面出现'共N个/职位列表N个'统计。返回 bool。"""
    state = js("JSON.stringify({url: location.href, txt: document.body.innerText.slice(0, 2000)})")
    import json as _json
    try:
        s = _json.loads(state)
    except Exception:
        return False
    u = s.get('url', '')
    if any(m in u.lower() for m in ['?q=', '&q=', 'query=', 'keyword=']):
        return True
    t = s.get('txt', '')
    import re
    if re.search(r'(共\s*\d+\s*(个|条)|职位列表\s*\d+\s*个|全部校招职位\s*\(\d+\)|暂无职位)', t):
        return True
    return False
