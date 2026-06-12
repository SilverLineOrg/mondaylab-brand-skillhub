---
name: article-heading-structure
description: Normalize and polish Chinese article or WeChat public-account Markdown heading hierarchy. Use when Codex is asked to 整理标题层级, 优化文章标题, 统一 Markdown 标题, format headings for 星期一研究室/MondayLab style, convert an article to long-form/short-form/only-second heading style, add coherent emoji to first-level headings, or make Chinese outline levels visually comfortable without rewriting the article.
---

# Article Heading Structure

## Core Rule

Before editing headings, ask the user which hierarchy type to use unless they already specified one:

- Long-form: 1-4 levels
- Short-form: 1-2 levels
- Only Second: only `##` headings

After the user chooses, apply the matching system strictly. Optimize heading levels, numbering, and visual rhythm. Preserve the article's meaning and body text unless the user asks for broader rewriting.

## Workflow

1. Inspect the article structure: identify preface/background, main chapters, modules, submodules, reference material, and ending notes.
2. Select the hierarchy type from the user's choice. If no choice is present, ask one concise question and stop.
3. Normalize Markdown heading syntax, Chinese numbering, spacing, and emoji according to the selected type.
4. Keep heading levels logically nested. Do not skip levels in Long-form mode.
5. Ensure the final outline is scannable: similar sections should have similar heading patterns, and headings at the same level should have similar granularity.
6. Return the optimized article or, if the article is long and the user asked for review only, return a before/after heading outline plus concrete edits.

## Long-Form Type

Use for long articles with chapters, modules, and detailed submodules.

| Level | Markdown | Numbering | Example | Usage |
| --- | --- | --- | --- | --- |
| First-level | `#` | `一、二、三` | `# 一、函数基础入门` | Chapter title |
| Second-level | `##` | `1、2、3` | `## 1、常用函数介绍` | Major module |
| Third-level | `###` | `(1) (2) (3)` | `### (1) 文本函数` | Submodule; use Chinese parentheses |
| Fourth-level | `####` | `①②③` | `#### ① LEFT 函数` | Use sparingly for detailed points |

Additional long-form rules:

- If the article has background context, make it a standalone first-level section named `# 前言`.
- First-level headings must follow `# 一、{emoji}{heading}` when using emoji.
- Emoji must form a coherent series: use the same semantic family or closely related imagery across all first-level headings.
- If the topic has an obvious visual metaphor, use that metaphor consistently. For example, landscape-themed articles should use landscape-related emoji for all first-level headings.
- Put reference material at the end as its own first-level heading: `# 🐣彩蛋 One More Things`.
- Use fourth-level headings only when the section is dense enough to justify one more layer.

## Short-Form Type

Use for medium or short articles that need structure but not deep nesting.

| Level | Markdown | Numbering | Example | Usage |
| --- | --- | --- | --- | --- |
| First-level | `#` | `一、二、三` | `# 一、函数基础入门` | Chapter title |
| Second-level | `##` | `1、2、3` | `## 1、常用函数介绍` | Major module |

Short-form rules:

- Do not create `###` or `####` headings.
- Fold minor subpoints into paragraphs, ordered lists, or bold lead-ins under the nearest `##`.
- Use first-level emoji only when it improves visual rhythm; if used, keep the same coherent-series rule as Long-form.

## Only Second Type

Use when the user wants a flat, lightweight structure.

- Use only Markdown second-level headings: `##`.
- Use Chinese parenthesized numbering: `(1) (2) (3)`.
- Example: `## (1) 文本函数`
- Do not use `#`, `###`, or `####`.
- Keep every heading at comparable scope. Merge overly tiny sections into body paragraphs.

## Emoji Guidance

Use emoji only for first-level headings unless the user asks otherwise.

Choose emoji by semantic series:

- Landscape or journey topics: mountain, road, compass, sunrise, map, river.
- Tools or methods topics: toolbox, wrench, hammer, gear, magnifier, ruler.
- Learning or knowledge topics: book, lamp, seedling, telescope, puzzle, graduation cap.
- Business or growth topics: chart, rocket, target, seedling, storefront, briefcase.
- Review or retrospective topics: hourglass, calendar, archive, memo, lens, checkpoint.

Avoid random emoji mixing. Do not use emoji that changes the tone into cute, comic, or overly casual unless the source article already has that style.

## Output Standards

- Maintain valid Markdown.
- Use Chinese punctuation in numbering: `一、` and `1、`.
- Keep a space after Markdown heading marks: `# 一、标题`, not `#一、标题`.
- Do not add a table of contents unless the user asks.
- Do not invent new sections unless they are needed to repair the hierarchy.
- Do not rewrite body copy for style unless explicitly requested.
