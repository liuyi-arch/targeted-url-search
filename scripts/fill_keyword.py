# -*- coding: utf-8 -*-
"""3c 动作：填入搜索关键词。方法：fill_keyword（native setter + InputEvent，适配受控组件）/ fill_keyword_clickable（可见可点框，VIVO 多框混淆用）。"""


def fill_keyword(js, keyword):
    """定位搜索框（placeholder 含 搜索/职位/岗位/search/keyword）→ native setter 填入关键词。返回 'filled'/'no-input'。"""
    return js("""
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


def fill_keyword_clickable(js, keyword):
    """**受控组件+多框混淆专用**：逐框 elementFromPoint 校验，选**可见可点**框（hit=INPUT）→ native setter 填入。
    适配 VIVO/t-ray：页面多个"搜索职位关键词"框（顶部被覆盖 hit=DIV、侧栏框非目标、列表区框 hit=INPUT），
    CDP insertText 对 React 受控组件无效（事件到达但 value 被重置）→ 必须 native setter + InputEvent。返回 'filled'/'no-input'。"""
    return js("""
    (function(){
        let inputs = [...document.querySelectorAll('input')].filter(x=>(x.placeholder||'').includes('搜索职位'));
        for (let inp of inputs) {
            let r = inp.getBoundingClientRect();
            if (inp.offsetParent === null || r.width <= 0) continue;
            let cx = Math.round(r.x + r.width/2), cy = Math.round(r.y + r.height/2);
            let top = document.elementFromPoint(cx, cy);
            if (!(top && (top.tagName === 'INPUT' || top === inp))) continue;
            let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            setter.call(inp, '%s');
            inp.dispatchEvent(new InputEvent('input',{bubbles:true, inputType:'insertText', data:'%s'}));
            inp.dispatchEvent(new Event('change',{bubbles:true}));
            inp.focus();
            return 'filled';
        }
        return 'no-input';
    })()
    """ % (keyword, keyword))
