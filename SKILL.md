---
name: targeted-url-search
description: "Automated job search on recruitment websites with dual-mode trigger. Workflow mode: triggered by 'targeted-url-search', batch-searches URLs from previous node. Atomic mode: triggered by 'search specific content on specific website' semantics. Validates required inputs (URL+keyword) before execution."
version: 3.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
display_name: "招聘网站自动化搜索"
display_name_en: "Job Site Auto Search"
description_zh: "两种触发模式：工作流模式（提及targeted-url-search，对上一节点输出网站批量检索）和原子模式（在特定网站检索特定内容语义）。自动校验必填参数（URL+关键词），收集补充信息后执行：打开网站→勾选复选框→搜索关键词→第一页结果筛选→输出报告"
description_en: "Two trigger modes: workflow (mention targeted-url-search, batch search from previous node output) and atomic (search specific content on specific website). Validates required inputs, collects supplementary info, executes: open→check→search→filter first page→report"
visibility: "public"
agent_created: true
---

# 招聘网站自动化岗位搜索

两种触发模式 + 必填参数校验 + 自动执行：打开网站 → 勾选招聘项目复选框 → 搜索关键词 → 从第一页结果中筛选标题含搜索词的岗位链接 → 输出精炼报告。

---

## 一、触发模式

本技能有两种触发模式，根据用户提示词自动判断。

### 模式一：工作流模式

| 项目 | 说明 |
|------|------|
| **触发条件** | 用户明确提及 "targeted-url-search" |
| **适用场景** | 上一个节点已输出网站列表（如从智能表格筛选出的企业投递链接 JSON），需要对这些网站进行批量检索 |
| **URL 来源** | 上一节点输出的 JSON 文件（含企业名和投递链接） |

### 模式二：原子模式

| 项目 | 说明 |
|------|------|
| **触发条件** | 用户提示词包含类似"在特定网站检索特定内容"语义（如"在 xx 网站上搜索前端岗位"、"帮我看看这个链接里有没有算法岗"） |
| **适用场景** | 用户直接提供待检索网站 URL，不依赖上一节点输出 |
| **URL 来源** | 用户直接输入 |

> **触发判断优先级**：如果用户同时满足两种条件，优先判定为**工作流模式**。
>
> **触发词模式详见** `references/mode-detection.md`。

---

## 二、前置步骤：输入收集与校验

### Step 0a: 检测触发模式

检查用户提示词：

- 提示词包含 "targeted-url-search" → **工作流模式**，进入 Step 0b（工作流）
- 提示词包含"在...网站...检索/搜索..."或"帮我看...链接...有没有...岗位"等类似语义 → **原子模式**，进入 Step 0b（原子）
- 两者都不匹配 → **不触发本技能**

### Step 0b: 从用户提示词中提取输入数据

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
- 若选择"选择性检索"：继续询问"请说明哪些网页不需要检索（给出序号）、检索关键词、补充信息（可选）"

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

精炼 4 段式报告（详见 `references/report-template.md`）：
1. 任务参数（触发模式、勾选模式、搜索词、URL 来源、站点数）
2. 标题含搜索词的岗位表（企业名 + 职位标题 + 链接）
3. 标题不含搜索词的岗位表（企业名 + 职位标题 + 链接）
4. 注意事项（站点适配问题 + 错误处理经验）

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
```

---

## 五、核心规则

1. **始终用 `browser-use open <url>`**（headless 模式，0 交互）。**禁止**用 `browser-use connect`。
2. **始终用 CLI 命令**（`browser-use input`、`browser-use click`、`browser-use state`）而非 Python harness 函数。
3. **交互前先运行 `browser-use state`** 获取元素索引。
4. **用 `browser-use state` 替代截图**进行页面分析。
5. **合并 JS 查询**——用单次 `browser-use eval` 提取所有需要的数据。
6. **只看第一页结果**——搜索后不滚动、不分页，只提取当前可见的第一页职位。

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
browser-use open "$URL"
browser-use state  # 获取页面元素索引
```

