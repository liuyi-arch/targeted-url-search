# 站点适配模式参考

不同招聘网站的页面结构差异较大，本文件记录已知的站点适配模式，供 Step 3c-3g 使用。

## 站点适配总表

| 站点 | URL 特征 | 招聘项目控制 | 搜索框 | 职位链接选择器 | 备注 |
|------|---------|------------|--------|----------------|------|
| 飞书招聘 | `*.jobs.feishu.cn` | `.atsx-tree-checkbox` 自定义复选框 | `input[placeholder*="搜索"]` | `a[href*="position"]` + `href` 含 `/detail` | 搜索正常工作 |
| INTSIG (zhiye) | `*.zhiye.com` | URL 路径 `/campus/`=校招, `/social/`=社招 | `input[placeholder*="搜索"]` | `[class*="JobTitle"]` 父级 `a` | 搜索按钮点击可能不触发过滤 |
| 通用标准站 | — | `input[type="checkbox"]` + `<label>` | `input[type="text/search"]` | `a[href*="position/job/detail"]` | 标准 HTML 结构 |

---

## 一、飞书招聘 (jobs.feishu.cn)

### 页面特征
- 域名格式: `{company}.jobs.feishu.cn/s/{shareId}` 或 `{company}.jobs.feishu.cn/{companyId}/position/list`
- 使用自定义 UI 组件库 (atsx)，非标准 HTML checkbox

### 招聘项目复选框 (MODE 1/2)

**自定义复选框类名**: `.atsx-tree-checkbox`

**定位逻辑**:
```bash
# 1. 列出所有复选框及其邻近文本
browser-use eval "JSON.stringify([...document.querySelectorAll('.atsx-tree-checkbox')].map((el,i)=>({i,text:el.parentElement?.parentElement?.textContent?.trim()?.substring(0,30)||'',checked:el.className.includes('checked')})))"

# 2. 根据 MODE 找到目标索引:
#    MODE=1: text 含 "校园招聘" 或 "校招"
#    MODE=2: text 含 "实习"

# 3. 点击目标复选框
browser-use eval "document.querySelectorAll('.atsx-tree-checkbox')[<index>].click()"

# 4. 验证
browser-use state
```

### 搜索框

```bash
# placeholder 通常为 "搜索职位"
browser-use state  # 找到 input 元素索引
browser-use input <index> "$KEYWORD"
```

### 搜索按钮

```bash
# 按钮文本通常为 "搜索"
browser-use state  # 找到 button 元素索引
browser-use click <button_index>
```

### 职位链接提取

```bash
# 飞书职位详情页链接含 position 和 detail
browser-use eval "JSON.stringify([...document.querySelectorAll('a[href*=\"position\"]')].filter(a=>a.href.includes('detail')&&a.textContent.trim().length>2).map(a=>({title:a.textContent.trim(),link:a.href})))"
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
# 查找导航标签
browser-use eval "JSON.stringify([...document.querySelectorAll('a,button,span,div')].filter(el=>el.textContent.trim()==='校园招聘'||el.textContent.trim()==='校招招聘').map((el,i)=>({tag:el.tagName,text:el.textContent.trim(),href:el.href||''})))"
# 找到后点击对应索引
```

**MODE=2 (实习)**:
- 如果 URL 含 `/intern/`，模式2已自动满足
- 否则查找 "实习生招聘" / "实习" 导航标签

### 搜索框

```bash
# placeholder 通常为 "搜索职位关键词"
browser-use state
browser-use input <index> "$KEYWORD"
```

### 搜索按钮

```bash
# 按钮文本通常为 "搜索职位"
browser-use click <button_index>
```

### 搜索不触发过滤的备选方案

INTSIG 网站的搜索按钮点击可能不触发过滤（JS 框架事件兼容性问题）：

```bash
# 方案A: URL 参数搜索
browser-use open "https://${domain}/campus/jobs?keyword=$KEYWORD"

# 方案B: 表单 submit
browser-use eval "document.querySelector('form')?.requestSubmit()"

# 方案C: 键盘事件
browser-use click <search_input_index>
browser-use type "$KEYWORD"
browser-use keys "Enter"
```

