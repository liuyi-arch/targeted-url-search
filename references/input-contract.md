# 输入契约

本文件定义 `targeted-url-search` 的输入字段、默认值、JSON 字段映射和企业名推断规则。

## 一、标准输入模型

| 参数 | 变量名 | 类型 | 必填 | 来源 |
|------|--------|------|------|------|
| URL 列表 | `URL_LIST` | `array<string>` | 是 | 工作流来自 JSON；原子模式来自用户输入 |
| 企业名列表 | `COMPANY_LIST` | `array<string>` | 否 | 工作流来自 JSON；原子模式可推断 |
| 搜索关键词 | `KEYWORD` | `string` | 是 | 用户输入或从提示词提取 |
| 招聘项目模式 | `PROJECT_MODE` | `string` | 否 | 由补充信息推导 |
| 补充信息 | `SUPPLEMENTARY` | `string` | 否 | 用户输入 |
| 触发模式 | `TRIGGER_MODE` | `string` | 是 | `workflow` 或 `atomic` |
| 排除序号 | `EXCLUDE_INDICES` | `array<int>` | 否 | 工作流模式专用 |

## 二、必填校验

以下字段必须存在：

- `URL_LIST` 或能构建出 `URL_LIST` 的 `JSON_FILE`
- `KEYWORD`

以下字段可缺省：

- `COMPANY_LIST`
- `SUPPLEMENTARY`
- `EXCLUDE_INDICES`

## 三、PROJECT_MODE 映射

`PROJECT_MODE` 不再使用数字枚举，统一使用语义枚举：

| 关键词 | PROJECT_MODE | 说明 |
|--------|--------------|------|
| 校招、校园招聘、秋招、春招、应届、全职、正式 | `campus` | 校招或正式岗位 |
| 实习、日常实习、暑假实习、暑期实习、日常 | `intern` | 实习岗位 |
| 社招、社会招聘 | `social` | 社会招聘岗位 |
| 未提及或不确定 | `none` | 不做项目筛选 |

说明：

- `campus` 与 `social` 不再合并，避免站点路径和页面控件歧义
- 如果用户同时表达多个类型，优先保留最明确的一类；需要多模式并查时由后续版本扩展

## 四、工作流模式 JSON 输入

### 推荐输入结构

```json
{
  "records": [
    {
      "招聘企业": "示例企业",
      "投递链接": "https://example.com/jobs"
    }
  ]
}
```

### 字段别名映射

读取工作流 JSON 时，按以下优先级提取：

- 企业名字段：
  - `招聘企业`
  - `company`
  - `company_name`
  - `name`
- URL 字段：
  - `投递链接`
  - `url`
  - `link`
  - `job_url`

提取策略：

1. 若存在 `records[]`，优先遍历 `records`
2. 若不存在 `records[]`，可回退到顶层数组
3. 若字段名不固定，允许用通用 URL 扫描提取链接，并用域名兜底命名

### 排除序号

`EXCLUDE_INDICES` 仅作用于最终待执行列表，不修改源 JSON 内容。

## 五、原子模式输入

### URL_LIST

- 从用户提示词中直接提取
- 支持单个或多个 URL
- 若用户输入的是站点名而不是 URL，不自动猜测 URL

### COMPANY_LIST

若用户未提供企业名，则按以下顺序推断：

1. 站点注册表中的 `display_name`
2. URL 子域名推断
3. 根域名作为站点标识

示例：

- `dexmal-inc.jobs.feishu.cn` -> `dexmal-inc`
- `intsig.zhiye.com` -> `intsig`
- 无法识别时直接使用完整域名

## 六、构建后的运行输入

主流程收到的最终输入应满足：

```text
URL_LIST.length >= 1
KEYWORD is not empty
PROJECT_MODE in {campus, intern, social, none}
TRIGGER_MODE in {workflow, atomic}
```

## 七、维护要求

- 新增输入字段时，必须先更新本文件，再更新 `SKILL.md`
- 调整字段别名时，只改本文件，不要回写到多个文档
- 上游 JSON 契约变化时，优先扩充别名映射，不要直接写死单一字段名
