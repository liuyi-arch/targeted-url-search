# 详细执行流程

本文件包含 `targeted-url-search` 技能的完整执行步骤（Step 0-5），含所有 bash/JS 代码。SKILL.md 仅提供概览，实际执行时按本文件操作。

---

## Step 0: 输入收集与校验

### 0a. 从用户提示词提取数据

#### 工作流模式

1. **JSON_FILE**：检查上下文中是否存在上一节点输出的 JSON 文件路径。若存在，读取获取 URL 列表和企业名。
2. **KEYWORD**：从提示词提取搜索关键词。
3. **SUPPLEMENTARY**：从提示词提取补充信息（如"校招"、"实习"）。
4. **EXCLUDE_INDICES**：从提示词提取用户排除的网站序号（如"第2个不用查"）。

#### 原子模式

1. **URL_LIST**：从提示词匹配 `https?://` 开头的字符串，支持多个。
2. **KEYWORD**：从提示词提取搜索关键词。
3. **SUPPLEMENTARY**：从提示词提取补充信息。

> 详细提取规则见 `mode-detection.md` 第五节。

### 0b. 校验必填字段

**必填**：`URL`（或 `JSON_FILE`）和 `KEYWORD`

| 检查项 | 工作流模式 | 原子模式 |
|--------|-----------|---------|
| URL 来源 | JSON 文件存在且含有效 URL | 用户提供了有效 URL |
| KEYWORD | 用户给出了搜索关键词 | 用户给出了搜索关键词 |

校验通过 → 进入 0d。校验失败 → 按 0c 重新询问。

### 0c. 校验失败时重新询问

#### 工作流模式

使用 `AskUserQuestion`：

```
问题: "是否对上一个节点输出网站进行全量检索？"
选项:
  - "全量检索" → 继续询问关键词和补充信息
  - "选择性检索" → 询问排除序号、关键词、补充信息
```

#### 原子模式

直接提示：

> "请输入待检索网站网址、检索关键词、其余补充信息（可选）。"

并指出缺失字段。收集后回到 0b 重新校验。

> 循环终止：必填字段通过，或用户取消。

### 0d. 解析补充信息 → MODE

| 补充信息关键词 | MODE | 含义 |
|--------------|------|------|
| "校招" "全职" "正式" "秋招" "春招" "社招" | 1 | 勾选校招/全职类复选框 |
| "实习" "日常" "暑假" "暑期" | 2 | 勾选实习类复选框 |
| 未提及或不确定 | 3 | 不勾选（默认） |

---

## Step 1: 构建 URL 列表

### 工作流模式

```bash
# 用 jq 提取企业名和 URL
# 如果有排除序号，先过滤
jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"' "$JSON_FILE"
```

> 如果 JSON 结构不同，用 `jq -r '.. | .url? // empty'` 通用提取，或 `jq keys` 查看字段名。
> 用户指定的排除序号（EXCLUDE_INDICES）跳过对应行。

### 原子模式

用户提供的 URL 列表即为 `URL_LIST`，企业名从 URL 域名推断。无法推断时用域名本身作为标识。

---

## Step 2: 环境检查

```bash
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor  # 确认安装正常
```

---

## Step 3: 逐站点处理

对 `URL_LIST` 中每个 URL，依次执行 3a-3g。

### 3a. 打开页面

```bash
browser-use <<'PY'
new_tab("$URL")
info = page_info()
print(f"Title: {info.get('title', '')}")
PY
```

> 页面重定向时，以最终 URL 和标题为准。

### 3b. 等待加载并获取页面结构

```bash
browser-use <<'PY'
wait_for_load()
text = js("document.body.innerText")
print(f"Page text length: {len(text)}")
print(text[:2000])
PY
```

> 文本长度 < 200 → 可能加载失败，记录为"页面加载失败"。

### 3c. 处理招聘项目复选框

**MODE=3**：跳过，直接到 3d。

**MODE=1 或 MODE=2**：

优先级 1：检查 URL 是否已暗示招聘类型
- MODE=1：URL 含 `/campus/` `/social/` `/full-time/` → 已满足，跳过
- MODE=2：URL 含 `/intern/` `/practice/` → 已满足，跳过

优先级 2：用 JS 查找并点击复选框

