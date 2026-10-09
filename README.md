# Codex 技能集合

这是一个便于迁移的 Codex 个人技能集合仓库。

## 仓库结构

`skills/` 下的技能按**功能**分两层：`skills/<分类目录>/<技能名>/`。每个技能目录含 `SKILL.md`。

```
skills/
├── 01-代码生产/                需求 / spec → 可运行代码
│   ├── grill-me/
│   ├── grilling/
│   ├── implement/
│   └── tdd/
├── 02-代码检验/                已有代码 → 问题清单
│   ├── code-review/
│   ├── codeql/
│   ├── diagnosing-bugs/
│   └── semgrep/
├── 03-外部信息获取/            库名 / 网址 → 文档、数据、集成代码
│   ├── context7-mcp/
│   ├── firecrawl-build/
│   ├── firecrawl-build-scrape/
│   └── firecrawl-build-search/
├── 04-工程软件自动化/          参数 → 零件 / 装配 / 图纸文件
│   └── solidworks-automation/
├── 05-辅助学习/                目标 / 困惑 → 结构化方案
│   └── learn-anything-fast/
├── 06-情感部分/                情感 / 关系类，不参与安装
│   ├── goutoujunshi/
│   └── jev-chat-jarvis/
├── 07-健康管理/                饮食 / 体重数据 → 营养核算与配餐方案
│   ├── diet-tracker/
│   ├── health-data-toolkit/
│   └── meal-plan/
└── 08-消息协作/                文本 → 微信消息
    └── wechat-send/
```

分类目录只是容器，本身不是技能。同步脚本只读 `skills-manifest.json` 里的 `path` 字段，**不扫描目录**，所以分组对安装没有影响；`情感部分/` 不在清单的 `skills` 数组里，不会被安装。

系统自带技能和插件缓存已排除。

## 仓库是源，机器上的是镜像

**编辑只发生在仓库侧。**各 agent 的技能目录（`~/.codex/skills`、`~/.workbuddy/skills` …）只是派生镜像，不要在那里手工改 —— 改了也会被下一次同步覆盖。

镜像默认用**目录链接（junction）**指向仓库，所以改完仓库**立即生效**，不需要重跑任何命令，也不存在「仓库更新了但机器没变」的漂移。

```
仓库 skills/  ──▶  sync.ps1（幂等镜像）  ──▶  ~/.codex/skills/
                                             ~/.workbuddy/skills/
```

```powershell
# 首次，或换了一台电脑（克隆之后）
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1"

# 随时体检：只报告不改动，有差异时退出码为 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\sync.ps1" -Check

# 其它
.\sync.ps1 -Targets codex     # 只同步一个目标
.\sync.ps1 -Mode copy         # 不用链接，改成复制（改完仓库必须重跑）
.\sync.ps1 -Prune             # 摘掉镜像里已从清单移除的技能
.\sync.ps1 -Check -Log r.txt  # 体检结果写成 UTF-8 文本
```

`-Targets` 可选 `codex`、`workbuddy`、`claude-code`、`cursor`，默认前两个。`install.ps1` 保留为转发入口，参数原样透传。

> 执行策略若禁止运行脚本，用上面的 `-ExecutionPolicy Bypass` 形式；它只影响这一次调用，不改系统设置。

### 怎么定制

改 `skills/<分类目录>/<技能名>/` 里的文件 → 本机立刻生效 → `git commit` + `git push` → 另一台电脑 `git pull` 后再跑一次 `sync.ps1`。

### 安全约定

