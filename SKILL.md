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
| MODE | 否 | 1=校招/全职, 2=实习, 3=不勾选(默认) |
| EXCLUDE_INDICES | 否 | 工作流模式：用户指定跳过的站点序号 |

### MODE 判定

| 补充信息关键词 | MODE |
|--------------|------|
| 校招、全职、正式、秋招、春招、社招 | 1 |
| 实习、日常、暑假、暑期 | 2 |
| 未提及 | 3 |

### 输入校验

必填字段缺失时：工作流模式用 `AskUserQuestion` 询问"全量检索/选择性检索"后补全；原子模式直接提示用户输入 URL + KEYWORD。循环直到校验通过或用户取消。

---

## 三、执行流程

### 前置：环境检查

```bash
pkill -9 -f "Google Chrome" # 杀掉可能残留的 Chrome 进程（避免旧连接干扰）

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

**3c. 处理招聘项目复选框**（MODE=3 跳过）

先检查 URL 是否已暗示类型（`/campus/` `/intern/` 等），已满足则跳过。否则用 JS 查找并点击含目标关键词的复选框/标签：

```javascript
(function() {
    let kws = MODE==1 ? ['校招','校园招聘','全职','正式','秋招','春招','社招']
                       : ['实习','日常实习','暑假','暑期','日常'];
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

找不到时记录并继续搜索。

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
# 填入关键词并触发搜索
if search_input != 'null':
    inp = json.loads(search_input)
    selector = f"#{inp['id']}" if inp.get('id') else f"input[placeholder='{inp['placeholder']}']"
    fill_input(selector, "$KEYWORD")
    js("""(function() {
        let btns = document.querySelectorAll('button');
        for (let b of btns) {
            let t = b.textContent.trim();
            if ((t==='搜索'||t.includes('搜索')||t.includes('Search')) && b.offsetParent!==null) { b.click(); return 'clicked'; }
        }
        document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
        return 'enter';
    })()""")
```

> 找不到搜索框 → 记录"搜索框未找到"，跳过该站点。

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


### Step 3：关闭浏览器

```bash
browser-use --reload
pkill -9 -f "Google Chrome" 2>/dev/null
```

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
