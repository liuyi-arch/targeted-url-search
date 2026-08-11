# 站点模式库（Patterns）

> 本文件是**唯一的模式增长点**。每类站点一个模式：识别信号 → 应对 → 代表站点。SKILL.md 只引用本文件索引表做路由。
> 新增经验：要么改进已有模式小节，要么按文末模板新增模式。**不要**把站点特例写进 SKILL.md。

## 模式索引表（路由用）

| # | 模式 | 识别信号（域名/URL/页面特征） | 应对要点 | 代表站点 |
|---|------|------------------------------|---------|---------|
| P1 | antd 菜单站点 | 导航含 `ant-menu`、`data-menu-id`、submenu 带箭头；JS dispatchEvent 无效 | CDP 真实 mouseMoved + 提取 data-menu-id 直接 goto_url + 视口放大防折叠 | 网易互娱 `campus.game.163.com` |
| P2 | zhiye 系（北森） | 域名 `*.zhiye.com`；搜索框 placeholder="搜索职位关键词" | 3f 容器提取 + 点击容器取 URL；类别=校园/实习生/日常实习 | 普渡/卓驭/360/欣旺达 |
| P3 | hover 下拉站点 | 点击 Tab 进入介绍页而非职位页（URL 变但无搜索框） | hover 展开下拉 → 点"职位/岗位"项 → 验证出现搜索框/职位列表 | 汇川 `recruit.inovance.com` |
| P4 | 登录墙站点 | 点击岗位卡片弹"登录"弹窗 | 用职位列表页 URL + 岗位标题，标注"详情需登录"，不跳过 | 网易岗位详情 |
| P5 | 反爬/拦截站点 | `goto_url` 后停在 `about:blank` | URL 校验 → 重试 1 次 → "页面加载失败(疑似反爬拦截)" | 百度 `talent.baidu.com` |
| P6 | hotjob 系 | 域名 `wecruit.hotjob.cn`；招聘类型在 URL 参数 recruitType | 找"职位/岗位"Tab；先改 recruitType 参数再打开 | 荣耀/新安能/三环 |
| P7 | 飞书招聘系 | 域名 `*.jobs.feishu.cn` | 标准流程；岗位为 `<a>` 或卡片跳详情 | metaAPP/去哪儿 |
| P8 | 自研站点 | 无常见招聘系统特征；DOM 千差万别 | 自主动作 3+5 个；iframe 兜底；无搜索框提取默认列表 | 万得/九坤/OPPO/视源/4399/联想 |
| P9 | 非 `<a>` 岗位站点 | `a[href*=position]` 数量 0~1 但页面有岗位 | 3f 三层提取（容器→点击容器取 SPA URL） | 美团/360 |

---

## P1 · antd 菜单站点

**识别**：导航出现 `class*="ant-menu"`、`data-menu-id="rc-menu-uuid-*"`、submenu 标题带下拉箭头；hover 后 popup 渲染在 body 根部。

**应对**：
1. **先放大视口**（窗口过窄 antd 会折叠进"更多"，仅剩 `rc-menu-more`）：
   `cdp("Emulation.setDeviceMetricsOverride", width=1920, height=1000, deviceScaleFactor=1, mobile=False)`，若已折叠需 `goto_url` 刷新。
2. **CDP 真实鼠标移动**触发展开（JS dispatchEvent 无效——rc-trigger 只认可信事件流）：
   取 `[data-menu-id="rc-menu-uuid-<path>"]` 中心坐标 → `cdp("Input.dispatchMouseEvent", type="mouseMoved", x, y)`。
3. **读取 popup 菜单项**：`li[role=menuitem]` 的 **`data-menu-id` 属性即目标 URL**（如 `rc-menu-uuid-/app/job/position?id=102`）→ 提取后直接 `goto_url`，**不要模拟点击**（React 的 JS .click() 常不触发）。
4. **详情卡片**：若 JS .click() 不跳转，用 CDP 真实点击；弹出登录 → 按 P4。

**坑点**：菜单折叠与窗口宽度相关，每次新连接后菜单状态可能不同；`cdp` 需用 `cdp(method, session_id=None, **params)` 签名。

**代码**：`assets/scripts/antd_hover.py`。

---

## P2 · zhiye 系（北森招聘系统）

**识别**：`*.zhiye.com`；页面搜索框 placeholder="搜索职位关键词"；类别标签=校园招聘/实习生招聘/日常实习招聘；岗位标题**不是 `<a>`**（实测 `aCnt=0`）。

**应对**：
- 搜索框定位：placeholder 含"搜索"。
- 岗位提取：3f 第二层容器提取（`[class*=job-title],[class*=position-name]` 等）；容器无链接时第三层点击容器取 SPA 详情 URL。
- 类别切换：页面内标签"校园招聘/实习生招聘/日常实习招聘"可点击切换，等同于 Tab 导航。

