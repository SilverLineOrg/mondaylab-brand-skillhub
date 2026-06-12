#!/usr/bin/env python3
"""Render MondayLab 信息美学家 Markdown into WeChat-ready HTML."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


BLUE = "#0816f1"
TEXT = "#111111"
BODY_TEXT = "#4a4a4a"
MUTED = "#888888"
BORDER = "rgba(204, 204, 204, 0.45)"
FONT_STACK = "Optima, 'Microsoft YaHei', PingFangSC-Regular, 'PingFang SC', serif"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"`([^`]+)`", r'<code style="background:#f3f4f6;border-radius:4px;padding:2px 5px;font-size:0.92em;color:#111;">\1</code>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="color:#000;font-weight:bold;">\1</strong>', text)
    text = re.sub(r"==(.+?)==", rf'<span style="display:inline-block;background:{BLUE};color:#fff;border-radius:999px;padding:0 8px;line-height:1.08;">\1</span>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" style="color:#1a56db;text-decoration:none;">\1</a>', text)
    return text


def visual_len(text: str) -> int:
    text = re.sub(r"==(.+?)==", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"[，,。！？!?、\s|｜]", "", text)
    return len(text)


def split_h2_title(title: str) -> list[str]:
    title = title.strip()
    if "｜" in title or "|" in title:
        return [part.strip() for part in re.split(r"[｜|]", title) if part.strip()]

    if visual_len(title) <= 12:
        return [title]

    comma_match = re.search(r"[，,]", title)
    if comma_match:
        before = title[: comma_match.start()].strip()
        after = title[comma_match.end() :].strip()
        if before and after:
            return [before, after]

    highlight_match = re.search(r"==.+?==", title)
    if highlight_match and highlight_match.start() >= 3:
        before = title[: highlight_match.start()].strip()
        after = title[highlight_match.start() :].strip()
        if before and after:
            return [before, after]

    target = visual_len(title) // 2
    count = 0
    split_at = None
    in_marker = False
    i = 0
    while i < len(title):
        if title.startswith("==", i):
            in_marker = not in_marker
            i += 2
            continue
        if not in_marker and title[i].strip():
            count += 1
        if count >= target and not in_marker:
            split_at = i + 1
            break
        i += 1
    if split_at and split_at < len(title):
        return [title[:split_at].strip(), title[split_at:].strip()]
    return [title]


def h2_highlight(text: str) -> str:
    chars = []
    for char in text:
        if char.isspace():
            chars.append(esc(char))
            continue
        chars.append(
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:1.18em;height:1.18em;margin:0 0.035em;border-radius:999px;'
            f'background:{BLUE};color:#fff;line-height:1;font-size:0.86em;font-weight:900;">{esc(char)}</span>'
        )
    return (
        '<span style="display:inline-flex;align-items:center;white-space:nowrap;'
        'vertical-align:baseline;margin:0 4px;">'
        + "".join(chars)
        + "</span>"
    )


def h2_inline(text: str) -> str:
    parts = []
    pos = 0
    for match in re.finditer(r"==(.+?)==", text):
        parts.append(inline(text[pos : match.start()]))
        parts.append(h2_highlight(match.group(1)))
        pos = match.end()
    parts.append(inline(text[pos:]))
    return "".join(parts)


def split_section_title(text: str) -> tuple[str | None, str]:
    match = re.match(r"^\s*[（(]\s*(\d+)\s*[）)]\s*(.+?)\s*$", text)
    if match:
        return match.group(1), match.group(2)
    match = re.match(r"^\s*(\d+)[、.]\s*(.+?)\s*$", text)
    if match:
        return match.group(1), match.group(2)
    return None, text.strip()


def render_h1(text: str) -> str:
    return (
        '<h1 style="font-size:22px;line-height:1.45;font-weight:800;'
        'letter-spacing:0;margin:0 0 30px;color:#111;text-align:left;">'
        f"{inline(text)}</h1>"
    )


def render_h2(text: str) -> str:
    number, title = split_section_title(text)
    index = (
        f'<span style="font-family:\'Source Han Sans SC\',\'Noto Sans CJK SC\',\'思源黑体\',sans-serif;font-weight:200;">(</span>'
        f'<span style="font-family:\'Source Han Sans SC\',\'Noto Sans CJK SC\',\'思源黑体\',sans-serif;font-weight:400;">{esc(number)}</span>'
        f'<span style="font-family:\'Source Han Sans SC\',\'Noto Sans CJK SC\',\'思源黑体\',sans-serif;font-weight:200;">)</span>'
        if number
        else ""
    )
    title_lines = "".join(
        f'<span style="display:block;">{h2_inline(line)}</span>'
        for line in split_h2_title(title)
    )
    return f"""