- 只处理 `skills-manifest.json` 的 `skills` 数组。镜像里的 `.system`、别处装来的技能、迁移 json **一律不碰**。
- 覆盖已有目录前先**移动**到 `~\.skill-archive\<目标>\<时间戳>\`（移动可逆，不做删除）。确认无用后自行清掉。
- 摘链接用 `rmdir`（只删链接本身），不用 `Remove-Item`。
- 归档目录刻意放在 agent 技能目录之外，否则里面的 `SKILL.md` 会被当成技能再扫一遍。

## 从 GitHub 安装单个技能

如果系统已安装 Python，也可以使用 Codex 技能安装器安装单个目录：

```powershell
$installer = "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py"
python $installer --repo heisetiantang/codex-skills-RE --path skills/03-外部信息获取/context7-mcp
```

## 技能清单

`skills-manifest.json` 是标准技能清单（v3 起带 `taxonomy` 分类表、每个技能带 `category` 字段，并用 `unlisted` 数组记录未入清单目录）；`THIRD_PARTY_SOURCES.md` 记录了上游来源和许可证说明。

**不知道某个技能是干什么的、什么时候该用？先看 [`技能速查.md`](技能速查.md)** —— 第一节按**功能**（输入 → 输出）分成代码生产 / 代码检验 / 外部信息获取 / 工程软件自动化 / 辅助学习 / 健康管理，第四节另有按场景反查的组合表，并标注了每个技能的依赖前提和自动触发条件。

可选的 `sources/` 目录保存上游源码快照，用于审计和后续更新，不会被同步脚本使用。

## 功能与调用方式

在 Codex 中可直接使用 `/技能名` 显式调用；也可以在任务中描述相同意图，让 Codex 自动匹配。少数技能声明了 `disable-model-invocation`（如 `implement`、`grill-me`），只能显式调用。下表是全量明细（按名称字母序），按**功能**分类的一页版见 [`技能速查.md`](技能速查.md)。

「功能域」列（括号内为所在分类目录）：① 代码生产 `01-代码生产`　② 代码检验 `02-代码检验`　③ 外部信息获取 `03-外部信息获取`　④ 工程软件自动化 `04-工程软件自动化`　⑤ 辅助学习 `05-辅助学习`　⑥ 情感 `06-情感部分`（不入安装清单）　⑦ 健康管理 `07-健康管理`　⑧ 消息协作 `08-消息协作`

| 功能域 | Skill | 用途 | 调用示例 |
| --- | --- | --- | --- |
| ② | `code-review` | 从规范和需求两个角度审查分支或 PR | `/code-review` 或“审查当前分支相对 main 的改动” |
| ② | `codeql` | 对多语言项目做跨文件安全与数据流分析 | `/codeql` 或“对当前仓库运行 CodeQL 安全扫描” |
| ③ | `context7-mcp` | 查询最新库、框架和 API 文档 | `/context7-mcp` 或“查当前版本的 Next.js middleware 文档” |
| ② | `diagnosing-bugs` | 建立可复现反馈回路，定位错误和性能回归 | `/diagnosing-bugs` 或“诊断这个接口偶发 500 的原因” |
| ⑦ | `diet-tracker` | 报餐自动估算热量与蛋白/脂肪/碳水/水分/纤维，按天周汇总并标达标 | `/diet-tracker` 或“我早上吃了两个鸡蛋一杯牛奶，帮我算算” |
| ③ | `firecrawl-build` | 在应用中集成 Firecrawl 网页数据能力 | `/firecrawl-build` 或“给应用加入网页抓取能力” |
| ③ | `firecrawl-build-scrape` | 在应用中抓取已知 URL 的单个网页 | `/firecrawl-build-scrape` 或“抓取这个 URL 的正文和 metadata” |
| ③ | `firecrawl-build-search` | 在应用中先搜索网页，再提取结果 | `/firecrawl-build-search` 或“给应用增加网页搜索功能” |
| ① | `grill-me` | 动手前用连环提问把计划和设计问到每个分支都有结论 | `/grill-me` 或“先把这个方案问清楚再动手” |
| ① | `grilling` | 被 `grill-me` 调用的访谈引擎：把决策当设计树，分轮只问已解锁的问题 | 一般不用手打，由 `grill-me` 触发 |
| ⑦ | `health-data-toolkit` | 餐食记账 + 体重追踪的脚本工具箱：xlsx/docx 双写、幂等记、闭环自查 | `/health-data-toolkit` 或“把今天的体重记下来，顺便查有没有漏记” |
| ① | `implement` | 按 spec 或 ticket 完成功能实现、测试和复核 | `/implement` 或“按这个 spec 实现功能并补齐测试” |
| ⑤ | `learn-anything-fast` | 制定学习路线、练习、测验和知识总结 | `/learn-anything-fast` 或“帮我制定一周的 Rust 学习计划” |
| ⑦ | `meal-plan` | 按体重与目标出热量线、三餐搭配、外卖白名单、应酬应对与平台期排查 | `/meal-plan` 或“体重卡住不掉了，先查什么” |
| ② | `semgrep` | 快速扫描常见安全问题和代码模式 | `/semgrep` 或“用 Semgrep 扫描这个项目的安全问题” |
| ④ | `solidworks-automation` | 通过 Python COM 自动化 SolidWorks 建模和导出 | `/solidworks-automation` 或“在 SolidWorks 中创建一个带孔圆盘” |
| ① | `tdd` | 以红绿重构方式先写测试再实现功能 | `/tdd` 或“用 TDD 实现购物车折扣规则” |
| ⑧ | `wechat-send` | 用桌面版微信给群 / 好友发消息，先准备后核验再发送 | `/wechat-send` 或“把这份总结发到我微信” |

常用组合：需求还没想清楚时先 `grill-me` 过一遍，再进 ①→②（`implement` + `tdd` → `code-review`）；排查问题用 `diagnosing-bugs` + `tdd`；安全扫描用 `semgrep` 后接 `codeql`；涉及第三方库、动手前先用 `context7-mcp`。记饮食与体重用 `diet-tracker`（零依赖）或 `health-data-toolkit`（需 xlsx/docx），**两者只留一个**，否则同一顿饭会被记两遍；配餐、外卖怎么点、平台期先查什么，用 `meal-plan`。要往微信发消息（把结论 / 提醒 / 日报发给自己或群里）用 `wechat-send`，前提是本机微信 PC 版已登录、且屏幕空闲（脚本带空闲门控，不会在你打字时抢焦点）。

请不要提交 Token、凭据、`.env` 文件、Codex 运行时缓存或本地数据库文件。
