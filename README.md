# Codex 技能集合

这是一个便于迁移的 Codex 个人技能集合仓库。

## 仓库结构

`skills/` 下的技能按**功能**分两层：`skills/<分类目录>/<技能名>/`。每个技能目录含 `SKILL.md`。

```
skills/
├── 01-code-production/          需求 / spec → 可运行代码
│   ├── implement/
│   └── tdd/
├── 02-code-inspection/          已有代码 → 问题清单
│   ├── code-review/
│   ├── codeql/
│   ├── diagnosing-bugs/
│   └── semgrep/
├── 03-info-retrieval/           库名 / 网址 → 文档、数据、集成代码
│   ├── context7-mcp/
│   ├── firecrawl-build/
│   ├── firecrawl-build-scrape/
│   └── firecrawl-build-search/
├── 04-engineering-automation/   参数 → 零件 / 装配 / 图纸文件
│   └── solidworks-automation/
├── 辅助学习/                    目标 / 困惑 → 结构化方案
│   └── learn-anything-fast/
└── 情感部分/                    情感 / 关系类，不参与安装
    ├── goutoujunshi/
    └── jev-chat-jarvis/
```

分类目录只是容器，本身不是技能。安装脚本只读 `skills-manifest.json` 里的 `path` 字段，**不扫描目录**，所以分组对安装没有影响；`情感部分/` 不在清单的 `skills` 数组里，不会被安装。

系统自带技能和插件缓存已排除。

## 在另一台 Windows 工作站安装

克隆本仓库，在仓库根目录打开 PowerShell，然后运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

安装脚本会把缺少的技能复制到 `$env:USERPROFILE\.codex\skills`，不会覆盖已有技能。安装完成后请重启 Codex。

## 从 GitHub 安装单个技能

如果系统已安装 Python，也可以使用 Codex 技能安装器安装单个目录：

```powershell
$installer = "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py"
python $installer --repo heisetiantang/codex-skills-RE --path skills/03-info-retrieval/context7-mcp
```

## 技能清单

`skills-manifest.json` 是标准技能清单（v3 起带 `taxonomy` 分类表、每个技能带 `category` 字段，并用 `unlisted` 数组记录未入清单目录）；`THIRD_PARTY_SOURCES.md` 记录了上游来源和许可证说明。

**不知道某个技能是干什么的、什么时候该用？先看 [`技能速查.md`](技能速查.md)** —— 第一节按**功能**（输入 → 输出）分成代码生产 / 代码检验 / 外部信息获取 / 工程软件自动化 / 辅助学习，第四节另有按场景反查的组合表，并标注了每个技能的依赖前提和自动触发条件。

可选的 `sources/` 目录保存上游源码快照，用于审计和后续更新，不会被安装脚本使用。

## 功能与调用方式

在 Codex 中可直接使用 `/技能名` 显式调用；也可以在任务中描述相同意图，让 Codex 自动匹配。少数技能（如 `implement`）声明了 `disable-model-invocation`，只能显式调用。下表是全量明细（按名称字母序），按**功能**分类的一页版见 [`技能速查.md`](技能速查.md)。

「功能域」列（括号内为所在分类目录）：① 代码生产 `01-code-production`　② 代码检验 `02-code-inspection`　③ 外部信息获取 `03-info-retrieval`　④ 工程软件自动化 `04-engineering-automation`　⑤ 辅助学习 `辅助学习`

| 功能域 | Skill | 用途 | 调用示例 |
| --- | --- | --- | --- |
| ② | `code-review` | 从规范和需求两个角度审查分支或 PR | `/code-review` 或“审查当前分支相对 main 的改动” |
| ② | `codeql` | 对多语言项目做跨文件安全与数据流分析 | `/codeql` 或“对当前仓库运行 CodeQL 安全扫描” |
| ③ | `context7-mcp` | 查询最新库、框架和 API 文档 | `/context7-mcp` 或“查当前版本的 Next.js middleware 文档” |
| ② | `diagnosing-bugs` | 建立可复现反馈回路，定位错误和性能回归 | `/diagnosing-bugs` 或“诊断这个接口偶发 500 的原因” |
| ③ | `firecrawl-build` | 在应用中集成 Firecrawl 网页数据能力 | `/firecrawl-build` 或“给应用加入网页抓取能力” |
| ③ | `firecrawl-build-scrape` | 在应用中抓取已知 URL 的单个网页 | `/firecrawl-build-scrape` 或“抓取这个 URL 的正文和 metadata” |
| ③ | `firecrawl-build-search` | 在应用中先搜索网页，再提取结果 | `/firecrawl-build-search` 或“给应用增加网页搜索功能” |
| ① | `implement` | 按 spec 或 ticket 完成功能实现、测试和复核 | `/implement` 或“按这个 spec 实现功能并补齐测试” |
| ⑤ | `learn-anything-fast` | 制定学习路线、练习、测验和知识总结 | `/learn-anything-fast` 或“帮我制定一周的 Rust 学习计划” |
| ② | `semgrep` | 快速扫描常见安全问题和代码模式 | `/semgrep` 或“用 Semgrep 扫描这个项目的安全问题” |
| ④ | `solidworks-automation` | 通过 Python COM 自动化 SolidWorks 建模和导出 | `/solidworks-automation` 或“在 SolidWorks 中创建一个带孔圆盘” |
| ① | `tdd` | 以红绿重构方式先写测试再实现功能 | `/tdd` 或“用 TDD 实现购物车折扣规则” |

常用组合：新功能走 ①→②（`implement` + `tdd` → `code-review`）；排查问题用 `diagnosing-bugs` + `tdd`；安全扫描用 `semgrep` 后接 `codeql`；涉及第三方库、动手前先用 `context7-mcp`。

请不要提交 Token、凭据、`.env` 文件、Codex 运行时缓存或本地数据库文件。
