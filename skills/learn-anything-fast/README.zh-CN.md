# 十倍速学习教练

[English](README.md)

> 把任何主题变成一个基于可靠资料、可以验收的学习闭环。

`learn-anything-fast` 是一个可移植的 [Agent Skill](https://agentskills.io/specification)，帮助学习者把一个模糊目标，例如“学会 AI Agent”，拆成一条可以执行、练习和验证的路线。它采用“建立地图、主动回忆、动手实践、纠错、压缩、费曼复述、外部校准”的循环，而不是只做内容总结。

这里的“十倍速”是学习效率的愿景，不是未经验证的承诺。真正的进步要通过可观察的证据证明：可运行的作品、测试结果、测验、自己的解释和独立完成的任务。

## 它能做什么

- 根据学习者当前能力建立从入门到独立工作的能力阶梯。
- 找出最值得优先掌握的 20% 核心内容，并区分现在学习、先认识、以后再学的内容。
- 生成包含时间安排、里程碑、练习任务、交付物和晋级门槛的学习计划。
- 以一次一个问题或任务的方式进行辅导，先让学习者作答，不提前泄露答案。
- 区分知识缺口、推理错误、执行错误和粗心错误，并维护薄弱项台账。
- 只根据学习者实际接触过的材料制作一页速查表。
- 通过费曼复述发现含糊、遗漏或被术语掩盖的理解。
- 对照一手资料、官方文档和真实运行结果，校准学习结论。

## 学习模式

skill 会根据请求选择最合适的模式：

| 模式 | 适合场景 |
|---|---|
| `Plan` | 学习路线、时间表、里程碑和练习顺序 |
| `Coach` | 每轮只进行一个问题或任务的互动辅导 |
| `Diagnose` | 基线测试和薄弱项台账 |
| `Resource` | 最多五个经过筛选的可靠学习资源 |
| `Compress` | 一页速查表 |
| `Teach-back` | 评审和修正学习者自己的讲解 |
| `Full loop` | 组合以上模式并持续维护学习状态的完整学习计划 |

## 学习闭环

```text
建立地图 -> 聚焦 -> 主动回忆 -> 实践 -> 纠错 -> 压缩 -> 讲解 -> 验证
    ^                                                        |
    +--------------------- 根据证据调整 ----------------------+
```

学习者的产出应多于 AI。熟悉感不等于掌握：只有通过规定的门槛，例如两轮主动回忆达到标准并独立完成一个实现任务，才允许进入下一个阶段。

## 兼容性

跨 Agent 的核心文件是 `SKILL.md` 和相对路径引用的 `references/` 目录。`agents/openai.yaml` 是可选的 Codex/ChatGPT 界面元数据，不支持该文件的宿主会自动忽略它。本仓库本身不依赖 API Key、MCP Server 或额外运行时。

| 宿主 | 用户级目录 | 项目级目录 | 使用方式 |
|---|---|---|---|
| Codex | `~/.agents/skills/learn-anything-fast/` | `.agents/skills/learn-anything-fast/` | 输入 `$learn-anything-fast` 或使用 `/skills` |
| Claude Code | `~/.claude/skills/learn-anything-fast/` | `.claude/skills/learn-anything-fast/` | 输入 `/learn-anything-fast` 或直接描述学习需求 |
| VS Code 中的 GitHub Copilot | `~/.copilot/skills/learn-anything-fast/` | `.github/skills/learn-anything-fast/` 或 `.agents/skills/learn-anything-fast/` | 输入 `/learn-anything-fast`，或让 Copilot 自动加载 |
| Gemini CLI | `~/.gemini/skills/learn-anything-fast/` | `.gemini/skills/learn-anything-fast/` | 执行 `/skills reload` 后让 Gemini 使用它 |
| 其他兼容宿主 | 以宿主文档为准 | 以宿主文档为准 | 遵循宿主的发现和调用方式 |

Codex 的部分桌面版本还会暴露 `~/.codex/skills/`；可以用 `/skills` 查看当前实际发现路径。同一个 skill 只需安装到一个有效目录。

## 安装

将仓库克隆到对应宿主的 skills 目录。下面以用户级安装为例：

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.agents/skills/learn-anything-fast
```

已有安装时更新：

```bash
git -C ~/.agents/skills/learn-anything-fast pull
```

如果宿主没有立即发现 skill，请执行对应的 skills reload 命令或重启宿主。未来如果仓库增加脚本或工具，启用前请先审阅 skill 内容。

## 各主流 Agent 的安装和使用

### Codex

Codex 当前推荐的用户级目录是 `~/.agents/skills/`，项目内目录是 `.agents/skills/`。部分桌面版本也会使用 `~/.codex/skills/`，请用 `/skills` 确认。

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.agents/skills/learn-anything-fast
```

显式使用：

```text
$learn-anything-fast 帮我学习 Python 异步编程，每天 30 分钟，目标是能独立写出可靠的异步服务。
```

### Claude Code

Claude Code 的用户级目录是 `~/.claude/skills/`，项目级目录是 `.claude/skills/`。

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.claude/skills/learn-anything-fast
```

显式使用：

```text
/learn-anything-fast 为我设计一条每天 30 分钟的 Python 异步编程学习路线。
```

### VS Code 中的 GitHub Copilot

VS Code 支持项目级 `.github/skills/`、`.claude/skills/`、`.agents/skills/`，也支持用户级 `~/.copilot/skills/`。

在项目根目录执行：

```bash
mkdir -p .github/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git .github/skills/learn-anything-fast
```

然后在 Copilot Chat 中使用：

```text
/learn-anything-fast 为我设计一条每天 30 分钟的 Python 学习路线。
```

输入 `/skills` 可以查看和管理已发现的 skills。

### Gemini CLI

Gemini CLI 的用户级目录是 `~/.gemini/skills/`，项目级目录是 `.gemini/skills/`。

```bash
mkdir -p ~/.gemini/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.gemini/skills/learn-anything-fast
```

在 Gemini CLI 中执行：

```text
/skills reload
/skills list
```

然后使用：

```text
Use the learn-anything-fast skill to create a source-grounded roadmap for learning RAG in 30 minutes per day.
```

### 其他兼容 Agent Skills 的宿主

将整个仓库目录复制到宿主文档指定的 skills 目录。可移植入口始终是 `SKILL.md`；需要时再读取 `references/prompts-and-templates.md`。

如果某个 Agent 不支持 Agent Skills 规范，仍可手动使用：把 `SKILL.md` 内容放入它的系统提示词或项目规则，再把 `references/` 作为辅助上下文提供。但这时不会有自动发现、斜杠命令和按需加载。

## 使用方法

显式调用 skill：

```text
使用 $learn-anything-fast 帮我学习 Python 异步编程，每天 30 分钟，目标是能独立写出可靠的异步服务。
```

也可以指定模式：

```text
使用 $learn-anything-fast 的 Diagnose 模式，测试我对 RAG 的理解。
```

创建完整学习计划：

```text
使用 $learn-anything-fast 帮我从零掌握 AI Agent 应用开发，要求有项目、测验、晋级门槛和每周复盘。
```

## 仓库结构

```text
learn-anything-fast/
├── SKILL.md                         # 可移植的 skill 核心指令
├── agents/
│   └── openai.yaml                  # 可选的 Codex/ChatGPT 元数据
├── references/
│   └── prompts-and-templates.md      # 输出模板和学习状态格式
├── README.md                        # 英文文档，默认首页
├── README.zh-CN.md                  # 中文文档
└── LICENSE
```

## 设计原则

1. **证据优先。** “我看过了”不算完成证据。
2. **先实践再解释。** 先主动回忆或动手构建，再看完整答案。
3. **一次修正一个关键缺口。** 优先修复当前阻碍进步的最小问题。
4. **结论有来源。** 优先使用一手资料和官方文档，并标记不确定性与推断。
5. **根据证据调整范围。** 达成目标能力后停止无意义地扩展课程。
6. **保留人的主动性。** AI 负责组织练习和反馈，学习者负责思考和构建。

## 参与贡献

欢迎贡献：

- 面向具体领域的新示例和练习任务。
- 针对常见学习错误的更好评分标准。
- 面向不同主题的官方资源学习路径。
- 保留学习闭环行为的翻译，而不只是逐句翻译。
- 包含提示词、期望行为、实际行为和上下文的 Bug 报告。

请让模板具体且可测试，避免把这个 skill 变成泛泛的鸡汤教练或被动总结器。

## 许可证

MIT，详见 [LICENSE](LICENSE)。

## 官方文档

- [Agent Skills 规范](https://agentskills.io/specification)
- [Codex：构建 Skills](https://developers.openai.com/plugins/build/skills.md)
- [Claude Code：扩展 Claude](https://code.claude.com/docs/en/skills)
- [VS Code：使用 Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Gemini CLI：工具与 Skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/tools.md)
