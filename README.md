# Codex Skills

Personal Codex skill collection managed as one portable repository.

## Repository layout

Each direct child under `skills/` is an independently installable skill and contains a `SKILL.md` file. System-provided Codex skills and plugin caches are intentionally excluded.

## Install on another Windows workstation

Clone this repository, open PowerShell in the repository root, and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
```

The installer copies missing skills to `$env:USERPROFILE\.codex\skills`. It does not overwrite existing skills. Restart Codex after installation.

## Install one skill from GitHub

When Python is available, the Codex skill installer can install an individual directory:

```powershell
$installer = "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py"
python $installer --repo zgl610329-wq/codex-skills --path skills/context7-mcp
```

## Inventory

See `skills-manifest.json` for the canonical inventory and `THIRD_PARTY_SOURCES.md` for upstream sources and license notes.

The optional `sources/` directory contains upstream source snapshots for audit and future updates. It is not used by the installer.

Do not commit tokens, credentials, `.env` files, Codex runtime caches, or local database files.