### 职位链接提取

```bash
# 职位标题用 class 含 "JobTitle" 或 "STJobTitle"
# 链接在标题元素的父级或同级 <a> 标签上
browser-use eval "JSON.stringify([...document.querySelectorAll('[class*=\"JobTitle\"],[class*=\"job-title\"]')].map(t=>({title:t.textContent.trim(),link:t.closest('a')?.href||t.parentElement?.querySelector('a')?.href||''})))"
```

### 已知问题
- 搜索按钮点击可能不触发过滤 → 用 URL 参数 `?keyword=xxx` 备选
- 页面使用滚动加载（"没有更多了~"），但**本技能只看第一页**，不滚动

---

## 三、通用标准站点

### 页面特征
- 标准 HTML `<input type="checkbox">` + `<label>` 结构
- 标准 `<input type="text">` 或 `<input type="search">` 搜索框
- 标准 `<button>` 搜索按钮

### 招聘项目复选框 (MODE 1/2)

```bash
# 列出所有复选框及标签
browser-use eval "JSON.stringify([...document.querySelectorAll('input[type=\"checkbox\"]')].map((el,i)=>{const label=el.closest('label')||el.parentElement;return {i,text:label?.textContent?.trim()?.substring(0,30)||'',checked:el.checked,id:el.id}}))"

# MODE=1: 找 text 含 "校招" "校园" "全职" "正式" 的复选框
# MODE=2: 找 text 含 "实习" "日常" "暑假" "暑期" 的复选框
# 点击:
browser-use click <index>
# 或用 JS:
browser-use eval "document.querySelectorAll('input[type=\"checkbox\"]')[<index>].click()"
```

### 搜索框 + 搜索按钮

```bash
browser-use state  # 找到 input[type="text/search"] 和 button 的索引
browser-use input <search_idx> "$KEYWORD"
browser-use click <button_idx>
```

### 职位链接提取

```bash
# 通用: 查找 href 含 position/job/detail 的 <a> 标签
browser-use eval "JSON.stringify([...document.querySelectorAll('a')].filter(a=>{const h=a.href||'';return h.includes('position')||h.includes('job')||h.includes('detail')}).filter(a=>a.textContent.trim().length>2&&a.textContent.trim().length<200).map(a=>({title:a.textContent.trim(),link:a.href})))"
```

---

## 四、新增站点适配流程

遇到新站点时，按以下流程适配：

1. `browser-use open <url>` + `browser-use state` 获取页面元素
2. 如果 `state` 输出不够清晰，用 `browser-use eval` 搜索关键词：
   ```bash
   browser-use eval "JSON.stringify([...document.querySelectorAll('*')].filter(el=>{const t=el.textContent.trim();return t.length>0&&t.length<30&&(t.includes('校招')||t.includes('实习')||t.includes('搜索'))}).map((el,i)=>({tag:el.tagName,text:el.textContent.trim().substring(0,30),type:el.type||'',className:el.className?.substring(0,50)||''}))})"
   ```
3. 根据返回结果确定：复选框/导航标签、搜索框、搜索按钮的定位方式
4. 记录到本文件的站点适配总表中，供下次复用

---

## 五、职位链接提取通用策略

如果专用选择器无效，按以下优先级尝试：

```bash
# 策略1: href 含 position/detail/job
browser-use eval "JSON.stringify([...document.querySelectorAll('a')].filter(a=>/position|detail|job/i.test(a.href)).filter(a=>a.textContent.trim().length>2).map(a=>({title:a.textContent.trim(),link:a.href})))"

# 策略2: class 含 title/Title 的元素 + closest('a')
browser-use eval "JSON.stringify([...document.querySelectorAll('[class*=\"title\"],[class*=\"Title\"]')].filter(el=>el.textContent.trim().length>2&&el.textContent.trim().length<200).map(el=>({title:el.textContent.trim(),link:el.closest('a')?.href||el.querySelector('a')?.href||''})))"

# 策略3: 如果以上都提取不到链接, 用 get html 分析结构
browser-use get html --selector "[class*=\"list\"]"  # 查看列表区域 HTML
# 然后根据实际 HTML 结构编写专用选择器
```
