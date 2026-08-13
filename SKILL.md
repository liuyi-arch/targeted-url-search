# 招聘网站自动化岗位搜索（分层架构 v3.0）

> **设计原则**：
>
> - **本文件 = 编排 + 核心 workflow**：3a–3e 完整流程、判定标准、兜底逻辑内置本文件，执行时无需跳转。
> - **经验/脚本外置**：站点经验在 `references/`（patterns 模式库 + site-notes 站点笔记），脚本在 `scripts/`（一个动作一个文件，文件内多函数=不同实现方法）；本文件不出现任何脚本代码，只引用文件名。脚本速查见文末"七、附录"。

---

## 一、触发模式

| 模式  | 触发条件                         | URL 来源       |
| --- | ---------------------------- | ------------ |
| 工作流 | 提示词含 `targeted-url-search`   | 上一节点 JSON 文件 |
| 原子  | 提示词含"在…网站/链接…搜索/检索…岗位/关键词"语义 | 用户直接输入       |

> 两种同时匹配时，工作流优先。

---

## 二、输入参数

| 参数              | 必填 | 说明                                      |
| --------------- | -- | --------------------------------------- |
| URL_LIST        | 是  | 工作流：从 JSON `records[].投递链接` 提取；原子：用户输入  |
| COMPANY_LIST    | 否  | 工作流：从 JSON `records[].招聘企业` 提取；原子：从域名推断 |
| KEYWORD         | 是  | 搜索关键词，如"前端"、"算法"                        |
| MODE            | 否  | 1=校招/全职, 2=实习, 3=校招+实习(默认)              |
| EXCLUDE_INDICES | 否  | 工作流模式：用户指定跳过的站点序号                       |

### MODE 判定

| 信息关键词                | MODE |
| -------------------- | ---- |
| 校招、全职、正式、秋招、春招、社招、应届 | 1    |
| 实习、日常、暑假、暑期          | 2    |
| 未提及                  | 3    |

### 输入校验

必填字段缺失时：工作流模式用 `AskUserQuestion` 询问"全量检索/选择性检索"后补全；原子模式直接提示用户输入 URL + KEYWORD。循环直到校验通过或用户取消。

---

## 三、执行流程（编排 + 核心 workflow）

### Step 0 · 环境检查

> **意图**：Chrome 调试实例在 9222 监听、可被 browser-use 连接，不阻塞 3a–3e。
> **成功判定**：`env_check.sh` 退出码 0 且输出 `[ok] Chrome 调试端口 9222 已监听`（curl `/json/version` 含 `"Browser"`）。
> **失败归因**：端口有响应但验证未命中（如 IPv6 监听而 curl 用 127.0.0.1、轮询不足）→ **M 类**（加方法）；其余（无监听、启动失败、残留占端口）→ **S 类**（进特例层）。

**执行链路**：`bash scripts/env_check.sh`：lsof 清 9222 → 二进制启动 Chrome(IPv4, --no-sandbox) → 轮询验证（最多 15s，失败 tail 日志并 exit 1），通过 → 进入 3a。

### Step 1 执行策略

1. **一律先走常规工作流 3a–3e**——特例不是查表查出来的，是执行中走不通才触发的。
2. 执行中**每个动作失败时记录失败信号**（不中断，动作有兜底），流程结束后汇总判定：
   - **方法性失败（M 类）**＝目标元素**存在**但当前方法未命中（如页面有下拉菜单但 hover 方法都不触发、有岗位但提取方法拿不到）→ 判定"工作流可行，仅方法不足" → 动作文件加方法（见"五、经验沉淀"）。
   - **结构性失败（S 类）**＝目标元素**不存在**（如 3b 导航区无任何招聘入口、3d 页面无任何岗位元素、3a 页面打不开）→ 判定"该站点常规工作流走不通" → 进入特例流程（见"五、经验沉淀"）。
3. 已知特例站点（patterns.md 命中）→ 直接按该模式应对执行，跳过重复走流程。

### Step 2：构建 URL 列表

