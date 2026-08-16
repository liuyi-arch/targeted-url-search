# 招聘网站自动化岗位搜索（分层架构 v3.0）

> **设计原则**：
>
> - **本文件 = 编排 + 核心 workflow**：3a–3f 完整流程、判定标准、兜底逻辑内置本文件，执行时无需跳转。
> - **经验/脚本外置**：站点经验在 `references/`（patterns 模式库 + site-notes 站点笔记），脚本在 `scripts/`（一个动作一个文件，文件内多函数=不同实现方法）；本文件不出现任何脚本代码，只引用文件名。脚本速查见文末"六、附录"。

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

> **意图**：启动独立 Chrome 调试实例（端口自动分配 + 独立 profile），可被 browser-use 连接。
> **成功判定**：`bash scripts/env_check.sh` 退出码 0 且输出 `[ok] Chrome 调试实例就绪，端口 ${PORT}（系统自动分配，独立 profile）`。
> **失败归因**：端口有响应但验证未命中 → **M 类**；无监听/启动失败 → **S 类**。

**执行链路**：启动独立实例 → 读取端口 → 验证就绪 → 输出连接信息，成功判定通过 → 进入 3a：

- **节点1 · 启动独立实例**（`scripts/env_check.sh`）：
  - 方法1：唯一 profile（`/tmp/chrome-debug-profile-$(date +%s)`）+ `--remote-debugging-port=0` 启动 Chrome（`--disable-blink-features=AutomationControlled` 防反自动化站点检测）。
- **节点2 · 读取端口**：
  - 方法1：读 `DevToolsActivePort` 文件第一行（Chrome 自动分配的空闲端口，系统保证不与用户进程冲突）。
- **节点3 · 验证就绪**（≤15s 轮询）：
  - 方法1：`curl /json/version` 含 `"Browser"` → 就绪；超时 → `[FAIL]` + tail 日志 + exit 1。
- **节点4 · 输出连接信息**：
  - 方法1：输出 `[ok] ... 端口 ${PORT}` + `[hint] export BU_CDP_URL=http://127.0.0.1:${PORT}`（browser-use 调用必须带此环境变量强制指向独立实例）。

### Step 1 执行总则

1. **错误记录**：执行过程中出现的 M/S 类错误，按站点记录到 `references/site-notes.md`（URL 入口 + 失败环节 + 原因）。
2. **站点失败兜底链**（3a–3f 任一节点**所有方法执行失败或异常**后触发，按序执行）：
   1. **查特例层索引**（下表 / `references/patterns.md`）：命中已收录特例 → 按对应模式应对执行，成功则继续后续节点；未命中 → 进入下一步；
   2. **每个站点AI 自主操作 ≤30s**：允许大模型非流程自由尝试；解决则继续，未解决 → 进入下一步；
   3. **结束当前站点**：site-notes 记录失败环节+原因（M/S 归类），直接进入下一站点。

### Step 2：构建 URL 列表

- **工作流**：读取 JSON 文件，用 `jq -r '.records[] | "\(.招聘企业)\t\(.投递链接)"'` 提取，按 `EXCLUDE_INDICES` 跳过对应行。
- **原子**：用户提供的 URL 列表即 `URL_LIST`。

### Step 3：逐站点处理（核心 workflow，3a–3f）

对每个 URL 执行以下子步骤，全部通过 `browser-use <<'PY' ... PY` Python pipe 模式调用。

> **多方法尝试约定**：动作文件多方法按序尝试，任一成功，不再执行后续方法；站点执行过程M/S归类，写入site-notes 标注失败环节+原因。

> **正常/异常定义（全文统一）**：**正常**＝脚本成功执行（返回值 true/false 均属正常，false/空列表是合法结果）；**异常**＝脚本执行过程抛错（报异常），或所有既定方法均无法解决问题。

> **pipe 模式执行约定**：① js() 返回值已解析，勿再包 json.loads；② target 跨 pipe 持久，跨调用 Target.getTargets 按 URL 找回 tid；③ 裸 js() 默认落在 attached tab（about:blank）→ open_page_create(..., switch_tab=switch_tab) 已内置激活，此后裸 js()/cdp() 自动路由该 tab，未用则全程 target_id 定向；④ CDP Input 域命令（如 Input.dispatchMouseEvent/insertText）须 activateTarget + attach sessionId 并带 session_id=，否则不生效。

