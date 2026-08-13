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

## 北森 italent/zhiye 系站点（普渡/卓驭/360，P1 特征）

- 入口：普渡 `https://pudutech1.zhiye.com/campus/jobs`；卓驭 `https://we.zyt.com/campus/jobs`；360 `https://360campus.zhiye.com/jobs`
- 坑点1：岗位详情为 **SPA 弹层跳转**（点击卡片触发 `GetSubmitLimit?jobAdId=` API 但 URL 不变）→ **解法（重要）**：点击卡片就地展开详情面板（`STDetailPanel`）后，面板底部有"查看详情"按钮（`STDetailBtn`）→ 点击触发 `window.open('/campus/detail?jobAdId={uuid}')` → **完整详情 URL 模板：`https://{tenant}.zhiye.com/campus/detail?jobAdId={uuid}`**（重写 window.open 捕获即可拿到，已验证可独立访问）。注意：卡片点击本身不跳转，须再点"查看详情"
- 坑点2：搜索框 placeholder="搜索职位关键词"，**页面有两个同名输入框**：第一个隐藏（rect 0,0，`find_search_input` 会误命中它导致 fill 无效），**第二个可见**（~716,420）→ 必须过滤 `offsetParent!==null && rect.width>0` 再定位；触发方式：**CDP 真实鼠标点击可见输入框 → 键盘输入"前端" → CDP 点击搜索按钮 `button.n4CX554ba6hctr1kensJ`（~1079,420）**，搜索后统计文案变为"全部职位（共 N 个）"且 URL 不变（SPA 内部过滤），`search_verified` 的 stats 正则此时才是真命中
- 坑点3：**API 可用**：POST `/api/Jobad/GetJobAdPageList`（body `{pageSize,pageIndex,categoryId:2,type:1,langType:'zh_CN'}`）返回全量岗位，含 JobAdName/JobAdId → 按名称过滤即可确认岗位存在
- 坑点4：岗位卡片 class 为 styled-components（`style__STListItemContent-editor__sc-*`），不在 JOB_CONTAINER_SELECTOR；标题在 `[class*=STJobTitle]`
- 坑点5：卓驭 SPA 偶发白屏（BodyLen=0），重试 goto 数次可恢复
- 坑点6（普渡 3b 正确解法）：**"校园招聘"是下拉父菜单**（非普通 Tab）！导航区 `div.sc-iqseJM`（坐标 ~1312,30，文本"校园招聘"）点击后展开二级菜单"校招职位"(~1349,80) / "实习生职位"(~1349,114)，点击"校招职位"→ URL `/campus/jobs`。`find_tab` 找不到是因 styled-components 非标准元素 + 下拉结构 → 需 CDP 真实鼠标按坐标点击，不能用 JS click
- 坑点7（卓驭同解）：卓驭 `https://we.zyt.com/campus/jobs` 与普渡同构——"校园招聘"下拉父菜单(~1202,30)→"校招职位"(~1239,80)；可见搜索框"搜索职位关键词"(~1066,420) + 搜索按钮 `button.n4CX554ba6hctr1kensJ`(~1479,420)；详情链接同模板 `/campus/detail?jobAdId={uuid}`（"查看详情"按钮 ~1500,751 触发 window.open）

## 360（360campus.zhiye.com，italent 变体）

- 入口：`https://360campus.zhiye.com/jobs`
- 坑点1：**顶部导航无下拉**（与普渡/卓驭不同）——"招聘职位"即当前页；校招/实习筛选在**页面内"招聘类别"Tab**："校园招聘"(~564,475) 点击后 106→35 个
- 坑点2：可见搜索框"搜索职位关键词"(~716,420) + 搜索按钮 `button.n4CX554ba6hctr1kensJ`(~1079,420)，CDP 输入+点击 → 过滤生效
- 坑点3：**详情 URL 模板为 `/jobs/detail?jobAdId={uuid}`**（域名路径是 /jobs 非 /campus）；获取 uuid 方式：**点击岗位卡片触发 `GetSubmitLimit?jobAdId={uuid}` API**，从 performance 资源请求里抓取（360 无"查看详情"window.open 机制）
- 已验证：26春-Web前端开发工程师-5154 uuid=aa87fc53-8436-4684-89c2-9f23ab9e6bd5；26秋-Web前端开发工程师-4898 uuid=dcdf18b2-0536-41a4-9ac4-3c984097de35；26春-AI应用开发工程师（侧重前端方向）(J12343) uuid=d28994e2-194e-42a6-9d89-608796e0edef

## 快手（campus.kuaishou.cn，antd 下拉菜单）

