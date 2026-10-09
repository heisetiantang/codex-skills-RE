---
name: wechat-send
display_name: 微信群发助手
display_name_en: WeChat Sender
description: 通过 Windows 微信 PC 版（Weixin.exe 4.x）自动向指定微信群或好友发送消息，支持多行文本、Emoji、@所有人/@指定成员；内置"先准备后确认"两段式安全流程、截图核验、只读诊断与防打扰空闲门控。当用户提出"给某个微信群/好友发消息""在群里通知一下""@所有人""定时群发""微信自动发送"等需求时使用本技能。
description_zh: 用桌面版微信向指定群或好友安全发送消息，支持多行文本、Emoji、@所有人；先准备后确认、截图核验、空闲门控，不抢用户焦点。
description_en: Send messages to any WeChat group or contact from the Windows WeChat desktop client, with multi-line text, emoji and @all mentions. Includes a two-stage prepare/verify/send safety flow and idle-gating so it never steals focus while you are working.
category: collaboration
version: 1.0.0
author: 待填写
---

# 微信发送（wechat-send）

用桌面版微信的 UI 自动化发消息。微信没有官方开放 API，所以本技能靠"搜索聊天 → 打开会话 → 剪贴板粘贴 → 回车发送"完成，**每一步都先截图、后发送**，避免发错人、发错群。

## 适用与不适用

- 适用：Windows 版微信（Weixin.exe 4.x）已登录的机器，发群消息或好友消息。
- 不适用：企业微信（用 webhook/群机器人更稳）、需要秒级精度的任务、微信未登录或电脑关机的场景。

## 环境准备（首次使用）

```bash
python -m venv "<SKILL_DIR>/.venv"
"<SKILL_DIR>/.venv/Scripts/python.exe" -m pip install -r "<SKILL_DIR>/scripts/requirements.txt"
```

之后统一用 `<SKILL_DIR>/.venv/Scripts/python.exe` 运行脚本。`<SKILL_DIR>` 是本技能所在目录。

## 不打扰原则（重要，先读这一节）

自动化会**抢走鼠标键盘焦点**几秒钟。用户在电脑前工作时反复触发，体验非常糟糕。所以：

1. **默认只用只读方式验证**：`scripts/selftest.py`（纯逻辑，不碰窗口/键盘/剪贴板）和
   `--stage probe`（只读窗口状态 + 截图，绝不激活窗口）。改完脚本先跑这两个。
2. **真机联调必须加空闲门控**：
   ```bash
   --require-idle 10 --wait-idle-max 180
   ```
   含义：等用户连续 10 秒没有键鼠输入再动手；最多等 180 秒，超时以退出码 6 放弃
   （**什么都不会发**）。宁可晚一点，也不要在用户打字时抢窗口。
3. **不要在用户明确正在操作微信时做真机测试**，先问一句。
4. 定时任务建议带上 `--require-idle 8 --wait-idle-max 150`，用户正在忙时自动让路。

## 命令参考

```
python wx_send.py --stage <probe|search|prepare|prepare-mention|send|abort> \
  [--chat "<群名或好友名>"] \
  [--message-file <正文文件> | --text "<正文>"] \
  [--mention-file <@消息文件> | --mention-text "<@消息>"] [--mention-name "所有人"] \
  --outdir <截图目录> \
  [--click-entry-y <像素Y> | --down <N>] \
  [--require-idle <秒>] [--wait-idle-max <秒>] [--config <json>]
```

| 参数 | 说明 |
| --- | --- |
| `--stage probe` | **只读**。打印微信窗口状态与用户空闲时长，存 `probe.png`。不需要 `--chat` |
| `--chat` | 群名称或好友备注名，必须能被微信搜索命中；`--group` 是它的旧别名 |
| `--message-file` / `--text` | 正文，二选一；文件按 UTF-8 读，`--text` 里的 `\n` 转成换行 |
| `--mention-file` / `--mention-text` | @消息的正文（**不含** `@某人` 本身，提及由脚本生成） |
| `--mention-name` | 默认 `所有人`；填姓名时会先在成员选择框里过滤再回车选中 |
| `--click-entry-y` | **推荐**。目标搜索结果行在 `s1_search.png` 里的像素 Y，脚本精确点击该行 |
| `--down` | 备选。方向键下移 N 行后回车；`0`（默认）= 直接回车首行 |
| `--require-idle` / `--wait-idle-max` | 空闲门控，见上一节 |
| `--config` | 覆盖默认坐标与等待时长（JSON） |

