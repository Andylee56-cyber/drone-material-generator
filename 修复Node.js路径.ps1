# Node.js PATH 修复脚本
# 使用方法：以管理员身份运行 PowerShell，然后执行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Node.js PATH 修复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 错误：请以管理员身份运行 PowerShell！" -ForegroundColor Red
    Write-Host "   右键点击 PowerShell → 以管理员身份运行" -ForegroundColor Yellow
    pause
    exit
}

# 可能的 Node.js 安装路径
$nodePaths = @(
    "D:\claude code所有组件+配置",  # 用户自定义安装路径
    "C:\Program Files\nodejs",
    "C:\Program Files (x86)\nodejs",
    "$env:APPDATA\npm"
)

Write-Host "正在搜索 Node.js 安装位置..." -ForegroundColor Yellow

$foundPath = $null
foreach ($path in $nodePaths) {
    if (Test-Path "$path\node.exe") {
        $foundPath = $path
        Write-Host "✅ 找到 Node.js: $path" -ForegroundColor Green
        break
    }
}

# 如果没找到，尝试搜索 D 盘
if (-not $foundPath) {
    Write-Host "在默认位置未找到，正在搜索 D 盘..." -ForegroundColor Yellow
    $searchPaths = @(
        "D:\",
        "C:\Program Files",
        "C:\Program Files (x86)"
    )
    
    foreach ($searchPath in $searchPaths) {
        if (Test-Path $searchPath) {
            $result = Get-ChildItem -Path $searchPath -Filter "node.exe" -Recurse -ErrorAction SilentlyContinue -Depth 3 | Select-Object -First 1
            if ($result) {
                $foundPath = $result.DirectoryName
                Write-Host "✅ 找到 Node.js: $foundPath" -ForegroundColor Green
                break
            }
        }
    }
}

if (-not $foundPath) {
    Write-Host ""
    Write-Host "❌ 未找到 Node.js 安装！" -ForegroundColor Red
    Write-Host "请先安装 Node.js：" -ForegroundColor Yellow
    Write-Host "1. 访问: https://npmmirror.com/mirrors/node/" -ForegroundColor Cyan
    Write-Host "2. 下载最新 LTS 版本" -ForegroundColor Cyan
    Write-Host "3. 安装时确保勾选 'Add to PATH'" -ForegroundColor Cyan
    pause
    exit
}

# 检查系统 PATH
Write-Host ""
Write-Host "检查系统 PATH 环境变量..." -ForegroundColor Yellow
$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($systemPath -like "*$foundPath*") {
    Write-Host "✅ Node.js 路径已存在于系统 PATH 中" -ForegroundColor Green
} else {
    Write-Host "⚠️ Node.js 路径不在系统 PATH 中，正在添加..." -ForegroundColor Yellow
    $newPath = "$systemPath;$foundPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "✅ 已添加到系统 PATH: $foundPath" -ForegroundColor Green
}

# 检查用户 PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$foundPath*") {
    Write-Host "✅ Node.js 路径已存在于用户 PATH 中" -ForegroundColor Green
} else {
    Write-Host "⚠️ 同时添加到用户 PATH..." -ForegroundColor Yellow
    $newUserPath = if ($userPath) { "$userPath;$foundPath" } else { $foundPath }
    [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    Write-Host "✅ 已添加到用户 PATH: $foundPath" -ForegroundColor Green
}

# 刷新当前会话的 PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证
Write-Host "验证 Node.js 是否可用..." -ForegroundColor Yellow
try {
    $nodeVersion = node -v 2>&1
    $npmVersion = npm -v 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $nodeVersion -match "v\d+\.\d+\.\d+") {
        Write-Host "✅ Node.js 版本: $nodeVersion" -ForegroundColor Green
        Write-Host "✅ npm 版本: $npmVersion" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 修复成功！Node.js 现在可以正常使用了！" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 命令已添加，但需要重启 PowerShell 才能生效" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ 需要重启 PowerShell 才能生效" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "重要提示：" -ForegroundColor Yellow
Write-Host "1. 如果 node -v 仍然不工作，请关闭并重新打开 PowerShell" -ForegroundColor Cyan
Write-Host "2. 或者重启电脑（最彻底的方法）" -ForegroundColor Cyan
Write-Host "3. 然后运行: node -v 和 npm -v 验证" -ForegroundColor Cyan
Write-Host ""

pause

