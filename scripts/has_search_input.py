# -*- coding: utf-8 -*-
"""3b/3c 动作：搜索框定位与检查（3b 验证复用；3c 定位）。动作文件内多个方法 = 不同实现方式：

- has_search_input()    —— 方法1：检查页面是否出现搜索框（bool），供 nav_verified 验证复用
- find_search_input()   —— 方法2：定位搜索框，返回元素信息 {id, name, placeholder}，供 3d 填入复用
- find_in_iframe()      —— 方法3：主文档找不到时 iframe 兜底定位（跨源 contentDocument 抛错则跳过）
"""


def has_search_input(js):
    """页面是否出现搜索框。返回 bool。"""
    n = js("document.querySelectorAll('input[type=text], input[type=search], input[placeholder]').length")
    return int(n or 0) > 0


def find_search_input(js):
    """定位搜索框（placeholder 含 搜索/职位/岗位/search/keyword）。返回 {id, name, placeholder} 或 None。"""
    res = js("""
    (function() {
        let inputs = document.querySelectorAll('input');
        for (let inp of inputs) {
            let ph = (inp.placeholder || '').toLowerCase();
            if (ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search')||ph.includes('keyword'))
                return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder});
        }
        return 'null';
    })()
    """)
    return None if res == 'null' else res


def find_in_iframe(js):
    """主文档无搜索框时，遍历 iframe 在子文档内定位。返回元素信息或 None（跨源抛错则跳过）。"""
    res = js("""
    (function() {
        for (let iframe of document.querySelectorAll('iframe')) {
            try {
                let doc = iframe.contentDocument;
                if (!doc) continue;
                let inputs = doc.querySelectorAll('input');
                for (let inp of inputs) {
                    let ph = (inp.placeholder || '').toLowerCase();
                    if (ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search')||ph.includes('keyword'))
                        return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder});
                }
            } catch(e) { /* 跨源 iframe，跳过 */ }
        }
        return 'null';
    })()
    """)
    return None if res == 'null' else res
