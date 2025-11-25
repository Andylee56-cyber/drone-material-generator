# 快速部署到Streamlit Cloud
# GitHub: Andylee56-cyber/drone-material-generator

Write-Host "开始准备部署到Streamlit Cloud..." -ForegroundColor Green
Write-Host ""

cd D:\mlflow_learning_project

Write-Host "检查Git状态..." -ForegroundColor Yellow
git status

$status = git status --porcelain
if ($status) {
    Write-Host "发现未提交的更改，准备提交..." -ForegroundColor Yellow
    git add .
    $commitMessage = "准备部署到Streamlit Cloud - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMessage
    Write-Host "代码已提交" -ForegroundColor Green
} else {
    Write-Host "没有未提交的更改" -ForegroundColor Green
}

Write-Host ""
Write-Host "检查远程仓库配置..." -ForegroundColor Yellow
$remote = git remote get-url origin
Write-Host "远程仓库: $remote" -ForegroundColor Cyan

if ($remote -notmatch "Andylee56-cyber") {
    Write-Host "警告：远程仓库不匹配！" -ForegroundColor Red
} else {
    Write-Host "远程仓库配置正确" -ForegroundColor Green
}

Write-Host ""
Write-Host "检查GitHub Token配置..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin
$tokenConfigured = $remoteUrl -match "ghp_"

if ($tokenConfigured) {
    Write-Host "Token已在远程URL中配置" -ForegroundColor Green
} else {
    Write-Host "Token未在URL中配置" -ForegroundColor Yellow
    Write-Host "运行 .\配置GitHub_Token.ps1 来配置Token" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "准备推送到GitHub..." -ForegroundColor Yellow
if (-not $tokenConfigured) {
    Write-Host "提示：如果首次推送，可能需要输入Token" -ForegroundColor Yellow
    Write-Host "请运行: .\配置GitHub_Token.ps1 来配置Token" -ForegroundColor Cyan
    Write-Host "或运行: .\配置GitHub_Token.ps1" -ForegroundColor Cyan
}
Write-Host ""

$push = Read-Host "是否现在推送代码到GitHub? (Y/N)"
if ($push -eq "Y" -or $push -eq "y") {
    git push
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "代码已推送到GitHub！" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "推送失败！" -ForegroundColor Red
        Write-Host "运行: .\配置GitHub_Token.ps1" -ForegroundColor Cyan
    }
} else {
    Write-Host "跳过推送" -ForegroundColor Yellow
}

Write-Host ""
$sep = "============================================================"
Write-Host $sep -ForegroundColor Cyan
Write-Host "下一步操作：" -ForegroundColor Green
Write-Host $sep -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 访问 Streamlit Cloud" -ForegroundColor Yellow
Write-Host "   https://share.streamlit.io" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. 使用GitHub账号登录（Andylee56-cyber）" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. 点击 New app，选择仓库" -ForegroundColor Yellow
Write-Host "   Andylee56-cyber/drone-material-generator" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. 配置" -ForegroundColor Yellow
Write-Host "   Branch: main" -ForegroundColor Cyan
Write-Host "   Main file: material_generator_app_optimized.py" -ForegroundColor Cyan
Write-Host "   App URL: drone-ai-system（可选）" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. 点击 Deploy，等待3-5分钟" -ForegroundColor Yellow
Write-Host ""
Write-Host "完成后，你会得到一个网址" -ForegroundColor Green
Write-Host "   https://drone-ai-system.streamlit.app" -ForegroundColor Cyan
Write-Host ""
Write-Host $sep -ForegroundColor Cyan