- 入口：`https://campus.kuaishou.cn/recruit/campus/e/#/campus/jobs?code=...`
- 坑点1（3b 关键）：**导航"应届招聘"与"实习招聘"都是 antd 下拉菜单**（class `ant-dropdown-trigger`），不能用 click_tab 直接点，须 CDP 真实鼠标 **hover** 展开再点二级项：
  - "应届招聘"(~925,26) → 下拉项："职位列表"(~924,88)、"职位解读"(~924,134)
  - "实习招聘"(~1001,26) → 下拉项："留用实习"(~1000,88)、"日常实习"(~1000,134)
  - 点击后 URL 的 `recruitSubProjectCodes` 参数变化即切换成功（应届=20271779425607；留用实习=20271772783534）
- 坑点2：`tab_has_dropdown` 的 antd 探测（data-menu-id）对该站点不命中 → 直接按坐标 hover 处理
- 坑点3：CDP IPC 偶发超时（TimeoutError），重试即可
- 坑点4（日常实习视图）："实习招聘→日常实习"跳转**独立站点** `zhaopin.kuaishou.cn/recruit/e/#/official/trainee/`（快手招聘-日常实习），搜索框"搜索职位"(~1330,543) 输入+回车 → URL 带 `name={关键词}`；岗位在 **ant-table 表格行**（`tr.ant-table-row`，无 <a>），点击行触发 `window.open('/official/trainee/job-info/{id}')` 捕获详情链接；详情 URL 模板 `https://zhaopin.kuaishou.cn/recruit/e/#/official/trainee/job-info/{id}`（验证时须 reload 确保 SPA 刷新对应岗位）
- 快手日常实习前端岗位（已验证）：主站31255 / 可灵AI-Android大前端25913 / 商业化28004 / 全栈-大前端29992 / 【实习】前端25287

## 美团（zhaopin.meituan.com）

- 入口：`https://zhaopin.meituan.com/web/campus`（**打开即校园招聘页，无需点击"校园招聘"Tab**，URL 不变属正常）
- 坑点1：**搜索 = JS 填入（native setter）+ JS click `.zp_search_btn`**；页面有两个同名"输入关键词搜索岗位"输入框：第一个隐藏（rect 0,0）、**第二个可见（~620,420）**；`.zp_search_btn` rect 0,0 不可真实点击但 JS click 有效；CDP 真实点击会超时
- 坑点2：搜索后 URL 变为 `?keyword={关键词}`；岗位卡片 `.position_list_item` 含 **`data-jobunionid`** 属性
- URL 模板：详情页 `https://zhaopin.meituan.com/web/position/detail?jobUnionId={id}`（已验证有效）
- 已验证前端岗位：前端开发实习生 507746100 / 前端技术组-日常实习 3072326071 / 前端开发实习生（AI产品方向）4299852548

## metaAPP（meta.jobs.feishu.cn，飞书招聘系统）

- 入口：`https://meta.jobs.feishu.cn/{portalId}/position/list?share_token=...`（**打开即职位列表页，无需点 Tab**）
- 搜索：填入"前端"+Enter 后 URL 带 `keywords=前端`（**search_verified 漏判**：正则只认 q/query/keyword 不认 keywords，但搜索实际生效，结果统计"开启新的工作（N）"）
- 岗位卡片 `[data-test=positionItem]` 本身无链接，**祖先 `<a>` 有 href**：`/position/{id}/detail?share_token=...` → 提取后补全域名即为完整详情链接
- 详情页验证：直接访问详情 URL 标题正确（"{岗位名} - 加入MetaApp"），headless 下内容区可能不渲染（仅导航）；**详情 API `/api/v1/job/posts/{id}?portal_type=6` 无需登录可直连**返回完整 description/requirement（可作内容佐证）
- 已验证：Web开发工程师 7667455281391585574（厦门）/ web开发工程师 7665998202159794474（北京）/ TS开发工程师 7573975010268825919 / 游戏开发工程师（成都）7553122638065338665

## 招商网络科技（cmbnt.cmbchina.com）

- 入口：`https://cmbnt.cmbchina.com/pages/schoolRecruit/index.html`（内推绑定页 `bindInvited` 无职位，需点导航"校园招聘"进入）
- **坑点（3a 阈值）**：初始 URL `bindInvited` 是内推绑定页，**正文仅 45 字**，默认 3a 阈值 200 会误判失败 → **该站点 3a 须用 min_len=40**（页面正常加载，标题"招银网络科技"无错误特征）；调低阈值后 3a 通过
- 坑点2：绑定页导航"校园招聘"是 `a.menu-item`（JS click 有效，CDP 会超时），点击后 URL → `/pages/schoolRecruit/index.html`，校招 5 个在招职位（需滚动加载）
- URL 模板：详情页 `https://cmbnt.cmbchina.com/pages/socialRecruit/detail.html?jobId={id}&currentType=0&isTop=0`
- 已验证：前端开发工程师 jobId=A96D2284169948F781AA2485D9EB7BA2（2027 届，深圳/杭州/成都）

## 新增站点笔记模板

```markdown
## {站点名}（{所属模式/特征}）

- 入口：`{URL}`
- 坑点：{一句话描述坑}
- URL 模板：{搜索后 URL 格式}
```