> **执行时间约定**：3a-3f任一节点所有方法执行失败或异常时，按 **Step 1.2 站点失败兜底链**处理（查特例索引 → AI 自主 ≤30s → 结束站点进入下一站），AI 非流程尝试不超过 30 秒。
>
> **兜底链衔接（重要）**：下文各节点中"所有方法执行失败/异常 → **结束该站点，归类M/S**"均为**兜底链最后一步的简写**——触发时须先走 Step 1.2（查特例索引 → AI 自主 ≤30s），仍失败才结束该站点并记录 site-notes。

---

#### 3a · 打开页面并确认可用

**执行链路**：打开（createTarget 新开 + 轮询就绪）→ 慢加载兜底，成功判定通过 → 进入 3b：

- **节点1 · 打开页面**（`scripts/open_page.py`）：
  - 方法1 `open_page_create(cdp, js, url, switch_tab=switch_tab)`：createTarget 新开 + 内置 switch_tab 激活该 tab；
  - 任一方法脚本成功执行且判断打开页面正常（正文 ≥ 40 + 标题无错误特征），进入 3b；否则，进入节点2；所有方法脚本执行异常，结束当前站点，归类S。
- **节点2 · 慢加载兜底**（`scripts/open_page_wait.py`）：
  - 方法1 `open_page_wait(js, wait_for_load)`：wait_for_load → 再等 5s 复查 → 返回 bool；
  - 任一方法bool为true，进入3b；所有方法bool为false或慢加载兜底异常，退出当前站点，归类S。


#### 3b · 导航至目标招聘类型 Tab（含 hover 下拉展开）

**目标 Tab 分类**：

| 类别         | 语义关键词                                              |
| ------------ | ------------------------------------------------------- |
| 类别一(校招) | 校园招聘 / 校招 / 应届招聘 / 校招职位 / 校招岗位 / 应届 |
| 类别二(实习) | 实习招聘 / 实习生 / 实习                                |
| 类别三(通用) | 职位 / 招聘职位 / 职位列表 / 岗位 / 岗位投递            |
| 类别四(社招) | 社招 / 社会招聘                                         |

**降级链（根据MODE选择降级链，降级链任意一级执行成功，不进行降级链后续节点执行）**：

| MODE | 降级链                                                       |
| ---- | ------------------------------------------------------------ |
| 1    | 类别一 → 类别三（若找到类别三tab，结果说明"可能包含社招/实习岗位"） |
| 2    | 类别二 → 类别一（若找到类别一tab，结果说明“可能包含校招正式批次岗位”） → 类别三（若找到类别三tab，结果说明"可能包含校招正式批次/社招批次岗位"） |
| 3    | 先按 MODE=1 走完 3b–3e，再按 MODE=2 走完 3b–3e               |

**每个类别执行链路**：找类别对应的tab → 探测该tab有无下拉 → 有下拉，下拉展开并点击；无下拉，直接点击tab → 验证：

- **节点1 · 找 tab**（`scripts/find_tab.py`）：
  - 方法1 `find_tab(js, mode)`：按 MODE 语义关键词找直接可见 Tab → 返回 {found, text}；
  - 任一方法找到，进入节点2；任一方法找不到，进入降级链下一级，若已是降级链最后一级，进入3c；所有方法找tab异常，进入3c，归类M。
- **节点2 · 探测有无下拉**（`scripts/tab_has_dropdown.py`）：
  - 方法1 `tab_has_dropdown(js, text)` → 返回 {has_dropdown, menu_id}；
  - 任一方法脚本成功执行且探测有下拉，进入节点3；任一方法脚本成功执行且探测无下拉，进入节点4；所有方法脚本执行异常，进入3c，归类M。
- **节点3 · 下拉展开并点击**（ `scripts/hover_expand.py` ）：
  - 方法1 `hover_expand_css(js)`：普通 CSS/JS 下拉 → 1s 后 `click_dropdown_item(js)` 点"职位/岗位"项；
  - 方法2 `hover_expand_antd(cdp, js, menu_id, goto_url)`：antd 系菜单（用节点2 返回的 menu_id，JS dispatchEvent 无效）；**反自动化站点禁用 goto_url 参数，改用 target_id 定向**（见上文"pipe 模式执行约定③"：open_page_create 内置 switch_tab 激活，target_id 跨 pipe 持久）
  - 任一方法脚本成功执行且下拉展开并点击正常，进入节点5；所有方法脚本执行异常，进入3c，归类M。
