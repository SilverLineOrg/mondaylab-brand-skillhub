#!/usr/bin/env python3
"""Render MondayLab 信息美学家 Markdown into WeChat-ready HTML."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


BLUE = "#1028ff"
TEXT = "#111111"
MUTED = "#666666"
BORDER = "#e8e8e8"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"`([^`]+)`", r'<code style="background:#f3f4f6;border-radius:4px;padding:2px 5px;font-size:0.92em;color:#111;">\1</code>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="font-weight:700;">\1</strong>', text)
    text = re.sub(r"==(.+?)==", rf'<span style="display:inline-block;background:{BLUE};color:#fff;border-radius:999px;padding:0 8px;line-height:1.08;">\1</span>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" style="color:#1a56db;text-decoration:none;">\1</a>', text)
    return text


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
        'letter-spacing:0;margin:0 0 28px;color:#111;text-align:left;">'
        f"{inline(text)}</h1>"
    )


def render_h2(text: str) -> str:
    number, title = split_section_title(text)
    index = f"({number})" if number else ""
    return f"""
<section style="margin:72px 0 34px;">
  <div style="display:flex;align-items:flex-start;gap:18px;margin-bottom:10px;">
    <div style="font-size:66px;line-height:0.95;font-weight:500;color:{BLUE};font-family:Arial, Helvetica, sans-serif;white-space:nowrap;">{esc(index)}</div>
    <div style="padding-top:6px;">
      <div style="font-size:34px;line-height:1.12;font-weight:900;color:{TEXT};letter-spacing:0;">{inline(title)}</div>
      <div style="font-size:18px;line-height:1.4;font-weight:800;color:{TEXT};margin-top:14px;">信息美学家Weekly &gt;&gt;&gt;</div>
    </div>
  </div>
</section>""".strip()


def render_h3(text: str) -> str:
    return (
        '<div style="text-align:center;margin:42px 0 22px;">'
        '<span style="display:inline-block;background:#050505;color:#fff;'
        'font-size:15px;line-height:1.35;font-weight:800;padding:6px 14px;'
        'border-radius:0;">'
        f"{inline(text)}</span></div>"
    )


def render_h4(text: str) -> str:
    return (
        '<p style="font-size:15px;line-height:1.85;font-weight:800;'
        'margin:26px 0 10px;color:#111;text-align:left;">'
        f"{inline(text)}</p>"
    )


def render_paragraph(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines).strip()
    if not text:
        return ""
    if re.fullmatch(r"【📷截图：.+?】", text):
        return (
            '<div style="margin:22px 0;padding:14px 16px;background:#f7f7f7;'
            f'border:1px dashed #cfcfcf;color:{MUTED};font-size:14px;line-height:1.7;">'
            f"{esc(text)}</div>"
        )
    image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", text)
    if image:
        alt, src = image.group(1), image.group(2)
        return (
            '<figure style="margin:24px 0;text-align:center;">'
            f'<img src="{esc(src)}" alt="{esc(alt)}" style="display:block;width:100%;max-width:100%;height:auto;border-radius:0;margin:0 auto;" />'
            f'<figcaption style="font-size:12px;line-height:1.6;color:#999;margin-top:8px;">{esc(alt)}</figcaption>'
            '</figure>'
        )
    return (
        '<p style="font-size:15px;line-height:1.95;color:#222;margin:16px 0;'
        'letter-spacing:0;text-align:left;">'
        f"{inline(text)}</p>"
    )


def render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    body = []
    for item in items:
        body.append(f'<li style="margin:6px 0;line-height:1.85;">{inline(item)}</li>')
    return (
        f'<{tag} style="font-size:15px;line-height:1.85;color:#222;'
        'padding-left:1.3em;margin:14px 0;">'
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
        '<table style="border-collapse:collapse;width:100%;margin:22px 0;'
        'font-size:14px;line-height:1.7;color:#222;">'
    ]
    for ridx, row in enumerate(rows):
        out.append("<tr>")
        for cell in row:
            tag = "th" if ridx == 0 else "td"
            bg = "#f4f4f4" if ridx == 0 else "#ffffff"
            weight = "700" if ridx == 0 else "400"
            out.append(
                f'<{tag} style="border:1px solid {BORDER};background:{bg};'
                f'font-weight:{weight};padding:8px 10px;text-align:left;vertical-align:top;">'
                f"{inline(cell)}</{tag}>"
            )
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def render_blockquote(lines: list[str]) -> str:
    body = "<br/>".join(inline(line.lstrip("> ").strip()) for line in lines)
    return (
        '<blockquote style="margin:18px 0;padding:12px 16px;border-left:4px solid '
        f'{BLUE};background:#f7f8ff;color:#333;font-size:14px;line-height:1.85;">'
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
<body style="margin:0;background:#ffffff;color:#111;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;">
  <main style="max-width:677px;margin:0 auto;padding:28px 24px 56px;box-sizing:border-box;">
    {render_h1(title)}
    {content}
  </main>
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
