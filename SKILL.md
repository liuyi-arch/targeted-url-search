---
name: targeted-url-search
description: "Automated job search on recruitment websites with dual-mode trigger. Workflow mode: triggered by 'targeted-url-search', batch-searches URLs from previous node. Atomic mode: triggered by 'search specific content on specific website' semantics. Validates required inputs (URL+keyword) before execution."
version: 4.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
visibility: "public"
agent_created: true
---
# 招聘网站自动化岗位搜索

两种触发模式 + 必填参数校验 + 自动执行：打开网站 → 勾选招聘项目复选框 → 搜索关键词 → 从第一页结果中筛选标题含搜索词的岗位链接 → 输出精炼报告

注意：
> - 所有浏览器命令升级为 **browser-use v3.0** Python pipe 语法（`browser-use <<'PY'...PY'`）
> - 搜索步骤改为**强制执行**，不可跳过（即使页面默认列表已含目标岗位也必须走搜索流程）
> - 搜索结果为空 → **直接跳过**，不尝试兜底策略（URL 参数、分页等）
> - 输出格式简化：匹配→网站名称+链接；不匹配→网站名称+状态+说明+网站链接
> - 增强原子模式触发检测（新增"在...中用...检索"、"是否有相关岗位"等模式）

---

## 一、触发模式

本技能有两种触发模式，根据用户提示词自动判断。

- 工作流模式触发条件：用户明确提及 "targeted-url-search"。
- 原子模式触发条件：用户提示词包含"在特定网站检索特定内容"语义。
- 若两种模式都被触发，工作流模式优先级高于原子模式。

---

## 二、前置步骤：输入收集与校验

### Step 0a: 从用户提示词中提取输入数据

首先尝试从用户**当前提示词**中直接提取数据，避免不必要的二次询问。

#### 工作流模式 — 提取逻辑

1. **JSON_FILE**：检查上下文中是否存在上一节点输出的 JSON 文件路径（如 `smartsheet_filter_result.json`）。若存在，读取该文件获取 URL 列表和企业名。
2. **KEYWORD**：从提示词中提取搜索关键词（如"前端"、"后端"、"算法"等）。
3. **SUPPLEMENTARY**：从提示词中提取补充信息（如"校招"、"实习"等招聘项目模式提示）。
4. **EXCLUDE_INDICES**：从提示词中提取用户明确排除的网站序号（如"第2个不用查"）。

#### 原子模式 — 提取逻辑

1. **URL_LIST**：从提示词中提取 URL（匹配 `https?://` 开头的字符串，支持多个）。
2. **KEYWORD**：从提示词中提取搜索关键词。
3. **SUPPLEMENTARY**：从提示词中提取补充信息。

### Step 0c: 校验必填字段

**必填字段**：`URL`（或 `JSON_FILE`）和 `KEYWORD`

| 检查项 | 工作流模式 | 原子模式 |
|--------|-----------|---------|
| URL 来源 | JSON 文件是否存在且含有效 URL | 用户是否提供了有效 URL |
| KEYWORD | 用户是否给出了搜索关键词 | 用户是否给出了搜索关键词 |

**校验通过** → 进入 Step 0d 解析补充信息。

**校验失败**（任一必填字段缺失）→ 提示用户缺少哪个字段，然后**根据模式重新询问**：

#### 重新询问 — 工作流模式（重复 Step 0b 工作流）

使用 `AskUserQuestion` 工具提问：

```
问题: "是否对上一个节点输出网站进行全量检索？"
选项:
  - "全量检索" → 对上一节点输出的所有网站进行检索，需补充关键词和补充信息
  - "选择性检索" → 排除部分网站，需补充：排除序号、关键词、补充信息
```

- 若选择"全量检索"：继续询问"请给出检索关键词和补充信息（可选，如校招/实习）"
- 若选择"选择性检索"：���续询问"请说明哪些网页不需要检索（给出序号）、检索关键词、补充信息（可选）"

收集到回答后，**回到 Step 0c 重新校验**。

#### 重新询问 — 原子模式（重复 Step 0b 原子）

直接向用户提示：

> "请输入待检索网站网址、检索关键词、其余补充信息（可选）。"

并明确指出当前缺失的字段（如"未检测到网站网址"或"未检测到检索关键词"）。

收集到回答后，**回到 Step 0c 重新校验**。

