---
name: targeted-url-search-pro
description: "招聘网站自动化岗位搜索。工作流模式：由'targeted-url-search'触发，从上一节点JSON批量检索；原子模式：由'在特定网站搜索特定内容'语义触发。分层架构：SKILL.md只装通用流程与模式匹配，站点经验全部外置于 references/（模式库/流程模板/站点笔记），支持 100+ 站点经验持续沉淀而不膨胀。"
version: 2.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
agent_created: true
---

# 招聘网站自动化岗位搜索（分层架构 v2.0）

> **设计原则**：本文件只包含"不变的通用逻辑 + 如何匹配站点模式"。所有站点经验（antd 菜单、zhiye 系、hover 下拉、登录墙、反爬拦截等）一律**外置**到 `references/`，按需加载：
>
> - `references/patterns.md` — **模式库**：每类站点一个模式（识别信号 + 应对 + 代表站点），含索引表。新增网站教训 → 归纳为新模式或并入已有模式，**不改本文件**。
> - `references/workflow.md` — **3a–3g 详细步骤与代码模板**（通用逻辑的完整实现）。
> - `references/site-notes.md` — **站点级笔记**：踩坑站点的一行式要点（URL 入口、坑点、URL 模板）。
> - `assets/scripts/` — **可复用脚本**：fill_search / extract_jobs / antd_hover，参数化调用。

---

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

### Step 0：环境检查 + 模式识别（每次执行前必做）

```bash
pkill -9 -f "remote-debugging-port=9222" # 只清理调试实例，避免误杀用户日常 Chrome
sleep 1
open -a "Google Chrome" --args --remote-debugging-port=9222
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor
```

**模式识别（核心路由逻辑，替代"现象堆砌"）**：

1. 读取 `references/patterns.md` 的**模式索引表**（按域名/URL/页面特征匹配）。
2. **命中模式** → 按该模式的"应对"执行；模式详情在 patterns.md 对应小节，必要时读 `site-notes.md` 对应站点笔记。
3. **未命中** → 走 `references/workflow.md` 的**通用流程**（LLM 自主 + 兜底原则），跑完后按"五、经验沉淀"决定是否新增模式。

> 目标：每处理 1 个站点，只加载 1 个模式文件（几十行），上下文开销恒定，不随站点总数增长。

### Step 1：构建 URL 列表