#### 3b. 获取页面元素索引

`browser-use state` 返回所有可交互元素及其索引号，用于后续 `click`/`input` 命令。

#### 3c. 处理招聘项目复选框（根据 MODE）

**此步骤是核心步骤**——不同用户需求不同（校招/实习），必须根据 MODE 参数找到并勾选对应的复选框。

**MODE=3（不勾选）**：跳过此步骤，直接到 3d。

**MODE=1（校招/全职/正式）或 MODE=2（实习/日常/暑假）**：按以下顺序尝试：

**优先级 1：检查 URL 是否已暗示招聘类型**
```
# MODE=1 时，URL 含 /campus/ 或 /social/ 或 /full-time/ → 已满足，跳过
# MODE=2 时，URL 含 /intern/ 或 /practice/ → 已满足，跳过
```

**优先级 2：用 state 输出查找复选框**
```bash
# state 输出中查找含以下关键词的可点击元素：
# MODE=1: "校招" "校园招聘" "全职" "正式" "秋招" "春招" "社招"
# MODE=2: "实习" "日常实习" "暑假" "暑期" "日常"
# 找到后用索引号点击：
browser-use click <index>
browser-use state  # 验证勾选状态
```

**优先级 3：用 eval 查找自定义复选框**

不同网站使用不同的复选框实现方式，详见 `references/site-patterns.md`：

```bash
# 飞书招聘 (jobs.feishu.cn): atsx-tree-checkbox 类
# MODE=1: 找"校园招聘"/"校招招聘"对应的复选框
browser-use eval "JSON.stringify([...document.querySelectorAll('.atsx-tree-checkbox')].map((el,i)=>({i,text:el.parentElement?.parentElement?.textContent?.trim()?.substring(0,20)||'',checked:el.className.includes('checked')})))"
# 找到目标索引后点击
browser-use eval "document.querySelectorAll('.atsx-tree-checkbox')[<target_index>].click()"
```

**优先级 4：导航标签替代复选框**

部分网站用导航标签（如"校园招聘"/"社会招聘"/"实习生招聘"）而非复选框。用 state 找到对应标签文本的元素索引并点击。

> 如果 MODE 对应的招聘类型在页面上完全找不到（既无复选框也无导航标签也无 URL 路径暗示），记录到注意事项并继续搜索。

#### 3d. 输入搜索词并搜索

```bash
# 1. 从 state 输出找到搜索输入框索引
#    查找 placeholder 含"搜索"/"职位"/"岗位"/"search" 的 input 元素
# 2. 输入搜索词
browser-use input <search_input_index> "$KEYWORD"
# 3. 点击搜索按钮
#    从 state 输出查找含"搜索"/"查询"/"search" 的 button 元素
browser-use click <search_button_index>
# 4. 验证搜索结果
browser-use state
```

**备选方案：如果点击搜索按钮未触发过滤**
```bash
# 方案A：用 URL 参数直接搜索
browser-use open "${BASE_URL}?keyword=$KEYWORD"
# 方案B：在搜索框聚焦后按回车
browser-use click <search_input_index>
browser-use type "$KEYWORD"
browser-use keys "Enter"
# 方案C：触发表单 submit 事件
browser-use eval "document.querySelector('form')?.requestSubmit()"
```

#### 3e. 获取第一页结果

**只看第一页，不滚动、不分页。** 搜索完成后等待结果加载：

```bash
browser-use wait text "职位" --timeout 5000  # 等待结果区域出现
browser-use state  # 确认结果已加载
```

#### 3f. 提取职位标题和链接

用单次 `browser-use eval` 一次性提取第一页所有职位的标题和链接：

```bash
# 通用提取脚本（适配多种网站结构）
browser-use eval "JSON.stringify([...document.querySelectorAll('a')].filter(a=>{const t=a.textContent.trim();const h=a.href||'';return t.length>2&&t.length<200&&(h.includes('position')||h.includes('job')||h.includes('detail')||a.closest('[class*=JobTitle],[class*=job-title],[class*=position]'))}).map(a=>({title:a.textContent.trim(),link:a.href})))"
```

