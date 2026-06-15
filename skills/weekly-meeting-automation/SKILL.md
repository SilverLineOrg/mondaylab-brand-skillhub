---
name: weekly-meeting-automation
description: 当需要为 MondayLab / KiteoLab 的业务周会准备本周周报记录、更新本周视图筛选、复制周会模板、刷新周会配置表，或需要复跑某一周的周会准备流程时使用。适用于“每周五创建空白人力周报”“更新 06 周会配置”“生成本周业务周会文档”“让周六 Base 自动化读取配置并发提醒”等固定流程。
---

# MondayLab 周会自动化准备

这个 Skill 用于执行 MondayLab / KiteoLab 的固定周会准备流程。

它负责周五要完成的准备动作：

1. 找到本周对应的周度范围。
2. 参考往期周报记录，创建本周 6 条空白人力记录，并填好人员和负责子板块。
3. 更新“本周周报”视图筛选，让视图只展示当前周度范围。
4. 复制业务周会模板，生成本周周会文档。
5. 修改会议文档里的时间安排、会议主题和主持人。
6. 更新 `06 周会配置` 表中的 `weekly_current` 记录，让周六 17:00 的 Base 自动化可以直接读取本周数据并发送提醒。

默认不由 Codex 单独发群消息。群消息触达交给原有飞书 Base 自动化完成。

## 触发场景

当用户提到以下需求时，使用这个 Skill：

- “帮我跑一下这周的周会准备”
- “创建本周空白人力周报”
- “更新本周周报视图筛选”
- “复制本周周会模板”
- “更新 06 周会配置 / weekly_current”
- “复跑某个周五的周会自动化”
- “检查本周周会准备有没有完成”

如果用户只是要写文章、复盘 SOP 或生成说明文档，不要执行脚本；可以引用这里的流程作为事实背景。

## 前置条件

运行脚本前确认：

- 本机已安装并配置 `lark-cli`。
- 当前用户已经通过 `lark-cli auth login` 获得访问对应飞书多维表格、Wiki 和文档的权限。
- 在仓库根目录或 Skill 目录内运行脚本都可以，但建议从 Skill 目录运行，便于定位脚本。

脚本位置：

```bash
skills/weekly-meeting-automation/scripts/prepare_weekly_meeting.py
```

## 推荐执行方式

先 dry-run 看本次会操作哪一周：

```bash
python3 skills/weekly-meeting-automation/scripts/prepare_weekly_meeting.py --dry-run
```

确认无误后正式执行：

```bash
python3 skills/weekly-meeting-automation/scripts/prepare_weekly_meeting.py
```

如果需要复跑指定日期所在周，例如补跑 2026-06-12 这一周：

```bash
python3 skills/weekly-meeting-automation/scripts/prepare_weekly_meeting.py --date 2026-06-12
```

默认脚本只准备数据、文档和配置，不发送群消息。只有用户明确要求“由 Codex 直接发提醒”时，才加：

```bash
python3 skills/weekly-meeting-automation/scripts/prepare_weekly_meeting.py --send-reminder
```

## 主持人轮值

主持人按以下顺序轮值：

```text
冬灵 -> 周一同学Zelina -> 见莲花 -> 海豹 -> 亚克 -> 依谨
```

脚本会根据周度标签中的“第 N 周”自动计算本周主持人，并写入：

- 本周会议文档的“主持人”
- `06 周会配置` 的“主持人”
- `06 周会配置` 的提醒文案

## 输出检查

脚本执行完成后会输出 JSON。重点检查这些字段：

- `created_blank_rows`：本周新建了几条空白周报记录。
- `created_people`：本周新建记录对应的人员。
- `view_filter_updated`：本周周报视图筛选是否已更新。
- `meeting_doc_title`：生成或复用的周会文档标题。
- `meeting_time`：会议时间是否为本周周五晚上 19:00-20:00。
- `meeting_host`：本周主持人是否符合轮值顺序。
- `meeting_config_record_id`：`weekly_current` 配置记录是否已更新。
- `reminder_sent`：默认应为 `false`，除非显式加了 `--send-reminder`。

## 工作流边界

Codex / Agent 负责周五准备：

- 创建本周空白周报数据。
- 更新视图筛选。
- 复制并个性化会议文档。
- 刷新 `06 周会配置`。

飞书 Base 自动化负责周六触达：

- 每周六 17:00 触发。
- 查找 `06 周会配置` 中 `配置名称 = weekly_current` 的记录。
- 读取主持人、会议时间、会议主题、会议文档链接和周报填写链接。
- 发送周报填写提醒到群。

不要同时让 Codex 和 Base 自动化各发一条群消息，避免提醒重复。

## 异常处理

如果脚本失败：

1. 看错误是否来自 `lark-cli` 权限不足。若是，按提示补充授权。
2. 检查日期仓库里是否存在本周周度范围记录。
3. 检查往期周报是否有可参考的人员记录。
4. 检查周会模板和目标目录是否仍然存在。
5. 检查 `06 周会配置` 表字段是否被改名或删除。

如果只是重复执行同一周，脚本会尽量复用已有记录和文档，避免重复创建。
