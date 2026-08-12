# -*- coding: utf-8 -*-
"""3c 动作：填入搜索关键词。方法：fill_keyword（native setter + InputEvent，适配受控组件）。"""


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
