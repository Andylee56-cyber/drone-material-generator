# ========================================
# 创建桌面快捷方式 - 应用快速入口
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "创建桌面快捷方式" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取桌面路径
$desktopPath = [Environment]::GetFolderPath("Desktop")
$htmlPath = Join-Path $PSScriptRoot "桌面快捷方式_应用入口.html"
$shortcutPath = Join-Path $desktopPath "无人机素材生成系统.lnk"

Write-Host "桌面路径：$desktopPath" -ForegroundColor Gray
Write-Host ""

# 方法1：创建HTML文件快捷方式（推荐）
if (Test-Path $htmlPath) {
    Write-Host "方法1：创建HTML快捷方式..." -ForegroundColor Yellow
    
    # 创建VBScript来创建快捷方式
    $vbsScript = @"
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "$shortcutPath"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "$htmlPath"
oLink.WorkingDirectory = "$PSScriptRoot"
oLink.IconLocation = "shell32.dll,13"
oLink.Description = "无人机素材多角度生成与分析系统"
oLink.Save
"@
    
    $vbsFile = Join-Path $env:TEMP "create_shortcut.vbs"
    $vbsScript | Out-File -FilePath $vbsFile -Encoding ASCII -Force
    
    & cscript.exe //nologo $vbsFile
    
    if (Test-Path $shortcutPath) {
        Write-Host "✅ 桌面快捷方式已创建！" -ForegroundColor Green
        Write-Host "   位置：$shortcutPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "双击桌面上的'无人机素材生成系统'图标即可打开" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  快捷方式创建失败，使用备用方法..." -ForegroundColor Yellow
    }
    
    Remove-Item $vbsFile -ErrorAction SilentlyContinue
} else {
    Write-Host "⚠️  HTML文件不存在，正在创建..." -ForegroundColor Yellow
}

# 方法2：直接打开HTML文件
Write-Host ""
Write-Host "方法2：直接打开HTML文件..." -ForegroundColor Yellow
if (Test-Path $htmlPath) {
    Start-Process $htmlPath
    Write-Host "✅ HTML文件已打开" -ForegroundColor Green
    Write-Host ""
    Write-Host "提示：可以将此HTML文件复制到桌面，双击即可打开" -ForegroundColor Yellow
} else {
    Write-Host "❌ HTML文件不存在" -ForegroundColor Red
}

# 方法3：创建批处理文件
Write-Host ""
Write-Host "方法3：创建批处理文件..." -ForegroundColor Yellow
$batPath = Join-Path $desktopPath "打开应用.bat"
$batContent = @"
@echo off
start https://drone-material-generator-ha8mscbtjeytbixqy6qtut.streamlit.app
"@

$batContent | Out-File -FilePath $batPath -Encoding ASCII -Force

if (Test-Path $batPath) {
    Write-Host "✅ 批处理文件已创建：$batPath" -ForegroundColor Green
    Write-Host "   双击'打开应用.bat'即可在浏览器中打开应用" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "现在您可以通过以下方式打开应用：" -ForegroundColor White
Write-Host "1. 双击桌面上的'无人机素材生成系统'快捷方式" -ForegroundColor Gray
Write-Host "2. 双击桌面上的'打开应用.bat'文件" -ForegroundColor Gray
Write-Host "3. 双击桌面上的'桌面快捷方式_应用入口.html'文件" -ForegroundColor Gray
Write-Host ""




