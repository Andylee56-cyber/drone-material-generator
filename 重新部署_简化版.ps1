# ========================================
# 重新部署修复后的代码到GitHub和Streamlit Cloud（简化版）
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📤 步骤1：确保文件已更新" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 确保在项目根目录
cd D:\mlflow_learning_project

# 检查文件是否存在
if (Test-Path "app\web\material_generator_app.py") {
    Write-Host "✅ material_generator_app.py 文件已存在" -ForegroundColor Green
    Write-Host "   如果文件已包含修复，可以直接继续步骤2" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "❌ 文件不存在，请先确保文件已创建" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📤 步骤2：提交并推送到GitHub" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 添加文件
Write-Host "📦 添加文件到Git..." -ForegroundColor Yellow
git add app/web/material_generator_app.py

# 提交
Write-Host "💾 提交更改..." -ForegroundColor Yellow
git commit -m "Fix: 1. Move image count slider to main UI 2. Ensure detection boxes are drawn correctly 3. Add download functionality for enhanced images"

# 推送到GitHub
Write-Host ""
Write-Host "📤 推送到GitHub..." -ForegroundColor Yellow
Write-Host "⚠️  提示：如果要求输入密码，请使用Personal Access Token" -ForegroundColor Red
Write-Host "   用户名：Andylee56-cyber" -ForegroundColor Gray
Write-Host "   密码：输入您的Personal Access Token" -ForegroundColor Gray
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 代码已成功推送到GitHub！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址：https://github.com/Andylee56-cyber/drone-material-generator" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 Streamlit Cloud会自动重新部署（约1-2分钟）" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请访问：https://share.streamlit.io" -ForegroundColor Cyan
    Write-Host "查看部署状态和日志" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ 推送失败，请检查：" -ForegroundColor Red
    Write-Host "1. GitHub仓库是否已创建" -ForegroundColor Yellow
    Write-Host "2. 是否使用了Personal Access Token（不是密码）" -ForegroundColor Yellow
    Write-Host "3. 网络连接是否正常" -ForegroundColor Yellow
}

