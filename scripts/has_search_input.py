# -*- coding: utf-8 -*-
"""3b/3c 动作：搜索框定位与检查（3b 验证复用；3c 定位）。动作文件内多个方法 = 不同实现方式：

- has_search_input()         —— 方法1：检查页面是否出现搜索框（bool），供 nav_verified 验证复用
- find_search_input()        —— 方法2：定位搜索框，返回元素信息 {id, name, placeholder}，供 3d 填入复用
- find_in_iframe()           —— 方法3：主文档找不到时 iframe 兜底定位（跨源 contentDocument 抛错则跳过）
- find_visible_search_input()—— 方法4：**只返回可见搜索框**（过滤 offsetParent!==null && rect.width>0）。
  适配坑：italent/zhiye 系（普渡/卓驭/360）与美团页面存在**两个同名"搜索职位关键词"输入框**，
  第一个隐藏（rect 0,0），find_search_input 会误命中它导致 fill 无效 → 必须走本方法定位可见项。
"""


def has_search_input(js):
    """页面是否出现搜索框。返回 bool。"""
    n = js("document.querySelectorAll('input[type=text], input[type=search], input[placeholder]').length")
    return int(n or 0) > 0


def find_search_input(js):
    """定位搜索框（placeholder 含 搜索/职位/岗位/search/keyword）。返回 {id, name, placeholder} 或 None。
    注意：不保证可见性（可能命中隐藏输入框），见 find_visible_search_input。"""
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


def find_visible_search_input(js):
    """**方法4（推荐）**：定位**可见**搜索框（offsetParent!==null && rect.width>0）。返回元素信息或 None。
    适配 italent/zhiye 系与美团双输入框坑：跳过 rect 0,0 的隐藏输入框，确保 fill 落到真实可见项。"""
    res = js("""
    (function() {
        let inputs = document.querySelectorAll('input');
        for (let inp of inputs) {
            let ph = (inp.placeholder || '').toLowerCase();
            if (!(ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search')||ph.includes('keyword'))) continue;
            let r = inp.getBoundingClientRect();
            if (inp.offsetParent !== null && r.width > 0 && r.height > 0)
                return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder,
                                       x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width)});
        }
        return 'null';
    })()
    """)
    return None if res == 'null' else res


def find_clickable_search_input(js):
    """**方法5（VIVO 坑专用）**：逐框 elementFromPoint 校验，返回**真正可点击**的搜索框（命中元素为 INPUT）。
    适配 VIVO/t-ray：页面多个含"搜索"输入框——顶部框被导航层覆盖（elementFromPoint 命中 DIV）、
    侧栏"搜索"框可见但非搜索目标（find_visible_search_input 会误命中它）；须选 placeholder 含"搜索职位"
    且 elementFromPoint 命中 INPUT 的列表区框。返回 {x, y, placeholder} 或 None。"""
    res = js("""
    (function() {
        let inputs = document.querySelectorAll('input');
        for (let inp of inputs) {
            let ph = (inp.placeholder || '').toLowerCase();
            if (!(ph.includes('搜索职位')||ph.includes('职位关键词')||ph.includes('搜索岗位'))) continue;
            let r = inp.getBoundingClientRect();
            if (inp.offsetParent === null || r.width <= 0) continue;
            let cx = Math.round(r.x + r.width/2), cy = Math.round(r.y + r.height/2);
            let el = document.elementFromPoint(cx, cy);
            if (el && (el.tagName === 'INPUT' || el === inp))
                return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder, x: cx, y: cy, w: Math.round(r.width)});
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
