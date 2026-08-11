# targeted-url-search-pro

> WorkBuddy Skill: 招聘网站自动化岗位搜索。基于 browser-use v3.0，双模式触发 + 输入校验 + 自动执行。**v2.0 分层架构**：经验外置、按需加载，支持 100+/500+ 站点教训持续沉淀而不膨胀。

## 功能概述

给定 JSON 文件（工作流模式）或直接 URL（原子模式）、搜索关键词、可选招聘项目模式，自动完成：

1. **识别触发模式**（工作流 vs 原子）
2. **收集与校验**必填输入（URL + 关键词）— 缺失时询问用户
3. **模式识别**：查 `references/patterns.md` 索引 → 命中模式按模式应对；未命中走通用流程并事后沉淀
4. 通过 browser-use v3.0 Python pipe 语法**复用同一标签页**逐站点打开招聘网站
5. 导航对应招聘类型 Tab（hover 下拉 / antd 真实鼠标 / 降级链）
6. 勾选招聘项目复选框（Tab 导航成功时跳过）
7. 强制搜索关键词（iframe 兜底、提取默认列表兜底）
8. 第一页三层提取岗位链接（兼容非 `<a>` 岗位；无匹配取前 3 兜底；登录墙标注）
9. 输出 3 段式精炼报告（含降级/兜底/登录墙原因标注）

## 架构（v2.0 分层）

```
targeted-url-search-pro/
├── SKILL.md                    # 精简骨架：触发/参数/流程概述/模式路由/报告模板/经验沉淀SOP
├── references/
│   ├── patterns.md             # ⭐ 模式库（唯一模式增长点）：索引表 + 每类站点一个模式
│   ├── workflow.md             # 3a–3g 详细步骤与代码模板（通用逻辑）
│   └── site-notes.md           # 站点笔记（单站点经验，每站 ≤10 行）
└── assets/scripts/             # 可复用脚本（参数化）
    ├── antd_hover.py           # antd 菜单：CDP 真实鼠标展开 + data-menu-id 提取 URL + 真实点击
    ├── fill_search.py          # 搜索框填入 + 触发 + 生效验证
    └── extract_jobs.py         # 岗位三层提取 + 点击容器取 SPA URL + 统计读取
```

**设计原则**：
- **模式抽象优先于站点枚举**：500 个网站教训归纳为 ~10 类模式（antd 菜单/zhiye 系/hover 下拉/登录墙/反爬/hotjob/飞书/自研/非a标签）。SKILL.md 只装"如何识别模式"，不装"如何处理每个站点"。
- **按需加载**：每次执行只加载 SKILL.md（~150 行）+ 命中的 1 个模式文件（几十行）→ 上下文 O(1)，不随站点数增长。
- **经验沉淀闭环**：跑完复盘 → 单站点经验进 site-notes.md；同坑 ≥2 次归纳为新模式进 patterns.md；SKILL.md 永不因此变大。
- **代码与文档分离**：可复用脚本进 assets/scripts，workflow.md 只引用文件名。

## 双模式触发

| 模式 | 触发条件 | URL 来源 |
|------|---------|---------|
| 工作流 | 提示词含 `targeted-url-search` | 上一节点 JSON 文件 |
| 原子 | 提示词含"在…网站/链接…搜索/检索…岗位/关键词"语义 | 用户直接输入 |

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| URL_LIST | 是 | 工作流：从 JSON `records[].投递链接` 提取；原子：用户输入 |
| COMPANY_LIST | 否 | 工作流：从 JSON `records[].招聘企业` 提取；原子：从域名推断 |
| KEYWORD | 是 | 搜索关键词，如"前端"、"算法" |
| MODE | 否 | 1=校招/全职, 2=实习, 3=校招+实习(默认) |
| EXCLUDE_INDICES | 否 | 工作流模式：用户指定跳过的站点序号 |

## 执行流程

### Step 0：环境检查 + 模式识别
```bash
pkill -9 -f "remote-debugging-port=9222"; sleep 1
open -a "Google Chrome" --args --remote-debugging-port=9222
export PATH="$HOME/.local/bin:$PATH"; browser-use doctor
```
读取 `references/patterns.md` 索引 → 按域名/URL/特征匹配模式；未命中走通用流程（workflow.md）并事后沉淀。

### Step 1：构建 URL 列表
- **工作流**：`jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过
- **原子**：用户提供的 URL 列表即 `URL_LIST`

### Step 2：逐站点处理（3a–3g）

| 子步骤 | 动作 | 要点 |
|--------|------|------|
| 3a | 打开页面 | `goto_url` 复用当前标签页（勿用 new_tab） |
| 3b | 等待加载 | URL 校验（about:blank=反爬→重试1次）+ 文本长度；失败→"页面加载失败(疑似反爬拦截)" |
| 3c_1 | 导航招聘类型 Tab | 四类语义 Tab + 降级链；hover 下拉（普通 CSS 用 JS 事件，**antd 用 CDP 真实鼠标**）；导航后验证；自研站点 3 个自主动作 |
| 3c_2 | 处理复选框 | Tab 导航成功则跳过；MODE=3 两轮勾选 |
| 3d | ⭐ 搜索（强制） | 定位（iframe 兜底）→ native setter 填入 → 触发 → **验证生效**；失败→自主 5 个动作→提取默认列表并标注，**不跳过站点** |
| 3e | 等待结果 | 轮询岗位容器出现（最多 ~10s） |
| 3f | 提取岗位 | 三层提取（`<a>`→容器→点击容器取 SPA URL）；React 卡片 CDP 真实点击；登录墙→标注"详情需登录"；只取第一页 |
| 3g | 筛选记录 | 标题含 KEYWORD→岗位链接；非空无匹配→**取前3兜底**；空→"无匹配岗位" |

### Step 3：关闭浏览器
```bash
browser-use --reload
pkill -9 -f "remote-debugging-port=9222" 2>/dev/null
```

## 输出报告

生成 Markdown 报告，保存到 `output/{KEYWORD}岗位检索报告.md`，包含 3 段（任务参数 / 匹配结果 / 不匹配结果）。

**检索状态枚举**：`匹配成功` / `无精确匹配(取前N岗位)` / `无匹配岗位` / `搜索失败` / `搜索框未找到` / `页面加载失败` / `详情需登录` / `跳过`

## 经验沉淀 SOP（增长机制）

| 情况 | 动作 |
|------|------|
| 命中模式但应对不够 | 改进 patterns.md 对应模式小节 |
| 新站点、新坑 | 补一行到 site-notes.md（≤10 行） |
| 同坑 ≥2 次 | 归纳为新模式进 patterns.md（10–30 行 + 索引行） |
| 模式 ≥5 个互相独立 | patterns.md 可拆分为 patterns/ 子目录，索引表保持单一增长点 |
| 新增可复用脚本 | 放 assets/scripts/，参数化，workflow.md 引用 |

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
