$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $repositoryRoot "skills-manifest.json"
$destinationRoot = Join-Path $env:USERPROFILE ".codex\skills"
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

New-Item -ItemType Directory -Force -Path $destinationRoot | Out-Null

foreach ($skill in $manifest.skills) {
    $source = Join-Path $repositoryRoot $skill.path
    $destination = Join-Path $destinationRoot $skill.name

    if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md"))) {
        throw "Invalid skill directory: $source"
    }

    if (Test-Path -LiteralPath $destination) {
        Write-Host "SKIP  $($skill.name) (already exists)"
        continue
    }

    Copy-Item -LiteralPath $source -Destination $destination -Recurse
    Write-Host "OK    $($skill.name)"
}

Write-Host ""
Write-Host "Installation complete. Restart Codex to load the new skills."
