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
BODY_FONT_SIZE = 14
H2_TITLE_FONT_SIZE = 68
H2_TITLE_LINE_HEIGHT = 1.05


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_underline(match: re.Match[str]) -> str:
    content = inline(html.unescape(match.group(1)))
    return (
        '<span style="text-decoration:underline;text-underline-offset:3px;'
        f'text-decoration-thickness:1px;">{content}</span>'
    )


def inline(text: str) -> str:
    text = esc(text)
    text = re.sub(r"&lt;u&gt;(.*?)&lt;/u&gt;", render_underline, text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"`([^`]+)`", r'<code style="background:#f3f4f6;border-radius:4px;padding:2px 5px;font-size:0.92em;color:#111;">\1</code>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="color:#000;font-weight:bold;">\1</strong>', text)
    text = re.sub(r"==(.+?)==", rf'<span style="display:inline-block;background:{BLUE};color:#fff;border-radius:999px;padding:0 8px;line-height:1.08;">\1</span>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" style="color:#1a56db;text-decoration:none;">\1</a>', text)
    return text


def visual_len(text: str) -> int:
    text = re.sub(r"==(.+?)==", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"^\[[^\]]+\]", "", text)
    text = re.sub(r"[，,。！？!?、\s|｜]", "", text)
    return len(text)


def auto_mark_h2_highlight(line: str) -> str:
    if "==" in line:
        return line
    candidates = [
        "轻量素材库",
        "视觉资产库",
        "素材库",
        "画册视图",
        "视觉库",
        "找不到",
        "可复用",
        "可发布",
        "可找",
        "好用",
        "实践",
    ]
    for phrase in candidates:
        if phrase in line:
            return line.replace(phrase, f"=={phrase}==", 1)
    return line


def split_h2_title(title: str) -> list[str]:
    title = title.strip()
    title = re.sub(r"^\[[^\]]+\]\s*", "", title)
    title = re.sub(r"^结语[:：]\s*", "", title)
    title = re.sub(r"\[[^\]]*\]", "", title)
    title = re.sub(r"[?？]", "", title)
    if "｜" in title or "|" in title:
        return [auto_mark_h2_highlight(part.strip()) for part in re.split(r"[｜|]", title) if part.strip()][:2]

    if visual_len(title) <= 12:
        return [auto_mark_h2_highlight(title)]

    comma_match = re.search(r"[，,]", title)
    if comma_match:
        before = title[: comma_match.start()].strip()
        after = title[comma_match.end() :].strip()
        if before and after:
            return [auto_mark_h2_highlight(before), auto_mark_h2_highlight(after)]

    highlight_match = re.search(r"==.+?==", title)
    if highlight_match and highlight_match.start() >= 3:
        before = title[: highlight_match.start()].strip()
        after = title[highlight_match.start() :].strip()
        if before and after:
            return [auto_mark_h2_highlight(before), after]

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
        return [auto_mark_h2_highlight(title[:split_at].strip()), auto_mark_h2_highlight(title[split_at:].strip())]
    return [auto_mark_h2_highlight(title)]


def h2_highlight(text: str) -> str:
    chars = []
    for idx, char in enumerate(text):
        if char.isspace():
            chars.append(esc(char))
            continue
        margin_left = "-0.22em" if idx else "0"
        chars.append(
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'min-width:1.16em;min-height:1.16em;padding:4px;margin-left:{margin_left};border-radius:999px;box-sizing:content-box;'
            f'background:{BLUE};color:#fff;line-height:1;font-size:0.88em;font-weight:900;letter-spacing:0;">{esc(char)}</span>'
        )
    return (
        '<span style="display:inline-flex;align-items:center;white-space:nowrap;'
        'vertical-align:middle;margin:0 0.05em;">'
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
        'letter-spacing:0;margin:0 0 30px;padding:0 16px;color:#111;text-align:left;">'
        f"{inline(text)}</h1>"
    )


def render_motion_styles() -> str:
    return f"""
<style>
@keyframes iaw-line {{
  0% {{ transform: scaleX(0.12); opacity: 0.28; }}
  48% {{ transform: scaleX(1); opacity: 1; }}
  100% {{ transform: scaleX(1); opacity: 0.58; }}
}}
@keyframes iaw-pulse {{
  0%, 100% {{ transform: scale(0.88); opacity: 0.45; }}
  50% {{ transform: scale(1.18); opacity: 1; }}
}}
@keyframes iaw-scan {{
  0% {{ transform: translateX(-42px); opacity: 0; }}
  35% {{ opacity: 0.72; }}
  100% {{ transform: translateX(42px); opacity: 0; }}
}}
</style>""".strip()