> 不同网站的职位链接选择器可能不同，详见 `references/site-patterns.md` 中的站点适配表。如果通用脚本提取不到结果，改用站点专用选择器。

#### 3g. 按标题子串筛选

在提取的 JSON 结果中，检查每个职位标题是否包含搜索词作为**连续子串**：

```bash
# 在 eval 中直接 filter
browser-use eval "JSON.stringify({matched:[...document.querySelectorAll('a')].filter(a=>a.textContent.includes('$KEYWORD')).map(a=>({title:a.textContent.trim(),link:a.href})),unmatched:[...document.querySelectorAll('a')].filter(a=>{const t=a.textContent.trim();return t.length>2&&t.length<200&&!t.includes('$KEYWORD')&&(a.href.includes('position')||a.href.includes('detail'))}).map(a=>({title:a.textContent.trim(),link:a.href}))})"
```

将结果按 `企业名` 分组暂存。

### Step 4: 关闭浏览器

```bash
browser-use close
```

### Step 5: 生成精炼报告

按 `references/report-template.md` 格式生成报告，包含 4 个部分：

1. **任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数
2. **标题含搜索词的岗位表**：企业名 | 职位标题 | 链接
3. **标题不含搜索词的岗位表**：企业名 | 职位标题 | 链接
4. **注意事项**：站点适配问题 + 错误处理经验（供下次执行参考）

---

## 七、站点适配快速参考

| 站点类型 | 复选框定位 | 搜索框定位 | 职位链接选择器 |
|---------|-----------|-----------|--------------|
| 飞书招聘 (jobs.feishu.cn) | `.atsx-tree-checkbox` + 邻近文本 | `input[placeholder*="搜索"]` | `a[href*="position"]` |
| INTSIG (intsig.zhiye.com) | URL 路径含 `/campus/` 即满足 | `input[placeholder*="搜索"]` | `[class*="JobTitle"]` + `a` |
| 通用 | `input[type="checkbox"]` + label | `input[type="text/search"]` | `a[href*="position/job/detail"]` |

详见 `references/site-patterns.md`。

---

## 八、注意事项（错误处理经验）

### 环境问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `browser-use: command not found` | 未安装或 PATH 未设置 | `export PATH="$HOME/.local/bin:$PATH"` 然后 `uv tool install browser-use` |
| Python 版本过低 | 系统 Python < 3.11 | 用 `uv tool install`（自动安装 Python 3.13），**不要**用 `pip3 install` |

### 浏览器问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 页面打不开 | session 异常 | `browser-use close` 然后重试 |
| 元素找不到 | 页面未加载完 | `browser-use wait text "xxx" --timeout 10000` |
| 搜索未过滤 | JS 框架事件不兼容 | 用 URL 参数 `?keyword=xxx` 或 `requestSubmit()` |

### 数据提取问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 职位链接提取不到 | 选择器不匹配 | 用 `browser-use get html` 查看结构，调整选择器 |
| 标题和链接不匹配 | DOM 层级复杂 | 用 `a.closest('[class*=JobTitle]')` 或反向 `titleEl.closest('a')` |
| 链接不完整（相对路径） | 网站用相对 URL | 用 `new URL(link, location.origin).href` 补全 |

### 搜索词匹配规则

- **匹配条件**：搜索词是职位标题的**连续子串**（如 "前端" 匹配 "前端开发工程师"，不匹配 "前/端工程师"）
- **大小写**：JS 的 `String.includes()` 区分大小写，中文无此问题，英文关键词需注意
- **只看第一页**：不滚动加载更多，不分页检查，只提取搜索后当前可见的职位

---

## 九、优化数据

| 指标 | 无技能 | 使用本技能 |
|------|--------|-----------|
| 步骤数 | 57 | 12-15（视站点数） |
| 耗时 | ~34 min | ~5-8 min |
| Token | ~45K | ~8-12K |
| 用户交互 | 3 | 0（参数齐全时）/ 1-2（需补充参数时） |
