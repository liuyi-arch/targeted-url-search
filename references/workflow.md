# 详细流程与代码模板（3a–3g 通用逻辑）

> 本文件存放与具体站点无关的通用步骤与代码。站点特例一律引用 `patterns.md` 的模式。
> 所有代码通过 `browser-use <<'PY' ... PY` Python pipe 模式执行。

---

## 3a · 打开页面（复用同一标签页）

```python
goto_url("$URL")          # 复用当前标签页，站点之间不 new_tab —— new_tab 会越开越多、资源耗尽
info = page_info()
print(f"Title: {info.get('title', '')}")
```

---

## 3b · 等待加载（先看 URL，再重试）

```python
import time
time.sleep(3); wait_for_load()
chk = js("JSON.stringify({url: location.href, len: document.body.innerText.length, title: document.title})")
# 1) about:blank / '' → 反爬拦截（如 talent.baidu.com）→ 重试
# 2) 文本 < 200 且标题不含站点名 → 再等 5s 复查
# 3) 重试 1 次仍失败 → 判"页面加载失败(疑似反爬拦截/需人工验证)"，跳过该站点
if 'about:blank' in chk or 'len":' in chk and int(chk.split('"len":')[1].split(',')[0]) < 200:
    time.sleep(5)
    chk2 = js("JSON.stringify({url: location.href, len: document.body.innerText.length})")
    if 'about:blank' in chk2:
        goto_url("$URL")
        time.sleep(5)
```

---

## 3c_1 · 导航招聘类型 Tab

四类语义 Tab：类别一=校招（校园招聘/校招/应届招聘/校招职位/校招岗位/应届）；类别二=实习（实习招聘/实习生/实习）；类别三=通用（职位/招聘职位/职位列表/岗位/岗位投递/Jobs/Positions）；类别四=社招。

**降级链**：MODE=1: 类别一→类别三→找搜索框→抛错；MODE=2: 类别二→类别一→类别三→找搜索框→抛错；MODE=3: 两轮。

**每级三步：找 Tab → 点击/展开 → 验证（URL 变 且 出现搜索框或职位列表）**。

### 找直接可见 Tab 并点击

```javascript
(function() {
    let kwMap = {1:['校园招聘','校招','应届招聘','校招职位','校招岗位','应届'],
                 2:['实习招聘','实习生','实习'],
                 3:['职位','招聘职位','职位列表','岗位','岗位投递','Jobs','Positions']};
    let kws = kwMap[MODE] || kwMap[1];
    let navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
    let areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
    for (let area of areas) {
        for (let el of area.querySelectorAll('a, button, li, span, div[role=tab]')) {
            let t = el.textContent.trim();
            if (kws.some(k => t.includes(k)) && t.length < 20 && el.offsetParent !== null) {
                el.click();
                return JSON.stringify({clicked: true, text: t});
            }
        }
    }
    return JSON.stringify({clicked: false});
})()
```

### hover 展开下拉（普通 CSS/JS 下拉）

```javascript
// ① hover 导航区元素触发下拉
(function() {
    const navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
    const areas = document.querySelectorAll(navSel).length ? document.querySelectorAll(navSel) : [document.body];
    const isVis = e => e.offsetParent !== null && e.getClientRects().length > 0;
    for (let area of areas) {
        for (let el of area.querySelectorAll('a, button, li, span, div')) {
            let t = (el.textContent||'').trim();
            if (t.length < 20 && isVis(el) && /校招|校园|实习|招聘|职位|岗位|Join|Career/i.test(t)) {
                ['mouseenter','mouseover','mousemove'].forEach(ev => el.dispatchEvent(new MouseEvent(ev, {bubbles: true})));
                return JSON.stringify({hovered: true, text: t});
            }
        }
    }
    return JSON.stringify({hovered: false});
})()
```

```javascript
// ② hover 后 1s，在下拉列表找"职位/岗位"项并点击
(function() {
    const kws = ['职位','岗位','招聘','全部职位','Jobs','Positions'];
    const isVis = e => e.offsetParent !== null && e.getClientRects().length > 0;
    for (let el of document.querySelectorAll('a, button, li, span, div[role=menuitem]')) {
        let t = (el.textContent||'').trim();
        if (t.length < 20 && isVis(el) && kws.some(k => t.includes(k))) {
            el.click();
            return JSON.stringify({clicked: true, text: t});
        }
    }
    return JSON.stringify({clicked: false});
})()
```

### antd 系菜单（JS dispatchEvent 无效 → CDP 真实鼠标）

见 `assets/scripts/antd_hover.py`（模式 P1）。

> **通用规则**：popup/下拉菜单项若带 `data-menu-id`/`href` 属性 → **直接提取 URL 导航**，不要模拟点击（React/antd 的 JS .click() 常不触发；真实点击可能弹登录框）。

---

## 3c_2 · 处理招聘项目复选框

> **跳过条件**：3c_1 已成功导航进入目标语义 Tab 时直接跳过（Tab 已隐含招聘类型）。