def render_opening_block() -> str:
    return f"""
<section data-iaw-opening="true" style="margin:0 16px 44px;padding:34px 0 18px;text-align:center;box-sizing:border-box;">
  <div style="display:inline-block;position:relative;width:100%;max-width:430px;min-height:152px;padding:24px 50px 34px 50px;text-align:left;box-sizing:border-box;background:#fff;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Source Han Sans SC','Noto Sans CJK SC','Microsoft YaHei',Arial,sans-serif;overflow:hidden;">
    <span style="position:absolute;left:14px;top:20px;bottom:8px;width:8px;background:{BLUE};display:block;transform:skewY(-2deg);transform-origin:center center;"></span>
    <span style="position:absolute;left:14px;bottom:8px;width:76px;height:8px;background:{BLUE};display:block;transform:skewX(-18deg);transform-origin:left center;"></span>
    <span style="position:absolute;right:18px;top:14px;width:92px;height:8px;background:{BLUE};display:block;transform:skewX(8deg);transform-origin:right center;animation:iaw-line 5.8s ease-in-out infinite;"></span>
    <span style="position:absolute;right:18px;top:14px;bottom:8px;width:8px;background:{BLUE};display:block;transform:skewY(3deg);transform-origin:center center;"></span>
    <span style="position:absolute;right:18px;bottom:8px;width:118px;height:8px;background:{BLUE};display:block;transform:skewX(5deg);transform-origin:right center;"></span>
    <p style="position:absolute;left:4px;top:56px;margin:0;padding:0;color:#111;font-size:10px;line-height:1;font-weight:900;letter-spacing:0.12em;text-transform:uppercase;writing-mode:vertical-rl;transform:rotate(180deg);font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;">ORIGIN</p>
    <p style="position:absolute;right:1px;top:34px;margin:0;padding:0;color:#111;font-size:9px;line-height:1;font-weight:900;letter-spacing:0.1em;text-transform:uppercase;writing-mode:vertical-rl;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;">ONE SYSTEM</p>
    <div style="position:relative;z-index:1;margin:0;padding:0;">
      <p style="margin:0 0 5px;padding:0;color:#888;font-size:9px;line-height:1;font-weight:900;letter-spacing:0.18em;text-transform:uppercase;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;">FOLLOW US</p>
      <p style="margin:0 0 2px;padding:0;color:#000;font-size:26px;line-height:1;font-weight:900;letter-spacing:0.01em;text-align:left;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;">MONDAYLAB</p>
      <p style="display:inline-block;margin:0 0 12px;padding:0 3px;color:#111;font-size:15px;line-height:1.35;font-weight:900;letter-spacing:0.04em;text-align:left;background:linear-gradient(180deg,rgba(255,255,255,0) 48%,rgba(8,22,241,0.2) 48%);font-family:'PingFang SC','Source Han Sans SC','Noto Sans CJK SC','Microsoft YaHei',Arial,sans-serif;">关注星期一研究室</p>
      <p style="margin:0;padding:0;color:#111;font-size:8px;line-height:1.35;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;text-align:left;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;">
        AI PRODUCT · AI PKM/PMO · AI SYSTEM
      </p>
    </div>
  </div>
</section>""".strip()


