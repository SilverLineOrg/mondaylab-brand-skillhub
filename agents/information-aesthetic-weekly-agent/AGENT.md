# information-aesthetic-weekly-agent

这个 Agent 是「信息美学家 Weekly」的外层生产线。它不作为 skill 被其他流程引用，而是负责调用仓库内外的 skill，把每周固定动作串起来。

## 调用的能力

- `mondaylab-information-aesthetic-column`：校准栏目语气、结构和内容边界。
- `mondaylab-information-aesthetic-wechat-layout`：把 Markdown 渲染成公众号 HTML。
- `make-it-pop-poster`：公共杂志级栏头图 skill，默认位于 `../magazine-visuals/skills/make-it-pop-poster`。

## 每周流程

1. 每次都用飞书 CLI 从飞书文档重新拉取 Markdown 和 full detail，不使用浏览器页面内容或旧本地缓存作为源数据：

```bash
lark-cli docs +fetch --api-version v2 --doc "<飞书链接>" --doc-format markdown
lark-cli docs +fetch --api-version v2 --doc "<飞书链接>" --detail full
```

2. 清洗飞书导出内容，保留图片链接，并回填正文下划线。
3. 为栏头图单独提炼 poster copy，再按 `make-it-pop-poster` 的杂志级视觉原则生成本期栏头 HTML 和 PNG。
4. 生成星期一研究室关注引导卡 GIF，并插入 Markdown 的 H1 后面；HTML 渲染时会把这张图片提升到文章标题前面，作为公众号关注卡下面的视觉引导。
5. 把栏头 PNG 插入 Markdown 的 H1 后面。
6. 把二级标题渲染成固定 `1080×500` PNG，避免公众号编辑器破坏复杂标题样式。
7. 生成国际化 END 卡 PNG，并追加到 Markdown 末尾；HTML 渲染时不再重复输出内联 END，但会在 END 图下保留独立署名文字。
8. 默认把本期生成的关注卡 GIF、关注卡 PNG 备用图、栏头图、标题图和 END 卡复制到仓库 `assets/information-aesthetic-weekly/{slug}/`，并在 Markdown/HTML 里替换成 GitHub raw HTTPS 地址。
9. 调用 `mondaylab-information-aesthetic-wechat-layout` 生成公众号 HTML。
10. 检查 GitHub 资产、标题图、飞书图片链接。
11. 启动或复用 `8765` 本地预览服务。

## 运行方式

```bash
python3 agents/information-aesthetic-weekly-agent/scripts/run_weekly.py \
  --doc "<飞书链接>" \
  --slug article-013-topic \
  --issue 013
```

常用参数：

- `--doc`：飞书文档或 wiki 链接。
- `--slug`：输出文件名前缀。
- `--issue`：期数，栏头图显示为 `ISSUE 013`。
- `--output-dir`：输出目录，默认仓库根目录。
- `--poster-skill-dir`：公共 `make-it-pop-poster` skill 目录。
- `--skip-masthead`：只重新生成 Markdown 和 HTML。
- `--skip-section-images`：保留二级标题 HTML，不生成标题 PNG。
- `--use-local-assets`：不替换为 GitHub raw 地址，保留本地相对路径。
- `--github-raw-base`：生成资产的 GitHub raw URL 前缀，默认指向当前仓库 `main` 分支。
- `--serve`：生成后启动本地预览服务。

## 标注约定

- `|` 或 `｜`：二级标题视觉折行。
- `==重点==`：指定蓝色强调重点。
- `[结语：]`：只给 agent 看的删除标记，不进入视觉标题。
- 飞书正文下划线：尽量转成 `<u>...</u>` 并交给 HTML 渲染脚本保留。

如果标题没有 `== ==`，由排版 skill 自动选择一个短重点词。

## 正文清洗边界

飞书导出的图片 alt 里可能包含很长的机器描述，例如 `图片展示的是……该图片与上下文……`。这些内容只用于识别图片，不作为公众号可见图片说明。Agent 写 Markdown 前需要把这类自动生成的长 alt 清空，避免 HTML 渲染器把它们变成灰色 figcaption。

飞书文档里用户手写的图片描述在 full detail XML 的 `<img caption="...">` 属性里，不在 Markdown 的图片 alt 里。处理图片时必须：

1. 从 `--doc-format markdown` 拿图片链接和正文顺序。
2. 从 `--detail full` 的 `<img caption="...">` 读取真实图片说明。
3. 用真实 `caption` 回填 Markdown 的图片 alt。
4. 如果只有机器生成的长 alt、没有 `caption`，则清空 alt，不显示图片说明。

不要在 agent 的 Markdown 清洗阶段删除标题里的问号、`[结语：]`、`|` 等人工标记；这些只交给公众号排版 skill 在视觉标题渲染时处理。源 Markdown 尽量保留飞书原文。

## 栏头图边界

栏头图是一条独立支线，只把飞书文档的 H1 和开头正文交给 `make-it-pop-poster` 风格系统，不读取公众号排版脚本的上下文。

禁止把这些规则混进栏头图：

- 二级标题 `|` / `｜` 折行规则。
- `==重点==` 蓝色强调字规则。
- H2 自动重点词候选。
- `[结语：]`、问号删除等视觉标题清洗规则。
- 正文 HTML 的字号、编号、蓝底强调样式。

栏头图只产出这几个文案字段：

- `kicker`：H1 里的场景或前提，例如 `AI 生成一堆素材后`。
- `headline_lines`：主标题短行，例如 `怎么整理成` / `好找又好用` / `的视觉资产库？`。
- `highlight`：2-6 字强重点，优先选 H1 中最适合做视觉中心的短语。
- `microcopy`：开头正文里最能解释本期价值的一句话。
- `pills`：从 H1 和开头正文里提取的少量标签，只作为海报视觉辅助。

这层提炼只服务栏头图，不反向影响 Markdown 和公众号 HTML。
