# 星期一研究室品牌 SkillHub

这个仓库用于沉淀星期一研究室 / MondayLab 的品牌导向 Skill。

它的目标是把品牌战略、商业化思考、内容方向、企业培训产品等资产，转化成可复用的 AI Agent 指令资产。后续写文章、做选题、设计产品、打磨企业方案时，都可以用这些 Skill 来校准方向。

## 已有 Skill

- `mondaylab-brand-strategy`：用于校准品牌定位、商业化边界、产品结构、平台策略。
- `mondaylab-content-direction`：用于公众号、小红书、X 等公域内容的选题规划、文章纠偏、CTA 设计、内容资产沉淀。
- `mondaylab-enterprise-training`：用于 B 端企业培训、工作坊、诊断咨询、企业产品设计。
- `article-heading-structure`：用于统一中文文章、公众号正文、星期一研究室长文的 Markdown 标题层级、编号和视觉节奏。
- `mondaylab-professional-article-style`：用于统一星期一研究室场景测评、产品测试、专业公众号文章的语言风格、内容组织和写法禁区。
- `mondaylab-ai-product-reviewer`：用于撰写、改写和评审 AI 产品测评、场景测评、横向对比、工具测试类文章。

## 写文章时怎么引用

如果是日常文章选题、公众号 / 小红书 / X 文案、文章结构纠偏，主要引用：

```text
mondaylab-content-direction
```

它负责判断一篇内容是否符合星期一研究室接下来的内容打法：AI Native、信息美学、最终产物、场景工作流、课程转化、平台无关能力。

如果文章涉及更底层的品牌定位、商业化边界、飞书是不是主线、C 端 / B 端产品结构，需要同时引用：

```text
mondaylab-brand-strategy
```

如果文章是企业培训、B 端案例、企业工作流、管理中枢相关内容，需要再加：

```text
mondaylab-enterprise-training
```

最常用的文章纠偏提示词：

```text
请基于 mondaylab-content-direction 和 mondaylab-brand-strategy，帮我判断这篇文章是否符合星期一研究室的内容方向，并给出改写建议。
```

如果已经确定文章方向，只需要整理标题层级、编号和阅读节奏，可以引用：

```text
article-heading-structure
```

常用标题整理提示词：

```text
请使用 article-heading-structure，按长篇类型整理这篇文章的标题层级，只调整标题结构和编号，不重写正文。
```

如果文章方向已经确定，需要统一“星期一研究室”的专业写作风格，尤其是 AI 产品场景测评、测试中文章、工具实测文章，可以引用：

```text
mondaylab-professional-article-style
```

常用风格润色提示词：

```text
请使用 mondaylab-professional-article-style，帮我把这篇文章改成星期一研究室的专业场景测评风格，保留核心观点，但优化语言风格、案例组织、截图提示和价值输出。
```

如果要写 AI 产品深度测评、场景测评、横向对比、工具测试文章，可以引用：

```text
mondaylab-ai-product-reviewer
```

常用测评写作提示词：

```text
请使用 mondaylab-ai-product-reviewer，帮我把这个 AI 产品测评选题整理成一篇星期一研究室风格的公众号文章，要求有真实场景、测试过程、截图提示、Prompt 示例、结果判断和 reference。
```

## 使用规则

- `SKILL.md` 保持简洁，写清楚触发场景、判断标准和输出要求。
- 长篇战略文档放在 `references/` 里，不要全部塞进 `SKILL.md`。
- 后续文章、选题、课程材料、企业方案、平台合作思路，都优先用这里的 Skill 做方向校准。
- 新增品牌相关 Skill 时，统一放进这个仓库，不要散落在本地其他目录。

## 来源文档

第一批 Skill 来自以下 3 份战略文档：

- `星期一研究室商业化思考.md`
- `星期一研究室文章商业化优化分析.md`
- `星期一研究室企业培训产品设计.md`
