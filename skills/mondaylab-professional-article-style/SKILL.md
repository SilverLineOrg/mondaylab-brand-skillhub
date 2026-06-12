---
name: mondaylab-professional-article-style
description: Use when writing, rewriting, or reviewing 星期一研究室 / MondayLab professional articles, especially AI product scenario reviews, tool testing articles, public-account drafts, YouMind-style writing prompts, scene-based evaluations, prompt examples, screenshot notes, reference lists, and articles that need MondayLab's warm but professional Chinese voice.
---

# MondayLab Professional Article Style

Use this skill to keep 星期一研究室 professional articles consistent in voice, structure, and reader value.

This skill controls writing style. For topic direction, use `mondaylab-content-direction`. For Markdown heading hierarchy, use `article-heading-structure`.

## Writing Voice

Use a warm, conversational, public-account style:

- Use natural address terms such as “我们”, “小编”, “小伙伴”.
- Keep the tone relaxed and approachable, not stiff or academic.
- Use internet-native expressions and mild emotional phrasing when useful.
- Use transition phrases such as “我们”, “大家”, “值得一提的是”, “细心的小伙伴已经发现”等, adjusted to the scene.
- Stay professional even when conversational. Do not become cute, exaggerated, or salesy.

## Content Organization

After introducing a concept or method, immediately connect it to a concrete operation, example, screenshot, prompt, or result.

Required patterns:

- If a feature is demonstrated, include a concrete screenshot or result display when possible.
- If a screenshot is needed but not available, mark it clearly as `【截图图：{说明内容}】`.
- Use tables to organize complex information.
- Provide accessible links when referencing tools, products, docs, templates, or demos.
- Put references at the end when external materials are used.

## Value Output

Do not only introduce tool features. Each article should explain the practical scene and why the scene matters.

For scene reviews:

- Describe the scene and its goal in detail.
- Explain why this scene helps a user, team, or industry improve efficiency.
- Provide a concrete prompt example when testing AI output.
- Keep prompt examples roughly 100-300 Chinese characters unless the user requests otherwise.
- After each scene test, explain the result: what worked, what failed, and what the reader can learn.
- Titles should start from macro observation or market/user interest, not only from product functions.

## Article Format

Use this default structure for professional scenario-review articles:

1. Background: describe the test background, user problem, or market observation.
2. Main body: write the article with structured sections and real examples.
3. Ending: summarize the value and raise the industry/workflow meaning.

Heading style:

- First-level headings: `# 一、{emoji}{heading}`
- Second-level headings: `## 1、{heading}`
- Third-level headings: `### (1) {heading}`
- Fourth-level headings: `#### ① {heading}`

Use fourth-level headings sparingly. Avoid making the hierarchy too deep.

First-level heading emoji should not repeat in the same article. Avoid overly casual emoji such as hearts, clapping hands, or medal-style decorations unless the source article already uses that tone.

## Scene-Test Inputs

Before writing from scratch, ask for missing essentials if they are not provided:

- What AI tool or product is being tested?
- Which specific feature or scene should be tested?
- What should readers understand after reading?
- Desired length:
  - first tier: 1000-2000 Chinese characters
  - second tier: 2000-3000 Chinese characters
  - third tier: 3000-4000 Chinese characters

If enough context is already present, do not ask; proceed with reasonable assumptions.

## AI Tone Removal

Avoid these AI-ish expressions:

- “不是……而是……”
- “这就是我说的……”
- “这不是……”
- “这就是……”
- “这里的终极解法是……”
- “孤岛”
- “孤立”
- “给你最直接、最不绕弯……”

Also avoid repetitive conclusion-heavy phrasing. Prefer concrete observations, examples, and practical judgments.

## Output Standards

- Maintain valid Markdown unless writing directly into Feishu XML.
- Keep body copy readable and human.
- Use examples and scenes before abstract conclusions.
- Do not write as a generic AI product review account.
- Do not invent screenshots, links, or references. If missing, mark placeholders clearly.
- When paired with `mondaylab-content-direction`, follow the content north star: explain how the tool enters a real workflow and becomes a final deliverable.
