# 站点适配模式参考

不同招聘网站的页面结构差异较大，本文件记录已知的站点适配模式，供 Step 3c-3g 使用。

## 站点适配总表

| 站点 | URL 特征 | 搜索框 | 搜索触发方式 | 职位链接选择器 | 特殊行为 | 备注 |
|------|---------|--------|------------|----------------|---------|------|
| 飞书招聘 | `*.jobs.feishu.cn` | `input[placeholder*="搜索"]` | 点击搜索按钮 | `a[href*="position"]` + `href` 含 `/detail` | — | 搜索正常工作 |
| INTSIG (zhiye) | `*.zhiye.com` | `input[placeholder*="搜索"]` | fill + Enter 或 button | `[class*="JobTitle"]` 父级 `a` | — | 搜索按钮点击可能不触发过滤 |
| **拼多多校招** | `careers.pddglobalhr.com` | `input#name`（placeholder="搜索职位名称"） | `.page-job-list_searchButton__bYEas` 按钮 | `.page-job-list_jobList__UqU9K` 内 `a` 标签 | ⚠️ 默认列表不展示全部岗位 | **必须搜索**才能发现全部岗位 |
| 通用标准站 | — | `input[type="text/search"]` | fill + Enter | `a[href*="position/job/detail"]` | — | 标准 HTML 结构 |

---

## 一、飞书招聘 (jobs.feishu.cn)

### 页面特征
- 域名格式: `{company}.jobs.feishu.cn/s/{shareId}` 或 `{company}.jobs.feishu.cn/{companyId}/position/list`
- 使用自定义 UI 组件库 (atsx)，非标准 HTML checkbox

### 招聘项目复选框 (MODE 1/2)

**自定义复选框类名**: `.atsx-tree-checkbox`

**定位逻辑**:
```bash
browser-use <<'PY'
# 1. 列出所有复选框及其邻近文本
result = js("JSON.stringify([...document.querySelectorAll('.atsx-tree-checkbox')].map((el,i)=>({i,text:el.parentElement?.parentElement?.textContent?.trim()?.substring(0,30)||'',checked:el.className.includes('checked')})))")
print(result)

# 2. 根据 MODE 找到目标索引:
#    MODE=1: text 含 "校园招聘" 或 "校招"
#    MODE=2: text 含 "实习"

# 3. 点击目标复选框
js("document.querySelectorAll('.atsx-tree-checkbox')[<index>].click()")

# 4. 验证
info = page_info()
print(f"After click: {info.get('url', '')}")
PY
```

### 搜索框

```bash
browser-use <<'PY'
# placeholder 通常为 "搜索职位"
fill_input('input[placeholder*="搜索"]', "$KEYWORD")
PY
```

### 搜索按钮

```bash
browser-use <<'PY'
# 按钮文本通常为 "搜索"
js("""
(function() {
    let btns = document.querySelectorAll('button');
    for (let btn of btns) {
        if (btn.textContent.trim() === '搜索' && btn.offsetParent !== null) {
            btn.click();
            return 'clicked';
        }
    }
    return 'not found';
})()
""")
PY
```

### 职位链接提取

```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('a[href*=\"position\"]')].filter(a=>a.href.includes('detail')&&a.textContent.trim().length>2).map(a=>({title:a.textContent.trim(),link:a.href})))")
print(result)
PY
```

### 已知问题
- 搜索功能正常，URL 会更新为 `keywords=xxx&project=xxx`
- 分页: 搜索结果底部显示页码，**只取第一页**

---

## 二、INTSIG / zhiye 系 (intsig.zhiye.com)

### 页面特征
- 域名格式: `{company}.zhiye.com/{type}/jobs`
- URL 路径直接指示招聘类型: `/campus/`=校招, `/social/`=社招, `/intern/`=实习
- 使用导航标签而非复选框

### 招聘项目控制 (MODE 1/2)

**MODE=1 (校招)**:
- 如果 URL 含 `/campus/`，模式1已自动满足，跳过复选框步骤
- 如果 URL 不含 `/campus/`，查找导航标签 "校园招聘" 并点击

```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('a,button,span,div')].filter(el=>el.textContent.trim()==='校园招聘'||el.textContent.trim()==='校招招聘').map((el,i)=>({tag:el.tagName,text:el.textContent.trim(),href:el.href||''})))")
print(result)
# 找到后点击对应元素
js("document.querySelectorAll('a,button,span,div')[<index>].click()")
PY
```