def render_end_block() -> str:
    return f"""
<section data-iaw-ending="true" style="margin:58px 16px 0;padding:52px 0 34px;text-align:center;box-sizing:border-box;">
  <div style="display:inline-block;width:100%;max-width:430px;text-align:left;box-sizing:border-box;">
    <p style="margin:0 0 42px;padding:0;text-align:center;font-size:0;line-height:1;">
      <span style="display:inline-block;width:68px;height:1px;background:rgba(0,0,0,0.16);vertical-align:middle;margin-right:15px;"></span>
      <span style="display:inline-block;color:#777;font-size:18px;line-height:1;font-weight:500;letter-spacing:0.2em;text-transform:uppercase;vertical-align:middle;">END</span>
      <span style="display:inline-block;width:7px;height:7px;border-radius:999px;background:{BLUE};vertical-align:middle;margin-left:13px;animation:iaw-pulse 3.8s ease-in-out infinite;"></span>
    </p>
    <div style="padding-top:18px;text-align:center;">
      <p style="margin:0 0 10px;padding:0;color:#777;font-size:12px;line-height:1.7;font-weight:500;letter-spacing:0;text-align:center;">
        内容排版 / 周一同学Zelina
      </p>
      <p style="margin:0;padding:0;color:#777;font-size:12px;line-height:1.7;font-weight:500;letter-spacing:0;text-align:center;">
        内容策划 / 周一同学Zelina
      </p>
    </div>
  </div>
</section>""".strip()


def render_h2(text: str) -> str:
    number, title = split_section_title(text)
    has_manual_break = "｜" in title or "|" in title
    title_parts = split_h2_title(title)
    index_font_size = round(
        H2_TITLE_FONT_SIZE * H2_TITLE_LINE_HEIGHT * max(1.75, 0.98 * len(title_parts)),
        2,
    )
    index = (
        f'<span style="font-family:\'Source Han Sans SC\',\'Noto Sans CJK SC\',\'思源黑体\',sans-serif;font-weight:200;display:inline-block;">(</span>'
        f'<span style="font-family:\'Roboto Slab\',Rockwell,Georgia,\'Times New Roman\',serif;font-weight:400;display:inline-block;margin-left:-0.07em;margin-right:-0.07em;">{esc(number)}</span>'
        f'<span style="font-family:\'Source Han Sans SC\',\'Noto Sans CJK SC\',\'思源黑体\',sans-serif;font-weight:200;display:inline-block;">)</span>'
        if number
        else ""
    )
    title_lines = "".join(
        f'<span style="display:flex;align-items:center;flex-wrap:nowrap;column-gap:0;row-gap:0;white-space:nowrap;{"margin-left:24px;" if has_manual_break and idx else ""}">{h2_inline(line)}</span>'
        for idx, line in enumerate(title_parts)
    )
    return f"""
<section style="margin:0;padding:18px 0 24px;">
  <div style="display:flex;align-items:center;gap:4px;margin:0;">
    <div style="font-size:{index_font_size}px;color:{BLUE};letter-spacing:0;white-space:nowrap;text-align:left;transform:scaleX(0.92);transform-origin:center center;">{index}</div>
    <div style="min-width:0;flex:1;">
      <div style="font-size:{H2_TITLE_FONT_SIZE}px;line-height:{H2_TITLE_LINE_HEIGHT};font-family:'Source Han Sans SC','Noto Sans CJK SC','思源黑体',sans-serif;font-weight:900;color:{TEXT};letter-spacing:0;">{title_lines}</div>
    </div>
  </div>
  <div style="font-size:42px;line-height:1.22;font-weight:900;color:{TEXT};margin-top:12px;margin-left:12px;letter-spacing:0;text-align:left;">信息美学家Weekly &gt;&gt;&gt;</div>
</section>""".strip()


def render_h3(text: str) -> str:
    return (
        '<p style="text-align:center;margin:46px 16px 18px;padding:0;'
        'line-height:1.9;font-size:0;">'
        '<span style="display:inline-block;background:#050505;color:#fff;'
        'font-size:15px;line-height:1.9;font-weight:800;padding:0 14px;'
        'border-radius:0;text-align:center;margin:0 auto;">'
        f"&nbsp;&nbsp;{inline(text)}&nbsp;&nbsp;</span></p>"
    )


def render_h4(text: str) -> str:
    return render_h3(text)