- **节点4 · 直接点击tab**（`scripts/click_tab.py`）：
  - 方法1 `click_tab(js, text)`：无下拉时直接点击 Tab；
  - 方法2 `click_tab_fiber(js, text)`：**React fiber onClick 触发**（JS click 无效时用，CVTE 坑——首页"查看全部岗位"为 BUTTON 无 href，JS click 不触发路由，须触发 `__reactProps.onClick`）；
  - 任一方法脚本成功执行且点击tab正常，进入节点5；所有方法脚本执行异常，进入3c，归类M。

- **节点5 · 验证**（`scripts/nav_verified.py`）：
  - 方法1 `nav_verified(js, before_url)`：URL 变化 且（搜索框或职位列表出现）表示成功；
  - 方法2 `has_type_evidence(js, mode)`：**M 类归因证据（非成功判定）**——仅用于验证失败时区分 M/S（页面含目标类型关键词=目标视图存在→归 M；不含=目标视图不存在→归 S）；
  - 任一方法验证成功（仅方法1），进入3c；所有方法验证失败，进入降级链下一级，若已是降级链最后一级，进入3c；所有方法验证异常，进入3c，归类M。

---

#### 3c · 搜索

**执行链路**：定位搜索框 → 填入 → 触发 → 验证生效：

- **节点1 · 定位搜索框**（`scripts/has_search_input.py`）：
  - 方法1 `find_visible_search_input(js)`：只返回**可见**搜索框（过滤 `offsetParent!==null && rect.width>0`）；
  - 方法2 `find_clickable_search_input(js)`：逐框 elementFromPoint 校验，返回**真正可点击**框（命中 INPUT）；
  - 方法3 `find_search_input(js)`：主文档定位（placeholder 含 搜索/职位/岗位，不保证可见）；
  - 方法4 `find_in_iframe(js)`：iframe 兜底（跨源跳过）；
  - 任一方法，找到搜索框，进入节点2；所有方法找不到搜索框（正常空结果），结束该站点，归类S；所有方法定位搜索框异常（脚本抛错），结束该站点，归类M。
- **节点2 · 填入**（`scripts/fill_keyword.py`）：
  - 方法1 `fill_keyword(js, keyword)`：native setter + InputEvent（`fill_input` 对受控组件无效，禁用），填入后主动 `focus()` 保持焦点；
  - 方法2 `fill_keyword_clickable(js, keyword)`：**受控组件+多框混淆专用**（VIVO/t-ray italent 系）——逐框 elementFromPoint 校验选可见可点框（hit=INPUT）+ native setter（CDP insertText 对受控组件无效，事件到达但 value 被重置）；
  - 任一方法填入成功，进入节点3；所有方法填入失败，结束该站点，归类M。
- **节点3 · 触发**（`scripts/trigger_search.py`，按 3 轮 23 站实测成功率排序）：
  - 方法1 `trigger_enter(js)`：派发回车（React onSubmit）——**零成本首选**，实测 60%（12/20）直接命中，失败代价低；其余方法均需特定页面元素，前置反而对表单型站点多一次 no-btn 切换；
  - 方法2 `click_search_btn(js)`：点搜索按钮（onClick 不触发 onSubmit，按钮兜底；网易 ant-input-search-button、Beisen 系"搜索职位"按钮用），实测 6/6=100%；
  - 方法3 `click_search_icon(js, icon_selector='.searchBox .icon--search')`：**点搜索图标触发**（4399 坑——JS fill+回车无效，点图标有效，URL 变 `?key={词}`），实测 1/1=100%；
  - 方法4 `search_via_url_param(js, keyword, param='postKey')`：**URL 参数触发搜索**（hotjob/北森系：新安能/荣耀——antd-mobile 搜索框 JS fill+回车均不触发过滤，URL 加 `postKey={词}` 刷新立即生效），实测 1/1=100%；
  - 方法5 `click_btn_by_selector(js, selector)`：按 CSS 选择器 JS click 指定按钮（**需显式传 selector**，未实测，最后兜底）；
  - 任一方法成功，进入节点4；所有方法触发失败，结束该站点，归类M。
- **节点4 · 验证生效**（`scripts/search_verified.py`）：
  - 方法1 `url_has_query(js)`；
  - 方法2 `stats_changed(js)`；
  - 任一方法验证生效，进入3d；所有方法验证未生效，结束该站点，归类M。


