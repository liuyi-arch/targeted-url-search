# -*- coding: utf-8 -*-
"""3b 动作：找目标 Tab（只找不点击）。方法：find_tab（CSS/JS 通用）。

四类语义 Tab：类别一=校招（校园招聘/校招/应届招聘/校招职位/校招岗位/应届）；类别二=实习（实习招聘/实习生/实习）；
类别三=通用（职位/招聘职位/职位列表/岗位/岗位投递/Jobs/Positions）；类别四=社招。
未找到（found=false）→ 直接进入降级链下一级。
"""


def find_tab(js, mode):
    """按 MODE 语义关键词在导航区找直接可见 Tab。返回 {found, text}。"""
    return js("""
    (function() {
        let kwMap = {1:['校园招聘','校招','应届招聘','校招职位','校招岗位','应届'],
                     2:['实习招聘','实习生','实习'],
                     3:['职位','招聘职位','职位列表','岗位','岗位投递','Jobs','Positions']};
        let kws = kwMap[%d] || kwMap[1];
        let navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
        let areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
        for (let area of areas) {
            for (let el of area.querySelectorAll('a, button, li, span, div[role=tab]')) {
                let t = el.textContent.trim();
                if (kws.some(k => t.includes(k)) && t.length < 20 && el.offsetParent !== null) {
                    return JSON.stringify({found: true, text: t});
                }
            }
        }
        return JSON.stringify({found: false});
    })()
    """ % mode)
