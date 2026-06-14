#!/usr/bin/env python3
"""Run the 信息美学家 Weekly production pipeline."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import importlib.util
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
LAYOUT_SCRIPT = ROOT / "skills/mondaylab-information-aesthetic-wechat-layout/scripts/render_wechat_html.py"
DEFAULT_POSTER_SKILL = ROOT.parent / "magazine-visuals/skills/make-it-pop-poster"
FRAGMENT_RENDERER = Path(__file__).resolve().parent / "render-fragment.mjs"
DEFAULT_GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SilverLineOrg/mondaylab-brand-skillhub/main"
GENERATED_ASSET_DIR = ROOT / "assets/information-aesthetic-weekly"


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\n\nSTDERR:\n"
            + result.stderr
        )
    return result.stdout


def parse_lark_output(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    def find_markdown(node: Any) -> str | None:
        if isinstance(node, dict):
            for key in ("markdown", "content", "text"):
                value = node.get(key)
                if isinstance(value, str) and value.lstrip().startswith("#"):
                    return value
            for key in ("document", "data", "result"):
                value = node.get(key)
                found = find_markdown(value)
                if found:
                    return found
            for value in node.values():
                found = find_markdown(value)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = find_markdown(item)
                if found:
                    return found
        return None

    found = find_markdown(data)
    if found:
        return found
    return raw


def fetch_markdown(doc: str) -> str:
    raw = run(["lark-cli", "docs", "+fetch", "--api-version", "v2", "--doc", doc, "--doc-format", "markdown"])
    return parse_lark_output(raw)


def fetch_detail(doc: str) -> str:
    try:
        return run(["lark-cli", "docs", "+fetch", "--api-version", "v2", "--doc", doc, "--detail", "full"])
    except RuntimeError:
        return ""


def extract_document_content(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    document = data.get("data", {}).get("document", {}) if isinstance(data, dict) else {}
    content = document.get("content") if isinstance(document, dict) else None
    return content if isinstance(content, str) else raw


def first_h1(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return strip_markdown(match.group(1))
    return fallback


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`=#<>]", "", text)
    return text.strip()


def extract_issue_from_slug(slug: str) -> str:
    match = re.search(r"article-(\d+)", slug)
    return match.group(1) if match else ""


def collect_underlined_phrases(detail: str) -> list[str]:
    phrases: list[str] = []
    if not detail.strip():
        return phrases

    def add(text: str) -> None:
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) >= 2 and clean not in phrases:
            phrases.append(clean)

    try:
        data = json.loads(detail)
    except json.JSONDecodeError:
        data = None

    def walk(node: Any, inherited_underline: bool = False) -> None:
        if isinstance(node, dict):
            style = node.get("style") or node.get("text_style") or node.get("textStyle") or {}
            style_text = json.dumps(style, ensure_ascii=False).lower() if isinstance(style, dict) else str(style).lower()
            own_underline = inherited_underline or bool(node.get("underline")) or "underline" in style_text
            text = node.get("text") or node.get("content") or node.get("plain_text") or node.get("plainText")
            if own_underline and isinstance(text, str):
                add(text)
            for value in node.values():
                walk(value, own_underline)
        elif isinstance(node, list):
            for item in node:
                walk(item, inherited_underline)

    if data is not None:
        walk(data)
    else:
        for match in re.finditer(r"<u>(.*?)</u>", detail, flags=re.I | re.S):
            add(re.sub(r"<[^>]+>", "", match.group(1)))
        for match in re.finditer(r"<[^>]*(?:underline|textDecoration)[^>]*>(.*?)</[^>]+>", detail, flags=re.I | re.S):
            add(re.sub(r"<[^>]+>", "", match.group(1)))

    return phrases


def apply_underlines(markdown: str, phrases: list[str]) -> str:
    if not phrases:
        return markdown
    lines = []
    for line in markdown.splitlines():
        if line.startswith("#") or line.startswith("!") or "<u>" in line:
            lines.append(line)
            continue
        updated = line
        for phrase in sorted(phrases, key=len, reverse=True):
            if phrase in updated:
                updated = updated.replace(phrase, f"<u>{phrase}</u>", 1)
        lines.append(updated)
    return "\n".join(lines) + ("\n" if markdown.endswith("\n") else "")


def normalize_markdown(markdown: str) -> str:
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def extract_image_captions(detail: str) -> dict[str, str]:
    detail = extract_document_content(detail)
    captions: dict[str, str] = {}
    for tag in re.findall(r"<img\b[^>]*>", detail):
        href_match = re.search(r'\bhref="([^"]+)"', tag)
        caption_match = re.search(r'\bcaption="([^"]*)"', tag)
        if not href_match or not caption_match:
            continue
        caption = html.unescape(caption_match.group(1)).strip()
        if caption:
            captions[html.unescape(href_match.group(1)).strip()] = caption
    return captions


def clean_image_alts(markdown: str, captions: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        alt = match.group(1).strip()
        src = match.group(2).strip()
        if src in captions:
            alt = captions[src]
        elif should_hide_image_caption(alt):
            alt = ""
        return f"![{alt}]({src})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, markdown)


def should_hide_image_caption(alt: str) -> bool:
    if not alt:
        return False
    generated_prefixes = (
        "图片展示",
        "图片展示的是",
        "图片展示了",
        "该图片",
        "该图",
        "此图",
    )
    generated_markers = (
        "与上下文",
        "上下文提到",
        "对应文档中",
        "紧密相关",
        "直观呈现",
        "作为示例",
    )
    return len(alt) > 42 and (
        alt.startswith(generated_prefixes) or any(marker in alt for marker in generated_markers)
    )


def insert_masthead(markdown: str, masthead_name: str) -> str:
    image_line = f"![]({masthead_name})"
    markdown = re.sub(r"\n!\[[^\]]*\]\([^)]*masthead\.png\)\n", "\n", markdown)
    lines = markdown.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[: idx + 1] + ["", image_line, ""] + lines[idx + 1 :]).strip() + "\n"
    return image_line + "\n\n" + markdown


def insert_follow_card(markdown: str, follow_card_name: str) -> str:
    image_line = f"![]({follow_card_name})"
    markdown = re.sub(r"\n!\[[^\]]*\]\([^)]*follow-card\.png\)\n", "\n", markdown)
    lines = markdown.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[: idx + 1] + ["", image_line, ""] + lines[idx + 1 :]).strip() + "\n"
    return image_line + "\n\n" + markdown


def make_masthead_html(title: str, issue: str, markdown: str, poster_skill: Path) -> str:
    if not (poster_skill / "SKILL.md").exists():
        raise FileNotFoundError(f"Cannot find make-it-pop-poster skill: {poster_skill}")
    poster_copy = extract_poster_copy(markdown, title, issue)
    issue_text = f"ISSUE {issue}" if issue else "WEEKLY"
    headline = render_poster_headline(poster_copy["headline_lines"], poster_copy["highlight"])
    pills = poster_copy["pills"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(title)}</title>
  <style>
    :root {{
      --paper: #f7f8ff;
      --ink: #060606;
      --muted: #55565f;
      --blue: #0816f1;
      --soft-blue: rgba(8, 22, 241, .13);
      --grid: rgba(8, 22, 241, .08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #dfe3ff;
      font-family: Inter, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }}
    .poster {{
      position: relative;
      width: 1080px;
      height: 1440px;
      overflow: hidden;
      color: var(--ink);
      background:
        radial-gradient(circle at 88% 12%, rgba(8, 22, 241, .16), transparent 24%),
        radial-gradient(circle at 8% 88%, rgba(8, 22, 241, .08), transparent 18%),
        linear-gradient(90deg, var(--grid) 1px, transparent 1px),
        linear-gradient(0deg, var(--grid) 1px, transparent 1px),
        var(--paper);
      background-size: auto, auto, 90px 90px, 90px 90px, auto;
      box-shadow: 0 26px 80px rgba(0, 0, 0, .16);
    }}
    .poster::before {{
      content: "";
      position: absolute;
      inset: 0;
      opacity: .26;
      pointer-events: none;
      background-image:
        repeating-radial-gradient(circle at 18% 22%, rgba(0, 0, 0, .12) 0 1px, transparent 1px 5px),
        repeating-linear-gradient(110deg, transparent 0 14px, rgba(0, 0, 0, .04) 14px 15px);
      mix-blend-mode: multiply;
    }}
    .topbar {{
      position: absolute;
      top: 68px;
      left: 76px;
      right: 76px;
      z-index: 2;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
    }}
    .masthead {{ display: grid; gap: 16px; }}
    .masthead-cn {{
      font-size: 86px;
      line-height: .9;
      font-weight: 950;
      letter-spacing: 0;
      white-space: nowrap;
    }}
    .masthead-en {{
      color: #30323a;
      font-size: 23px;
      line-height: 1;
      font-weight: 760;
      letter-spacing: .01em;
      white-space: nowrap;
    }}
    .issue {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      margin-top: 18px;
      color: #171717;
      font-size: 18px;
      line-height: 1;
      font-weight: 860;
      letter-spacing: .04em;
    }}
    .issue::before {{
      content: "";
      width: 13px;
      height: 13px;
      border-radius: 50%;
      background: var(--blue);
      box-shadow: 0 0 0 5px rgba(8, 22, 241, .12);
    }}
    .callout {{
      position: absolute;
      top: 264px;
      right: 76px;
      z-index: 3;
      display: flex;
      height: 52px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(255, 255, 255, .94);
      box-shadow: 0 12px 28px rgba(8, 22, 241, .12);
      border: 1px solid rgba(8, 22, 241, .14);
      font-size: 19px;
      font-weight: 760;
    }}
    .callout span {{
      display: grid;
      place-items: center;
      height: 100%;
      padding: 0 20px;
      border-right: 1px solid rgba(8, 22, 241, .12);
    }}
    .callout span:last-child {{ border-right: 0; }}
    .main {{
      position: absolute;
      left: 76px;
      right: 76px;
      top: 346px;
      z-index: 2;
    }}
    .kicker {{
      margin: 0 0 48px 306px;
      font-size: 45px;
      line-height: 1;
      font-weight: 950;
      letter-spacing: 0;
    }}
    .headline {{
      margin: 0;
      max-width: 920px;
      font-size: 102px;
      line-height: .96;
      font-weight: 950;
      letter-spacing: 0;
    }}
    .line {{
      display: block;
      white-space: nowrap;
    }}
    .thin {{ font-weight: 480; }}
    .select {{
      position: relative;
      display: inline-block;
      padding: 0 .08em .04em;
      color: var(--blue);
      isolation: isolate;
    }}
    .select::before {{
      content: "";
      position: absolute;
      left: -.04em;
      right: -.04em;
      top: .11em;
      bottom: .03em;
      z-index: -1;
      background: var(--soft-blue);
      border: 2px solid rgba(8, 22, 241, .25);
    }}
    .select::after {{
      content: "";
      position: absolute;
      top: .04em;
      right: -.13em;
      width: .2em;
      height: .2em;
      border-radius: 50%;
      background: var(--blue);
      box-shadow: -2.25em 0 0 var(--blue);
    }}
    .microcopy {{
      position: absolute;
      left: 82px;
      right: 92px;
      top: 964px;
      z-index: 2;
      max-width: 820px;
      color: #282a32;
      font-size: 25px;
      line-height: 1.62;
      font-weight: 540;
      letter-spacing: 0;
    }}
    .microcopy strong {{ font-weight: 820; }}
    .pill {{
      position: absolute;
      z-index: 4;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 45px;
      padding: 7px 22px 9px;
      border-radius: 12px;
      color: #fff;
      background: var(--blue);
      font-size: 25px;
      line-height: 1;
      font-weight: 860;
      letter-spacing: 0;
      box-shadow: 0 13px 18px rgba(8, 22, 241, .2);
      transform-origin: center;
      white-space: nowrap;
    }}
    .pill.light {{
      color: var(--blue);
      background: #e8eaff;
      border: 1px solid rgba(8, 22, 241, .22);
    }}
    .p1 {{ top: 300px; left: 706px; transform: rotate(-1deg); }}
    .p2 {{ top: 492px; left: 82px; transform: rotate(4deg); }}
    .p3 {{ top: 668px; left: 666px; transform: rotate(-6deg); }}
    .p4 {{ top: 842px; left: 396px; transform: rotate(-7deg); }}
    .star {{
      position: absolute;
      z-index: 4;
      top: 305px;
      left: 288px;
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      color: #fff;
      background: var(--blue);
      font-size: 26px;
      font-weight: 900;
      box-shadow: 0 8px 16px rgba(8, 22, 241, .2);
    }}
    .bracket {{
      position: absolute;
      top: 654px;
      left: 84px;
      width: 22px;
      height: 154px;
      border-left: 12px solid var(--blue);
      border-top: 12px solid var(--blue);
      border-bottom: 12px solid var(--blue);
      opacity: .95;
    }}
    .cursor {{
      position: absolute;
      z-index: 5;
      top: 585px;
      right: 120px;
      width: 112px;
      height: 112px;
      filter: drop-shadow(0 8px 5px rgba(0, 0, 0, .14));
      transform: rotate(-13deg);
    }}
    .cursor::before {{
      content: "";
      position: absolute;
      inset: 0;
      background: #070706;
      clip-path: polygon(7% 2%, 93% 55%, 56% 65%, 74% 98%, 55% 100%, 38% 69%, 12% 96%);
    }}
    .bottom {{
      position: absolute;
      z-index: 6;
      left: 76px;
      right: 76px;
      bottom: 72px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 30px;
      color: #4c4f5b;
      font-size: 16px;
      line-height: 1;
      font-weight: 720;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .publisher {{ display: grid; gap: 10px; }}
    .brand-cn {{
      color: var(--ink);
      font-size: 20px;
      font-weight: 880;
      letter-spacing: 0;
    }}
    .tagline {{
      color: var(--blue);
      font-size: 16px;
      font-weight: 800;
      letter-spacing: .12em;
      text-align: right;
      white-space: nowrap;
    }}
  </style>
</head>
<body>
  <article class="poster" aria-label="信息美学家第{escape_html(issue or '')}期栏头图">
    <div class="topbar">
      <div class="masthead">
        <div class="masthead-cn">信息美学家</div>
        <div class="masthead-en">Information Aesthetician Weekly</div>
      </div>
      <div class="issue">{escape_html(issue_text)}</div>
    </div>
    <div class="callout">
      <span>Collect</span>
      <span>Tag</span>
      <span>Reuse</span>
    </div>
    <span class="star">★</span>
    <span class="pill p1">{escape_html(pills[0])}</span>
    <span class="pill light p2">{escape_html(pills[1])}</span>
    <span class="pill p3">{escape_html(pills[2])}</span>
    <span class="pill light p4">{escape_html(pills[3])}</span>
    <span class="bracket"></span>
    <span class="cursor"></span>
    <main class="main">
      <p class="kicker">{escape_html(poster_copy["kicker"])}</p>
      <h1 class="headline">
        {headline}
      </h1>
    </main>
    <section class="microcopy">
      <p>{escape_html(poster_copy["microcopy"])}</p>
    </section>
    <footer class="bottom">
      <div class="publisher">
        <div class="brand-cn">星期一研究室出品</div>
        <div>THE INFORMATION AESTHETICIAN</div>
      </div>
      <div class="tagline">TOOLS / SYSTEMS / VISUAL ORDER</div>
    </footer>
  </article>
</body>
</html>
"""


