<#
    install.ps1 - 兼容入口，真正的实现在 sync.ps1

    为什么换掉旧逻辑
      旧版是「目标已存在就 SKIP」，装过一次的技能永远不会更新 —— 这与
      「本机定制 → 上传 → 其他电脑生效」的目标直接冲突。
      现在统一走 sync.ps1 的幂等镜像：让镜像始终等于仓库。

    用法（参数原样转发给 sync.ps1）
      powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1"
      powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install.ps1" -Check

      可转发：-Mode link|copy  -Targets codex,workbuddy  -Check  -Prune  -Log 报告路径

    动手前先体检，它会告诉你哪些镜像与仓库不一致：
      .\sync.ps1 -Check
#>
& (Join-Path $PSScriptRoot 'sync.ps1') @args
