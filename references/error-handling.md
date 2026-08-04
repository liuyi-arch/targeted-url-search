# 错误处理与故障排查

本文件记录 `targeted-url-search` 技能执行过程中的常见问题、原因和解决方案。

---

## 环境问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `browser-use: command not found` | 未安装或 PATH 未设置 | `export PATH="$HOME/.local/bin:$PATH"` 然后 `uv tool install browser-use` |
| Python 版本过低 | 系统 Python < 3.11 | 用 `uv tool install`（自动安装 Python 3.13），不要用 `pip3 install` |
| browser-use v2 vs v3 语法不兼容 | 旧技能使用 `browser-use open/state/close` 等废弃命令 | 本技能 v5.0 已全部适配 v3.0 `<<'PY'` 语法，不要混用旧命令 |

---

## 浏览器问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| Chrome 弹出 "Allow remote debugging?" | macOS 首次远程调试需授权 | 在弹窗点击 Allow；或预先用 `open -a "Google Chrome" --args --remote-debugging-port=9222 '--remote-allow-origins=*'` 启动 |
| zsh 报 `no matches found` | `--remote-allow-origins=*` 的 `*` 被 zsh 通配符展开 | 使用单引号包裹：`'--remote-allow-origins=*'` |
| 浏览器会话残留 | 上次 `--reload` 未执行 | 执行 `browser-use --reload` 后 `pkill -9 -f "Google Chrome"` |
| 页面打不开 | session 异常 | `browser-use --reload` 然后重试 |
| 搜索未触发过滤 | JS 框架事件不兼容 | 用 `fill_input` + JS `requestSubmit()` 或键盘事件 `Enter` |

---

## 数据提取问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 职位链接提取不到 | 选择器不匹配 | 参考 `site-patterns.md` 站点专用选择器 |
| 默认列表不包含目标岗位 | SPA 站点分页/懒加载 | 必须走搜索步骤（3d），不依赖默认列表 |
| 搜索后结果为空 | 该站点确实无相关岗位 | 直接记录"搜索成功，无匹配"，跳过该站点，不尝试兜底 |

---

## 搜索词匹配规则

| 规则 | 说明 |
|------|------|
| **匹配条件** | 搜索词是职位标题的**连续子串**（如 "前端" 匹配 "前端开发工程师" 和 "Web前端研发工程师"） |
| **大小写** | JS 的 `String.includes()` 区分大小写，中文无此问题，英文关键词需注意 |
| **只看第一页** | 不滚动加载更多，不分页检查，只提取搜索后当前可见的职位 |
| **空结果处理** | 直接跳过，不尝试 URL 参数、分页、滚动加载等兜底策略 |