def render_paragraph(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines).strip()
    if not text:
        return ""
    if re.fullmatch(r"【📷截图：.+?】", text):
        return (
            '<div style="margin:14px 16px 10px;padding:14px 16px;background:#f7f7f7;'
            f'border:1px dashed #cfcfcf;color:{MUTED};font-size:14px;line-height:1.7;border-radius:4px;">'
            f"{esc(text)}</div>"
        )
    image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", text)
    if image:
        alt, src = image.group(1), image.group(2)
        is_section_heading = bool(re.search(r"-section-\d+\.png$", src))
        caption = (
            f'<figcaption style="color:{MUTED};font-size:14px;line-height:1.5em;'
            f'letter-spacing:0;text-align:center;font-weight:normal;margin:7px 0 0;padding:0;">{esc(alt)}</figcaption>'
            if alt and not is_section_heading else ""
        )
        figure_margin = "26px 16px 12px" if is_section_heading else "16px 16px 14px"
        image_style = (
            'display:block;margin:0 auto;width:100%;max-width:100%;height:auto;'
            'border:none;border-radius:0;object-fit:fill;box-shadow:none;'
            if is_section_heading
            else (
                'display:block;margin:0 auto;width:100%;max-width:100%;height:auto;'
                'border:none;border-radius:4px;object-fit:fill;box-shadow:rgba(170,170,170,0.5) 0px 0px 6px 0px;'
            )
        )
        return (
            f'<figure style="margin:{figure_margin};padding:0;display:flex;'
            'flex-direction:column;justify-content:center;align-items:center;text-align:center;">'
            f'<img src="{esc(src)}" alt="{esc(alt)}" style="{image_style}" />'
            f"{caption}"
            '</figure>'
        )
    return (
        f'<p style="color:{BODY_TEXT};font-size:{BODY_FONT_SIZE}px;line-height:1.8em;letter-spacing:0.02em;'
        'text-align:left;text-indent:0;margin:0;padding:20px 16px 8px;">'
        f"{inline(text)}</p>"
    )


def render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    body = []
    for item in items:
        body.append(f'<li style="margin:5px 0;color:#010101;font-size:{BODY_FONT_SIZE}px;line-height:1.8em;letter-spacing:0;text-align:left;font-weight:normal;">{inline(item)}</li>')
    return (
        f'<{tag} style="list-style-type:{"decimal" if ordered else "disc"};'
        'margin:8px 16px;padding:0 0 0 25px;color:#000;">'
        + "\n".join(body)
        + f"</{tag}>"
    )


def parse_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def render_table(lines: list[str]) -> str:
    rows = [parse_table_row(line) for line in lines if line.strip()]
    rows = [row for row in rows if not all(re.fullmatch(r":?-+:?", cell) for cell in row)]
    if not rows:
        return ""
    out = [
        '<section style="margin:12px 16px 10px;padding:0;overflow-x:auto;">'
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
        '<blockquote style="margin:18px 16px 10px;padding:12px 16px;border-left:4px solid '
        f'{BLUE};background:#f7f8ff;color:#333;font-size:{BODY_FONT_SIZE}px;line-height:1.8em;letter-spacing:0.02em;">'
        f"{body}</blockquote>"
    )


def render_callout(lines: list[str]) -> str:
    cleaned = [line.strip() for line in lines if line.strip()]
    plain_text = " ".join(cleaned)
    body = "<br/>".join(inline(line) for line in cleaned)
    if not body:
        return ""
    is_prompt = bool(re.search(r"prompt|提示词", plain_text, flags=re.IGNORECASE))
    label = "Prompt" if is_prompt else "Note"
    sub_label = "Copy Ready" if is_prompt else "Context"
    return (
        '<section style="margin:24px 16px 16px;padding:16px 16px 16px 18px;'
        f'background:#f7f7f7;border-left:4px solid {BLUE};box-sizing:border-box;">'
        '<p style="margin:0 0 12px;padding:0;line-height:1;font-size:0;text-align:left;">'
        '<span style="display:inline-block;background:#111;color:#fff;font-size:10px;'
        'line-height:1;font-weight:900;letter-spacing:0.12em;text-transform:uppercase;'
        f'padding:5px 8px 4px;">{label}</span>'
        f'<span style="display:inline-block;color:{BLUE};font-size:10px;line-height:1;'
        f'font-weight:800;letter-spacing:0.08em;text-transform:uppercase;margin-left:8px;">{sub_label}</span>'
        '</p>'
        f'<p style="margin:0;color:#2f2f2f;font-size:{BODY_FONT_SIZE}px;'
        f'line-height:1.85em;letter-spacing:0.02em;text-align:left;">{body}</p>'
        '</section>'
    )