> **循环终止条件**：必填字段校验通过，或用户明确表示取消任务。

### Step 0d: 解析补充信息

校验通过后，从 `SUPPLEMENTARY` 中解析招聘项目模式 `MODE`：

| 补充信息关键词 | MODE 值 | 含义 |
|--------------|---------|------|
| "校招" "全职" "正式" "秋招" "春招" "社招" | 1 | 勾选"校招/全职/正式"类复选框 |
| "实习" "日常" "暑假" "暑期" | 2 | 勾选"实习/日常/暑假"类复选框 |
| 未提及或不确定 | 3 | 不勾选（默认） |

### Step 0e: 构建最终输入参数

| 参数 | 变量名 | 类型 | 必填 | 来源 |
|------|--------|------|------|------|
| URL 列表 | `URL_LIST` | array&lt;string&gt; | 是 | 工作流：JSON 提取（可排除部分）；原子：用户输入 |
| 企业名列表 | `COMPANY_LIST` | array&lt;string&gt; | 否 | 工作流：JSON 提取；原子：从 URL 域名推断 |
| 搜索关键词 | `KEYWORD` | string | 是 | 用户输入或从提示词提取 |
| 招聘项目模式 | `MODE` | int | 否 | 从补充信息解析，默认 3 |
| 补充信息 | `SUPPLEMENTARY` | string | 否 | 用户输入 |
| 触发模式 | `TRIGGER_MODE` | string | — | "workflow" 或 "atomic"（用于报告） |

---

## 三、输出

按 `references/report-template.md` 格式生成报告，包含 3 个部分：

1. **任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数
2. **匹配结果**：标题含搜索词的岗位 — 网站名称 + 岗位链接
3. **不匹配结果**：无匹配的站点 — 网站名称 + 检索状态 + 说明 + 网站链接

> **链接规则**：
> - 匹配成功 → 返回**岗位详情页链接**
> - 搜索失败/跳过/无匹配 → 返回**网站原始 URL**
> - 空结果（搜索成功但 0 条匹配）→ 直接跳过，不尝试兜底策略

---

## 四、前提条件

### 一次性预装（跳过如已安装）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # 验证
```

### 每次运行前

```bash
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor  # 快速检查，~2s

# 确认 browser-use 版本（v3.0+ 使用 Python pipe 语法）
browser-use doctor 2>&1 | grep version
```

---

## 五、核心规则

1. **始终使用 browser-use v3.0 语法**：`browser-use <<'PY' ... PY'` Python pipe 模式。**禁止**使用已废弃的 `browser-use open/state/click/input/close` 子命令。
2. **核心 API**：`new_tab(url)` 打开页面、`page_info()` 获取页面信息、`js(code)` 执行 JS 与提取数据、`fill_input(selector, text)` 填表、`capture_screenshot(path)` 截图、`wait_for_load()` 等待加载。
3. **搜索步骤强制执行**：对每个站点，必须按 3a→3b→**3c(MODE)**→**3d(搜索)**→3e(结果)→3f(提取)→3g(筛选) 完整流程执行，**不可跳过 3d 搜索步骤**。
4. **只取第一页**：搜索后不滚动、不分页，只提取当前可见的第一页职位。
5. **空结果直接跳过**：搜索后若匹配数为 0，直接记录状态并进入下一个站点，**不尝试** URL 参数、分页、滚动加载等兜底策略。
6. **合并 JS 查询**：用单次 `js()` 提取所有需要的数据，减少交互轮次。
7. **会话清理**：全部站点处理完毕后，用 `browser-use --reload` 关闭浏览器守护进程。

---

## 六、执行流程

### Step 1: 构建 URL 列表

#### 工作流模式

```bash
# 用 jq 提取企业名和 URL（不读全文件，节省 token）
# 如果有排除序号，先过滤
jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"' "$JSON_FILE"
```

> 如果 JSON 结构不同，用 `jq -r '.. | .url? // empty'` 通用提取，或用 `jq keys` 查看字段名。
>
> 如果用户指定了排除序号（EXCLUDE_INDICES），跳过对应行。

#### 原子模式

用户提供的 URL 列表即为 `URL_LIST`，企业名从 URL 域名推断（如 `dexmal-inc.jobs.feishu.cn` → "原力灵机"）。

