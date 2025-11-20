# 📤 第四步：初始化Git并推送到GitHub
# 请先完成：1. 生成GitHub Personal Access Token并输入 2. 创建GitHub仓库

# 确保在项目根目录
cd D:\mlflow_learning_project

# 初始化Git（如果还没有）
if (-not (Test-Path ".git")) {
    git init
    Write-Host "✅ Git仓库已初始化" -ForegroundColor Green
}

# 配置Git用户信息（请替换为您的实际邮箱）
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📝 配置Git用户信息" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
$userEmail = Read-Host "请输入您的GitHub邮箱（用于Git提交记录）"
git config user.name "Andylee56-cyber"
git config user.email $userEmail
Write-Host "✅ Git用户信息已配置" -ForegroundColor Green

# 添加所有文件
Write-Host ""
Write-Host "📦 添加文件到Git..." -ForegroundColor Yellow
git add .

# 提交
Write-Host "💾 提交更改..." -ForegroundColor Yellow
git commit -m "部署：无人机素材生成系统（移动端优化版）"

# 检查是否已创建GitHub仓库
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📝 确认GitHub仓库已创建" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请确认您已经完成以下操作：" -ForegroundColor White
Write-Host "  ✅ 访问 https://github.com/new" -ForegroundColor Green
Write-Host "  ✅ 仓库名: drone-material-generator" -ForegroundColor Gray
Write-Host "  ✅ 设置为 Public" -ForegroundColor Gray
Write-Host "  ✅ 不要添加README" -ForegroundColor Gray
Write-Host ""
Read-Host "确认完成后，按回车键继续"

# 添加远程仓库
Write-Host ""
Write-Host "🔗 添加远程仓库..." -ForegroundColor Yellow
git remote remove origin -ErrorAction SilentlyContinue
git remote add origin https://github.com/Andylee56-cyber/drone-material-generator.git

# 验证远程仓库
Write-Host "✅ 远程仓库已添加" -ForegroundColor Green
git remote -v

# 推送到GitHub
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📤 推送到GitHub" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  重要提示：" -ForegroundColor Red
Write-Host "   - 用户名：Andylee56-cyber" -ForegroundColor Yellow
Write-Host "   - 密码：请输入您的Personal Access Token（不是GitHub密码）" -ForegroundColor Yellow
Write-Host ""

git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 代码已成功推送到GitHub！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址：https://github.com/Andylee56-cyber/drone-material-generator" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 下一步：部署到Streamlit Cloud" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ 推送失败，请检查：" -ForegroundColor Red
    Write-Host "1. GitHub仓库是否已创建" -ForegroundColor Yellow
    Write-Host "2. 是否使用了Personal Access Token（不是密码）" -ForegroundColor Yellow
    Write-Host "3. 网络连接是否正常" -ForegroundColor Yellow
    Write-Host "4. Token权限是否包含repo（全部）" -ForegroundColor Yellow
}