---

#### 3d · 等待并取搜索结果（最多 5 个职位标题）

**执行链路**：等待岗位容器 → 判断结果 → 取职位标题：

- **节点1 · 等待岗位容器**（`scripts/wait_results.py`）：
  - 方法1 `wait_jobs(js, wait_for_load)`：轮询等待岗位容器出现（`[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post]`，最多 ~10s）；
  - 任一方法脚本成功执行（wait_jobs 返回 true **或 false 均属正常**，false=超时无岗位容器），进入节点2 判断结果；所有方法脚本执行异常（抛错），结束该站点，归类M。
- **节点2 · 判断结果**：
  - **空** → 结束该站点，标注"没有相关岗位"；
  - **非空** → 进入节点3。
- **节点3 · 取职位标题**（`scripts/extract_titles.py`）：
  - 方法1 `get_job_titles(js, limit=5)`：取最多 5 个职位标题；
  - 任一方法取职位标题脚本正常，进入3e；所有方法取职位标题异常，结束该站点，归类M。

---

#### 3e · 筛选并记录（返回的必须是岗位链接，不是官网首页链接）

**执行链路**：判定 KEYWORD 是否是标题的连续子串 → 提取链接 → 记录：

- **节点1 · 判定命中**（`scripts/match_links.py`）：
  - 方法1 `match_titles(titles, keyword)`：KEYWORD 是否为标题**连续子串**；
  - 任一方法脚本成功执行（match_titles 返回列表，命中与否均属正常，空列表=未命中），进入节点2；所有方法脚本执行异常（抛错），结束该站点，归类M。
- **节点2 · 提取链接**（`scripts/extract_links.py` + `match_links.py` 编排 `extract_matched_links`，**按 3 轮实测成功率排序（均 100%，按成本从低到高），任一成功即停止**）：
  - 方法1 `extract_a_links`：`<a>` 链接提取（零成本；实测 3/3=100%：4399/去哪儿/招商）；
  - 方法2 `extract_by_click`：JS click 跳转取 URL（SPA 路由跳转场景；实测 2/2=100%：欣旺达/新安能）；
  - 方法3 `extract_via_window_open_click(js, titles, card_sel=None)`：**卡片有 onclick（原生或 React）且点击 window.open 新标签页**（联想/百度/美团）→ 重写 window.open + 直接 `el.click()` 捕获；比 fiber 版更通用（不依赖 `__reactProps`），兼带 SPA URL 变化兜底；实测 3/3=100%；
  - 方法4 `extract_via_api`：点击卡片触发 API → 从 performance 资源请求抓 uuid 拼接详情链接（Beisen 系 VIVO/普渡/卓驭/360：`GetSubmitLimit?_timestamp=...&jobAdId={uuid}` → `/campus/detail?jobAdId={uuid}`）；实测 4/4=100%；
  - 方法5 `extract_via_fiber_onclick`：React/antd 卡片无 `<a>` 且 click 不跳转 → 重写 window.open + 触发 fiber onClick 捕获（未实测，最后尝试）；
  - 备用底层方法（未编排进主链，可单独调用）：`extract_ancestor_a`（卡片本身无 `<a>`，取祖先 `<a>` href）、`extract_via_attr`（卡片 div 带 data- 属性如美团 `data-jobunionid` → 读属性 + URL 模板拼接）、`extract_via_detail_btn`（SPA 内嵌详情面板：点卡片展开 → 点"查看详情" → 重写 window.open 捕获）；
  - 任一方法脚本成功执行：标题含 KEYWORD（连续子串）→ 取所有精准命中岗位链接，进入3f；标题不含（未命中）→ 兜底取第一个岗位链接，进入3f（命中与未命中均属正常结果）；所有方法脚本执行异常（抛错）或均无法产出岗位链接，结束该站点，归类M。

#### 3f · **保活关闭（强制执行，tab 数保持 ≤2）**

- **节点1**（`scripts/close_tab_keepalive.py`）：
  - 方法1 `close_tab_keepalive(cdp, tid)`：关闭前若该 tab 将是最后一个 page tab，先建 about:blank 占位，防窗口消失/浏览器重启；
  - 任一方法脚本成功执行，该站点执行完毕，进入下一站点；所有方法脚本执行异常（抛错），**仍进入下一站点**（tab 未关闭不阻断流程），site-notes 标注"3f 关闭失败+原因"。

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