def split_callout_line(line: str) -> tuple[str | None, str, str | None]:
    start = None
    end = None
    body = line
    start_match = re.search(r"<callout\b[^>]*>", body, flags=re.IGNORECASE)
    if start_match:
        start = body[: start_match.start()]
        body = body[start_match.end() :]
    end_match = re.search(r"</callout>", body, flags=re.IGNORECASE)
    if end_match:
        end = body[end_match.end() :]
        body = body[: end_match.start()]
    return start, body.strip(), end


def render_markdown(md: str, title: str | None = None) -> str:
    lines = md.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []
    table_lines: list[str] = []
    quote_lines: list[str] = []
    callout_lines: list[str] = []
    in_callout = False

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
        if in_callout:
            if re.search(r"</callout>", line, flags=re.IGNORECASE):
                _, body, _ = split_callout_line(line)
                if body:
                    callout_lines.append(body)
                blocks.append(render_callout(callout_lines))
                callout_lines = []
                in_callout = False
            else:
                callout_lines.append(line)
            continue
        if re.search(r"<callout\b", line, flags=re.IGNORECASE):
            flush_all()
            _, body, _ = split_callout_line(line)
            callout_lines = [body] if body else []
            if re.search(r"</callout>", line, flags=re.IGNORECASE):
                blocks.append(render_callout(callout_lines))
                callout_lines = []
            else:
                in_callout = True
            continue
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

    if in_callout:
        blocks.append(render_callout(callout_lines))
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
  <div data-copy-toolbar="true" style="position:sticky;top:0;z-index:20;background:rgba(255,255,255,0.96);border-bottom:1px solid rgba(0,0,0,0.08);padding:12px 16px;text-align:center;backdrop-filter:saturate(140%) blur(8px);">
    <button id="copy-wechat-html" type="button" style="appearance:none;border:1px solid #111;background:#111;color:#fff;border-radius:0;padding:9px 18px;font-size:13px;line-height:1;font-weight:800;letter-spacing:0.02em;cursor:pointer;font-family:{FONT_STACK};">复制到公众号</button>
    <span id="copy-wechat-status" style="display:inline-block;margin-left:10px;color:#666;font-size:12px;line-height:1.4;vertical-align:middle;"></span>
  </div>
  <section id="nice" data-tool="mondaylab-information-aesthetic-wechat-layout" style="max-width:677px;margin:0 auto;padding:28px 0 56px;background:rgba(0,0,0,0);width:auto;font-family:{FONT_STACK};font-size:16px;color:#000;line-height:1.5em;word-spacing:0;letter-spacing:0;word-break:break-word;overflow-wrap:break-word;text-align:left;box-sizing:border-box;">
    {render_motion_styles()}
    {render_opening_block()}
    {render_h1(title)}
    {content}
    {render_end_block()}
  </section>
  <script>
    (function () {{
      var button = document.getElementById("copy-wechat-html");
      var status = document.getElementById("copy-wechat-status");
      var article = document.getElementById("nice");
      function plainText(node) {{
        return node ? node.innerText.replace(/\\n{{3,}}/g, "\\n\\n").trim() : "";
      }}
      function setStatus(text) {{
        status.textContent = text;
        window.setTimeout(function () {{ status.textContent = ""; }}, 2200);
      }}
      function copyBySelection() {{
        var range = document.createRange();
        range.selectNode(article);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        var copied = document.execCommand("copy");
        selection.removeAllRanges();
        if (!copied) {{
          throw new Error("execCommand copy failed");
        }}
      }}
      async function copyRichHtml() {{
        if (!article) return;
        var html = article.outerHTML;
        var text = plainText(article);
        if (navigator.clipboard && window.ClipboardItem) {{
          try {{
            await navigator.clipboard.write([
              new ClipboardItem({{
                "text/html": new Blob([html], {{ type: "text/html" }}),
                "text/plain": new Blob([text], {{ type: "text/plain" }})
              }})
            ]);
            return;
          }} catch (error) {{
            copyBySelection();
            return;
          }}
        }}
        copyBySelection();
      }}
      button.addEventListener("click", function () {{
        copyRichHtml().then(function () {{
          var oldText = button.textContent;
          button.textContent = "已复制";
          setStatus("现在可以粘贴到公众号编辑器");
          window.setTimeout(function () {{ button.textContent = oldText; }}, 1600);
        }}).catch(function () {{
          setStatus("复制失败，请全选正文区域手动复制");
        }});
      }});
    }})();
  </script>
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
