# targeted-url-search

> WorkBuddy Skill: Automated job search on recruitment websites using browser-use CLI. Dual-mode trigger with input validation.

## What It Does

Given a JSON file (workflow mode) or direct URLs (atomic mode), a search keyword, and optional recruitment mode, this skill automatically:

1. **Detects trigger mode** from user's prompt (workflow vs atomic)
2. **Collects & validates** required inputs (URL + keyword) — asks user if missing
3. Opens each recruitment website (headless browser, zero browser interaction)
4. Checks the appropriate recruitment project checkbox (campus/intern)
5. Types the search keyword and clicks search
6. Extracts job titles and links from the **first page** of results
7. Filters jobs where the keyword is a **contiguous substring** of the title
8. Outputs a concise 4-section report

## Dual-Mode Trigger

### Workflow Mode
- **Trigger**: User mentions "targeted-url-search"
- **URL source**: JSON file from previous node (company names + URLs)
- **Input collection**: Asks "全量检索 or 选择性检索?" + keyword + supplementary info

### Atomic Mode
- **Trigger**: User prompt contains "search specific content on specific website" semantics
- **URL source**: User provides URLs directly
- **Input collection**: Prompts "请输入待检索网站网址、检索关键词、其余补充信息（可选）"

### Input Validation
- **Required fields**: URL(s) + keyword
- If missing → re-asks user (mode-specific prompt) until both are provided
- Supplementary info (e.g. "校招"/"实习") is parsed into MODE parameter

## Input Parameters

| Parameter | Variable | Required | Description |
|-----------|----------|----------|-------------|
| URL list | `URL_LIST` | Yes | Workflow: from JSON; Atomic: user input |
| Search keyword | `KEYWORD` | Yes | e.g. "前端", "后端", "算法", "产品" |
| Recruitment mode | `MODE` | No | 1=campus, 2=intern, 3=none (default) |
| Supplementary info | `SUPPLEMENTARY` | No | User-provided extra context |
| Trigger mode | `TRIGGER_MODE` | — | "workflow" or "atomic" (auto-detected) |

## Output Format

1. **Task Parameters** — trigger mode, recruitment mode, keyword, URL source, site count
2. **Matched Jobs** — title contains keyword (company | title | link)
3. **Unmatched Jobs** — title does NOT contain keyword (company | title | link)
4. **Notes** — site-specific issues + error handling tips

## Prerequisites

```bash
# One-time install
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # verify
```

## File Structure

```
targeted-url-search/
├── README.md                     # This file
├── SKILL.md                      # Main skill (dual-mode trigger + validation + 5-step workflow)
└── references/
    ├── mode-detection.md         # Trigger word patterns + input extraction rules
    ├── site-patterns.md          # Site adaptation (Feishu/INTSIG/Generic)
    └── report-template.md       # 4-section report template (with dual-mode examples)
```

## Supported Site Types

| Site | URL Pattern | Checkbox | Search Box | Job Links |
|------|------------|----------|------------|-----------|
| Feishu Recruiting | `*.jobs.feishu.cn` | `.atsx-tree-checkbox` | `input[placeholder*="搜索"]` | `a[href*="position"]` |
| INTSIG/zhiye | `*.zhiye.com` | URL path `/campus/` or `/social/` | `input[placeholder*="搜索"]` | `[class*="JobTitle"]` |
| Generic | - | `input[type="checkbox"]` + `<label>` | `input[type="text/search"]` | `a[href*="position/detail"]` |

## Key Design Decisions

- **Dual-mode trigger**: Workflow (batch from JSON) vs Atomic (single/few direct URLs)
- **Input validation**: Required fields checked before execution; re-asks if missing
- **Headless mode only**: Uses `browser-use open <url>` (zero browser interaction)
- **CLI commands over Python harness**: `browser-use input/click/state` instead of `fill_input()/js()`
- **First page only**: No scrolling, no pagination
- **Text state over screenshots**: `browser-use state` (low token cost)
- **Single eval queries**: Merge multiple JS queries into one call

## Performance

| Metric | Without Skill | With Skill |
|--------|--------------|------------|
| Steps | 57 | 12-15 |
| Time | ~34 min | ~5-8 min |
| Tokens | ~45K | ~8-12K |
| User interactions | 3 | 0 (inputs complete) / 1-2 (need to collect) |

## License

MIT

