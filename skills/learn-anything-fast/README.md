# Learn Anything Fast

[中文说明](README.zh-CN.md)

> Turn any topic into a source-grounded, measurable learning loop.

`learn-anything-fast` is a portable [Agent Skill](https://agentskills.io/specification) for learning a topic deeply enough to use it independently. It turns a vague goal such as “learn AI agents” into a practical loop of mapping, retrieval, practice, correction, compression, teach-back, and external verification.

The skill treats “10x” as an aspiration, not a promise. Progress is demonstrated with observable evidence: working artifacts, test results, quizzes, explanations, and independent tasks.

## Compatibility

The portable core is the `SKILL.md` file plus the relative `references/` directory. The optional `agents/openai.yaml` file adds Codex/ChatGPT UI metadata and is ignored by hosts that do not use it. This repository has no API-key, MCP, or runtime dependency of its own.

| Host | User-level location | Project-level location | How to use |
|---|---|---|---|
| Codex | `~/.agents/skills/learn-anything-fast/` | `.agents/skills/learn-anything-fast/` | Type `$learn-anything-fast` or use `/skills` |
| Claude Code | `~/.claude/skills/learn-anything-fast/` | `.claude/skills/learn-anything-fast/` | Type `/learn-anything-fast` or ask naturally |
| GitHub Copilot in VS Code | `~/.copilot/skills/learn-anything-fast/` | `.github/skills/learn-anything-fast/` or `.agents/skills/learn-anything-fast/` | Use `/learn-anything-fast` or let Copilot auto-load it |
| Gemini CLI | `~/.gemini/skills/learn-anything-fast/` | `.gemini/skills/learn-anything-fast/` | Run `/skills reload`, then ask Gemini to use it |
| Other compatible hosts | Their documented skills directory | Their documented project skills directory | Follow the host's discovery and invocation rules |

Codex desktop builds may also expose `~/.codex/skills/`; use the `/skills` list or the host documentation to confirm the active path. Only one Codex location is needed.

## What It Does

- Builds a level ladder from a learner's current ability to independent performance.
- Identifies the highest-leverage 20% of concepts and separates what to learn now, recognize, or defer.
- Creates time-boxed learning plans with milestones, practice tasks, deliverables, and advancement gates.
- Coaches with one question or task at a time, without revealing the answer first.
- Diagnoses knowledge, reasoning, execution, and careless errors in a compact weakness ledger.
- Produces one-page cheat sheets only from material the learner has actually encountered.
- Uses Feynman teach-backs to find vague, missing, or jargon-hidden understanding.
- Calibrates claims against primary sources, official documentation, and real artifacts.

## Learning Modes

The skill selects the smallest mode that fits the request:

| Mode | Use it for |
|---|---|
| `Plan` | A roadmap, schedule, milestones, and practice sequence |
| `Coach` | Interactive teaching with one question or task per turn |
| `Diagnose` | A baseline test and a weakness ledger |
| `Resource` | A shortlist of up to five source-grounded resources |
| `Compress` | A one-page cheat sheet |
| `Teach-back` | Review and repair of the learner's own explanation |
| `Full loop` | A complete program that combines the modes and maintains state |

## The Learning Loop

```text
Map -> Focus -> Retrieve -> Practice -> Correct -> Compress -> Teach -> Verify
  ^                                                               |
  +------------------------- adapt from evidence -----------------+
```

The learner produces more than the AI. Familiarity alone is not treated as mastery: advancement requires a defined threshold, such as two successful retrieval rounds plus an independent implementation task.

## Install

Clone this repository into the host's skills directory. Replace the destination with the path for your host from the table above:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.agents/skills/learn-anything-fast
```

For an existing installation, update it with:

```bash
git -C ~/.agents/skills/learn-anything-fast pull
```

If the host does not discover the skill immediately, reload its skills list or restart the host. Review the skill before enabling it in a trusted project, especially if future versions add scripts or tools.

## Install And Use By Host

### Codex

Codex's current user-level skills directory is `~/.agents/skills/`; repository skills live in `.agents/skills/`. Some desktop builds also expose `~/.codex/skills/`, so verify with `/skills`.

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.agents/skills/learn-anything-fast
```

Use it explicitly:

```text
$learn-anything-fast Help me learn Python async programming in 30 minutes per day and become able to build reliable async services.
```

Codex can also load it automatically when the request matches the `description` in `SKILL.md`.

### Claude Code

Claude Code discovers personal skills under `~/.claude/skills/` and project skills under `.claude/skills/`.

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.claude/skills/learn-anything-fast
```

Use it with:

```text
/learn-anything-fast Design a 30-minute-per-day plan to master Python async programming.
```

Claude Code can also activate it automatically when the request matches the skill description.

### GitHub Copilot In VS Code

VS Code supports project skills in `.github/skills/`, `.claude/skills/`, and `.agents/skills/`, plus personal skills under `~/.copilot/skills/`.

From the root of your project:

```bash
mkdir -p .github/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git .github/skills/learn-anything-fast
```

Then open the Chat view and use:

```text
/learn-anything-fast for a 30-minute-per-day Python learning plan
```

Or ask a matching learning question and let Copilot load the skill automatically. The `/skills` menu can list and manage discovered skills.

### Gemini CLI

Gemini CLI discovers user skills in `~/.gemini/skills/` and project skills in `.gemini/skills/`.

```bash
mkdir -p ~/.gemini/skills
git clone https://github.com/zgl610329-wq/learn-anything-fast.git ~/.gemini/skills/learn-anything-fast
```

Inside Gemini CLI, refresh and inspect the skill list:

```text
/skills reload
/skills list
```

Then use it explicitly:

```text
Use the learn-anything-fast skill to create a source-grounded roadmap for learning RAG in 30 minutes per day.
```

### Other Agent Skills-Compatible Hosts

Copy the repository directory into the host's documented skills location. The portable entrypoint is always `SKILL.md`; `references/prompts-and-templates.md` is loaded when the skill asks for a roadmap, quiz ledger, cheat sheet, or teach-back review.

If a host does not support the Agent Skills format, it can still use the project manually: paste the contents of `SKILL.md` into its system/project instructions and provide the `references/` files as supporting context. Automatic discovery, slash commands, and progressive loading will not be available in that case.

## Use It

Call the skill explicitly:

```text
使用 $learn-anything-fast 帮我学习 Python 异步编程，每天 30 分钟，目标是能独立写出可靠的异步服务。
```

You can also request a specific mode:

```text
使用 $learn-anything-fast 的 Diagnose 模式，测试我对 RAG 的理解。
```

For a complete learning program:

```text
使用 $learn-anything-fast 帮我从零掌握 AI Agent 应用开发，要求有项目、测验、晋级门槛和每周复盘。
```

## Repository Layout

```text
learn-anything-fast/
├── SKILL.md                         # Portable skill instructions
├── agents/
│   └── openai.yaml                  # Optional Codex/ChatGPT metadata
├── references/
│   └── prompts-and-templates.md      # Output templates and state formats
├── README.md                        # English documentation, default landing page
├── README.zh-CN.md                  # Chinese documentation
└── LICENSE
```

## Design Principles

1. **Evidence over feeling.** “I read it” is not completion evidence.
2. **Practice before explanation.** Try to retrieve or build before seeing a polished answer.
3. **One useful correction at a time.** Repair the smallest gap that blocks progress.
4. **Source-grounded claims.** Prefer primary and official sources; label uncertainty and inference.
5. **Adaptive scope.** Stop expanding the curriculum when the target performance is demonstrated.
6. **Human agency.** The AI structures practice and feedback; the learner does the thinking and building.

## Contributing

Useful contributions include:

- New domain-specific examples and practice tasks.
- Better rubrics for diagnosing common learning errors.
- Official-source resource paths for additional topics.
- Translations that preserve the learning-loop behavior, not just the wording.
- Bug reports with the prompt, expected behavior, actual behavior, and relevant context.

Keep templates concrete and testable. Avoid turning the skill into a generic motivational coach or a passive summarizer.

## License

MIT. See [LICENSE](LICENSE).

## Official Host Documentation

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex: Build skills](https://developers.openai.com/plugins/build/skills.md)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
- [VS Code: Use Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [Gemini CLI: Tools and skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/tools.md)
