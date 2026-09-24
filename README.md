# Codex 技能集合

这是一个便于迁移的 Codex 个人技能集合仓库。

## 仓库结构

`skills/` 下的每个直接子目录都是一个可独立安装的技能，并包含 `SKILL.md` 文件。系统自带技能和插件缓存已排除。

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
python $installer --repo heisetiantang/codex-skills-RE --path skills/context7-mcp
```

## 技能清单

`skills-manifest.json` 是标准技能清单；`THIRD_PARTY_SOURCES.md` 记录了上游来源和许可证说明。

**不知道某个技能是干什么的、什么时候该用？先看 [`技能速查.md`](技能速查.md)** —— 按场景（学习调研 / 写代码 / 机械工程 / 网页数据 / 安全检查）划分，并标注了每个技能的依赖前提和自动触发条件。

可选的 `sources/` 目录保存上游源码快照，用于审计和后续更新，不会被安装脚本使用。

## 功能与调用方式

在 Codex 中可直接使用 `/技能名` 显式调用；也可以在任务中描述相同意图，让 Codex 自动匹配。少数技能（如 `implement`）声明了 `disable-model-invocation`，只能显式调用。下表是全量明细，按场景组织的一页版见 [`技能速查.md`](技能速查.md)。

| Skill | 用途 | 调用示例 |
| --- | --- | --- |
| `arxiv-digest` | 获取并整理 arXiv 日刊论文摘要 | `/arxiv-digest` 或“运行今天的 arXiv 论文摘要” |
| `code-review` | 从规范和需求两个角度审查分支或 PR | `/code-review` 或“审查当前分支相对 main 的改动” |
| `codeql` | 对多语言项目做跨文件安全与数据流分析 | `/codeql` 或“对当前仓库运行 CodeQL 安全扫描” |
| `context7-mcp` | 查询最新库、框架和 API 文档 | `/context7-mcp` 或“查当前版本的 Next.js middleware 文档” |
| `diagnosing-bugs` | 建立可复现反馈回路，定位错误和性能回归 | `/diagnosing-bugs` 或“诊断这个接口偶发 500 的原因” |
| `firecrawl-build` | 在应用中集成 Firecrawl 网页数据能力 | `/firecrawl-build` 或“给应用加入网页抓取能力” |
| `firecrawl-build-scrape` | 在应用中抓取已知 URL 的单个网页 | `/firecrawl-build-scrape` 或“抓取这个 URL 的正文和 metadata” |
| `firecrawl-build-search` | 在应用中先搜索网页，再提取结果 | `/firecrawl-build-search` 或“给应用增加网页搜索功能” |
| `implement` | 按 spec 或 ticket 完成功能实现、测试和复核 | `/implement` 或“按这个 spec 实现功能并补齐测试” |
| `learn-anything-fast` | 制定学习路线、练习、测验和知识总结 | `/learn-anything-fast` 或“帮我制定一周的 Rust 学习计划” |
| `semgrep` | 快速扫描常见安全问题和代码模式 | `/semgrep` 或“用 Semgrep 扫描这个项目的安全问题” |
| `solidworks-automation` | 通过 Python COM 自动化 SolidWorks 建模和导出 | `/solidworks-automation` 或“在 SolidWorks 中创建一个带孔圆盘” |
| `spatial-agi-research` | 执行 Spatial AGI 论文检索、精读和每日思考流程 | `/spatial-agi-research` 或“运行今天的 Spatial AGI 研究流程” |
| `tdd` | 以红绿重构方式先写测试再实现功能 | `/tdd` 或“用 TDD 实现购物车折扣规则” |

常用组合：普通开发使用 `implement` + `tdd` + `code-review`；排查问题使用 `diagnosing-bugs` + `tdd`；安全检查使用 `semgrep` 后接 `codeql`；涉及第三方库时先使用 `context7-mcp`。

请不要提交 Token、凭据、`.env` 文件、Codex 运行时缓存或本地数据库文件。
