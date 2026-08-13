# -*- coding: utf-8 -*-
"""3c 动作：验证搜索是否生效。动作文件内多个方法 = 不同实现方式：

- url_has_query()   —— 方法1：URL 带 q/query/keyword/keywords 参数（如汇川 ?q=前端、metaAPP ?keywords=前端）
- stats_changed()   —— 方法2：页面出现"共N个/职位列表N个"统计变化（如网易"职位列表 1 个"）
- search_verified() —— 组合入口
"""

import json
import re


def url_has_query(js):
    """方法1：URL 是否带 q/query/keyword/**keywords** 参数。返回 bool。
    适配坑：metaAPP/快手搜索后 URL 带 `keywords=前端`（飞书系参数名），仅认 q/query/keyword 会漏判。"""
    u = js("location.href")
    return any(m in u.lower() for m in ['?q=', '&q=', 'query=', 'keyword=', 'keywords='])


# 固有统计文案（页面初始就存在，非搜索过滤后的结果变化）——用于排除假阳性
STATIC_STATS = re.compile(r'(全部职位\s*（\s*共\s*\d+\s*个\s*）|全部校招职位\s*（\s*\d+\s*）|共\s*\d+\s*个\s*职位)')
# 过滤后结果变化特征（真命中）：结果数统计 + 出现"暂无/未找到"等
CHANGED_STATS = re.compile(r'(共\s*\d+\s*(个|条)|职位列表\s*\d+\s*个|暂无职位|未找到匹配|没有相关职位)')


def stats_changed(js):
    """方法2：页面是否出现搜索统计变化（共N个/职位列表N个/暂无职位）。返回 bool。
    适配坑：italent/zhiye 系页面**固有**文案"全部职位（共 84 个）"会误命中 `共\s*\d+\s*个` → 假阳性。
    处理：若统计文案仅命中 STATIC_STATS（固有文案）且无"暂无/未找到" → 判 False；只有 CHANGED_STATS
    （结果数变化或空结果提示）才算真命中。"""
    t = js("document.body.innerText.slice(0, 3000)")
    changed = re.search(CHANGED_STATS, t)
    if not changed:
        return False
    # 若命中"共 N 个"类：排除仅固有文案的情况（无法区分时保守判 True，配合 url_has_query 兜底）
    m = re.search(r'共\s*\d+\s*(个|条)', t)
    if m and STATIC_STATS.search(t) and '暂无' not in t and '未找到' not in t:
        # 尝试比较"共 N 个"数字是否变化：数字 < 初始总量通常表示过滤生效
        total = re.search(r'全部职位\s*（\s*共\s*(\d+)\s*个\s*）|全部校招职位\s*（\s*(\d+)\s*）', t)
        cur = re.search(r'共\s*(\d+)\s*(个|条)', t)
        if total and cur and int(cur.group(1)) < int((total.group(1) or total.group(2)) or 0):
            return True
        return False
    return True


def search_verified(js):
    """组合入口：任一方法命中即判定搜索生效。返回 bool。"""
    return url_has_query(js) or stats_changed(js)