## 五、前提条件

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

## 六、附录：脚本速查（一个动作一个文件；antd 辅助收敛于 hover_expand.py）

| 脚本                    | 步骤   | 核心函数                                                                          |
| --------------------- | ---- | ----------------------------------------------------------------------------- |
| `env_check.sh`        | Step 0 | 环境检查（启动独立 Chrome 调试实例：端口 0 自动分配 + 唯一 profile → 输出端口与 BU_CDP_URL） |
| `open_page.py`        | 3a    | `open_page_create(cdp, js, url)`（**方案 A 默认**：createTarget 新开+轮询就绪，返回 tid）  |
| `close_tab_keepalive.py` | 3a | `close_tab_keepalive(cdp, tid)`（保活关闭：最后一个 tab 前先建 about:blank 占位，防窗口消失） |
| `open_page_wait.py`   | 3a    | `open_page_wait(js, wait_for_load)`（SPA 极慢加载兜底）                        |
| `find_tab.py`         | 3b    | `find_tab(js, mode)`                                                          |
| `tab_has_dropdown.py` | 3b    | `tab_has_dropdown(js, text)` → {has_dropdown, menu_id}（探测有无下拉）      |
| `click_tab.py`        | 3b    | `click_tab(js, text)` / `click_tab_fiber(js, text)`（React fiber onClick 触发，CVTE 坑）/ `click_el_select_option(js, option_text)`（el-select 项目弹窗选值，三环坑） |
| `nav_verified.py`     | 3b    | `nav_verified(js, before_url)`（组合 url_changed/has_*，排除宣传落地页）/ `has_type_evidence(js, mode)` |
| `url_changed.py`      | 3b    | `url_changed(js, before_url)`                                                 |
| `has_search_input.py` | 3b/3c | `find_visible_search_input(js)`（可见性过滤，**首选，实测 18/18**）/ `find_clickable_search_input(js)`（elementFromPoint 可点校验，VIVO 坑）/ `find_search_input(js)` / `find_in_iframe(js)` / `has_search_input(js)`（3b 验证 bool） |
| `has_jobs.py`         | 3b    | `has_jobs(js)`                                                                |
| `hover_expand.py`     | 3b/3d | 入口：`hover_expand_css(js)` / `hover_expand_antd(cdp, js, menu_id, goto_url=None)` / `click_dropdown_item(js)` / `real_click(cdp, js, selector)`；antd 辅助收敛：`ensure_wide_viewport` / `hover_submenu` / `get_popup_items` / `pick_url` |
| `fill_keyword.py`     | 3c    | `fill_keyword(js, keyword)`（native setter，禁用 fill_input）/ `fill_keyword_clickable(js, keyword)`（可见可点框，受控组件+多框混淆 VIVO/t-ray 用） |
| `trigger_search.py`   | 3c    | `trigger_enter(js)`（**零成本首选，实测 60%**）/ `click_search_btn(js)`（实测 6/6）/ `click_search_icon(js)`（4399 点搜索图标，实测 1/1）/ `search_via_url_param(js, keyword, param='postKey')`（hotjob 系新安能/荣耀，URL 参数触发，实测 1/1）/ `click_btn_by_selector(js, selector)`（需显式 selector，最后兜底） |
| `search_verified.py`  | 3c    | `url_has_query(js)`（含 keywords=） / `stats_changed(js)`（排除固有文案假阳性） / `search_verified(js)` |
| `wait_results.py`     | 3d    | `wait_jobs(js, wait_for_load)`                                                |
| `extract_titles.py`   | 3d    | `get_job_titles`（底层 `extract_container_titles`；空则 `extract_a_links` 兜底） |
| `extract_links.py`    | 3e    | 底层方法（编排顺序见 match_links.py，均实测 100%）：`extract_a_links` / `extract_by_click` / `extract_via_window_open_click`（卡片 onclick+window.open，联想/百度/美团）/ `extract_via_api`（Beisen 系 GetSubmitLimit）/ `extract_via_fiber_onclick`；备用：`extract_ancestor_a` / `extract_via_attr` / `extract_via_detail_btn` |
| `match_links.py`      | 3e    | 判定 + 编排：`match_titles` / `extract_matched_links`（依赖 extract_links 底层方法） |
