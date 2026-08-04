# targeted-url-search

> WorkBuddy Skill: Automated job search on recruitment websites using browser-use CLI v3.0. Dual-mode trigger with input validation.

## What It Does

Given a JSON file (workflow mode) or direct URLs (atomic mode), a search keyword, and optional recruitment mode, this skill automatically:

1. **Detects trigger mode** from user's prompt (workflow vs atomic)
2. **Collects & validates** required inputs (URL + keyword) — asks user if missing
3. Opens each recruitment website via browser-use v3.0 Python pipe syntax
4. Checks the appropriate recruitment project checkbox (campus/intern)
5. Types the search keyword and clicks search — **mandatory step, never skipped**
6. Extracts job titles and links from the **first page** of results
7. Filters jobs where the keyword is a **contiguous substring** of the title
8. Outputs a concise 3-section report

## Architecture (v5.0)

```
targeted-url-search/
├── SKILL.md                        # Core orchestration (~130 lines)
├── references/
│   ├── mode-detection.md           # Trigger word patterns + input extraction rules
│   ├── execution-flow.md           # Detailed Step 0-5 with all bash/JS code
│   ├── site-patterns.md            # Site adaptation (Feishu/INTSIG/PDD/Generic)
│   ├── report-template.md          # 3-section report template + examples
│   ├── error-handling.md           # Troubleshooting & error recovery
│   └── changelog.md                # Version history
```

**Design principle**: SKILL.md is the orchestration layer (what to do + where to find details). The `references/` directory is the implementation layer (how to do it). Each piece of information lives in exactly one place.

## Dual-Mode Trigger

### Workflow Mode
- **Trigger**: User mentions "targeted-url-search"
- **URL source**: JSON file from previous node (company names + URLs)
- **Input collection**: Asks "全量检索 or 选择性检索?" + keyword + supplementary info

### Atomic Mode
- **Trigger**: User prompt contains "search specific content on specific website" semantics
- **URL source**: User provides URLs directly
- **Input collection**: Prompts for URL, keyword, and optional supplementary info

## Input Parameters

| Parameter | Variable | Required | Description |
|-----------|----------|----------|-------------|
| URL list | `URL_LIST` | Yes | Workflow: from JSON; Atomic: user input |
| Search keyword | `KEYWORD` | Yes | e.g. "前端", "后端", "算法", "产品" |
| Recruitment mode | `MODE` | No | 1=campus, 2=intern, 3=none (default) |
| Trigger mode | `TRIGGER_MODE` | — | "workflow" or "atomic" (auto-detected) |

## Output Format

1. **Task Parameters** — trigger mode, recruitment mode, keyword, URL source, site count
2. **Matched Jobs** — website name + job detail page link
3. **Unmatched Jobs** — website name + search status + description + original site URL

## Supported Site Types

| Site | URL Pattern | Search Box | Search Trigger | Job Links |
|------|------------|------------|----------------|-----------|
| Feishu Recruiting | `*.jobs.feishu.cn` | `input[placeholder*="搜索"]` | Search button | `a[href*="position"]` |
| INTSIG/zhiye | `*.zhiye.com` | `input[placeholder*="搜索"]` | fill + Enter | `[class*="JobTitle"]` |
| PDD Campus | `careers.pddglobalhr.com` | `input#name` | `.page-job-list_searchButton__bYEas` | `[class*="jobList"] a` |
| Generic | - | `input[type="text/search"]` | fill + Enter | `a[href*="position/detail"]` |

## Key Design Decisions

- **browser-use v3.0 Python pipe**: All commands use `browser-use <<'PY' ... PY'` syntax (not deprecated `open/state/click` subcommands)
- **Mandatory search step**: Search is never skipped, even if the default list shows the keyword — SPA sites like PDD hide jobs behind search
- **First page only**: No scrolling, no pagination
- **Empty results = skip**: No fallback strategies (URL params, pagination, scroll-load)
- **Single JS queries**: Merge multiple JS operations into one `js()` call to reduce round-trips
- **Modular structure**: SKILL.md orchestrates; `references/` files contain implementation details

## Prerequisites

```bash
# One-time install
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install browser-use
browser-use install
browser-use doctor  # verify
```

## Performance

| Metric | Without Skill | With Skill (v5.0) |
|--------|--------------|-------------------|
| Steps | 57 | 12-15 (varies by site count) |
| Miss rate | High | Low (mandatory search) |
| Tokens | ~45K | ~8-12K |
| User interactions | 3 | 0-2 |

## License

MIT
