---
name: targeted-url-search
description: "Automated job search on recruitment websites with dual-mode trigger. Workflow mode: triggered by 'targeted-url-search', batch-searches URLs from previous node. Atomic mode: triggered by 'search specific content on specific website' semantics. Validates required inputs (URL+keyword) before execution."
version: 5.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
visibility: "public"
agent_created: true
---
# 招聘网站自动化岗位搜索

两种触发模式 + 必填参数校验 + 自动执行：打开网站 → 勾选招聘项目复选框 → 搜索关键词 → 从第一页结果中筛选标题含搜索词的岗位链接 → 输出精炼报告。

> **设计原则**：本文件仅包含核心编排逻辑（做什么）。详细实现（怎么做）见 `references/` 目录下各专题文件。

---

## 一、触发模式

| 模式 | 触发条件 | URL 来源 |
|------|---------|---------|
| 工作流 | 用户提及 "targeted-url-search" | 上一节点 JSON 文件 |
| 原子 | 用户提示词含"在特定网站检索特定内容"语义 | 用户直接输入 |

> 两种模式同时匹配时，工作流优先。详细触发词与提取规则见 `references/mode-detection.md`。

---

## 二、输入参数

| 参数 | 变量名 | 必填 | 说明 |
|------|--------|------|------|
| URL 列表 | `URL_LIST` | 是 | 工作流：JSON 提取；原子：用户输入 |
| 企业名列表 | `COMPANY_LIST` | 否 | 工作流：JSON 提取；原子：从域名推断 |
| 搜索关键词 | `KEYWORD` | 是 | 如"前端"、"算法" |
| 招聘项目模式 | `MODE` | 否 | 1=校招/全职, 2=实习, 3=不勾选(默认) |
| 触发模式 | `TRIGGER_MODE` | — | "workflow" 或 "atomic" |

> 必填字段缺失时按模式重新询问，直到校验通过或用户取消。详见 `references/execution-flow.md` Step 0。

---

## 三、核心规则

1. **browser-use v3.0 语法**：统一用 `browser-use <<'PY' ... PY'` Python pipe 模式。禁止 `browser-use open/state/click/input/close` 等废弃子命令。
2. **核心 API**：`new_tab(url)`、`page_info()`、`js(code)`、`fill_input(selector, text)`、`capture_screenshot(path)`、`wait_for_load()`。
3. **搜索强制执行**：每个站点必须完整走 3a→3b→3c(MODE)→**3d(搜索)**→3e→3f→3g，不可跳过 3d。
4. **只取第一页**：搜索后不滚动、不分页。
5. **空结果直接跳过**：搜索后 0 条匹配 → 记录状态并进入下一站点，不尝试兜底策略。
6. **合并 JS 查询**：用单次 `js()` 提取所有数据，减少交互轮次。
7. **会话清理**：全部站点处理完毕后执行 `browser-use --reload` + `pkill Chrome`。

---

## 四、执行流程概览

| Step | 动作 | 详情参考 |
|------|------|---------|
| 0 | 输入收集与校验 | `references/execution-flow.md` § Step 0 |
| 1 | 构建 URL 列表 | `references/execution-flow.md` § Step 1 |
| 2 | 环境检查 | `references/execution-flow.md` § Step 2 |
| 3 | 逐站点处理 (3a-3g) | `references/execution-flow.md` § Step 3 |
| 4 | 关闭浏览器 | `references/execution-flow.md` § Step 4 |
| 5 | 生成报告 | `references/report-template.md` |

**Step 3 子步骤摘要**：

| 子步骤 | 动作 |
|--------|------|
| 3a | 打开页面 (`new_tab`) |
| 3b | 等待加载，获取页面结构 |
| 3c | 处理招聘项目复选框 (MODE=3 时跳过) |
| 3d | ⭐ 搜索（强制执行，不可跳过） |
| 3e | 等待搜索完成 |
| 3f | 提取职位链接 |
| 3g | 按标题子串筛选并记录结果 |

> 站点专用选择器见 `references/site-patterns.md`。错误排查见 `references/error-handling.md`。

---

## 五、输出

按 `references/report-template.md` 生成 3 段式报告：

1. **任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数
2. **匹配结果**：网站名称 + 岗位详情页链接
3. **不匹配结果**：网站名称 + 检索状态 + 说明 + 网站原始链接

**链接规则**：匹配 → 岗位详情页 URL；不匹配/失败/跳过 → 网站原始 URL。

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

每次运行前执行 `browser-use doctor` 快速检查。

---

## 文件结构

```
targeted-url-search/
├── SKILL.md                        # 本文件 — 核心编排（~150行）
├── references/
│   ├── mode-detection.md           # 触发词模式 + 输入提取规则
│   ├── execution-flow.md           # 详细执行流程（Step 0-5 含代码）
│   ├── site-patterns.md            # 站点适配表（飞书/INTSIG/拼多多/通用）
│   ├── report-template.md          # 报告模板 + 字段说明 + 示例
│   ├── error-handling.md           # 错误处理与故障排查
│   └── changelog.md                # 版本变更记录
```
