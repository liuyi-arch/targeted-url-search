---
name: targeted-url-search
description: "Automated job search on recruitment websites with dual-mode trigger. Workflow mode reads URLs from an upstream JSON result; atomic mode reads URLs from the user's prompt. Uses browser-use v3 and site adapters to search the first result page and output a normalized report."
version: 5.0.0
allowed-tools: Bash(browser-use:*), Read, Write, Glob, Grep, AskUserQuestion
visibility: "public"
agent_created: true
---
# 招聘网站自动化岗位搜索

本技能用于在招聘网站上自动检索指定关键词，并输出统一格式的岗位筛选报告。

改造后的目标：

- `SKILL.md` 只保留编排入口和状态机
- 变化频繁的规则拆分到独立规范文件
- 所有浏览器操作统一采用 `browser-use v3.0+` Python pipe 语法
- 站点差异通过注册表维护，不再散落在主流程中

---

## 一、单一规范源

执行时按以下文件分工读取，不要在多个文件中重复定义同一条规则：

| 文件 | 作用 |
|------|------|
| `references/trigger-spec.md` | 触发模式判定、关键词提取、补问策略 |
| `references/input-contract.md` | 输入字段、默认值、JSON 字段映射、企业名推断 |
| `references/execution-policy.md` | 全局执行规则、失败处理、fallback 策略 |
| `references/site-registry.md` | 站点注册表、选择器、站点覆盖策略 |
| `references/report-schema.md` | 输出结构、状态枚举、链接规则 |
| `docs/add-site-checklist.md` | 新增站点时的维护清单 |

规则冲突时，按以下优先级处理：

1. `references/execution-policy.md`
2. `references/site-registry.md`
3. `references/report-schema.md`
4. `README.md`

---

## 二、前提条件

### 一次性安装

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor
```

### 每次运行前

```bash
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor
browser-use doctor 2>&1 | grep version
```

---

## 三、执行状态机

### State 1: 检测触发模式

按 `references/trigger-spec.md` 判定：

- `workflow`：用户明确提及 `targeted-url-search`
- `atomic`：用户表达“在某个网站检索某个关键词”的明确语义

若两者同时命中，`workflow` 优先。

### State 2: 收集并校验输入

按 `references/input-contract.md` 收集：

- `URL_LIST`
- `COMPANY_LIST`
- `KEYWORD`
- `PROJECT_MODE`
- `SUPPLEMENTARY`
- `TRIGGER_MODE`

若缺少必填字段，按 `references/trigger-spec.md` 的补问策略继续提问，直到：

- 校验通过，或
- 用户明确取消任务

### State 3: 构建待检索站点列表

- `workflow`：从上游 JSON 中读取 URL 和企业名
- `atomic`：从用户输入 URL 推断企业名
- 若用户给出排除序号，先过滤再执行

字段映射和兜底提取顺序以 `references/input-contract.md` 为准。

### State 4: 环境检查

```bash
export PATH="$HOME/.local/bin:$PATH"
browser-use doctor
```

若环境不可用，直接终止，并按 `report-schema` 记录失败原因。

### State 5: 逐站点执行

对 `URL_LIST` 中每个站点依次执行，所有行为受 `references/execution-policy.md` 约束。

#### 5.1 选择站点适配器

先读取 `references/site-registry.md`：

- 命中站点规则：使用站点覆盖配置
- 未命中：使用 `generic` 适配器

#### 5.2 打开页面并等待加载

```bash
browser-use <<'PY'
new_tab("$URL")
wait_for_load()
info = page_info()
print(info.get("url", ""))
print(info.get("title", ""))
PY
```

若页面文本过短、重定向异常或页面不可访问，按 `页面加载失败` 记录。

#### 5.3 处理招聘项目筛选

按 `PROJECT_MODE` 和站点适配器处理：

- `none`：跳过
- `campus` / `intern` / `social`：先检查 URL 是否已经满足，再决定是否点击页面控件

站点特有控件、选择器和跳过条件都从 `site-registry` 读取，不在主流程内写死。

#### 5.4 强制执行搜索

无论页面默认是否展示目标岗位，都必须执行一次真实搜索。

执行顺序：

1. 按站点适配器提供的搜索框定位方式尝试
2. 未命中时走通用输入框策略
3. 触发搜索时优先使用站点适配器指定的按钮或事件
4. 若全局策略允许，再按站点 `fallback_policy` 执行兜底

#### 5.5 等待结果并提取第一页链接

- 只读取第一页结果
- 不滚动、不翻页
- 尽量用单次 `js()` 返回标题和链接列表
- 若通用提取失败，再执行站点覆盖提取规则

#### 5.6 过滤与记录

按连续子串规则判断职位标题是否包含 `KEYWORD`：

- 匹配：记录企业名和岗位详情页链接
- 不匹配：记录企业名、状态、说明、网站原始链接
- 空结果：按执行策略记录为 `搜索成功` 或对应异常状态

### State 6: 清理会话

```bash
browser-use --reload
pkill -9 -f "Google Chrome" 2>/dev/null
```

### State 7: 输出报告

严格按 `references/report-schema.md` 生成，不要在 `SKILL.md` 中重新定义模板。

---

## 四、全局硬约束

- 只允许使用 `browser-use v3.0+` Python pipe 语法，禁止旧式 `open/state/click/input` 子命令
- 搜索步骤必须执行，不允许因为默认列表已有结果而跳过
- 结果只检查第一页
- 输出状态和值域必须来自 `report-schema`
- 站点特例只能写入 `site-registry`，不要回写到主流程

---

## 五、维护约束

- 要改触发规则：改 `references/trigger-spec.md`
- 要改输入结构：改 `references/input-contract.md`
- 要改全局执行策略：改 `references/execution-policy.md`
- 要改某站点选择器：改 `references/site-registry.md`
- 要改报告格式：改 `references/report-schema.md`
- 要新增站点：先看 `docs/add-site-checklist.md`

---

## 六、维护目标

本技能的维护目标不是让 `SKILL.md` 越写越长，而是让主流程保持稳定，把变化点收敛到：

- 输入契约
- 执行策略
- 站点注册表
- 报告协议

只要遵守这四类边界，新增站点、调整策略、修改输出格式都不需要重写主流程。