**MODE=2 (实习)**:
- 如果 URL 含 `/intern/`，模式2已自动满足
- 否则查找 "实习生招聘" / "实习" 导航标签

### 搜索框

```bash
browser-use <<'PY'
# placeholder 通常为 "搜索职位关键词"
fill_input('input[placeholder*="搜索"]', "$KEYWORD")
PY
```

### 搜索按钮

```bash
browser-use <<'PY'
# 按钮文本通常为 "搜索职位"
js("""
(function() {
    let btns = document.querySelectorAll('button');
    for (let btn of btns) {
        if ((btn.textContent.trim() === '搜索职位' || btn.textContent.trim() === '搜索') && btn.offsetParent !== null) {
            btn.click();
            return 'clicked';
        }
    }
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}));
    return 'enter';
})()
""")
PY
```

### 搜索不触发过滤的备选方案

INTSIG 网站的搜索按钮点击可能不触发过滤（JS 框架事件兼容性问题）：

```bash
browser-use <<'PY'
# 方案A: URL 参数搜索
new_tab("https://${domain}/campus/jobs?keyword=$KEYWORD")
wait_for_load()

# 方案B: 表单 submit
js("document.querySelector('form')?.requestSubmit()")

# 方案C: 键盘事件
js("""
let inp = document.querySelector('input[placeholder*=\"搜索\"]');
inp.focus();
inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}));
""")
PY
```

### 职位链接提取

```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('[class*=\"JobTitle\"],[class*=\"job-title\"]')].map(t=>({title:t.textContent.trim(),link:t.closest('a')?.href||t.parentElement?.querySelector('a')?.href||''})))")
print(result)
PY
```

### 已知问题
- 搜索按钮点击可能不触发过滤 → 用 URL 参数 `?keyword=xxx` 备选（仅当 3d 搜索失败时）
- 页面使用滚动加载（"没有更多了~"），但**本技能只看第一页**，不滚动

---

## 三、拼多多校招 (careers.pddglobalhr.com) 🆕

### 页面特征
- 域名: `careers.pddglobalhr.com`
- URL 会自动从移动端 `/m/` 重定向到桌面端 `/campus/grad`
- React SPA，默认列表仅为精选子集（~22 个岗位）
- ⚠️ **关键：默认列表不展示全部岗位，必须通过搜索才能发现所有岗位**

### 搜索框

```bash
browser-use <<'PY'
# 搜索框: <input id="name" placeholder="搜索职位名称" class="rocket-input">
fill_input("#name", "$KEYWORD")
PY
```

### 搜索按钮

```bash
browser-use <<'PY'
# 搜索按钮: <button class="page-job-list_searchButton__bYEas">搜索</button>
js("document.querySelector('.page-job-list_searchButton__bYEas').click()")
PY
```

### 等待搜索结果

```bash
browser-use <<'PY'
wait_for_load()
js("new Promise(r => setTimeout(r, 3000))")
PY
```

### 职位链接提取

```bash
browser-use <<'PY'
# 搜索后的结果在 .page-job-list_jobList__UqU9K 区域内
# 匹配结果: 显示"共N个岗位"
result = js("""
JSON.stringify([...document.querySelectorAll('.page-job-list_jobList__UqU9K a, [class*=\"job\"] a')].filter(a => {
    const t = a.textContent.trim();
    return t.length > 3 && t.length < 100 && a.href.includes('detail');
}).map(a => ({title: a.textContent.trim(), link: a.href})))
""")
print(result)
PY
```

### 检查搜索结果

```bash
browser-use <<'PY'
# 页面文本会显示"共N个岗位"
text = js("document.body.innerText")
count = text.count("$KEYWORD")
print(f"Keyword '$KEYWORD' occurrences: {count}")
print(text[:2000])
PY
```

### 岗位详情页

```bash
browser-use <<'PY'
# 点击岗位进入详情页
# 详情页 URL 格式: /campus/grad/detail?positionId={uuid}
js("""
(function() {
    let links = document.querySelectorAll('a');
    for (let a of links) {
        if (a.textContent.trim().includes('$KEYWORD') && a.href.includes('detail')) {
            a.click();
            return a.href;
        }
    }
    return null;
})()
""")
PY
```

