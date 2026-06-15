#!/usr/bin/env python3
"""Prepare KL weekly meeting resources in Feishu/Lark.

This script is intended to run every Friday. It creates blank weekly report
rows for the current week, updates the "本周周报" Base view filter, and copies
the weekly meeting template into the KL meeting Wiki folder.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from typing import Any
from zoneinfo import ZoneInfo


BASE_TOKEN = "L75CbCeOgax8yNstC7BcktvZnsb"
REPORT_TABLE_ID = "tbl6k8dXVQyAnLRN"
REPORT_VIEW_ID = "vewzR3NKc6"
DATE_TABLE_ID = "tblLsqd6yLCUCUzT"
MEETING_CONFIG_TABLE_ID = "tblmIbqLtw0TqFIV"

FIELD_OWNER = "fldWDeBMBX"
FIELD_SUB_BOARD = "fldtW6odCA"
FIELD_WEEK_RANGE = "fldhPqDTvC"
FIELD_WEEK_START = "fldtGAVrZr"
FIELD_WEEK_END = "flddmbf7b7"
FIELD_WEEK_LABEL = "fldEGG3Kkq"
CONFIG_NAME = "fldXEy23qo"
CONFIG_WEEK_RANGE = "fldHBTN2o5"
CONFIG_MEETING_TIME = "fldbb5yCbc"
CONFIG_TOPIC = "fld9Vltz8l"
CONFIG_HOST = "fld0s1AuCb"
CONFIG_DOC_URL = "fldAsDT8cC"
CONFIG_REPORT_URL = "fldboitx0q"
CONFIG_REMINDER_TEXT = "fldRf3qXHC"
CONFIG_RECORD_NAME = "weekly_current"

WIKI_SPACE_ID = "7622166928118811868"
TEMPLATE_NODE_TOKEN = "D1Aiw6mPOi6i7bkEJlDc2R9knkf"
TARGET_PARENT_NODE_TOKEN = "HZNDwBDCqiVqTpkfQYkcMx5Fn5H"
MEETING_TOPIC = "业务周会｜本周进展同步与下周计划对齐"
HOST_ROTATION = ["冬灵", "周一同学Zelina", "见莲花", "海豹", "亚克", "依谨"]
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
REMINDER_CHAT_ID = "oc_6a42fb162e6b8168ba9442d5e993025b"
REPORT_VIEW_URL = "https://jwf86xh1hew.feishu.cn/wiki/SyiPwZKSniyHygkwlJRc2kLlnCb?table=tbl6k8dXVQyAnLRN&view=vewzR3NKc6"
MEETING_FOLDER_URL = "https://jwf86xh1hew.feishu.cn/wiki/HZNDwBDCqiVqTpkfQYkcMx5Fn5H"
HOST_OPEN_IDS = {
    "冬灵": "ou_4e89d17b37a67f63a721c168b1e82306",
    "周一同学Zelina": "ou_0d3b2a324f3ad507c82674622534cd9a",
    "见莲花": "ou_3375a710ca5864f5abfb8ba27949799b",
    "海豹": "ou_0b8b66caba54d863b4470a6920b6d5cb",
    "亚克": "ou_c6783e4b9de8edc985dc0e07d10e8bb2",
    "依谨": "ou_c1c9c00689a9d13db92c8fbdab97c2cd",
}


class LarkCliError(RuntimeError):
    pass


def run_lark(args: list[str], *, skip: bool = False) -> dict[str, Any]:
    if skip:
        print("$ lark-cli " + " ".join(args))
        return {}

    completed = subprocess.run(
        ["lark-cli", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0:
        raise LarkCliError(output)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LarkCliError(f"Could not parse lark-cli JSON output: {output}") from exc


def week_start_for(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def parse_day(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    tz = ZoneInfo(os.environ.get("MEETING_TZ", "Asia/Shanghai"))
    return dt.datetime.now(tz).date()


def cell_ids(cell: Any) -> tuple[str, ...]:
    if not cell:
        return ()
    return tuple(item["id"] for item in cell if isinstance(item, dict) and item.get("id"))


def cell_names(cell: Any) -> list[str]:
    if not cell:
        return []
    return [item["name"] for item in cell if isinstance(item, dict) and item.get("name")]


def get_week_record(week_start: dt.date) -> dict[str, str]:
    payload = run_lark(
        [
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            DATE_TABLE_ID,
            "--field-id",
            FIELD_WEEK_START,
            "--field-id",
            FIELD_WEEK_END,
            "--field-id",
            FIELD_WEEK_LABEL,
            "--filter-json",
            json.dumps(
                {
                    "logic": "and",
                    "conditions": [[FIELD_WEEK_START, "==", f"ExactDate({week_start})"]],
                },
                ensure_ascii=False,
            ),
            "--limit",
            "10",
            "--as",
            "user",
            "--format",
            "json",
        ],
    )

    data = payload["data"]
    if len(data["record_id_list"]) != 1:
        raise LarkCliError(f"Expected exactly one date warehouse record for {week_start}, got {len(data['record_id_list'])}")
    return {
        "record_id": data["record_id_list"][0],
        "label": data["data"][0][2],
    }


def list_report_rows_for_week(week_record_id: str) -> list[dict[str, Any]]:
    payload = run_lark(
        [
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            REPORT_TABLE_ID,
            "--field-id",
            FIELD_OWNER,
            "--field-id",
            FIELD_SUB_BOARD,
            "--field-id",
            FIELD_WEEK_RANGE,
            "--filter-json",
            json.dumps(
                {
                    "logic": "and",
                    "conditions": [[FIELD_WEEK_RANGE, "intersects", [{"id": week_record_id}]]],
                },
                ensure_ascii=False,
            ),
            "--limit",
            "200",
            "--as",
            "user",
            "--format",
            "json",
        ],
    )

    rows = []
    for record_id, row in zip(payload["data"]["record_id_list"], payload["data"]["data"]):
        rows.append(
            {
                "record_id": record_id,
                "owner": row[0],
                "sub_board": row[1],
                "week_range": row[2],
            }
        )
    return rows


def find_source_rows(target_week_start: dt.date, *, dry_run: bool) -> tuple[dt.date | None, list[dict[str, Any]]]:
    for weeks_back in range(1, 13):
        source_week = target_week_start - dt.timedelta(days=7 * weeks_back)
        source_record = get_week_record(source_week)
        rows = list_report_rows_for_week(source_record["record_id"])
        if rows:
            return source_week, rows
    return None, []


def create_missing_blank_rows(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    target_week_record_id: str,
    *,
    dry_run: bool,
) -> tuple[int, list[str]]:
    existing_keys = {
        (cell_ids(row["owner"]), cell_ids(row["sub_board"]))
        for row in target_rows
    }
    rows_to_create = []
    people_to_create = []
    seen = set(existing_keys)
    for row in source_rows:
        owner_ids = cell_ids(row["owner"])
        if not owner_ids:
            continue
        key = (owner_ids, cell_ids(row["sub_board"]))
        if key in seen:
            continue
        seen.add(key)
        rows_to_create.append([row["owner"], row["sub_board"], [{"id": target_week_record_id}]])
        people_to_create.extend(cell_names(row["owner"]))

    if not rows_to_create:
        return 0, []

    run_lark(
        [
            "base",
            "+record-batch-create",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            REPORT_TABLE_ID,
            "--json",
            json.dumps(
                {
                    "fields": [FIELD_OWNER, FIELD_SUB_BOARD, FIELD_WEEK_RANGE],
                    "rows": rows_to_create,
                },
                ensure_ascii=False,
            ),
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )
    return len(rows_to_create), people_to_create


def update_report_view_filter(target_week_record_id: str, *, dry_run: bool) -> None:
    run_lark(
        [
            "base",
            "+view-set-filter",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            REPORT_TABLE_ID,
            "--view-id",
            REPORT_VIEW_ID,
            "--json",
            json.dumps(
                {
                    "logic": "and",
                    "conditions": [[FIELD_WEEK_RANGE, "intersects", [{"id": target_week_record_id}]]],
                },
                ensure_ascii=False,
            ),
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )


def meeting_day_for(target_week_start: dt.date) -> dt.date:
    meeting_day_offset = int(os.environ.get("MEETING_DAY_OFFSET", "4"))
    return target_week_start + dt.timedelta(days=meeting_day_offset)


def week_name_from_label(week_label: str) -> str:
    match = re.search(r"第\d+周", week_label)
    return match.group(0) if match else "本周"


def meeting_title(target_week_start: dt.date, week_label: str) -> str:
    meeting_day = meeting_day_for(target_week_start)
    week_name = week_name_from_label(week_label)
    return f"{meeting_day:%Y/%m/%d}-{week_name}-业务周会"


def host_for_week(week_label: str) -> str:
    match = re.search(r"第(\d+)周", week_label)
    if not match:
        return HOST_ROTATION[0]
    week_number = int(match.group(1))
    return HOST_ROTATION[(week_number - 1) % len(HOST_ROTATION)]


def list_child_nodes() -> list[dict[str, Any]]:
    payload = run_lark(
        [
            "wiki",
            "+node-list",
            "--space-id",
            WIKI_SPACE_ID,
            "--parent-node-token",
            TARGET_PARENT_NODE_TOKEN,
            "--page-all",
            "--as",
            "user",
            "--format",
            "json",
        ],
    )
    return payload["data"]["nodes"]


def copy_template(title: str, *, dry_run: bool) -> tuple[bool, str | None]:
    for node in list_child_nodes():
        if node["title"] == title:
            return False, node.get("obj_token")

    payload = run_lark(
        [
            "wiki",
            "+node-copy",
            "--space-id",
            WIKI_SPACE_ID,
            "--node-token",
            TEMPLATE_NODE_TOKEN,
            "--target-parent-node-token",
            TARGET_PARENT_NODE_TOKEN,
            "--title",
            title,
            "--yes",
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )
    if dry_run:
        return True, "<meeting-doc-token>"
    return True, payload["data"].get("obj_token")


def meeting_doc_url(doc_token: str | None) -> str:
    if doc_token and not doc_token.startswith("<"):
        return f"https://jwf86xh1hew.feishu.cn/docx/{doc_token}"
    return MEETING_FOLDER_URL


def parse_time_section(content: str) -> tuple[str, list[str]]:
    h2_match = re.search(r'<h2 id="([^"]+)">1、时间安排</h2>', content)
    if not h2_match:
        raise LarkCliError("Could not find the meeting time section heading.")
    li_ids = re.findall(r'<li id="([^"]+)">(?:时间：|会议主题：|主持人：|会议记录：)', content)
    if not li_ids:
        raise LarkCliError("Could not find meeting arrangement list items.")
    return h2_match.group(1), li_ids


def personalize_meeting_doc(
    doc_token: str | None,
    target_week_start: dt.date,
    week_label: str,
    *,
    dry_run: bool,
) -> dict[str, str]:
    meeting_day = meeting_day_for(target_week_start)
    weekday = WEEKDAY_NAMES[meeting_day.weekday()]
    host = host_for_week(week_label)
    meeting_time = f"{meeting_day:%Y/%m/%d}-{weekday}晚上 19:00-20:00"
    content = (
        f"<ul><li>时间：{meeting_time}</li>"
        f"<li>会议主题：{MEETING_TOPIC}</li>"
        f"<li>主持人：{host}</li>"
        '<li>会议记录：<span text-color="rgb(143,149,158)">这里存放妙计相关信息</span></li></ul>'
    )

    if not doc_token:
        raise LarkCliError("Meeting document token is empty; cannot personalize the copied document.")
    if doc_token.startswith("<"):
        print(f"Would personalize {doc_token}: 时间={meeting_time}, 会议主题={MEETING_TOPIC}, 主持人={host}")
        return {"meeting_time": meeting_time, "meeting_topic": MEETING_TOPIC, "host": host}

    fetched = run_lark(
        [
            "docs",
            "+fetch",
            "--api-version",
            "v2",
            "--doc",
            doc_token,
            "--scope",
            "keyword",
            "--keyword",
            "时间：\\|会议主题：\\|主持人：",
            "--context-before",
            "1",
            "--context-after",
            "1",
            "--detail",
            "with-ids",
            "--as",
            "user",
            "--format",
            "json",
        ],
    )
    section_content = fetched["data"]["document"]["content"]
    heading_id, old_li_ids = parse_time_section(section_content)

    run_lark(
        [
            "docs",
            "+update",
            "--api-version",
            "v2",
            "--doc",
            doc_token,
            "--command",
            "block_insert_after",
            "--block-id",
            heading_id,
            "--content",
            content,
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )
    run_lark(
        [
            "docs",
            "+update",
            "--api-version",
            "v2",
            "--doc",
            doc_token,
            "--command",
            "block_delete",
            "--block-id",
            ",".join(old_li_ids),
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )
    return {"meeting_time": meeting_time, "meeting_topic": MEETING_TOPIC, "host": host}


def send_reminder(
    *,
    meeting_time: str,
    meeting_topic: str,
    host: str,
    doc_token: str | None,
    title: str,
    dry_run: bool,
) -> bool:
    host_open_id = HOST_OPEN_IDS.get(host)
    if not host_open_id:
        raise LarkCliError(f"Host open_id is not configured for {host}.")

    text = (
        "本周业务周会提醒\n\n"
        f"会议时间：{meeting_time}\n"
        f"会议主题：{meeting_topic}\n"
        f"今天主持人：<at user_id=\"{host_open_id}\">{host}</at>\n"
        f"会议文档：{meeting_doc_url(doc_token)}\n"
        f"周报填写：{REPORT_VIEW_URL}\n\n"
        "请大家会前填写本周周报。"
    )
    run_lark(
        [
            "im",
            "+messages-send",
            "--chat-id",
            REMINDER_CHAT_ID,
            "--text",
            text,
            "--idempotency-key",
            f"weekly-meeting-reminder-{title}",
            "--as",
            "user",
            "--format",
            "json",
        ],
        skip=dry_run,
    )
    return True


def get_config_record_id() -> str | None:
    payload = run_lark(
        [
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            MEETING_CONFIG_TABLE_ID,
            "--field-id",
            CONFIG_NAME,
            "--filter-json",
            json.dumps(
                {
                    "logic": "and",
                    "conditions": [[CONFIG_NAME, "==", CONFIG_RECORD_NAME]],
                },
                ensure_ascii=False,
            ),
            "--limit",
            "10",
            "--as",
            "user",
            "--format",
            "json",
        ],
    )
    record_ids = payload["data"]["record_id_list"]
    if len(record_ids) > 1:
        raise LarkCliError(f"Expected one config record named {CONFIG_RECORD_NAME}, got {len(record_ids)}.")
    return record_ids[0] if record_ids else None


def update_weekly_config(
    *,
    week_record_id: str,
    meeting_time: str,
    meeting_topic: str,
    host: str,
    doc_token: str | None,
    dry_run: bool,
) -> tuple[bool, str | None]:
    host_open_id = HOST_OPEN_IDS.get(host)
    if not host_open_id:
        raise LarkCliError(f"Host open_id is not configured for {host}.")

    record_id = get_config_record_id()
    reminder_text = (
        f"会议时间：{meeting_time}\n"
        f"会议主题：{meeting_topic}\n"
        f"会议文档：{meeting_doc_url(doc_token)}\n"
        f"周报填写：{REPORT_VIEW_URL}\n\n"
        "请大家会前填写本周周报。"
    )
    fields = {
        CONFIG_NAME: CONFIG_RECORD_NAME,
        CONFIG_WEEK_RANGE: [{"id": week_record_id}],
        CONFIG_MEETING_TIME: meeting_time,
        CONFIG_TOPIC: meeting_topic,
        CONFIG_HOST: [{"id": host_open_id}],
        CONFIG_DOC_URL: meeting_doc_url(doc_token),
        CONFIG_REPORT_URL: REPORT_VIEW_URL,
        CONFIG_REMINDER_TEXT: reminder_text,
    }
    args = [
        "base",
        "+record-upsert",
        "--base-token",
        BASE_TOKEN,
        "--table-id",
        MEETING_CONFIG_TABLE_ID,
        "--json",
        json.dumps(fields, ensure_ascii=False),
        "--as",
        "user",
        "--format",
        "json",
    ]
    created = record_id is None
    if record_id:
        args.extend(["--record-id", record_id])
    payload = run_lark(args, skip=dry_run)
    if dry_run:
        return created, record_id or "<meeting-config-record-id>"
    updated_ids = payload["data"].get("record_id_list") or []
    if updated_ids:
        return created, updated_ids[0]
    return created, get_config_record_id()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Run as if today is this YYYY-MM-DD date.")
    parser.add_argument("--dry-run", action="store_true", help="Print lark-cli commands without writing.")
    parser.add_argument("--send-reminder", action="store_true", help="Send the Feishu group reminder with an @ mention.")
    args = parser.parse_args()

    today = parse_day(args.date)
    target_week_start = week_start_for(today)
    target_week = get_week_record(target_week_start)
    target_rows = list_report_rows_for_week(target_week["record_id"])
    source_week_start, source_rows = find_source_rows(target_week_start, dry_run=args.dry_run)

    if not source_rows and not args.dry_run:
        raise LarkCliError("Could not find source rows in the previous 12 weeks.")

    created_count, created_people = create_missing_blank_rows(
        source_rows,
        target_rows,
        target_week["record_id"],
        dry_run=args.dry_run,
    )
    update_report_view_filter(target_week["record_id"], dry_run=args.dry_run)
    title = meeting_title(target_week_start, target_week["label"])
    copied, meeting_doc_token = copy_template(title, dry_run=args.dry_run)
    meeting_doc = personalize_meeting_doc(
        meeting_doc_token,
        target_week_start,
        target_week["label"],
        dry_run=args.dry_run,
    )
    config_created, config_record_id = update_weekly_config(
        week_record_id=target_week["record_id"],
        meeting_time=meeting_doc["meeting_time"],
        meeting_topic=meeting_doc["meeting_topic"],
        host=meeting_doc["host"],
        doc_token=meeting_doc_token,
        dry_run=args.dry_run,
    )
    reminder_sent = False
    if args.send_reminder:
        reminder_sent = send_reminder(
            meeting_time=meeting_doc["meeting_time"],
            meeting_topic=meeting_doc["meeting_topic"],
            host=meeting_doc["host"],
            doc_token=meeting_doc_token,
            title=title,
            dry_run=args.dry_run,
        )

    print(
        json.dumps(
            {
                "target_date": str(today),
                "target_week_start": str(target_week_start),
                "target_week_record_id": target_week["record_id"],
                "target_week_label": target_week["label"],
                "source_week_start": str(source_week_start) if source_week_start else None,
                "created_blank_rows": created_count,
                "created_people": created_people,
                "view_filter_updated": True,
                "meeting_doc_title": title,
                "meeting_doc_copied": copied,
                "meeting_time": meeting_doc["meeting_time"],
                "meeting_topic": meeting_doc["meeting_topic"],
                "meeting_host": meeting_doc["host"],
                "meeting_config_record_id": config_record_id,
                "meeting_config_created": config_created,
                "reminder_sent": reminder_sent,
                "dry_run": args.dry_run,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LarkCliError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
