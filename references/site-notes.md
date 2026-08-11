# 站点笔记（site-notes）

> 踩坑站点一行式要点。**单站点经验只进这里**；同坑 ≥2 次才归纳为 patterns.md 的正式模式。
> 每条 ≤10 行：入口 URL、坑点、URL 模板。

---

## 网易互娱（antd 菜单 + 登录墙）

- 入口：`https://campus.game.163.com/?st=<token>`
- 坑点：导航为 antd Menu，"应届生/精英实习生"是 submenu（`data-menu-id="rc-menu-uuid-/campus"`、`/intern`）；**JS dispatchEvent 无法展开，必须 CDP 真实 mouseMoved**；窗口窄时折叠进"更多"，需视口放大（1920）后刷新。
- 校招职位入口：hover"应届生"→"网易互娱27届校园招聘" → `https://campus.game.163.com/app/job/position?id=102&st=<token>`（搜索框 placeholder="请输入职位信息、所属部门"）。
- 实习职位入口：hover"精英实习生"→"蛋仔派对AI实习专项" → `https://campus.game.163.com/app/job/position?id=75&st=<token>`。
- 坑点：岗位是 `.card-item` 卡片（非 `<a>`），JS .click() 不跳转，CDP 真实点击会弹**登录框** → 标注"详情需登录"。

## 汇川技术（hover 下拉）

- 入口：`https://recruit.inovance.com/#/jobs?ref=<code>`
- 坑点：点击"校园招聘"进入 `#/campus` **招聘流程介绍页（无搜索框）**；hover"校园招聘"后点"校招职位" → `#/campus/jobs`（搜索框"搜索校招职位..."）。
- 实习：直接点"实习生招聘" → `#/intern/jobs`（搜索框"搜索所有职位..."）。
- URL 模板：岗位详情 `https://recruit.inovance.com/#/jobs/{uuid}`；搜索后 URL 带 `?q=<kw>`。

## 百度（反爬拦截）

- 入口：`https://talent.baidu.com/jobs/list?recommendCode=...&recruitType=GRADUATE`
- 坑点：`goto_url` 后停在 `about:blank`（人工可打开）→ 重试 1 次仍失败 → 判"页面加载失败(疑似反爬拦截)"。

## 360 / 普渡 / 卓驭 / 欣旺达 / T-RAY（zhiye 系）

- 入口：`https://360campus.zhiye.com/jobs`、`https://pudutech1.zhiye.com/campus/jobs`、`https://we.zyt.com/campus/jobs`、`https://sunwodacampus.zhiye.com/custom/...`、`https://t-ray.zhiye.com/campus/jobs`
- 坑点：岗位标题非 `<a>`（`aCnt=0`）；搜索框 placeholder="搜索职位关键词"；类别标签"校园招聘/实习生招聘/日常实习招聘"可点击切换。

## 美团

- 入口：`https://zhaopin.meituan.com/web/campus`
- 坑点：页面有岗位（"全部校招职位(440)"）但 `<a>` 链接仅 1 个（`aLinks=1`）→ 必须容器提取；搜索框 placeholder="输入关键词搜索岗位"；搜索后统计变化（"全部校招职位(N)"）。

## 荣耀 / 新安能（hotjob 系）

- 入口：`https://career.honor.com/SU61b9ba97bef57c13bca5cffd/mc/position/intern?...&recruitType=12&postKey=前端`、`https://wecruit.hotjob.cn/SU6618fd381eb8053acd5fc2b9/mc/position/campus?...&recruitType=1`
- 坑点：招聘类型在 URL 参数（`recruitType`）+ 页面 Tab；可直接改 `postKey`/`recruitType` 参数再打开。

## 联想（页面内二级 Tab）

- 入口：`https://talent.lenovo.com.cn/campus`
- 坑点：先点"应届生招聘"Tab → 页面内再点"招聘岗位"**二级 Tab** 才出现职位列表 → 3c_1 自主动作 3 个。

## 去哪儿 / metaAPP（飞书招聘系）

- 入口：`https://hf7l9aiqzx.jobs.feishu.cn/704852/position/list?...`、`https://meta.jobs.feishu.cn/140297/position/list?...`
- 坑点：结构规范，标准流程；岗位 `<a>` 或卡片跳详情。

## 自研站点（万得/九坤/OPPO/视源/4399/三环/VIVO/招商网络）

- 万得 `https://www.wind.com.cn/mobile/JoinUS/RecruitDetail/zh.html?entry=school`
- 九坤 `https://jsj.top/f/Z4sGz6?x_field_1=wd`
- OPPO `https://careers.oppo.com/university/oppo/campus/post?shareId=18004`
- 视源 `https://campus.cvte.com/`
- 4399 `https://hr.4399om.com/weixin/?r=job/agent&type=2...`
- 三环 `https://hr.cctc.cc/school`、VIVO `https://hr-campus.vivo.com/campus/jobs`
- 招商网络 `https://cmbnt.cmbchina.com/bindInvited?...`
- 坑点：DOM 千差万别；无搜索框时提取默认列表并标注；iframe/二级 Tab 常见。

---

## 新增站点笔记模板

```markdown
## {站点名}（{所属模式}）

- 入口：`{URL}`
- 坑点：{一句话描述坑}
- URL 模板：{详情/搜索后 URL 格式，如可用}
```