```javascript
(function() {
    let kwMap = {
        1: ['应届','校园','校招','正式','全职','春招','秋招'],
        2: ['实习','暑假','暑期','日常'],
        3: ['应届','校园','校招','正式','全职','春招','秋招']  // MODE=3 第一轮先勾校招类
    };
    let kws = kwMap[MODE] || kwMap[1];
    let els = document.querySelectorAll('input[type="checkbox"], label, span, a, button, div');
    for (let el of els) {
        let t = el.textContent.trim();
        for (let kw of kws) {
            if (t.includes(kw) && t.length < 30 && el.offsetParent !== null) {
                el.click();
                return JSON.stringify({clicked: true, text: t});
            }
        }
    }
    return JSON.stringify({clicked: false});
})()
```

> 首次未找到 → 大模型自主最多 3 个动作 → 仍失败直接跳过进入 3d（报告标注）。
> MODE=3：第一轮勾校招类 → 3d~3g → 取消勾选 → 第二轮勾实习类 → 3d~3g；第二轮无实习类则只保留第一轮结果。

---

## 3d · ⭐ 搜索（强制执行，不可跳过）

```python
# 定位搜索框（主文档 → iframe 兜底）
search_input = js("""
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
# iframe 兜底：遍历 document.querySelectorAll('iframe')，同源查 iframe.contentDocument（跨源抛错则捕获跳过）
```

```python
# 填入关键词（native setter，触发 input/change 事件）
js(f"""
    (function() {{
        let inputs = document.querySelectorAll('input');
        for (let inp of inputs) {{
            let ph = (inp.placeholder||'').toLowerCase();
            if (ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search')) {{
                let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                setter.call(inp, '{KEYWORD}');
                inp.dispatchEvent(new InputEvent('input',{{bubbles:true, inputType:'insertText', data:'{KEYWORD}'}}));
                inp.dispatchEvent(new Event('change',{{bubbles:true}}));
                inp.focus();
                return;
            }}
        }}
    }})()
    """)
time.sleep(1)
# 触发搜索：回车 或 点击搜索按钮（优先点按钮，回车对 SPA 有时无效）
js("""(function() {
        let ae = document.activeElement;
        if (ae && ae.tagName === 'INPUT') {
            ae.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
            ae.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',keyCode:13,bubbles:true}));
            return 'enter';
        }
        return 'no-input';
    })()""")
time.sleep(3)
```

> **验证搜索生效**：URL 出现 q/query/keyword 参数，或页面"共 N 个/职位列表 N 个"统计变化（汇川 URL 变 `?q=前端`、网易变"职位列表 1 个"）。未生效 → 自主动作最多 5 个 → 仍失败 → **不跳过站点**，进入 3f 提取默认列表并标注"未执行搜索（搜索框未找到），取页面默认岗位列表"。

---

## 3e · 等待搜索完成（轮询，非固定延时）

```python
import time
for _ in range(10):                      # 最多等 ~10s
    n = js("document.querySelectorAll('[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post]').length")
    if n and n > 0:                      # 岗位容器出现即认为完成（360 ~4s、美团 ~6s、汇川/网易 ~5s）
        break
    time.sleep(1)
wait_for_load()
```

---

## 3f · 提取职位链接（三层提取，只取第一页）

```python
# 第一层：`<a>` 链接
links = js("""
JSON.stringify([...document.querySelectorAll('a')].filter(a => {
    const t = a.textContent.trim();
    const h = a.href || '';
    return t.length > 2 && t.length < 200 &&
           (h.includes('position')||h.includes('job')||h.includes('detail')||h.includes('recruit') ||
            a.closest('[class*=JobTitle],[class*=job-title],[class*=position],[class*=job-item]'));
}).map(a => ({title: a.textContent.trim(), link: a.href})))
""")

# 第二层：岗位标题容器（第一层为空时）
containers = js("""
JSON.stringify([...document.querySelectorAll('[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post],[class*=position-name],[class*=jobName],[class*=job-name]')]
  .filter(e => e.offsetParent !== null)
  .map(e => e.textContent.trim())
  .filter(t => t.length > 2 && t.length < 60))
""")

# 第三层：点击容器取 SPA 详情 URL（仅第一层链接数为 0 时启用）
#   循环：点击第 i 个岗位容器 → sleep 1.5s → location.href 变化则记录 {title, url} → js("history.back()") → 再点下一个
#   最多前 5 个容器；React 卡片 JS .click() 不触发 → CDP 真实点击；弹登录 → 模式 P4（列表页 URL + "详情需登录"）
```

---

## 3g · 筛选并记录（含前 3 兜底）

| 情况 | 记录 |
|------|------|
| 标题含 KEYWORD（连续子串） | 企业名 + 岗位详情页链接 |
| 搜索结果非空但无匹配（`0 < 岗位数`） | **取前 3 项岗位链接**（≥3 取前 3；<3 取全部），标注"无精确匹配，取前 N 个岗位" |
| 搜索结果为空（0 条） | 企业名 + 状态"无匹配岗位" + 原始 URL，直接跳过 |
| 搜索框未找到（已兜底提取默认列表） | 同匹配/前3兜底逻辑，标注"未搜索" |
| 岗位详情需登录 | 职位列表页 URL + 岗位标题，标注"详情需登录" |

> 返回的必须是**岗位链接**，不是官网首页链接。
