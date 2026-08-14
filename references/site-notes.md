# 站点笔记（site-notes）

> S 类失败新站点先记这里；同坑 ≥2 次 → 升 patterns.md。

## 联想（自研站点，P1 示例）

- 入口：`https://talent.lenovo.com.cn/campus`
- 坑点：需点"应届生招聘"→"招聘岗位"二级 Tab 才出职位列表（3b 自主动作 3 个）。

## 汇川技术（自研站点）

- 入口：`https://recruit.inovance.com/#/jobs?ref=AHGVKM5`
- 坑点：顶部"校园招聘/实习生"Tab 是宣传落地页；职位列表统一在 `#/jobs`，搜索框"搜索所有职位..."
- 卡片 `a.group`（href=`#/jobs/{uuid}`），标题在 H3；搜索后 `#/jobs?...&q={关键词}`；标题提取须排除导航区

## 网易互娱（antd 菜单，P1 示例）

- 入口：`https://campus.game.163.com/`（职位列表 `/app/job/position?id=102` 校招 / `id=75` 实习）
- 坑点1：卡片无 `<a>`，JS click 不跳转（实际 window.open）→ 重写 window.open + fiber onClick 捕获（extract_via_fiber_onclick），详情 `/app/detail/index?id={id}&projectId={pid}`
- 坑点2：antd 菜单须 CDP 真实鼠标 hover；CDP 偶发 IPC 超时 → 重启调试实例
- URL：搜索后不变，靠"职位列表 N 个"统计；标题 `.position-name`

## 北森 italent/zhiye 系（普渡/卓驭/360，P1 特征）

- 入口：普渡 `https://pudutech1.zhiye.com/campus/jobs`；卓驭 `https://we.zyt.com/campus/jobs`；360 `https://360campus.zhiye.com/jobs`
- 坑点1（详情）：卡片点击触发 `GetSubmitLimit?jobAdId=` API 但 URL 不变 → 点卡片展开 `STDetailPanel` → 点"查看详情"→ window.open 捕获；**URL 模板 `https://{tenant}.zhiye.com/campus/detail?jobAdId={uuid}`**
- 坑点2（搜索）：两个同名"搜索职位关键词"框，第一个隐藏（rect 0,0）→ 过滤可见框（~716,420）+ CDP 输入 + 点 `button.n4CX554ba6hctr1kensJ`（~1079,420）；统计"全部职位（共 N 个）"且 URL 不变
- 坑点3（API）：POST `/api/Jobad/GetJobAdPageList`（`{pageSize,pageIndex,categoryId:2,type:1,langType:'zh_CN'}`）返回全量 JobAdName/JobAdId
- 坑点4：卡片 styled-components（`STListItemContent`）不在 JOB_CONTAINER_SELECTOR；标题 `[class*=STJobTitle]`
- 坑点5：卓驭 SPA 偶发白屏 → 重试 goto
- 坑点6（普渡 3b）："校园招聘"是下拉父菜单（`div.sc-iqseJM` ~1312,30）→ 展开点"校招职位"(~1349,80)/"实习生职位"(~1349,114)；须 CDP 坐标点击，JS click 无效
- 坑点7（卓驭同解）："校园招聘"(~1202,30)→"校招职位"(~1239,80)；搜索框(~1066,420)+按钮(~1479,420)；"查看详情"~1500,751

## 360（360campus.zhiye.com，italent 变体）

- 入口：`https://360campus.zhiye.com/jobs`
- 坑点1：顶部导航无下拉，"招聘职位"即当前页；校招/实习在**页面内"招聘类别"Tab**："校园招聘"(~564,475) 106→35 个
- 坑点2：搜索框(~716,420) + 按钮 `button.n4CX554ba6hctr1kensJ`(~1079,420) CDP 输入
- 坑点3：详情 URL 为 **`/jobs/detail?jobAdId={uuid}`**（非 /campus）；点卡片触发 `GetSubmitLimit` API 从 performance 抓 uuid
- 已验证：Web前端-5154 aa87fc53-8436-4684-89c2-9f23ab9e6bd5；Web前端-4898 dcdf18b2-0536-41a4-9ac4-3c984097de35；AI应用前端(J12343) d28994e2-194e-42a6-9d89-608796e0edef

