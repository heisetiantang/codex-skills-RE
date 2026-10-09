<#
    sync.ps1 - 把仓库里的技能镜像到各 agent 的技能目录

    原理
      仓库是唯一事实源（single source of truth），机器上的 agent 技能目录只是派生镜像。
      所有编辑都发生在仓库侧；镜像侧不要手工改，改了也会被下一次同步覆盖。

    用法
      .\sync.ps1                    # 同步清单里的技能到 codex + workbuddy（默认）
      .\sync.ps1 -Check             # 只体检不改动；有差异时退出码 1
      .\sync.ps1 -Check -Log r.txt  # 顺便把报告写成 UTF-8 文本
      .\sync.ps1 -Mode copy         # 用复制代替目录链接
      .\sync.ps1 -Targets codex     # 只同步一个目标
      .\sync.ps1 -Prune             # 额外摘掉镜像里已从清单移除的技能链接

    安全约定
      1. 只处理 skills-manifest.json 的 skills 数组，镜像里的其它条目（.system、
         别处装来的技能、迁移 json）一律不碰。
      2. 覆盖已有目录前先"移动"到 ~\.skill-archive\<目标>\<时间戳>\，不做递归删除 ——
         移动可逆，删除不可逆；归档放在 agent 技能目录之外，免得被当成技能扫出来。
      3. 摘链接用 rmdir（只删链接本身），不用 Remove-Item（可能跟着进目标目录）。
#>
[CmdletBinding()]
param(
    [ValidateSet('link', 'copy')]
    [string]$Mode = 'link',

    [string[]]$Targets = @('codex', 'workbuddy'),

    [switch]$Check,
    [switch]$Prune,

    [string]$Log = ''
)

$ErrorActionPreference = 'Stop'