### 已知问题
- **默认列表不完整**：首页默认显示精选岗位，必须通过搜索才能发现全部岗位
- **移动端 URL 重定向**：`/m/pages/index/index` 会自动跳转到 `/campus/grad`
- **SPA 路由**：点击岗位后 URL 变化但无整页刷新，需等待 JS 渲染
- **搜索结果精确匹配**：搜索"前端"会返回"Web前端研发工程师"等包含"前端"的岗位

---

## 四、通用标准站点

### 页面特征
- 标准 HTML `<input type="checkbox">` + `<label>` 结构
- 标准 `<input type="text">` 或 `<input type="search">` 搜索框
- 标准 `<button>` 搜索按钮

### 招聘项目复选框 (MODE 1/2)

```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('input[type=\"checkbox\"]')].map((el,i)=>{const label=el.closest('label')||el.parentElement;return {i,text:label?.textContent?.trim()?.substring(0,30)||'',checked:el.checked,id:el.id}}))")
print(result)

# MODE=1: 找 text 含 "校招" "校园" "全职" "正式" 的复选框
# MODE=2: 找 text 含 "实习" "日常" "暑假" "暑期" 的复选框
# 点击:
js("document.querySelectorAll('input[type=\"checkbox\"]')[<index>].click()")
PY
```

### 搜索框 + 搜索按钮

```bash
browser-use <<'PY'
fill_input('input[type="text"], input[type="search"]', "$KEYWORD")
js("""
(function() {
    let btns = document.querySelectorAll('button');
    for (let btn of btns) {
        if ((btn.textContent.trim().includes('搜索') || btn.textContent.includes('Search')) && btn.offsetParent !== null) {
            btn.click();
            return 'clicked';
        }
    }
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}));
    return 'enter';
})()
""")
PY
```

### 职位链接提取

```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('a')].filter(a=>{const h=a.href||'';return h.includes('position')||h.includes('job')||h.includes('detail')}).filter(a=>a.textContent.trim().length>2&&a.textContent.trim().length<200).map(a=>({title:a.textContent.trim(),link:a.href})))")
print(result)
PY
```

---

## 五、新增站点适配流程

遇到新站点时，按以下流程适配：

1. 打开页面并获取信息：
```bash
browser-use <<'PY'
new_tab("<url>")
wait_for_load()
info = page_info()
print(f"Title: {info.get('title', '')}")
print(f"URL: {info.get('url', '')}")
text = js("document.body.innerText")
print(text[:1000])
PY
```

2. 定位关键元素：
```bash
browser-use <<'PY'
result = js("JSON.stringify([...document.querySelectorAll('input, button')].filter(el => el.offsetParent !== null).map(el => ({tag: el.tagName, type: el.type || '', placeholder: el.placeholder || '', text: el.textContent?.trim()?.substring(0, 30) || '', id: el.id, className: el.className?.substring(0, 60)})))")
print(result)
PY
```

3. 根据返回结果确定：搜索框、搜索按钮、职位链接选择器
4. 记录到本文件的站点适配总表中，供下次复用

---

## 六、职位链接提取通用策略

如果专用选择器无效，按以下优先级尝试：

```bash
browser-use <<'PY'
# 策略1: href 含 position/detail/job/recruit
result = js("JSON.stringify([...document.querySelectorAll('a')].filter(a=>/position|detail|job|recruit/i.test(a.href)).filter(a=>a.textContent.trim().length>2).map(a=>({title:a.textContent.trim(),link:a.href})))")
print(result)

# 策略2: class 含 title/Title 的元素 + closest('a')
result = js("JSON.stringify([...document.querySelectorAll('[class*=\"title\"],[class*=\"Title\"],[class*=\"job-title\"],[class*=\"JobTitle\"]')].filter(el=>el.textContent.trim().length>2&&el.textContent.trim().length<200).map(el=>({title:el.textContent.trim(),link:el.closest('a')?.href||el.querySelector('a')?.href||''})))")
print(result)

# 策略3: 查看列表区域 HTML 结构（最后手段）
js("document.querySelector('[class*=\"list\"], [class*=\"List\"]')?.outerHTML?.substring(0, 2000)")
PY
```