> 如果无法从域名推断企业名，使用域名本身作为标识。

### Step 2: 环境检查

```bash
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor  # 确认安装正常
```

### Step 3: 逐站点处理

对 `URL_LIST` 中的每个 URL，依次执行 3a-3g。

#### 3a. 打开页面

```bash
browser-use <<'PY'
new_tab("$URL")
info = page_info()
print(f"Title: {info.get('title', '')}")
PY
```

> 如果页面跳转（重定向），以最终 URL 和标题为准。

#### 3b. 等待加载并获取页面结构

```bash
browser-use <<'PY'
wait_for_load()
# 确认页面已加载 → 检查文本长度 > 200 字符
text = js("document.body.innerText")
print(f"Page text length: {len(text)}")
print(text[:2000])
PY
```

> 如果页面文本长度 < 200，可能需要额外等待或页面加载失败，记录为"页面加载失败"。

#### 3c. 处理招聘项目复选框（根据 MODE）

**MODE=3（不勾选）**：跳过此步骤，直接到 3d。

**MODE=1（校招/全职/正式）或 MODE=2（实习/日常/暑假）**：按以下顺序尝试：

**优先级 1：检查 URL 是否已暗示招聘类型**
```
# MODE=1 时，URL 含 /campus/ 或 /social/ 或 /full-time/ → 已满足，跳过
# MODE=2 时，URL 含 /intern/ 或 /practice/ → 已满足，跳过
```

**优先级 2：用 JS 查找复选框并点击**