def extract_poster_copy(markdown: str, title: str, issue: str) -> dict[str, Any]:
    """Extract poster-only copy from visible document text.

    This intentionally does not read H2 headings, WeChat layout markers, or
    title highlight syntax. The masthead poster has its own editorial copy
    layer before the article Markdown is handed to the HTML renderer.
    """
    body_lines = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!") or line.startswith("<"):
            continue
        if line.startswith("|") or line.startswith("- "):
            continue
        body_lines.append(strip_markdown(line))
        if len(body_lines) >= 3:
            break

    headline_source = re.sub(r"^第?\s*" + re.escape(issue) + r"\s*期\s*[▷：:|-]*\s*", "", title).strip() if issue else title
    kicker, headline_body = split_poster_kicker_and_headline(headline_source)
    highlight = choose_poster_highlight(headline_source)
    headline_lines = split_poster_headline(headline_body, highlight)
    microcopy = body_lines[1] if len(body_lines) > 1 else (body_lines[0] if body_lines else title)
    return {
        "headline_lines": headline_lines,
        "highlight": highlight,
        "kicker": kicker,
        "microcopy": microcopy,
        "pills": choose_poster_pills(headline_source + " " + microcopy),
    }


def render_poster_headline(title_lines: list[str], select_phrase: str) -> str:
    phrase = select_phrase
    lines = []
    for line in title_lines[:3]:
        escaped = escape_html(line)
        if phrase and phrase in line:
            escaped = escaped.replace(escape_html(phrase), f'<span class="select">{escape_html(phrase)}</span>', 1)
            phrase = ""
        lines.append(f'<span class="line">{escaped}</span>')
    return "\n        ".join(lines)


