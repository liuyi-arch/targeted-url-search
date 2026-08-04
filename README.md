# targeted-url-search

> WorkBuddy Skill: 在招聘网站中自动检索指定关键词，并输出统一格式的岗位筛选报告。

## What It Does

给定上游 JSON 文件中的招聘链接，或用户直接提供的 URL，本技能会：

1. 自动识别 `workflow` 或 `atomic` 触发模式
2. 收集并校验必填输入：URL 与搜索关键词
3. 使用 `browser-use v3.0+` 打开招聘站点并执行真实搜索
4. 只读取第一页结果，并筛选标题包含目标关键词的岗位
5. 输出统一结构的四段式报告

## Design Overview

当前版本采用“主流程收敛、规则外置”的结构：

- `SKILL.md`：编排入口与状态机
- `references/trigger-spec.md`：触发与补问规则
- `references/input-contract.md`：输入字段与 JSON 映射
- `references/execution-policy.md`：全局执行约束与 fallback 规则
- `references/site-registry.md`：站点适配注册表
- `references/report-schema.md`：报告结构与状态枚举
- `docs/add-site-checklist.md`：新增站点维护清单

## Trigger Modes

### Workflow Mode

- Trigger: 用户明确提及 `targeted-url-search`
- URL source: 上一节点输出的 JSON 文件
- Input collection: 优先从当前提示词提取，不足时补问

### Atomic Mode

- Trigger: 用户表达“在某个网站检索某个关键词”的语义
- URL source: 用户直接输入 URL
- Input collection: 从提示词提取 URL、关键词和补充信息

## Input Model

| Parameter | Variable | Required | Description |
|-----------|----------|----------|-------------|
| URL list | `URL_LIST` | Yes | 工作流来自 JSON，原子模式来自用户输入 |
| Company list | `COMPANY_LIST` | No | 工作流来自 JSON，原子模式可由域名推断 |
| Search keyword | `KEYWORD` | Yes | 如 `前端`、`后端`、`算法`、`产品` |
| Project mode | `PROJECT_MODE` | No | `campus` / `intern` / `social` / `none` |
| Supplementary info | `SUPPLEMENTARY` | No | 用户提供的额外提示 |
| Trigger mode | `TRIGGER_MODE` | - | `workflow` 或 `atomic` |

## Output Format

报告固定包含四个部分：

1. `任务参数`
2. `匹配结果`
3. `不匹配结果`
4. `注意事项`

完整格式以 `references/report-schema.md` 为准。

## Prerequisites

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor
```

## File Structure

```text
targeted-url-search/
├── README.md
├── SKILL.md
├── docs/
│   └── add-site-checklist.md
└── references/
    ├── execution-policy.md
    ├── input-contract.md
    ├── report-schema.md
    ├── site-registry.md
    └── trigger-spec.md
```

## Supported Site Families

| Site Family | URL Pattern | Search Support | Notes |
|-------------|-------------|----------------|-------|
| Feishu Recruiting | `*.jobs.feishu.cn` | Yes | 自定义组件较多，优先用站点适配器 |
| zhiye / INTSIG | `*.zhiye.com` | Yes | 某些站点允许站点级 fallback |
| PDD Campus | `careers.pddglobalhr.com` | Yes | 默认列表不完整，必须真实搜索 |
| Generic | Other | Best effort | 未命中注册表时使用通用适配器 |

## Maintenance Notes

- 不要在 `README.md` 重复写执行细节，避免与规范文件漂移
- 站点差异只在 `references/site-registry.md` 中维护
- 报告格式只在 `references/report-schema.md` 中维护
- 新增站点前先阅读 `docs/add-site-checklist.md`

## License

MIT