## 快手（campus.kuaishou.cn，antd 下拉菜单）

- 入口：`https://campus.kuaishou.cn/recruit/campus/e/#/campus/jobs?code=...`
- 坑点1（3b）："应届招聘"与"实习招聘"是 antd 下拉（`ant-dropdown-trigger`），须 CDP 真实鼠标 hover 展开：
  - 应届(~925,26) → 职位列表(~924,88)/职位解读(~924,134)
  - 实习(~1001,26) → 留用实习(~1000,88)/日常实习(~1000,134)
  - URL `recruitSubProjectCodes` 变化即切换成功（应届=20271779425607；留用实习=20271772783534）
- 坑点2：`tab_has_dropdown` antd 探测不命中 → 直接按坐标 hover
- 坑点3：CDP IPC 偶发超时 → 重试
- 坑点4（日常实习）：跳独立站 `zhaopin.kuaishou.cn/recruit/e/#/official/trainee/`，搜索框(~1330,543) 输入+回车 URL 带 `name=`；岗位在 ant-table 行（无 <a>），点击触发 window.open → 详情 `.../official/trainee/job-info/{id}`（验证须 reload）
- 已验证前端岗位：主站31255 / 可灵AI-Android大前端25913 / 商业化28004 / 全栈-大前端29992 / 【实习】前端25287

## 美团（zhaopin.meituan.com）

- 入口：`https://zhaopin.meituan.com/web/campus`（打开即校园招聘页）
- 坑点1：搜索 = JS 填入（native setter）+ JS click `.zp_search_btn`；两个同名输入框，第一个隐藏、第二个可见(~620,420)；`.zp_search_btn` rect 0,0 不可真实点击但 JS click 有效
- 坑点2：搜索后 URL `?keyword={关键词}`；卡片 `.position_list_item` 带 `data-jobunionid`
- URL：`https://zhaopin.meituan.com/web/position/detail?jobUnionId={id}`
- 已验证：前端开发实习生 507746100 / 前端技术组-日常实习 3072326071 / 前端（AI产品）4299852548

## metaAPP（meta.jobs.feishu.cn，飞书招聘系统）

- 入口：`https://meta.jobs.feishu.cn/{portalId}/position/list?share_token=...`（打开即职位列表）
- 搜索：填入+Enter 后 URL 带 `keywords=`（search_verified 已适配）；统计"开启新的工作（N）"
- 卡片 `[data-test=positionItem]` 无链接，祖先 `<a>` href：`/position/{id}/detail?share_token=...`
- 详情 API `/api/v1/job/posts/{id}?portal_type=6` 无需登录可直连
- 已验证：Web开发 7667455281391585574（厦门）/ web开发 7665998202159794474（北京）/ TS开发 7573975010268825919 / 游戏开发（成都）7553122638065338665

## 招商网络科技（cmbnt.cmbchina.com）

- 入口：`https://cmbnt.cmbchina.com/pages/schoolRecruit/index.html`（绑定页 `bindInvited` 无职位，点导航"校园招聘"进入）
- 坑点（3a 阈值）：绑定页正文仅 45 字 → **3a 须用 min_len=40**（否则误判失败）
- 坑点2：导航"校园招聘"是 `a.menu-item`（JS click 有效，CDP 超时），点击后校招 5 个职位（需滚动加载）
- URL：`https://cmbnt.cmbchina.com/pages/socialRecruit/detail.html?jobId={id}&currentType=0&isTop=0`
- 已验证：前端开发 jobId=A96D2284169948F781AA2485D9EB7BA2

## 百度（talent.baidu.com，反自动化检测站点）

