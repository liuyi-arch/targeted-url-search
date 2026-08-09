# targeted-url-search-pro

> WorkBuddy Skill: 招聘网站自动化岗位搜索。基于 browser-use v3.0，双模式触发 + 输入校验 + 自动执行。

## 功能概述

给定 JSON 文件（工作流模式）或直接 URL（原子模式）、搜索关键词、可选招聘项目模式，自动完成：

1. **识别触发模式**（工作流 vs 原子）
2. **收集与校验**必填输入（URL + 关键词）— 缺失时询问用户
3. 通过 browser-use v3.0 Python pipe 语法逐站点打开招聘网站
4. 勾选对应招聘项目复选框（校招/实习）
5. 填入搜索关键词并触发搜索 — **强制步骤，不可跳过**
6. 从搜索结果**第一页**提取职位标题与链接
7. 筛选标题中包含搜索词作为**连续子串**的岗位
8. 输出 3 段式精炼报告

## 架构（v1.0 精简版）

```
targeted-url-search-pro/
└── SKILL.md                        # 自包含单文件（~209行）
```

**设计原则**：所有核心逻辑（触发模式、输入校验、执行流程含代码、输出报告模板、前提条件）整合在单个 SKILL.md 中，无外部 references 依赖。

## 双模式触发

| 模式 | 触发条件 | URL 来源 |
|------|---------|---------|
| 工作流 | 提示词含 `targeted-url-search` | 上一节点 JSON 文件 |
| 原子 | 提示词含"在…网站/链接…搜索/检索…岗位/关键词"语义 | 用户直接输入 |

> 两种模式同时匹配时，工作流优先。

### 工作流模式
- 触发：用户提及 "targeted-url-search"
- URL 来源：上一节点输出的 JSON 文件（含 `records[].招聘企业` 和 `records[].投递链接`）
- 输入收集：用 `AskUserQuestion` 询问"全量检索/选择性检索" + 关键词 + 补充信息

### 原子模式
- 触发：用户提示词包含"在特定网站搜索特定内容"语义
- URL 来源：用户直接提供
- 输入收集：提示用户输入 URL、关键词、可选补充信息

## 输入参数

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

## 执行流程

### Step 1：构建 URL 列表
- **工作流**：读取 JSON 文件，用 `jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过对应行
- **原子**：用户提供的 URL 列表即 `URL_LIST`

### Step 2：逐站点处理（3a–3g）

| 子步骤 | 动作 | 说明 |
|--------|------|------|
| 3a | 打开页面 | `new_tab(url)` |
| 3b | 等待加载 | 文本长度 < 200 → 可能加载失败 |
| 3c | 处理招聘项目复选框 | MODE=3 跳过；先检查 URL 是否已暗示类型，否则用 JS 查找点击 |
| 3d | ⭐ 搜索（强制） | 定位搜索框 → 填入关键词 → 点击搜索/回车。找不到搜索框则跳过 |
| 3e | 等待搜索完成 | `wait_for_load()` + 3s 延时 |
| 3f | 提取职位链接 | 只取第一页，不滚动不分页。用通用 JS 选择器提取 |
| 3g | 筛选并记录 | 标题含 KEYWORD（连续子串）→ 记录岗位链接；不含 → 记录原始 URL |

### Step 3：关闭浏览器

```bash
browser-use --reload
pkill -9 -f "Google Chrome" 2>/dev/null
```

## 输出报告

生成 Markdown 报告，保存到 `output/{KEYWORD}岗位检索报告.md`，包含 3 段：

| 段落 | 内容 |
|------|------|
| 1. 任务参数 | 触发模式、勾选模式、搜索词、URL 来源、站点数 |
| 2. 匹配结果 | 网站 + 岗位详情页链接（标题含 KEYWORD 的岗位） |
| 3. 不匹配结果 | 网站 + 检索状态 + 说明 + 网站原始链接 |

**检索状态枚举**：`搜索成功`(无匹配) / `搜索失败` / `搜索框未找到` / `页面加载失败` / `跳过`

**链接规则**：匹配 → 岗位详情页 URL；不匹配/失败/跳过 → 网站原始 URL

## 关键设计决策

- **自包含单文件**：全部核心逻辑内联在 SKILL.md 中，无 references 依赖
- **browser-use v3.0 Python pipe**：统一用 `browser-use <<'PY' ... PY` 语法，核心 API 包括 `new_tab`、`page_info`、`js`、`fill_input`、`wait_for_load`
- **强制搜索步骤**：搜索不可跳过，即使默认列表已显示关键词 — SPA 站点（如拼多多）默认列表是精选子集
- **只取第一页**：不滚动、不分页
- **空结果直接跳过**：不尝试兜底策略（URL 参数、分页、滚动加载）
- **通用 JS 选择器**：通过 `a[href*="position/job/detail/recruit"]` 和 `[class*=JobTitle/job-title/position/job-item]` 通用匹配，无需站点专用适配表

## 前提条件

```bash
# 一次性安装
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # 验证
```

## License

MIT
