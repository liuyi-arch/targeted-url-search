# 站点笔记（site-notes）

> **S 类失败新站点先记这里**（≤10 行/条）；同坑 ≥2 次 → 升为 patterns.md 模式。

## 联想（自研站点，P1 示例）

- 入口：`https://talent.lenovo.com.cn/campus`
- 坑点：需点"应届生招聘"→ 再点"招聘岗位"**二级 Tab** 才出现职位列表 → 3b 自主动作 3 个。

## 汇川技术（自研站点）

- 入口：`https://recruit.inovance.com/#/jobs?ref=AHGVKM5`（"全部职位"列表页）
- 坑点：顶部"校园招聘/实习生招聘"Tab 是**宣传落地页**，非职位列表；职位列表统一在 `#/jobs`，搜索框 placeholder="搜索所有职位..."
- 坑点2：职位卡片 `a.group`（href=`#/jobs/{uuid}`），标题在 H3（class 含 text-base sm:text-lg font-black）
- URL 模板：搜索后 `#/jobs?ref=AHGVKM5&q={关键词}`；标题提取须排除导航区（曾误命中菜单）

## 网易互娱（antd 菜单，P1 示例）

- 入口：`https://campus.game.163.com/`（职位列表直达 `/app/job/position?id=102` 校招 / `id=75` 精英实习生）
- 坑点1：职位卡片无 `<a>`，JS .click()/real_click 均不跳转（实际 `window.open` 新标签页）→ 重写 window.open + 触发 React fiber onClick 提取详情 URL（`/app/detail/index?id={id}&projectId={pid}`），已沉淀为 extract_via_fiber_onclick
- 坑点2：antd 菜单须 CDP 真实鼠标 hover（JS dispatchEvent 无效）；CDP 偶发 IPC 超时 → 重启 Chrome 调试实例恢复
- URL 模板：搜索后 URL 不变，靠"职位列表 N 个"统计判定；岗位标题在 `.position-name`

## 新增站点笔记模板

```markdown
## {站点名}（{所属模式/特征}）

- 入口：`{URL}`
- 坑点：{一句话描述坑}
- URL 模板：{搜索后 URL 格式}
```