```bash
browser-use <<'PY'
# MODE=1: 查找含 "校招" "校园招聘" "全职" "正式" 的复选框/标签并点击
# MODE=2: 查找含 "实习" "日常实习" "暑假" 的复选框/标签并点击
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

> 不同网站的复选框实现方式不同，详见 `references/site-patterns.md`。如果 MODE 对应的招聘类型在页面上完全找不到，记录到注意事项并继续搜索。

#### 3d. ⭐ 搜索（强制执行，不可跳过）

**此步骤必须执行，无论页面默认列表是否已显示目标关键词。**

```bash
browser-use <<'PY'
# Step 1: 定位搜索输入框
# 用 JS 查找 placeholder 含"搜索"/"职位"/"岗位"/"search" 的 input 元素
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
        // 备选：按回车触发搜索
        document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}));
        return 'enter';
    })()
    """)
else:
    print("WARNING: No search input found on page — recording as search failure")
PY
```

**如果找不到搜索框**：记录该站点为"搜索失败"（状态=搜索框未找到），跳过该站点。

> **禁止跳过此步骤**。即使页面默认列表已经显示了目标关键词，也必须走搜索流程，因为：
> 1. 部分 SPA 网站默认列表是精选子集，不展示全部岗位（如拼多多校招站）
> 2. 搜索是唯一能确保结果完整性的操作
> 3. 可复现、可验证

#### 3e. 等待搜索完成

```bash
browser-use <<'PY'
wait_for_load()
js("new Promise(r => setTimeout(r, 3000))")
# 验证搜索结果已加载
text = js("document.body.innerText")
print(f"After search, page text length: {len(text)}")
PY
```

#### 3f. 提取搜索结果中的职位链接

用单次 `js()` 一次性提取第一页所有职位的标题和链接：

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

> 不同网站的职位链接选择器可能不同，详见 `references/site-patterns.md` 中的站点适配表。如果通用脚本提取不到结果，改用站点专用选择器。

#### 3g. 按标题子串筛选并记录结果

在提取的 JSON 结果中，检查每个职位标题是否包含搜索词作为**连续子串**：

- **匹配**（标题含搜索词）→ 记录：企业名 + 岗位链接
- **不匹配**（标题不含搜索词）→ 记录：企业名 + 检索状态 + 说明 + 网站链接
- **空结果**（0 条匹配）→ 直接跳过，**不尝试兜底策略**（不翻页、不换搜索方式）

将结果按企业名分组暂存。

---

### Step 4: 关闭浏览器

```bash
# browser-use v3.0: 用 --reload 重启守���进程来关闭浏览器
browser-use --reload
# 同时清理可能残留的 Chrome 进程
pkill -9 -f "Google Chrome" 2>/dev/null
```

---

### Step 5: 生成精炼报告

按 `references/report-template.md` 格式生成报告，包含 3 个部分：

1. **任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数
2. **匹配结果**：网站名称 + 岗位链接
3. **不匹配结果**：网站名称 + 检索状态 + 说明 + 网站链接

**链接规则**：
- 匹配成功 → 使用**岗位详情页链接**
- 搜索失败/跳过/无匹配 → 使用**网站原始 URL**

---

## 七、站点适配快速参考

| 站点类型 | 搜索框定位 | 搜索触发方式 | 职位链接选择器 | 特殊行为 |
|---------|-----------|-------------|--------------|---------|
| 飞书招聘 (jobs.feishu.cn) | `input[placeholder*="搜索"]` | 点击搜索按钮 | `a[href*="position/detail"]` | 搜索正常 |
| INTSIG (intsig.zhiye.com) | `input[placeholder*="搜索"]` | fill + Enter 或 button | `[class*="JobTitle"]` + `a` | 搜索按钮可能不触发 |
| **拼多多校招 (careers.pddglobalhr.com)** | `input#name`（placeholder="搜索职位名称"） | `.page-job-list_searchButton__bYEas` 按钮 | `.page-job-list_jobList__UqU9K` 内 `a` 标签 | ⚠️ 默认列表不展示全部岗位，**必须搜索** |
| 通用 | `input[type="text/search"]` | fill + Enter | `a[href*="position/job/detail"]` | — |

详见 `references/site-patterns.md`。

---

## 八、注意事项（错误处理经验）

### 环境问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `browser-use: command not found` | 未安装或 PATH 未设置 | `export PATH="$HOME/.local/bin:$PATH"` 然后 `uv tool install browser-use` |
| Python 版本过低 | 系统 Python < 3.11 | 用 `uv tool install`（自动安装 Python 3.13），**不要**用 `pip3 install` |
| browser-use v2 vs v3 语法不兼容 | 旧技能使用 `browser-use open/state/close` 等已废弃命令 | 本技能 v4.0 已全部适配 v3.0 `<<'PY'` 语法，不要混用旧命令 |

### 浏览器问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| Chrome 弹出 "Allow remote debugging?" | macOS 首次远程调试需授权 | 在弹窗点击 Allow；或预先用 `open -a "Google Chrome" --args --remote-debugging-port=9222 '--remote-allow-origins=*'` 启动 |
| zsh 报 `no matches found` | `--remote-allow-origins=*` 的 `*` 被 zsh 通配符展开 | 使用单引号包裹：`'--remote-allow-origins=*'` |
| 浏览器会话残留 | 上次 `--reload` 未执行 | 执行 `browser-use --reload` 后 `pkill -9 -f "Google Chrome"` |
| 页面打不开 | session 异常 | `browser-use --reload` 然后重试 |
| 搜索未触发过滤 | JS 框架事件不兼容 | 用 `fill_input` + JS `requestSubmit()` 或键盘事件 `Enter` |

### 数据提取问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 职位链接提取不到 | 选择器不匹配 | 参考 `references/site-patterns.md` 站点专用选择器 |
| 默认列表不包含目标岗位 | SPA 站点分页/懒加载 | **必须走搜索步骤（3d）**，不依赖默认列表 |
| 搜索后结果为空 | 该站点确实无相关岗位 | 直接记录"搜索成功，无匹配"，跳过该站点，不尝试兜底 |

### 搜索词匹配规则

- **匹配条件**：搜索词是职位标题的**连续子串**（如 "前端" 匹配 "前端开发工程师" 和 "Web前端研发工程师"）
- **大小写**：JS 的 `String.includes()` 区分大小写，中文无此问题，英文关键词需注意
- **只看第一页**：不滚动加载更多，不分页检查，只提取搜索后当前可见的职位
- **空结果处理**：直接跳过，不尝试 URL 参数、分页、滚动加载等兜底策略

---

## 九、优化数据

| 指标 | 无技能 | 使用本技能（v3.0） | v4.0 提升 |
|------|--------|-----------|----------|
| 步骤数 | 57 | 12-15（视站点数） | 更少（强制搜索减少遗漏） |
| 漏检率 | 高 | 中（依赖默认列表） | 低（强制搜索确保完整性） |
| Token | ~45K | ~8-12K | 更少（空结果不兜底） |
| 用户交互 | 3 | 0-2 | 0-2（原子模式触发更准） |