- **工作流**：读取 JSON 文件，用 `jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过对应行。
- **原子**：用户提供的 URL 列表即 `URL_LIST`。

### Step 3：逐站点处理（核心 workflow，3a–3e）

对每个 URL 执行以下子步骤，全部通过 `browser-use <<'PY' ... PY` Python pipe 模式调用。

> **多方法尝试约定**：当某动作文件含多个方法（如 hover 的 方法1/方法2）时，**按文件内顺序依次尝试；任一方法成功 → 立即停止尝试该文件内其余方法，进入该步骤的下一步**（方法间是"或"关系，不是"且"关系，不会成功后再执行后续方法）。全部方法失败 → 执行该步骤的兜底逻辑。

---

#### 3a · 打开页面并确认可用

> **意图**：页面可进入后续流程（非白屏/空壳 DOM/错误页）。
> **成功判定**（意图的充分条件）：正文 ≥ 40 且标题无错误特征 → 进入 3b。
> **失败归因**：DOM 有内容但方法未命中（如等待/取标题时机不对）→ **M 类**（加方法）；无 DOM/空壳/错误页 → **S 类**（进特例层）。

**执行链路**：导航打开（轮询就绪）→ 慢加载兜底（仅轮询超时后），成功判定通过 → 进入 3b：

- **导航打开**：`open_page(goto_url, js, url)`（`scripts/open_page.py`）：goto_url 导航（不 new_tab）→ 轮询正文 ≥ 40（每 1s，最多 15s）→ 返回 (title, body_len)。

- **慢加载兜底**（仅轮询超时正文仍 < 40 时）：`open_page_wait(js, wait_for_load)`（`scripts/open_page_wait.py`）：wait_for_load → 再等 5s 复查 → 返回 bool 是否达标。


#### 3b · 导航至目标招聘类型 Tab（含 hover 下拉展开）

> **意图**：切换到**目标招聘类型（MODE）职位视图**，为 3c 搜索准备上下文（非介绍/落地页）。
> **成功判定**（意图的充分条件）：`nav_verified(js, before_url)` 通过 = **URL 变化 且（搜索框 或 职位列表出现）**，**或 初始即目标态**（URL 未变但页面打开已含职位列表+搜索框）。
> **失败归因**：视图存在但方法未命中（含类型关键词 / 探测为下拉但 hover/提取 URL 失败 / 有列表或搜索框但切换未命中）→ **M 类**（加方法）；降级链走完仍无 Tab 且无类型切换机制 → **S 类**（进特例层）。

**目标 Tab 分类**（按语义，不分先后）：

| 类别         | 语义关键词                                              |
| ------------ | ------------------------------------------------------- |
| 类别一(校招) | 校园招聘 / 校招 / 应届招聘 / 校招职位 / 校招岗位 / 应届 |
| 类别二(实习) | 实习招聘 / 实习生 / 实习                                |
| 类别三(通用) | 职位 / 招聘职位 / 职位列表 / 岗位 / 岗位投递            |
| 类别四(社招) | 社招 / 社会招聘                                         |

**降级链**（严格按此顺序，每级失败即进入下一级，成功不进行后续链路，报告标注原因）：

| MODE | 降级链                                                       |
| ---- | ------------------------------------------------------------ |
| 1    | 类别一 → 类别三（结果说明"可能包含社招/实习岗位"） → 仍无 → 直接进入 3c 搜索，结果说明"不确定是否是校招正式批次岗位" |
| 2    | 类别二 → 类别一（结果说明"可能包含校招正式批次岗位"） → 类别三（结果说明"可能包含校招正式批次/社招批次岗位"） → 仍无 → 直接进入 3c 搜索，结果说明"不确定是否是实习批次岗位" |
| 3    | 先按 MODE=1 走完 3b–3e，再按 MODE=2 走完 3b–3e         |

**每级执行链**（找 tab → 探测有无下拉 → 按结果交互 → 验证；失败进入降级链下一级，不执行该级后续操作；成功进入执行链下一级）：

1. **找 tab**：`scripts/find_tab.py` 的 `find_tab(js, mode)` 按 MODE 语义关键词找直接可见 Tab（返回 {found, text}）。
2. **探测有无下拉**：`scripts/tab_has_dropdown.py` 的 `tab_has_dropdown(js, text)` 返回 `{has_dropdown, menu_id}`：
   - `has_dropdown=true` → 依次执行 `scripts/hover_expand.py`（多方法按序，任一成功 → 进入第 3 步验证）：
     - **方法1** `hover_expand_css(js)`：普通 CSS/JS 下拉 → 1s 后 `click_dropdown_item(js)` 点"职位/岗位"项；
     - **方法2** `hover_expand_antd(cdp, js, menu_id, goto_url)`：antd 系菜单（用第 2 步返回的 menu_id，JS dispatchEvent 无效，须 CDP 真实鼠标）；
   - `has_dropdown=false` → `scripts/click_tab.py` 的 `click_tab(js, text)` 直接点击。
3. **验证**：`scripts/nav_verified.py` 的 `nav_verified(js, before_url)`成功 → 进入 3c；失败 → 进入降级链下一级。
4. **仍失败 → 进入降级链下一级**

---

#### 3c · 搜索

> **意图**：让目标类型职位视图的职位集合**切换为按 KEYWORD 过滤后的结果**（搜索生效），为 3d 取搜索结果标题。
> **成功判定**（意图的充分条件）：`search_verified(js)` 通过 = URL 含 KEYWORD 查询参数**或** 职位统计/列表切换为过滤后结果 → 已按 KEYWORD 过滤。
> **失败归因**：搜索机制存在但方法未命中（页面有搜索入口但 定位/填入/触发/验证 任一失败）→ **M 类**（加方法）；搜索机制不存在（无搜索框/按钮/表单）→ **S 类**（进特例层）。

**执行链路**：定位 → 填入 → 触发 → 验证生效（四个动作各自独立成文件，多方法按序，任一成功 → 下一步）：

- **定位搜索框**：`scripts/has_search_input.py`（多方法按命中率排序）。
  - 方法1 `find_visible_search_input(js)`（最稳）：只返回**可见**搜索框（过滤 `offsetParent!==null && rect.width>0`）——适配 italent/zhiye 系与美团"两个同名输入框、第一个隐藏 rect 0,0"坑；
  - 方法2 `find_search_input(js)` 主文档定位（placeholder 含 搜索/职位/岗位，不保证可见）；
  - 方法3 `find_in_iframe(js)` iframe 兜底（跨源跳过）；
  - 均找不到 → 终止当前站点，标注"搜索框未找到"。

- **填入**：`scripts/fill_keyword.py` 。
  - 方法1`fill_keyword(js, keyword)` ， native setter + InputEvent（`fill_input` 对受控组件无效，禁用），填入后主动 `focus()` 保持焦点；
  - 失败 → 结束该站点，标注"填入关键词失败"。

- **触发**：`scripts/trigger_search.py` 。
  - 方法1 `trigger_enter(js)` 派发回车（React onSubmit）；
  - 方法2 `click_search_btn(js)` 点搜索按钮（onClick 不触发 onSubmit，按钮兜底）；
  - 方法3 `click_btn_by_selector(js, selector)` 按 CSS 选择器 JS click 指定按钮；
  - 均失败 → 结束该站点，标注"搜索未触发"。

- **验证生效**：`scripts/search_verified.py` 。
  - 方法1 `url_has_query(js)`；
  - 方法2 `stats_changed(js)`；
  - 均未命中 → 结束该站点，标注"搜索未生效"。


---

#### 3d · 等待并取搜索结果（最多 5 个职位标题）

> **意图**：等待搜索结果就绪；非空则取**最多 5 个职位的标题**，供 3e 判定 KEYWORD 是否命中。
> **成功判定**（意图的充分条件）：搜索结果非空 → 取到 ≤5 个职位标题 → 进入 3e。
> **失败归因**：有岗位但标题提取方法未命中 → **M 类**（加方法）；搜索结果为空（无任何岗位）→ 结束该站点，标注"没有相关岗位"。

先轮询等待岗位容器出现：`scripts/wait_results.py`的`wait_jobs(js, wait_for_load)`（`[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post]`，最多 ~10s）。

再判断搜索结果：
- **空** → 结束该站点，标注"没有相关岗位"；
- **非空** → `scripts/extract_titles.py` 的 `get_job_titles(js, limit=5)` 取最多 5 个职位标题。

---

#### 3e · 筛选并记录（返回的必须是岗位链接，不是官网首页链接）

> **意图**：判定 KEYWORD 是否为 3d 所取标题的**连续子串**，输出命中职位的**岗位链接**。
> **成功判定**（意图的充分条件）：产出 ≥1 个岗位链接（命中职位的链接，或未命中时第一个职位的链接）→ 记录。
> **失败归因**：标题已取到但链接提取方法未命中 → **M 类**（加方法）。

对 3d 取的职位标题判定（`scripts/match_links.py` 的 `match_titles(titles, keyword)`：连续子串）后，调用 `extract_matched_links(js, cdp, titles, keyword)` 提取：
- **有连续子串命中** → 提取**命中职位**的岗位链接；
- **无连续子串命中** → 函数兜底提取**第一个职位**的岗位链接，标注"无精确匹配，取第 1 个岗位"；

**提取链接的底层方法（`scripts/extract_links.py`，按命中率排序，任一成功即停止）**：
- `extract_a_links`（最稳）：`<a>` 链接提取（常规）
- `extract_ancestor_a`：卡片本身无 `<a>`，取祖先 `<a>` 的 href（metaAPP `[data-test=positionItem]` → `/position/{id}/detail?share_token=...`）
- `extract_via_attr`：卡片为 div 带 data- 属性（美团 `.position_list_item` 的 `data-jobunionid`）→ 读属性 + URL 模板拼接
- `extract_by_click`：JS click 跳转取 URL（SPA 路由跳转场景）
- `extract_via_detail_btn`：SPA 内嵌详情面板：点卡片展开面板 → 点"查看详情"按钮 → 重写 window.open 捕获 `/campus/detail?jobAdId={uuid}`
- `extract_via_api`：点击卡片触发 API → 从 performance 资源请求抓 uuid 拼接详情链接
- `extract_via_fiber_onclick`：React/antd 卡片无 `<a>` 且 click 不跳转（网易）→ 重写 window.open + 触发 fiber onClick 捕获

---

## 四、输出报告

生成 `output/{KEYWORD}岗位检索报告.md`，3 段：

**1. 任务参数**：触发模式、勾选模式、搜索词、URL 来源、站点数

**2. 匹配结果**（匹配类型三种：精准连续子串 / 降级 / 兜底）：

| # | 网站 | 匹配类型 | 岗位链接 |
| - | --- | ---- | ---- |
| 1 | {企业名} | {精准连续子串 / 降级 / 兜底} | {岗位详情页 URL} |

> 匹配类型枚举：`精准连续子串`（标题含 KEYWORD 连续子串）/ `降级`（降级链后匹配成功，如校招→通用 Tab）/ `兜底`（无精确匹配，取第 1 个岗位）。
> 链接填岗位详情页 URL；降级/兜底须在说明中写明原因。

**3. 不匹配结果**（状态两类：执行失败 / 搜索结果为空）：

| # | 网站 | 状态 | 说明 | 网站链接 |
| - | --- | ---- | --- | ---- |
| 1 | {企业名} | {执行失败 / 搜索结果为空} | {失败环节或空结果说明} | {原始 URL} |

> 状态枚举：`执行失败`（页面打开异常/加载失败/导航目标tab失败/搜索失败/岗位链接提取失败/其他——说明列写具体失败环节）/ `搜索结果为空`（无任何岗位）。
> 任何降级/兜底/失败都必须在"说明"列写明原因，方便人工复核。

---

## 五、经验沉淀流程（方法层优先，特例层兜底）

每次执行结束后复盘，先按 Step 1 的失败信号判定归属，再按**两级路由**更新知识库：

**判定入口（来自 Step 1）**：
- **M 类（方法不足）** → 走第一级方法层；
- **S 类（站点走不通）** → 走第二级特例层。

**第一级 · 方法层（优先）**：站点经验先进动作文件，作为新方法按序尝试

1. **M 类失败 → 动作文件加方法**：目标元素存在但当前方法未命中（如页面有下拉但 hover 方法都不触发、有岗位但提取方法拿不到），在对应动作文件（`scripts/*.py`）新增一个方法函数，按序追加在现有方法后。**不改 SKILL.md 主流程、不进 patterns.md**。
2. **同坑出现 ≥2 次** → 将最稳的方法**前移**到文件方法顺序首位（成功率自适应；若后续引入统计机制，按统计排序）。

**第二级 · 特例层（兜底）**：S 类失败（站点走不通）才升级为模式

3. **S 类失败的新站点** → 先补一行到 `references/site-notes.md`（URL 入口 + 坑点 + URL 模板，10 行内），供人工排查。
4. **同坑出现 ≥2 次且方法层无法覆盖** → 归纳为**新模式**：在 `references/patterns.md` 索引表加一行 + 新增模式小节（10–30 行），含"识别信号 / 应对 / 代表站点 / 代码引用"。
5. **模式 ≥5 个且互相独立** → 允许将 patterns.md 拆分为 `patterns/` 子目录按域名分组，索引表保持单一增长点。

> **准入红线**：M 类（方法不足）一律进方法层；只有 S 类（站点走不通）才允许升级到 patterns.md（特例层）。

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

> **browser-use v3.0**：统一用 `browser-use <<'PY' ... PY` pipe 模式。核心 API：`goto_url` / `page_info()` / `js(code)` / `fill_input` / `wait_for_load()` / `capture_screenshot()`。
> **高级 API（antd/React 必用）**：`cdp(method, session_id=None, **params)` —— `Input.dispatchMouseEvent`（mouseMoved/Pressed/Released，真实鼠标，JS dispatchEvent 无效）、`Emulation.setDeviceMetricsOverride`（1920 宽防菜单折叠）。

---

## 七、附录：脚本速查（一个动作一个文件；antd 辅助收敛于 hover_expand.py）

| 脚本                    | 步骤   | 核心函数                                                                          |
| --------------------- | ---- | ----------------------------------------------------------------------------- |
| `env_check.sh`        | Step 0 | 环境检查（清理→二进制启动 Chrome(IPv4)→轮询验证端口）                             |
| `open_page.py`        | 3a    | `open_page(goto_url, js, url)`（导航 + 轮询就绪）                            |
| `open_page_wait.py`   | 3a    | `open_page_wait(js, wait_for_load)`（SPA 极慢加载兜底）                        |
| `find_tab.py`         | 3b    | `find_tab(js, mode)`                                                          |
| `tab_has_dropdown.py` | 3b    | `tab_has_dropdown(js, text)` → {has_dropdown, menu_id}（探测有无下拉）      |
| `click_tab.py`        | 3b    | `click_tab(js, text)`                                                         |
| `nav_verified.py`     | 3b    | `nav_verified(js, before_url)`（组合 url_changed/has_*，排除宣传落地页）/ `has_type_evidence(js, mode)` |
| `url_changed.py`      | 3b    | `url_changed(js, before_url)`                                                 |
| `has_search_input.py` | 3b/3c | `has_search_input(js)` / `find_search_input(js)` / `find_in_iframe(js)` / `find_visible_search_input(js)`（可见性过滤，推荐） |
| `has_jobs.py`         | 3b    | `has_jobs(js)`                                                                |
| `hover_expand.py`     | 3b/3d | `hover_expand_css` / `hover_expand_antd` / `click_dropdown_item` / `real_click`（含 antd 辅助） |
| `fill_keyword.py`     | 3c    | `fill_keyword(js, keyword)`（建议 native setter，禁用 fill_input）             |
| `trigger_search.py`   | 3c    | `trigger_enter(js)` / `click_search_btn(js)` / `click_btn_by_selector(js, selector)`（JS click 指定按钮） |
| `search_verified.py`  | 3c    | `url_has_query(js)`（含 keywords=） / `stats_changed(js)`（排除固有文案假阳性） / `search_verified(js)` |
| `wait_results.py`     | 3d    | `wait_jobs(js, wait_for_load)`                                                |
| `extract_titles.py`   | 3d    | `get_job_titles`（底层 `extract_container_titles`；空则 `extract_a_links` 兜底） |
| `extract_links.py`    | 3e    | 底层方法：`extract_a_links` / `extract_by_click` / `extract_via_fiber_onclick` / `extract_ancestor_a` / `extract_via_attr` / `extract_via_detail_btn` / `extract_via_api` |
| `match_links.py`      | 3e    | 判定 + 编排：`match_titles` / `extract_matched_links`（依赖 extract_links 底层方法） |
