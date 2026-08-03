# targeted-url-search

> WorkBuddy Skill: Automated job search on recruitment websites using browser-use CLI.

## What It Does

Given a JSON file containing company URLs, a search keyword, and a recruitment mode (campus/intern/none), this skill automatically:

1. Opens each recruitment website (headless browser, zero user interaction)
2. Checks the appropriate recruitment project checkbox (campus/intern)
3. Types the search keyword and clicks search
4. Extracts job titles and links from the **first page** of results
5. Filters jobs where the keyword is a **contiguous substring** of the title
6. Outputs a concise 4-section report

## Input Parameters

| Parameter | Variable | Type | Description |
|-----------|----------|------|-------------|
| JSON file path | `JSON_FILE` | string | Contains company names and URLs |
| Search keyword | `KEYWORD` | string | e.g. "前端", "后端", "算法", "产品" |
| Recruitment mode | `MODE` | int | 1=campus/full-time, 2=intern/summer, 3=none |

## Output Format

1. **Task Parameters** - mode, keyword, source file
2. **Matched Jobs** - title contains keyword (company | title | link)
3. **Unmatched Jobs** - title does NOT contain keyword (company | title | link)
4. **Notes** - site-specific issues + error handling tips

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
├── README.md              # This file
├── SKILL.md               # Main skill definition (5-step workflow)
└── references/
    ├── site-patterns.md   # Site adaptation patterns (Feishu/INTSIG/Generic)
    └── report-template.md # 4-section report template
```

## Supported Site Types

| Site | URL Pattern | Checkbox | Search Box | Job Links |
|------|------------|----------|------------|-----------|
| Feishu Recruiting | `*.jobs.feishu.cn` | `.atsx-tree-checkbox` | `input[placeholder*="搜索"]` | `a[href*="position"]` |
| INTSIG/zhiye | `*.zhiye.com` | URL path `/campus/` or `/social/` | `input[placeholder*="搜索"]` | `[class*="JobTitle"]` |
| Generic | - | `input[type="checkbox"]` + `<label>` | `input[type="text/search"]` | `a[href*="position/detail"]` |

## Key Design Decisions

- **Headless mode only**: Uses `browser-use open <url>` (zero user interaction, never `connect`)
- **CLI commands over Python harness**: `browser-use input/click/state` instead of `fill_input()/js()`
- **First page only**: No scrolling, no pagination
- **Text state over screenshots**: `browser-use state` (low token cost) instead of `capture_screenshot()`
- **Single eval queries**: Merge multiple JS queries into one `browser-use eval` call

## Performance

| Metric | Without Skill | With Skill |
|--------|--------------|------------|
| Steps | 57 | 12-15 |
| Time | ~34 min | ~5-8 min |
| Tokens | ~45K | ~8-12K |
| User interactions | 3 | 0 |

## License

MIT