退出码：`0` 成功；`2` 环境失败（微信未运行/文件缺失）；`3` 安全拦截（窗口没能置前）；
`4` @成员选择框未弹出（输入框已清空，**未发送**）；`5` 查询词泄漏进了消息输入框
（Ctrl+F 没唤起搜索框，已自动清空，**未发送**）；`6` 用户正忙，主动让路（**未发送**）。

## 标准工作流（务必按顺序）

1. **search**：只输入查询词、不打开，产出 `s0_before_search.png`、`s1_search.png`。
2. **看图选行**：打开 `s1_search.png`，确认**搜索框里有查询词**（不是在消息输入框里），
   并找到目标会话所在行，记下该行中心的像素 Y。
   - 若第一行（高亮项）就是目标会话 → 可以不传 `--click-entry-y`，直接回车即可；
   - 若是"搜索网络结果"或别的条目 → **必须**用 `--click-entry-y` 精确点击目标行。
   - 若根本找不到目标会话 → 换更完整/唯一的名称重试，或放弃并报告。
3. **prepare**：打开会话并粘贴正文，**不发送**，产出 `s2_opened.png`、`s3_prepared.png`。
4. **核验**：`s3_prepared.png` 中聊天标题必须是目标群/人，输入框文字必须与预期完全一致。
   不符 → 执行 **abort**，报告失败，**不要发送**。
5. **send**：回车发送，产出 `s4_sent.png`；再核验消息气泡确实出现在目标会话里。
6. **@消息**（如需）：重复 3→4→5，改用 `prepare-mention`。
   核验 `s3b_prepared.png`：输入框里应出现**高亮提及样式**的 `@某人`，其后才是正文。

多行文本直接粘贴即可，粘贴的换行不会触发发送；只有脚本主动按回车才会发送。

## 安全机制（不要绕过）

- **两段式**：prepare 与 send 分离，中间必须有人（或 Agent）看图核验。
- **前台校验**：每次按键前都确认微信窗口在前台且未最小化，否则退出码 3。
  后台进程的 `SetForegroundWindow` 受系统限制，脚本内置 Alt 轻敲、最小化还原、
  TOPMOST 闪烁、`AttachThreadInput` 四重兜底。
- **泄漏防护**：Ctrl+F 偶发不生效时，查询词会掉进当前会话的输入框。脚本会对比
  "按 Ctrl+F 前"与"粘贴后"两张截图中的输入框区域，命中就清空并以退出码 5 中止，
  避免残文被误发。
- **提及保护**：`prepare-mention` 用截图差异判断成员选择框是否真的弹出，
  没弹出就清空输入框并退出码 4。
- **prepare 先清空输入框**（防上次残留被一起发出）；**send 阶段绝不清空**。

## 定时发送

用 `automation_update` 建 recurring 任务，prompt 里写全绝对路径与"看图核验"流程。
注意 RRULE 的 `BYHOUR` 与 `BYMINUTE` 会**叉乘**：要 10:00 和 14:35 两个时间点必须建两个任务。

内容需要"每天换说法但意思不变"时，把不可变更的事实写成规范文件，让每次运行先生成变体、
自检不通过就回退原文，再交给 prepare；用历史日志避免连续雷同。

## 调试与容错

- 坐标按窗口比例算（默认输入框 `0.68w, 0.82h`）。改版后点不到就调 `--config` 的 `input_xy`；
  搜索行点击的横向位置是 `result_click_x`（默认 `0.30w`）。
- DPI 缩放、窗口过小都会影响落点，建议窗口保持默认大小。
- 完整排障见 @references/troubleshooting.md。

## 关键约束

- 只允许发送用户明确要求的内容，不得自行改写正文含义。
- 未完成截图核验，一律不按 send。
- 用户正在用电脑时，优先让路（空闲门控）而不是抢焦点。