**代表站点**：普渡 `pudutech1.zhiye.com`、卓驭 `we.zyt.com`、360 `360campus.zhiye.com`、欣旺达 `sunwodacampus.zhiye.com`、T-RAY `t-ray.zhiye.com`。

---

## P3 · hover 下拉站点

**识别**：点击招聘类型 Tab 后 URL 变化，但进入的是**介绍页**（无搜索框、无职位列表），如汇川点击"校园招聘"→ `#/campus` 招聘流程页。

**应对**：
1. 点击 Tab → 等 3s → 验证（URL 变 且 出现搜索框/职位列表）→ 成功则继续。
2. 验证失败 → **hover 展开下拉**：JS 派发 `mouseenter/mouseover/mousemove`（普通 CSS 下拉够用）→ 1s 后找"职位/岗位"项点击（如汇川 hover"校园招聘"后点"校招职位"）→ 再次验证。
3. 仍失败 → 降级链下一级 + 报告标注。

**代表站点**：汇川 `recruit.inovance.com`（校招→hover"校园招聘"→"校招职位"→`#/campus/jobs`；实习→直接点"实习生招聘"→`#/intern/jobs`）、网易 `campus.game.163.com`（但网易是 antd，走 P1）。

---

## P4 · 登录墙站点

**识别**：点击岗位卡片后弹出"登录"弹窗（antd Modal），未登录无法取详情 URL。

**应对**：记录**职位列表页 URL** + 岗位标题，标注"详情需登录"；**不跳过站点**、不死磕；必要时提示用户登录后重跑详情轮。

---

## P5 · 反爬/拦截站点

**识别**：`goto_url` 后 `location.href` 停在 `about:blank` 或 `''`，文本长度为 0；但人工浏览器可打开。

**应对**：3b URL 校验 → 重试 1 次（再次 goto_url）→ 仍失败判"页面加载失败(疑似反爬拦截)"，报告标注"人工可打开但自动化被拦截"。

**代表站点**：百度 `talent.baidu.com/jobs/list`。

---

## P6 · hotjob 系

**识别**：域名含 `wecruit.hotjob.cn`；URL 带 `recruitType`、`projectId`、`acotycoCode` 等参数。

**应对**：直接找"职位/岗位"Tab（类别三）；`recruitType` 参数可先修改 URL 再打开（1=校招、12=实习等需按站验证）。

**代表站点**：荣耀 `career.honor.com`、新安能 `wecruit.hotjob.cn`、三环 `hr.cctc.cc`。

---

## P7 · 飞书招聘系

**识别**：域名 `*.jobs.feishu.cn`；结构规范（antd 风格但更规整）。

**应对**：标准流程即可；岗位为 `<a>` 或点击卡片跳详情（详情页 URL 可直接提取）。

**代表站点**：metaAPP `meta.jobs.feishu.cn`、去哪儿 `hf7l9aiqzx.jobs.feishu.cn`。

---

## P8 · 自研站点

**识别**：非以上任何系统特征，`/position`、`/jobs` 等路径可能 404；页面可能 iframe、无搜索框、二级 Tab、整页卡片点击。

**应对**：
- 3c_1：允许大模型自主最多 3 个导航动作（如联想需在页面内再点"招聘岗位"二级 Tab）。
- 3d：搜索框 iframe 兜底 + 自主 5 个动作；仍无 → 提取默认列表并标注"未搜索"。
- 3f：三层提取兜底。

**代表站点**：万得 `wind.com.cn`、九坤 `jsj.top`、OPPO `careers.oppo.com`、视源 `campus.cvte.com`、4399 `hr.4399om.com`、联想 `talent.lenovo.com.cn/campus`。

---

## P9 · 非 `<a>` 岗位站点

**识别**：页面明明有岗位列表，但 `document.querySelectorAll('a')` 中 href 含 position/job/detail/recruit 的数量为 0~1。

**应对**：3f 三层提取：
1. `<a>` 链接（常规）。
2. 岗位标题容器文本：`[class*=job-title],[class*=JobTitle],[class*=position],[class*=job-item],[class*=post],[class*=position-name],[class*=jobName],[class*=job-name]`。
3. 点击容器触发 SPA 跳转取详情 URL（最多前 5 个；React 卡片需 CDP 真实点击，弹登录→P4）。

**代表站点**：美团 `zhaopin.meituan.com`（aLinks=1）、360（aCnt=0）。

---

## 新增模式模板

```markdown
## P{n} · {模式名}

**识别**：{域名/URL/页面特征信号，可被自动判断}

**应对**：{步骤 1. 2. 3.，引用 workflow.md 步骤或 assets/scripts 脚本名}

**坑点**：{常见失败原因}

**代表站点**：{站点1 `url`、站点2 `url`}
```

> 维护规则：同坑出现 ≥2 次才提升为正式模式；单站点经验只进 site-notes.md。
