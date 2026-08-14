# 站点模式库（Patterns）

> **特例层**：只放 **S 类失败（站点走不通）** 的站点。M 类（方法不足）→ 动作文件加方法，**不进本文件**；单站点经验先进 site-notes.md，同坑 ≥2 次且方法层无法覆盖 → 提升为模式；索引表 = 唯一增长点。**不要**把站点特例写进 SKILL.md。

## 模式索引表（路由用）

| # | 模式 | 识别信号 | 应对要点 | 代表站点 |
|---|------|---------|---------|---------|
| P1 | 自研站点 | 无常见招聘系统特征，DOM 千差万别 | 自主动作兜底；iframe 兜底；无搜索框终止站点；页面内二级 Tab | 联想 `talent.lenovo.com.cn/campus` |
| P2 | 反自动化检测站点 | goto_url/new_tab 导航到 about:blank；title 监控（改 title 被还原）；switch_tab 后 insertText 失效 / `Inspected target navigated` / `Cannot find default execution context` | 禁用 switch_tab/goto_url/new_tab；createTarget + activateTarget+attach；js 全程 target_id 定向；CDP 输入+点击 | 百度 `talent.baidu.com/jobs/list` |

---

## P1 · 自研站点

**识别**：非常见招聘系统特征。

**应对**：
- 3b：自主最多 3 个导航动作（如联想页面内再点"招聘岗位"二级 Tab）。
- 3c：搜索框 iframe 兜底；仍无 → 终止站点，标"搜索框未找到"。
- 3d/3e：`get_job_titles` 判空取 ≤5 标题 → `extract_matched_links` 按 KEYWORD 提取命中/首个职位链接。

**代表站点**：联想 `talent.lenovo.com.cn/campus`。

---

## P2 · 反自动化检测站点

**识别**：脚本级操作触发检测——`goto_url`/`new_tab` 导航主 frame 到 about:blank（`reason: scriptInitiated`）；改 `document.title` ~2s 被还原（title 监控）；`switch_tab` 后 `Input.insertText` 失效（value 不进）且报 `Inspected target navigated` / `Cannot find default execution context`（执行上下文丢失）。

**应对**（按 3a–3e）：
- 3a：**禁用 `switch_tab`/`goto_url`/`new_tab` 封装**——`Target.createTarget` 打开（不 mark title）→ `Target.activateTarget` + sleep 1.5 → `Target.attachToTarget` 拿 sid；js 全程 `target_id=tid` 定向。
- 3c：JS focus 搜索框 + `Input.insertText(KEYWORD, session_id=sid)`（一次成功）→ CDP 点击搜索按钮（百度"百度一下" ~915,446）。
- 3e：卡片无 `<a>` 且 JS click 无效 → CDP 真实点击卡片 + 重写 window.open 捕获详情链接。

**坑点**：`switch_tab`（mark_tab 改 title）触发防御后**该 tab 报废不可恢复**（insertText 全失效、重新 activate+attach 无效），须重开 tab；Chrome 须带 `--disable-blink-features=AutomationControlled`（Step 0 保证）。

**代表站点**：百度 `https://talent.baidu.com/jobs/list?recommendCode={code}&recruitType=GRADUATE`（详情 `site-notes.md` 百度条目坑点1-5）。

---

## 新增模式模板

```markdown
## P{n} · {模式名}

**识别**：{可自动判断的页面/URL 特征}

**应对**：{按 3a–3e 步骤或 scripts/ 脚本名写 1–3 条}

**坑点**：{常见失败原因}

**代表站点**：{站点 `url`}
```
