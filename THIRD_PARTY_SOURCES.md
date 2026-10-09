# Third-Party Sources

The following skills are redistributed from upstream projects. Check the linked upstream repository before publishing changes or upgrading a skill.

The complete `mattpocock/skills` source snapshot is also kept under `sources/mattpocock-skills/` for audit and update reference; its `.git` metadata is intentionally excluded.

| Skills | Upstream | License note |
| --- | --- | --- |
| `implement`, `tdd`, `code-review`, `diagnosing-bugs`, `grill-me`, `grilling` | https://github.com/mattpocock/skills | Preserve the upstream repository license and notices. |
| `context7-mcp` | https://github.com/upstash/context7 | MIT according to the upstream package metadata. |
| `firecrawl-build`, `firecrawl-build-search`, `firecrawl-build-scrape` | https://github.com/firecrawl/firecrawl | The copied skill metadata declares ISC; verify upstream notices when updating. |
| `semgrep`, `codeql` | https://github.com/trailofbits/skills | CC BY-SA 4.0 according to the upstream repository README. Attribution and ShareAlike apply. |

`learn-anything-fast` and `solidworks-automation` are maintained in this collection or by its owner.

| Skills | Upstream | License note |
| --- | --- | --- |
| `diet-tracker`, `health-data-toolkit`, `meal-plan` | WorkBuddy 推荐市场（BuiltinMarket） | Redistributed from the WorkBuddy skill marketplace. The `_icon.png` files come from the marketplace CDN (`openplatform-cdn.codebuddy.cn`). A full static audit was run on 2026-09-29: no network calls, no auto-executed install/delete commands, no credential access. Marketplace IDs: `diet-tracker` = `skill_2097648139138326528`, `health-data-toolkit` = `skill_2098268065538043904`, `meal-plan` = `skill_2104100069178683392`. |
| `wechat-send` | WorkBuddy 推荐市场（BuiltinMarket） | Marketplace ID `skill_2104480104704995328`. Static audit run on 2026-09-30: **no network calls at all** (no `requests`/`urllib`/`socket`), no `subprocess`/`eval`/`exec`, no credential or filesystem-delete logic. It only drives the local WeChat desktop client through `pywin32` + `pillow` clipboard/screenshot automation, behind a two-stage prepare/verify/send flow and an idle gate. Dependencies: `pywin32`, `pillow` (declared in `scripts/requirements.txt`); the per-machine `.venv/` is git-ignored and intentionally not part of this repository. |