- 入口：`https://talent.baidu.com/jobs/list?recommendCode={code}&recruitType=GRADUATE`
- 坑点（about:blank）：脚本主动导航主 frame 到 about:blank（`reason: scriptInitiated`）→ 禁用 goto_url/new_tab 封装
- 解法：Chrome 参数含 `--disable-blink-features=AutomationControlled` + CDP createTarget 打开 + target_id 定向
- 坑点2：搜索须 CDP 真实输入+回车（163→5 条，URL 不变）；卡片 `[class*=post-item]` 无 `<a>` 且 JS click 无效 → CDP 真实点击 + 重写 window.open
- URL：`/jobs/detail/{recruitType}/{uuid}?recommendCode={code}&s=2`

## 三环（hr.cctc.cc，el-select 项目选择，3b S 类）

- 入口：`https://hr.cctc.cc/school`
- **坑点（3b 批次切换，S 类）**：**初始"共0个岗位"**、无标准 Tab → 先选招聘项目（`.left-box-search .el-select` 下拉"2027届提前批招聘"等 + "确 定"按钮，用 `click_el_select_option`）→ 加载 39 个岗位
- 坑点2：搜索框"请输入岗位名称"填入+回车；搜索后"共0个岗位"→ 空结果直接结束
- 卡片：`.right-list-item` / 标题 `.item-left-title`

## 去哪儿（jobs.feishu.cn，飞书招聘系统 metaAPP 变体）

- 入口：`https://hf7l9aiqzx.jobs.feishu.cn/704852/position/list?spread=...`（打开即目标态）
- 搜索：填入+回车 → URL 带 `keywords=前端`；统计"开启新的工作（N）"
- 卡片 `[data-test=positionItem]` 祖先 `<a>` href：`/position/{id}/detail?spread=...`（extract_ancestor_a）

## VIVO（hr-campus.vivo.com，italent 系变体）

- 入口：`https://hr-campus.vivo.com/campus/jobs`（打开即目标态；SPA 首载 BodyLen ~167 须等数秒）
- 坑点1（搜索框多框混淆）：4 个含"搜索"框——顶部被覆盖（hit=DIV）、侧栏"搜索"框（非目标）、列表区"搜索职位关键词"（hit=INPUT，正确目标）→ 逐框 elementFromPoint 校验（find_clickable_search_input）；按钮 `BUTTON.n4CX554ba6hctr1kensJ`
- 坑点2：标题 `[class*=STJobTitle]`；卡片 `STListItemContent` 无 `<a>` → 点卡片触发 `GetSubmitLimit?jobAdId={uuid}` 抓 uuid（须手动按 target_id）
- URL：`https://hr-campus.vivo.com/campus/detail?jobAdId={uuid}`

## t-ray（t-ray.zhiye.com，北森 italent 系）

- 入口：`https://t-ray.zhiye.com/campus/jobs`（打开即目标态：职位列表 9 个）
- 坑点：同 VIVO 构——顶部搜索框被覆盖，用列表区可见搜索框 + 按钮 `BUTTON.n4CX554ba6hctr1kensJ` CDP 输入

## Step 0 · 环境检查（非站点）

- **事故教训**：**绝不可按端口 kill**（`lsof -ti :9222 | xargs kill -9` 会误杀用户日常 Chrome，其 DevToolsActivePort 可能指向 9222）→ 按 `--user-data-dir` 精确匹配只清理自己实例
- **端口约定**：**端口 0 自动分配**（`--remote-debugging-port=0` → 读 DevToolsActivePort 端口）彻底避免冲突；browser-use 须带 `BU_CDP_URL=http://127.0.0.1:${PORT}` 强制指向独立实例
- **反自动化参数**：`--disable-blink-features=AutomationControlled`（否则百度等导航到 about:blank）
- **故障排查**：/json/version 无响应 → 实例已退出（须 run_in_background 驻留）；403 → Chrome 147+ 默认 profile 禁用 HTTP 发现

## 新增站点笔记模板

```markdown
## {站点名}（{所属模式/特征}）

- 入口：`{URL}`
- 坑点：{一句话描述坑}
- URL 模板：{搜索后 URL 格式}
```