<section style="margin:82px 0 38px;padding:0;">
  <div style="display:flex;align-items:flex-start;gap:24px;margin:0;">
    <div style="font-size:64px;line-height:1.2;color:{BLUE};letter-spacing:-8px;white-space:nowrap;">{index}</div>
    <div style="padding-top:5px;">
      <div style="font-size:32px;line-height:1.28;font-weight:900;color:{TEXT};letter-spacing:0;">{title_lines}</div>
      <div style="font-size:18px;line-height:1.4;font-weight:800;color:{TEXT};margin-top:16px;letter-spacing:0;">信息美学家Weekly &gt;&gt;&gt;</div>
    </div>
  </div>
</section>""".strip()


def render_h3(text: str) -> str:
    return (
        '<div style="text-align:center;margin:46px 0 18px;">'
        '<span style="display:inline-block;background:#050505;color:#fff;'
        'font-size:15px;line-height:1.35;font-weight:800;padding:6px 14px;'
        'border-radius:0;">'
        f"{inline(text)}</span></div>"
    )


def render_h4(text: str) -> str:
    return (
        '<p style="font-size:16px;line-height:1.8em;font-weight:bold;'
        'margin:0;padding:24px 0 8px;color:#000;text-align:left;letter-spacing:0.02em;">'
        f"{inline(text)}</p>"
    )


def render_paragraph(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines).strip()
    if not text:
        return ""
    if re.fullmatch(r"【📷截图：.+?】", text):
        return (
            '<div style="margin:14px 0 10px;padding:14px 16px;background:#f7f7f7;'
            f'border:1px dashed #cfcfcf;color:{MUTED};font-size:14px;line-height:1.7;border-radius:4px;">'
            f"{esc(text)}</div>"
        )
    image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", text)
    if image:
        alt, src = image.group(1), image.group(2)
        caption = (
            f'<figcaption style="color:{MUTED};font-size:14px;line-height:1.5em;'
            f'letter-spacing:0;text-align:center;font-weight:normal;margin:7px 0 0;padding:0;">{esc(alt)}</figcaption>'
            if alt else ""
        )
        return (
            '<figure style="margin:16px 0 14px;padding:0;display:flex;'
            'flex-direction:column;justify-content:center;align-items:center;text-align:center;">'
            f'<img src="{esc(src)}" alt="{esc(alt)}" style="display:block;margin:0 auto;'
            'width:100%;max-width:100%;height:auto;border:none;border-radius:4px;object-fit:fill;'
            'box-shadow:rgba(170,170,170,0.5) 0px 0px 6px 0px;" />'
            f"{caption}"
            '</figure>'
        )
    return (
        f'<p style="color:{BODY_TEXT};font-size:16px;line-height:1.8em;letter-spacing:0.02em;'
        'text-align:left;text-indent:0;margin:0;padding:20px 0 8px;">'
        f"{inline(text)}</p>"
    )


def render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    body = []
    for item in items:
        body.append(f'<li style="margin:5px 0;color:#010101;font-size:16px;line-height:1.8em;letter-spacing:0;text-align:left;font-weight:normal;">{inline(item)}</li>')
    return (
        f'<{tag} style="list-style-type:{"decimal" if ordered else "disc"};'
        'margin:8px 0;padding:0 0 0 25px;color:#000;">'
        + "\n".join(body)
        + f"</{tag}>"
    )


def parse_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def render_table(lines: list[str]) -> str:
    rows = [parse_table_row(line) for line in lines if line.strip()]
    rows = [row for row in rows if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)]
    if not rows:
        return ""
    out = [
        '<section style="margin:12px 0 10px;padding:0;overflow-x:auto;">'
        '<table style="display:table;border-collapse:collapse;width:100%;'
        'font-size:14px;line-height:1.5em;color:#000;text-align:left;">'
    ]
    for ridx, row in enumerate(rows):
        out.append("<tr>")
        for cell in row:
            tag = "th" if ridx == 0 else "td"
            bg = "rgb(240,240,240)" if ridx == 0 else ("rgb(248,248,248)" if ridx % 2 == 0 else "#ffffff")
            weight = "bold" if ridx == 0 else "normal"
            out.append(
                f'<{tag} style="border:1px solid {BORDER};background:{bg};'
                f'font-weight:{weight};padding:6px 10px;text-align:left;vertical-align:top;min-width:85px;">'
                f"{inline(cell)}</{tag}>"
            )
        out.append("</tr>")
    out.append("</table></section>")
    return "\n".join(out)


def render_blockquote(lines: list[str]) -> str:
    body = "<br/>".join(inline(line.lstrip("> ").strip()) for line in lines)
    return (
        '<blockquote style="margin:18px 0 10px;padding:12px 16px;border-left:4px solid '
        f'{BLUE};background:#f7f8ff;color:#333;font-size:15px;line-height:1.8em;letter-spacing:0.02em;">'
        f"{body}</blockquote>"
    )


def render_markdown(md: str, title: str | None = None) -> str:
    lines = md.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []
    table_lines: list[str] = []
    quote_lines: list[str] = []

    def flush_all() -> None:
        nonlocal paragraph, list_items, ordered_items, table_lines, quote_lines
        if paragraph:
            blocks.append(render_paragraph(paragraph))
            paragraph = []
        if list_items:
            blocks.append(render_list(list_items))
            list_items = []
        if ordered_items:
            blocks.append(render_list(ordered_items, ordered=True))
            ordered_items = []
        if table_lines:
            blocks.append(render_table(table_lines))
            table_lines = []
        if quote_lines:
            blocks.append(render_blockquote(quote_lines))
            quote_lines = []

    inferred_title = title
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_all()
            continue
        if line.startswith("|") and line.endswith("|"):
            if paragraph or list_items or ordered_items or quote_lines:
                flush_all()
            table_lines.append(line)
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_all()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and inferred_title is None:
                inferred_title = text
            elif level == 1:
                blocks.append(render_h1(text))
            elif level == 2:
                blocks.append(render_h2(text))
            elif level == 3:
                blocks.append(render_h3(text))
            else:
                blocks.append(render_h4(text))
            continue
        unordered = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered:
            if paragraph or table_lines or ordered_items or quote_lines:
                flush_all()
            list_items.append(unordered.group(1))
            continue
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if ordered:
            if paragraph or table_lines or list_items or quote_lines:
                flush_all()
            ordered_items.append(ordered.group(1))
            continue
        if line.startswith(">"):
            if paragraph or table_lines or list_items or ordered_items:
                flush_all()
            quote_lines.append(line)
            continue
        paragraph.append(line)

    flush_all()
    article_title = inferred_title or "信息美学家"
    content = "\n\n".join(block for block in blocks if block)
    return build_html(article_title, content)


def build_html(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
</head>
<body style="margin:0;background:#ffffff;color:#111;font-family:{FONT_STACK};">
  <section id="nice" data-tool="mondaylab-information-aesthetic-wechat-layout" style="max-width:677px;margin:0 auto;padding:28px 24px 56px;background:rgba(0,0,0,0);width:auto;font-family:{FONT_STACK};font-size:16px;color:#000;line-height:1.5em;word-spacing:0;letter-spacing:0;word-break:break-word;overflow-wrap:break-word;text-align:left;box-sizing:border-box;">
    {render_h1(title)}
    {content}
  </section>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument("--output", required=True, help="Output HTML file")
    parser.add_argument("--title", default=None, help="Override article title")
    args = parser.parse_args()

    md = Path(args.input).read_text(encoding="utf-8")
    html_text = render_markdown(md, args.title)
    Path(args.output).write_text(html_text, encoding="utf-8")


if __name__ == "__main__":
    main()