def split_poster_kicker_and_headline(text: str) -> tuple[str, str]:
    for sep in ("，", ","):
        if sep in text:
            before, after = [part.strip() for part in text.split(sep, 1)]
            if before and after:
                return before, after
    return "Weekly Topic", text


def choose_poster_pills(text: str) -> list[str]:
    pills = []
    candidates = [
        ("AI", "AI Images"),
        ("视觉资产", "Visual Assets"),
        ("画册", "Gallery View"),
        ("筛选", "Searchable"),
        ("复用", "Reusable"),
        ("素材", "Materials"),
        ("标签", "Taggable"),
    ]
    for needle, label in candidates:
        if needle in text and label not in pills:
            pills.append(label)
    fallback = ["Collect", "Visual Assets", "Gallery View", "Searchable"]
    return (pills + fallback)[:4]


def choose_poster_highlight(text: str) -> str:
    for phrase in ("好找又好用", "视觉资产库", "轻量素材库", "画册视图", "素材库"):
        if phrase in text:
            return phrase
    return ""


def split_poster_headline(title: str, highlight: str) -> list[str]:
    normalized = title.strip()
    if highlight and highlight in normalized:
        before, after = normalized.split(highlight, 1)
        lines = []
        before = before.strip()
        after = after.strip()
        if before:
            lines.append(before)
        lines.append(highlight)
        if after:
            lines.append(after)
        return lines
    for sep in ("，", ","):
        if sep in normalized:
            before, after = [part.strip() for part in normalized.split(sep, 1)]
            return [before + sep, *balanced_title_lines(after)]
    return balanced_title_lines(normalized)


