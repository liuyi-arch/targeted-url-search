---
name: targeted-url-search-pro
description: "招聘网站自动化岗位搜索。工作流模式：由'targeted-url-search'触发，从上一节点JSON批量检索；原子模式：由'在特定网站搜索特定内容'语义触发。自动打开网站→勾选招聘项目→搜索关键词→从第一页结果筛选标题含关键词的岗位链接→输出报告。"
version: 1.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
agent_created: true
---

# 招聘网站自动化岗位搜索

## 一、触发模式

| 模式 | 触发条件 | URL 来源 |
|------|---------|---------|
| 工作流 | 提示词含 `targeted-url-search` | 上一节点 JSON 文件 |
| 原子 | 提示词含"在…网站/链接…搜索/检索…岗位/关键词"语义 | 用户直接输入 |

> 两种同时匹配时，工作流优先。

---

## 二、输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| URL_LIST | 是 | 工作流：从 JSON `records[].投递链接` 提取；原子：用户输入 |
| COMPANY_LIST | 否 | 工作流：从 JSON `records[].招聘企业` 提取；原子：从域名推断 |
| KEYWORD | 是 | 搜索关键词，如"前端"、"算法" |
| MODE | 否 | 1=校招/全职, 2=实习, 3=校招+实习(默认) |
| EXCLUDE_INDICES | 否 | 工作流模式：用户指定跳过的站点序号 |

### MODE 判定

| 补充信息关键词 | MODE |
|--------------|------|
| 校招、全职、正式、秋招、春招、社招、应届 | 1 |
| 实习、日常、暑假、暑期 | 2 |
| 未提及 | 3 |

### 输入校验

必填字段缺失时：工作流模式用 `AskUserQuestion` 询问"全量检索/选择性检索"后补全；原子模式直接提示用户输入 URL + KEYWORD。循环直到校验通过或用户取消。

---

## 三、执行流程

### 前置：环境检查

```bash
pkill -9 -f "remote-debugging-port=9222" # 只清理调试实例：精确匹配调试端口参数，避免误杀用户日常 Chrome
sleep 1

open -a "Google Chrome" --args --remote-debugging-port=9222 # 用远程调试端口启动 Chrome

export PATH="$HOME/.local/bin:$PATH"
browser-use doctor # 验证 browser-use 连接
```

### Step 1：构建 URL 列表

- **工作流**：读取 JSON 文件，用 `jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过对应行。
- **原子**：用户提供的 URL 列表即 `URL_LIST`。

### Step 2：逐站点处理（3a–3g）

对每个 URL 执行以下子步骤，全部通过 `browser-use <<'PY' ... PY` Python pipe 模式调用。

**3a. 打开页面**

```python
goto_url("$URL")          # 在当前标签页直接导航，复用同一 tab
info = page_info()
print(f"Title: {info.get('title', '')}")
```

**3b. 等待加载**

```python
wait_for_load()
text = js("document.body.innerText")
# 文本长度 < 200 → 可能加载失败
```

**3c_1. 导航至目标招聘类型 Tab**

检查页面头部导航栏，根据 MODE 导航到对应语义的 Tab。Tab 导航优先于复选框（定位更可靠：文本短且独特、可见性好、点击副作用明显）。

| MODE | 优先导航 Tab 语义关键词 | 
|------|----------------------|
| 1 | 应届招聘 / 校园招聘 / 校招岗位 / 校招 / 应届 | 
| 2 | 实习招聘 / 实习生 / 实习 → 未找到则回退到 MODE=1 关键词（报告标注对应原因） | 
| 3 | 先导航 MODE=1 关键词 Tab → 执行 3c_2~3g → 再导航 MODE=2 关键词 Tab → 再执行 3c_2~3g | 

> **未找到MODE对应语义Tab**：导航至「岗位/职位」语义 Tab -> 若「岗位/职位」语义 Tab也未找到，允许大模型执行最多3个自助动作 -> 若仍未达成，跳过 3c_1（报告标注对应原因）。

Tab 查找与点击 JS：

```javascript
(function() {
    // MODE→目标 Tab 关键词映射（MODE=3 此处先取校招类，实习类在第二轮处理）
    let kwMap = {
        1: ['应届招聘','校园招聘','校招岗位','校招','应届'],
        2: ['实习招聘','实习生','实习'],
        3: ['应届招聘','校园招聘','校招岗位','校招','应届']
    };
    let kws = kwMap[MODE] || kwMap[1];
    let fallbackKws = ['岗位','职位','Jobs','Positions'];

    // 优先在导航栏区域查找（header/nav/菜单/Tab容器）
    let navSel = 'header, nav, [class*=nav], [class*=menu], [class*=header], [class*=tab]';
    let navAreas = document.querySelectorAll(navSel);
    let searchAreas = navAreas.length > 0 ? navAreas : [document.body];

    // 第一轮：目标语义 Tab
    for (let area of searchAreas) {
        for (let el of area.querySelectorAll('a, button, li, span, div[role="tab"]')) {
            let t = el.textContent.trim();
            for (let kw of kws) {
                if (t.includes(kw) && t.length < 20 && el.offsetParent !== null) {
                    el.click();
                    return JSON.stringify({clicked: true, text: t, kw: kw, fallback: false});
                }
            }
        }
    }

    // 第二轮回退：「岗位/职位」语义 Tab
    for (let area of searchAreas) {
        for (let el of area.querySelectorAll('a, button, li, span, div[role="tab"]')) {
            let t = el.textContent.trim();
            for (let kw of fallbackKws) {
                if (t.includes(kw) && t.length < 20 && el.offsetParent !== null) {
                    el.click();
                    return JSON.stringify({clicked: true, text: t, kw: kw, fallback: true});
                }
            }
        }
    }

    return JSON.stringify({clicked: false});
})()
```

导航后验证（URL 变化或 DOM 内容变化即视为成功）：

```python
import time
url_before = page_info().get('url', '')
text_before = js("document.body.innerText")[:200]
# ↑ 执行上面的 Tab 点击 JS ↓
time.sleep(3); wait_for_load()
url_after = page_info().get('url', '')
text_after = js("document.body.innerText")[:200]
tab_navigated = (url_before != url_after) or (text_before != text_after)
```

> **MODE=3 特殊流程**：3c_1 第一轮导航到校招类 Tab 后，依次执行 3c_2→3d→3e→3f→3g；然后回到 3c_1 第二轮导航到实习类 Tab，再次执行 3c_2→3d→3e→3f→3g。两轮结果均记入报告。

**3c_2. 处理招聘项目复选框**

> **跳过条件**：若 3c_1 已成功导航进入「应届招聘/校园招聘/校招岗位」或「实习招聘」等语义 Tab，则 3c_2 **直接跳过**——Tab 导航已隐含招聘类型，无需再勾选复选框。

3c_1 未成功导航到「应届招聘/校园招聘/校招岗位」或「实习招聘」等语义 Tab时，用 JS 查找并勾选含目标关键词的复选框/标签：

| MODE | 勾选复选框语义关键词 |
|------|-------------------|
| 1 | 应届 / 校园 / 校招 / 正式 / 全职 / 春招 / 秋招 |
| 2 | 实习 / 暑假 / 暑期 / 日常 |
| 3 | 第一轮勾选 MODE=1 关键词 → 执行 3d~3g → 第二轮勾选 MODE=2 关键词 → 再执行 3d~3g |

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

> **动作限制**：3c_2 中如果首次未找到复选框或未找到目标语义复选框（报告标注对应原因），允许大模型自主决策最多再执行 **3 个动作**（如查 `label[for]` 关联、扩大选择器到 `[class*=checkbox]` 等）。3 个动作后仍未达成，直接跳过 3c_2，进入 3d 搜索步骤。
>
> **MODE=3 特殊流程**：3c_2 第一轮勾选校招类复选框 → 执行 3d~3g → 取消勾选 → 第二轮勾选实习类复选框 → 再执行 3d~3g。若第二轮未找到实习类复选框，只保留第一轮结果。


**3d. ⭐ 搜索（强制执行，不可跳过）**

```python
# 定位搜索框
search_input = js("""
(function() {
    let inputs = document.querySelectorAll('input');
    for (let inp of inputs) {
        let ph = (inp.placeholder || '').toLowerCase();
        if (ph.includes('搜索')||ph.includes('职位')||ph.includes('岗位')||ph.includes('search'))
            return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder});
    }
    return 'null';
})()
""")
# 填入关键词
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
# 触发搜索
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