$report = New-Object System.Collections.Generic.List[string]
function Say {
    param([string]$Message)
    $report.Add($Message)
    Microsoft.PowerShell.Utility\Write-Output $Message
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $repoRoot 'skills-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) { throw "找不到清单：$manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

$TargetMap = [ordered]@{
    'codex'       = Join-Path $env:USERPROFILE '.codex\skills'
    'workbuddy'   = Join-Path $env:USERPROFILE '.workbuddy\skills'
    'claude-code' = Join-Path $env:USERPROFILE '.claude\skills'
    'cursor'      = Join-Path $env:USERPROFILE '.cursor\skills'
}

function Get-Fingerprint {
    param([string]$Path)
    $prefix = $Path.TrimEnd('\') + '\'
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($f in (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
                    Sort-Object FullName)) {
        if ($f.FullName -like '*\.git\*') { continue }
        if ($f.Name -eq 'desktop.ini') { continue }
        $rel = $f.FullName.Substring($prefix.Length).Replace('\', '/')
        $lines.Add($rel + ':' + (Get-FileHash -LiteralPath $f.FullName -Algorithm MD5).Hash)
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
    $md5 = [Security.Cryptography.MD5]::Create()
    return ([BitConverter]::ToString($md5.ComputeHash($bytes)) -replace '-', '')
}

function Get-LinkTarget {
    param([string]$Path)
    try { $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop } catch { return $null }
    if ($item.LinkType -ne 'Junction' -and $item.LinkType -ne 'SymbolicLink') { return $null }
    $t = $item.Target
    if ($t -is [array]) { $t = $t[0] }
    return $t
}

function New-DirLink {
    param([string]$Link, [string]$Target)
    try {
        New-Item -ItemType Junction -Path $Link -Target $Target -ErrorAction Stop | Out-Null
    } catch {
        $null = & cmd.exe /c mklink /J "$Link" "$Target"
        if ($LASTEXITCODE -ne 0) { throw "建立目录链接失败：$Link -> $Target" }
    }
}

function Move-ToArchive {
    param([string]$Path, [string]$ArchiveRoot, [string]$Name)
    New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
    $dest = Join-Path $ArchiveRoot $Name
    if (Test-Path -LiteralPath $dest) { $dest = $dest + '.' + (Get-Date -Format 'HHmmss') }
    Move-Item -LiteralPath $Path -Destination $dest -Force
    return $dest
}

function Exit-With {
    param([int]$Code)
    if ($Log -ne '') {
        $full = $Log
        if (-not [IO.Path]::IsPathRooted($full)) { $full = Join-Path $repoRoot $full }
        [IO.File]::WriteAllLines($full, $report, (New-Object Text.UTF8Encoding($false)))
        Write-Output ("报告已写入 " + $full)
    }
    exit $Code
}

$names = @($manifest.skills | ForEach-Object { $_.name })
$pending = $false
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

Say ''
Say ("仓库 : " + $repoRoot)
$modeLabel = $Mode
if ($Check) { $modeLabel = $modeLabel + '  [体检，不改动]' }
Say ("模式 : " + $modeLabel)
Say ("清单 : " + $names.Count + " 个技能")
Say ''

foreach ($t in $Targets) {
    if (-not $TargetMap.Contains($t)) {
        Say ("  ! 未知目标：" + $t + "（可选 " + (($TargetMap.Keys) -join ', ') + "）")
        continue
    }
    $targetRoot = $TargetMap[$t]

    Say ("[" + $t + "] " + $targetRoot)
    if (-not $Check) { New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null }
    if (-not (Test-Path -LiteralPath $targetRoot)) {
        Say '  目录不存在，跳过'
        Say ''
        continue
    }

    $archiveRoot = Join-Path $env:USERPROFILE ('.skill-archive\' + $t + '\' + $stamp)

    foreach ($skill in $manifest.skills) {
        $src = Join-Path $repoRoot $skill.path
        $dest = Join-Path $targetRoot $skill.name
        $state = $null

        if (-not (Test-Path -LiteralPath (Join-Path $src 'SKILL.md'))) {
            Say ("  src-missing " + $skill.name)
            $pending = $true
            continue
        }

        if (-not (Test-Path -LiteralPath $dest)) {
            $state = 'new'
        }
        else {
            $linkTarget = Get-LinkTarget -Path $dest
            if ($linkTarget) {
                if ($linkTarget.TrimEnd('\') -ieq $src.TrimEnd('\')) { $state = 'ok-link' }
                else { $state = 'relink' }
            }
            else {
                $same = ((Get-Fingerprint -Path $src) -eq (Get-Fingerprint -Path $dest))
                if ($same) {
                    if ($Mode -eq 'copy') { $state = 'ok-copy' } else { $state = 'relink-same' }
                }
                else {
                    if ($Mode -eq 'copy') { $state = 'update' } else { $state = 'relink-diff' }
                }
            }
        }

        if ($state -eq 'ok-link' -or $state -eq 'ok-copy') {
            Say ("  ok          " + $skill.name)
            continue
        }

        $pending = $true
        if ($Check) {
            Say ("  " + $state.PadRight(12) + $skill.name)
            continue
        }

        $note = ''
        if (Test-Path -LiteralPath $dest) {
            if ($state -eq 'relink-diff') { $note = '  (镜像侧与仓库不一致，旧版已归档)' }
            $null = Move-ToArchive -Path $dest -ArchiveRoot $archiveRoot -Name $skill.name
            if (-not $note) { $note = '  (旧副本已归档)' }
        }

        if ($Mode -eq 'link') {
            New-DirLink -Link $dest -Target $src
            Say ("  " + $state.PadRight(12) + $skill.name + " -> " + $skill.path + $note)
        }
        else {
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
            $null = & robocopy "$src" "$dest" /E /NFL /NDL /NJH /NJS /NP
            if ($LASTEXITCODE -ge 8) { throw "robocopy 失败：$src -> $dest" }
            Say ("  copy         " + $skill.name + $note)
        }
    }

    if ($Prune) {
        foreach ($d in (Get-ChildItem -LiteralPath $targetRoot -Directory -Force)) {
            if ($names -contains $d.Name) { continue }
            $linkTarget = Get-LinkTarget -Path $d.FullName
            if (-not $linkTarget) { continue }
            if ($linkTarget -notlike ($repoRoot + '\skills\*')) { continue }
            if ($Check) {
                Say ("  prune        " + $d.Name)
                $pending = $true
                continue
            }
            $null = & cmd.exe /c rmdir "$($d.FullName)"
            Say ("  prune        " + $d.Name + "  (已从清单移除)")
        }
    }

    if (Test-Path -LiteralPath $archiveRoot) {
        Say ("  归档目录   " + $archiveRoot)
    }
    Say ''
}

if ($Check) {
    if ($pending) {
        Say '结果：有差异，跑一次 .\sync.ps1 即可补齐。'
        Exit-With 1
    }
    Say '结果：镜像与仓库一致。'
    Exit-With 0
}

Say '同步完成。镜像侧不要手工改，改动请进仓库。'
Exit-With 0