def balanced_title_lines(text: str) -> list[str]:
    if len(text) <= 12:
        return [text]
    if len(text) <= 24:
        split_at = nearest_split(text, len(text) // 2)
        return [text[:split_at].strip(), text[split_at:].strip()]
    first_at = nearest_split(text, min(13, max(8, len(text) // 3)))
    rest = text[first_at:].strip()
    second_at = nearest_split(rest, len(rest) // 2)
    return [text[:first_at].strip(), rest[:second_at].strip(), rest[second_at:].strip()]


def nearest_split(text: str, target: int) -> int:
    candidates = [idx for idx, char in enumerate(text) if idx > 0 and char in " 的了后成把和又、"]
    if not candidates:
        return target
    return min(candidates, key=lambda idx: abs(idx - target)) + 1


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def find_chrome() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    return next((path for path in candidates if path and Path(path).exists()), None)


def render_masthead(html_path: Path, png_path: Path, poster_skill: Path) -> None:
    renderer = poster_skill / "scripts/render-html.mjs"
    if not renderer.exists():
        raise FileNotFoundError(f"Cannot find make-it-pop renderer: {renderer}")
    node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
    env = os.environ.copy()
    chrome = find_chrome()
    if chrome:
        env["CHROME_PATH"] = chrome
    bundled_modules = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
    if bundled_modules.exists():
        env["NODE_PATH"] = str(bundled_modules)
    run([node, str(renderer), str(html_path), str(png_path)], cwd=ROOT, env=env)


def node_env() -> tuple[str, dict[str, str]]:
    node = shutil.which("node") or str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
    env = os.environ.copy()
    chrome = find_chrome()
    if chrome:
        env["CHROME_PATH"] = chrome
    bundled_modules = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
    if bundled_modules.exists():
        env["NODE_PATH"] = str(bundled_modules)
    return node, env


def load_layout_module() -> Any:
    spec = importlib.util.spec_from_file_location("render_wechat_html", LAYOUT_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot load layout script: {LAYOUT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_section_heading_html(title: str) -> str:
    layout = load_layout_module()
    section = layout.render_h2(title)
    scale = 1.48
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(strip_markdown(title))}</title>
</head>
<body style="margin:0;background:#fff;">
  <div id="capture" style="width:1080px;height:500px;overflow:hidden;background:#fff;font-family:{layout.FONT_STACK};">
    <div style="width:677px;transform:translate(48px, 20px) scale({scale:.6f});transform-origin:top left;">
      {section}
    </div>
  </div>
</body>
</html>
"""


def make_follow_card_html() -> str:
    layout = load_layout_module()
    follow_card = layout.render_opening_block()
    scale = 1.48
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MondayLab Follow Card</title>
</head>
<body style="margin:0;background:#fff;">
  <div id="capture" style="width:1080px;height:360px;overflow:hidden;background:#fff;font-family:{layout.FONT_STACK};">
    <div style="width:677px;transform:translate(38px, 10px) scale({scale:.6f});transform-origin:top left;">
      {follow_card}
    </div>
  </div>
</body>
</html>
"""


def render_fragment(html_path: Path, png_path: Path, width: int = 1080, height: int = 500) -> None:
    if not FRAGMENT_RENDERER.exists():
        raise FileNotFoundError(f"Cannot find fragment renderer: {FRAGMENT_RENDERER}")
    node, env = node_env()
    command = [node, str(FRAGMENT_RENDERER), str(html_path), str(png_path)]
    if width != 1080 or height != 500:
        command.extend([str(width), str(height)])
    run(command, cwd=ROOT, env=env)


def render_section_heading(html_path: Path, png_path: Path) -> None:
    render_fragment(html_path, png_path)


def render_follow_card(html_path: Path, png_path: Path) -> None:
    render_fragment(html_path, png_path, width=1080, height=360)


def insert_section_heading_images(markdown: str, slug: str, output_dir: Path) -> tuple[str, list[Path]]:
    generated: list[Path] = []
    section_index = 0
    lines: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if not match:
            lines.append(line)
            continue
        section_index += 1
        title = match.group(1).strip()
        stem = f"{slug}-section-{section_index:02d}"
        html_path = output_dir / f"{stem}.html"
        png_path = output_dir / f"{stem}.png"
        html_path.write_text(make_section_heading_html(title), encoding="utf-8")
        render_section_heading(html_path, png_path)
        generated.append(png_path)
        lines.extend(["", f"![]({png_path.name})", ""])
    return "\n".join(lines).strip() + "\n", generated


def render_html(markdown_path: Path, html_path: Path) -> None:
    run([sys.executable, str(LAYOUT_SCRIPT), "--input", str(markdown_path), "--output", str(html_path)], cwd=ROOT)


def publish_generated_assets(markdown: str, assets: list[Path], slug: str, raw_base: str) -> str:
    asset_dir = GENERATED_ASSET_DIR / slug
    asset_dir.mkdir(parents=True, exist_ok=True)
    raw_base = raw_base.rstrip("/")
    for asset in assets:
        if not asset.exists():
            continue
        target = asset_dir / asset.name
        shutil.copy2(asset, target)
        repo_path = target.relative_to(ROOT).as_posix()
        markdown = markdown.replace(f"]({asset.name})", f"]({raw_base}/{repo_path})")
    return markdown


def collect_image_sources(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)


def local_path_for_repo_raw_url(src: str) -> Path | None:
    raw_base = DEFAULT_GITHUB_RAW_BASE.rstrip("/") + "/"
    if not src.startswith(raw_base):
        return None
    relative = src[len(raw_base) :]
    return ROOT / relative


def check_image(src: str, base_dir: Path) -> tuple[str, str]:
    local_raw = local_path_for_repo_raw_url(src)
    if local_raw and local_raw.exists():
        return src, "LOCAL_PENDING_PUSH"
    if re.match(r"https?://", src):
        request = urllib.request.Request(src, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                return src, str(response.status)
        except urllib.error.HTTPError as exc:
            if exc.code == 405:
                return check_image_get(src)
            return src, str(exc.code)
        except Exception as exc:  # noqa: BLE001
            return src, f"ERROR {exc.__class__.__name__}"
    return src, "OK" if (base_dir / src).exists() else "MISSING"


def check_image_get(src: str) -> tuple[str, str]:
    request = urllib.request.Request(src, method="GET", headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return src, str(response.status)
    except urllib.error.HTTPError as exc:
        return src, str(exc.code)
    except Exception as exc:  # noqa: BLE001
        return src, f"ERROR {exc.__class__.__name__}"


def serve(directory: Path, port: int) -> None:
    os.chdir(directory)
    server = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    print(f"Preview server: http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 信息美学家 Weekly Markdown, masthead, and HTML.")
    parser.add_argument("--doc", required=True, help="Feishu/Lark document or wiki URL")
    parser.add_argument("--slug", required=True, help="Output file stem, e.g. article-013-topic")
    parser.add_argument("--issue", default=None, help="Issue number, e.g. 013")
    parser.add_argument("--output-dir", default=str(ROOT), help="Output directory")
    parser.add_argument("--poster-skill-dir", default=str(DEFAULT_POSTER_SKILL), help="Path to make-it-pop-poster skill")
    parser.add_argument("--skip-masthead", action="store_true", help="Skip masthead HTML/PNG generation")
    parser.add_argument("--skip-section-images", action="store_true", help="Keep H2 section headings as HTML instead of PNG images")
    parser.add_argument("--use-local-assets", action="store_true", help="Keep generated masthead/section images as local relative paths")
    parser.add_argument("--github-raw-base", default=DEFAULT_GITHUB_RAW_BASE, help="GitHub raw URL base for generated assets")
    parser.add_argument("--serve", action="store_true", help="Start a local preview server after generation")
    parser.add_argument("--port", type=int, default=8765, help="Preview server port")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = args.slug
    issue = args.issue or extract_issue_from_slug(slug)
    markdown_path = output_dir / f"{slug}.md"
    html_path = output_dir / f"{slug}.html"
    follow_card_html = output_dir / f"{slug}-follow-card.html"
    follow_card_png = output_dir / f"{slug}-follow-card.png"
    masthead_html = output_dir / f"{slug}-masthead.html"
    masthead_png = output_dir / f"{slug}-masthead.png"

    markdown = normalize_markdown(fetch_markdown(args.doc))
    detail = fetch_detail(args.doc)
    markdown = apply_underlines(markdown, collect_underlined_phrases(detail))
    markdown = clean_image_alts(markdown, extract_image_captions(detail))

    title = first_h1(markdown, slug)
    generated_assets: list[Path] = []
    follow_card_html.write_text(make_follow_card_html(), encoding="utf-8")
    render_follow_card(follow_card_html, follow_card_png)
    generated_assets.append(follow_card_png)
    markdown = insert_follow_card(markdown, follow_card_png.name)

    if not args.skip_masthead:
        poster_skill = Path(args.poster_skill_dir).resolve()
        masthead_html.write_text(make_masthead_html(title, issue, markdown, poster_skill), encoding="utf-8")
        render_masthead(masthead_html, masthead_png, poster_skill)
        generated_assets.append(masthead_png)
        markdown = insert_masthead(markdown, masthead_png.name)

    section_images: list[Path] = []
    if not args.skip_section_images:
        markdown, section_images = insert_section_heading_images(markdown, slug, output_dir)
        generated_assets.extend(section_images)

    if generated_assets and not args.use_local_assets:
        markdown = publish_generated_assets(markdown, generated_assets, slug, args.github_raw_base)

    markdown_path.write_text(markdown, encoding="utf-8")
    render_html(markdown_path, html_path)

    checks = [check_image(src, output_dir) for src in collect_image_sources(markdown)]
    print(f"Markdown: {markdown_path}")
    print(f"HTML: {html_path}")
    print(f"Follow card HTML: {follow_card_html}")
    print(f"Follow card PNG: {follow_card_png}")
    if not args.skip_masthead:
        print(f"Masthead HTML: {masthead_html}")
        print(f"Masthead PNG: {masthead_png}")
    if section_images:
        print("Section PNGs:")
        for image in section_images:
            print(f"  {image}")
    print("Images:")
    for src, status in checks:
        print(f"  {status}  {src}")
    print(f"Preview: http://localhost:{args.port}/{html_path.name}")

    if args.serve:
        serve(output_dir, args.port)


if __name__ == "__main__":
    main()