> 以上定位搜索栏、填入关键词、触发搜索均只尝试一次，失败最多只允许ai自主决策执行3个动作，如果仍失败，直接跳过该站点，记录失败原因。

**3e. 等待搜索完成**

```python
wait_for_load()
js("new Promise(r => setTimeout(r, 3000))")
```

**3f. 提取职位链接**（只取第一页，不滚动不分页）

```javascript
JSON.stringify([...document.querySelectorAll('a')].filter(a => {
    const t = a.textContent.trim();
    const h = a.href || '';
    return t.length > 2 && t.length < 200 &&
           (h.includes('position')||h.includes('job')||h.includes('detail')||h.includes('recruit') ||
            a.closest('[class*=JobTitle],[class*=job-title],[class*=position],[class*=job-item]'));
}).map(a => ({title: a.textContent.trim(), link: a.href})))
```

**3g. 筛选并记录**

检查每个职位标题是否包含 KEYWORD 作为**连续子串**：

| 情况 | 记录 |
|------|------|
| 标题含 KEYWORD | 企业名 + 岗位详情页链接 |
| 标题不含 KEYWORD | 企业名 + 状态"搜索成功" + 说明 + 原始 URL |
| 0 条结果 | 直接跳过，不兜底 |

---

## 四、输出报告

生成 Markdown 报告，保存到 `output/{KEYWORD}岗位检索报告.md`，包含 3 段：

**1. 任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数

**2. 匹配结果**（标题含 KEYWORD 的岗位）：

| # | 网站 | 岗位链接 |
|---|------|---------|
| 1 | {企业名} | {岗位详情页 URL} |

> 链接填岗位详情页 URL；无匹配显示"无匹配岗位"。

**3. 不匹配结果**：

| # | 网站 | 检索状态 | 说明 | 网站链接 |
|---|------|---------|------|---------|

> 检索状态：`搜索成功`(无匹配) / `搜索失败` / `搜索框未找到` / `页面加载失败` / `跳过`；链接填网站原始 URL。

---

## 五、前提条件

```bash
# 一次性安装
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # 验证
```

> **browser-use v3.0 语法**：统一用 `browser-use <<'PY' ... PY` Python pipe 模式。核心 API：`new_tab(url)`、`page_info()`、`js(code)`、`fill_input(selector, text)`、`wait_for_load()`、`capture_screenshot(path)`。
