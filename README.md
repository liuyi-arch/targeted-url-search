# 招聘网站自动化岗位搜索（targeted-url-search）

基于 browser-use 的招聘网站岗位自动搜索 Skill：给定企业官网招聘页 URL + 关键词，自动完成
**打开页面 → 导航到目标招聘类型 Tab → 搜索关键词 → 提取匹配岗位链接** 的完整流程，并输出检索报告。

## 架构（分层）

| 层级 | 位置 | 职责 |
|---|---|---|
| 编排层 | `targeted-url-search-skill.md` | 触发模式、输入参数、3a–3e 完整 workflow、判定标准、兜底逻辑、经验沉淀流程（执行时无需跳转） |
| 经验层 | `references/patterns.md` | 特例层模式库（仅 S 类失败站点） |
| 经验层 | `references/site-notes.md` | 单站点经验临时记录（S 类新站点） |
| 动作层 | `scripts/*.py` | 一个动作一个文件；文件内多函数 = 不同实现方法 |

设计原则：**方法层优先，特例层兜底**——M 类失败（方法不足）→ 动作文件加方法；S 类失败（站点走不通）→ 升级为 patterns 模式。

## 快速开始

```bash
# 一次性安装
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # 验证

# 每次执行前
bash scripts/env_check.sh  # 清理调试实例 → 二进制启动 Chrome(9222, IPv4) → 轮询验证端口
```

## 使用方式

- **工作流模式**：提示词含 `targeted-url-search`，URL 来自上一节点 JSON `records[].投递链接`；
- **原子模式**：用户直接提供 URL 列表 + KEYWORD。

## 目录结构

```
targeted-url-search/
├── targeted-url-search-skill.md   # 编排 + 核心 workflow
├── README.md
├── references/
│   ├── patterns.md                # 特例层模式库（索引表 = 唯一增长点）
│   └── site-notes.md              # 单站点经验
└── scripts/                       # 一个动作一个文件
    ├── env_check.sh               # Step 0 环境检查
    ├── open_page.py / open_page_wait.py   # 3a 导航+轮询就绪 / 极慢加载兜底
    ├── find_tab.py / tab_has_dropdown.py / click_tab.py / nav_verified.py / url_changed.py   # 3b
    ├── has_search_input.py / has_jobs.py / hover_expand.py             # 3b/3c
    ├── fill_keyword.py / trigger_search.py / search_verified.py        # 3c
    ├── wait_results.py            # 3d 等待岗位容器
    ├── extract_titles.py          # 3d 取职位标题
    ├── extract_links.py           # 3e 链接提取底层方法
    └── match_links.py             # 3e 判定 + 编排提取
```

## 核心流程（3a–3e）

1. **3a 打开页面**：goto_url 导航 → 正文 ≥ 200 且标题无错误特征才可用（SPA 慢加载走复查）。
2. **3b 导航 Tab**：按 MODE 语义找目标招聘类型 Tab（校招/实习/通用/社招）→ 探测有无下拉（有 → hover 展开；无 → 直接点击）→ 验证（含降级链）。
3. **3c 搜索**：定位搜索框 → 填入 KEYWORD → 触发 → 验证生效（URL 参数或统计变化）。
4. **3d 取搜索结果**：等待岗位容器出现；空 → 结束站点标"没有相关岗位"；非空 → 取 ≤5 个职位标题。
5. **3e 筛选记录**：KEYWORD 连续子串命中 → 提取命中职位链接；未命中 → 提取第一个职位链接。

输出：`output/{KEYWORD}岗位检索报告.md`（任务参数 / 匹配结果 / 不匹配结果）。