```bash
browser-use <<'PY'
# MODE=1: 查找含 "校招" "校园招聘" "全职" "正式" 的元素并点击
# MODE=2: 查找含 "实习" "日常实习" "暑假" 的元素并点击
js("""
(function() {
    let keywords = MODE==1 ? ['校招','校园招聘','全职','正式','秋招','春招','社招'] : ['实习','日常实习','暑假','暑期','日常'];
    let all = document.querySelectorAll('input[type="checkbox"], label, span, a, button, div');
    for (let el of all) {
        let t = el.textContent.trim();
        for (let kw of keywords) {
            if (t.includes(kw) && t.length < 30 && el.offsetParent !== null) {
                el.click();
                return JSON.stringify({clicked: true, text: t, tag: el.tagName});
            }
        }
    }
    return JSON.stringify({clicked: false});
})()
""")
PY
```

> 不同网站复选框实现不同，详见 `site-patterns.md`。找不到对应类型时记录到注意事项并继续搜索。

### 3d. ⭐ 搜索（强制执行，不可跳过）

**此步骤必须执行，无论页面默认列表是否已显示目标关键词。**

```bash
browser-use <<'PY'
# Step 1: 定位搜索输入框
search_input = js("""
(function() {
    let inputs = document.querySelectorAll('input');
    for (let inp of inputs) {
        let ph = (inp.placeholder || '').toLowerCase();
        if (ph.includes('搜索') || ph.includes('职位') || ph.includes('岗位') || ph.includes('search')) {
            return JSON.stringify({id: inp.id, name: inp.name, placeholder: inp.placeholder, className: inp.className?.substring(0,50)});
        }
    }
    return 'null';
})()
""")
print(f"Search input: {search_input}")

# Step 2: 填入关键词并触发搜索
if search_input != 'null':
    import json
    inp = json.loads(search_input)
    selector = f"#{inp['id']}" if inp.get('id') else f"input[placeholder='{inp['placeholder']}']"
    fill_input(selector, "$KEYWORD")

    # 点击搜索按钮
    js("""
    (function() {
        let btns = document.querySelectorAll('button');
        for (let btn of btns) {
            let t = btn.textContent.trim();
            if ((t === '搜索' || t.includes('搜索') || t.includes('Search')) && btn.offsetParent !== null) {
                btn.click();
                return 'clicked';
            }
        }
        document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}));
        return 'enter';
    })()
    """)
else:
    print("WARNING: No search input found — recording as search failure")
PY
```

**找不到搜索框** → 记录该站点为"搜索框未找到"，跳过该站点。

> 禁止跳过此步骤。即使默认列表已显示目标关键词也必须搜索，因为部分 SPA 站点默认列表是精选子集（如拼多多）。

### 3e. 等待搜索完成

```bash
browser-use <<'PY'
wait_for_load()
js("new Promise(r => setTimeout(r, 3000))")
text = js("document.body.innerText")
print(f"After search, page text length: {len(text)}")
PY
```

### 3f. 提取职位链接

```bash
browser-use <<'PY'
result = js("""
JSON.stringify([...document.querySelectorAll('a')].filter(a => {
    const t = a.textContent.trim();
    const h = a.href || '';
    return t.length > 2 && t.length < 200 &&
           (h.includes('position') || h.includes('job') || h.includes('detail') || h.includes('recruit') ||
            a.closest('[class*=JobTitle],[class*=job-title],[class*=position],[class*=job-item]'));
}).map(a => ({title: a.textContent.trim(), link: a.href})))
""")
print(f"Extracted links: {result[:2000]}")
PY
```

> 站点专用选择器见 `site-patterns.md`。通用脚本提取不到时改用专用选择器。

### 3g. 按标题子串筛选并记录

在提取的 JSON 结果中，检查每个职位标题是否包含搜索词作为**连续子串**：

| 情况 | 记录内容 |
|------|---------|
| **匹配**（标题含搜索词） | 企业名 + 岗位详情页链接 |
| **不匹配**（标题不含搜索词） | 企业名 + 检索状态"搜索成功" + 说明 + 网站原始链接 |
| **空结果**（0 条匹配） | 直接跳过，不尝试兜底策略 |

将结果按企业名分组暂存。

---

## Step 4: 关闭浏览器

```bash
# browser-use v3.0: 用 --reload 重启守护进程来关闭浏览器
browser-use --reload
# 清理可能残留的 Chrome 进程
pkill -9 -f "Google Chrome" 2>/dev/null
```

---

## Step 5: 生成报告

按 `report-template.md` 格式生成 3 段式报告，保存到 `output/{KEYWORD}岗位检索报告.md`。

**链接规则**：
- 匹配成功 → 岗位详情页链接
- 搜索失败/跳过/无匹配 → 网站原始 URL