- **工作流**：`jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过。
- **原子**：用户提供的 URL 列表即 `URL_LIST`。

### Step 2：逐站点处理（3a–3g，详细代码见 references/workflow.md）

| 子步骤 | 动作（简述） | 要点 |
|--------|-------------|------|
| 3a | 打开页面 | `goto_url` 复用当前标签页，禁止 `new_tab` 批量开页 |
| 3b | 等待加载 | **先看 URL**（about:blank=反爬拦截→重试1次）；文本<200 再等 5s；仍失败→"页面加载失败(疑似反爬拦截)" |
| 3c_1 | 导航招聘类型 Tab | 四类语义 Tab + **降级链**（见下）；**hover 下拉展开**（普通 CSS 用 JS 事件；**antd 系用 CDP 真实鼠标**，脚本见 assets/scripts/antd_hover.py）；导航后**验证**（出现搜索框/职位列表），失败回退降级链下一级 |
| 3c_2 | 处理复选框 | Tab 导航成功则跳过；MODE=3 两轮勾选（校招→实习） |
| 3d | ⭐ 搜索（强制） | 定位搜索框（主文档→iframe 兜底）→ native setter 填入 → 触发（回车/按钮）→ **验证生效**（URL 带 q/统计变化）；找不到搜索框→自主动作 5 个→仍失败**不跳过**，提取默认列表并标注"未搜索" |
| 3e | 等待结果 | 轮询岗位容器出现（最多 ~10s），非固定延时 |
| 3f | 提取岗位 | **三层提取**：`<a>` 链接 → 标题容器 → 点击容器取 SPA 详情 URL；React 卡片需 CDP 真实点击，弹登录→标注"详情需登录"；只取第一页 |
| 3g | 筛选记录 | 标题含 KEYWORD（连续子串）→岗位链接；**非空无匹配→取前3兜底**；空→"无匹配岗位"；返回岗位链接而非官网链接 |

**Tab 降级链**（每级失败进入下一级，报告标注原因）：

| MODE | 降级链 |
|------|--------|
| 1 | 类别一(校招) → 类别三(职位/岗位) → 找搜索框 → 仍无 → 抛错"没有找到校招正式批信息，且网站找不到搜索框" |
| 2 | 类别二(实习) → 类别一 → 类别三 → 找搜索框 → 仍无 → 抛错"没有找到实习批次信息，且网站找不到搜索框" |
| 3 | 先按 MODE=1 走完 3c_2~3g → 再按 MODE=2 走完 3c_2~3g |

> Tab 语义分类：类别一=校园招聘/校招/应届招聘/校招职位/校招岗位/应届；类别二=实习招聘/实习生/实习；类别三=职位/招聘职位/职位列表/岗位/岗位投递/Jobs/Positions；类别四=社招/社会招聘。

---

## 四、输出报告

生成 Markdown 报告，保存到 `output/{KEYWORD}岗位检索报告.md`，包含 3 段：

**1. 任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数

**2. 匹配结果**（标题含 KEYWORD 的岗位 / 无精确匹配时前 3 兜底岗位）：

| # | 网站 | 岗位链接 |
|---|------|---------|
| 1 | {企业名} | {岗位详情页 URL} |

**3. 不匹配结果**：

| # | 网站 | 检索状态 | 说明 | 网站链接 |
|---|------|---------|------|---------|
| 1 | {企业名} | {状态} | {降级/兜底/失败原因} | {原始 URL} |

> 检索状态枚举：`匹配成功` / `无精确匹配(取前N岗位)` / `无匹配岗位` / `搜索失败` / `搜索框未找到` / `页面加载失败` / `详情需登录` / `跳过`。
> 任何降级都必须在"说明"列写明原因（含降级文案："没有找到网站校招正式批信息，可能包含实习生职位或社招职位"等），方便人工复核。

---

## 五、经验沉淀流程（增长机制，500 个网站也不膨胀）

每次执行结束后复盘，按以下规则更新知识库（**SKILL.md 永不因此变大**）：

1. **命中已有模式但应对不够** → 改进 `references/patterns.md` 对应模式小节（合并同类项）。
2. **新站点、新坑** → 先补一行到 `references/site-notes.md`（URL 入口 + 坑点 + URL 模板，10 行内）。
3. **同坑出现 ≥2 次** → 归纳为**新模式**：在 `references/patterns.md` 索引表加一行 + 新增模式小节（10–30 行），含"识别信号 / 应对 / 代表站点 / 代码引用"。
4. **模式 ≥5 个且互相独立** → 允许将 patterns.md 拆分为 `patterns/` 子目录按域名分组（zhiye系/自研/antd 等），索引表保持单一增长点。
5. **新增脚本** → 放入 `assets/scripts/`，参数化，workflow.md 引用文件名即可。

---

## 六、前提条件

```bash
# 一次性安装
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # 验证
```

> **browser-use v3.0 语法**：统一用 `browser-use <<'PY' ... PY` Python pipe 模式。核心 API：`goto_url`（复用标签页）、`page_info()`、`js(code)`、`fill_input(selector, text)`、`wait_for_load()`、`capture_screenshot(path)`。
> **高级 API（antd/React 站点必用）**：`cdp("Input.dispatchMouseEvent", type="mouseMoved"|"mousePressed"|"mouseReleased", x=.., y=.., button="left", clickCount=1)`（真实鼠标）；`cdp("Emulation.setDeviceMetricsOverride", width=1920, height=1000, deviceScaleFactor=1, mobile=False)`（防 antd 菜单折叠）。注意 cdp 签名 `cdp(method, session_id=None, **params)`。
