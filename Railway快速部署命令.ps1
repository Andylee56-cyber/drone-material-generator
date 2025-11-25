# Railway 快速部署 - 一键配置脚本

Write-Host "🚀 Railway 快速部署配置" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# 1. 创建 Procfile
Write-Host "`n📝 创建 Procfile..." -ForegroundColor Yellow
@"
web: streamlit run app/web/material_generator_app.py --server.port `$PORT --server.address 0.0.0.0
"@ | Out-File -FilePath Procfile -Encoding utf8 -NoNewline
Write-Host "✅ Procfile 已创建" -ForegroundColor Green

# 2. 检查 requirements.txt
Write-Host "`n📋 检查 requirements.txt..." -ForegroundColor Yellow
if (Test-Path requirements.txt) {
    Write-Host "✅ requirements.txt 存在" -ForegroundColor Green
} else {
    Write-Host "❌ requirements.txt 不存在，请先创建" -ForegroundColor Red
    exit 1
}

# 3. 提交到 Git
Write-Host "`n💾 提交到 Git..." -ForegroundColor Yellow
git add Procfile
git commit -m "Add Railway deployment configuration"
git push origin main

Write-Host "`n✅ 配置完成！" -ForegroundColor Green
Write-Host "`n📝 下一步操作：" -ForegroundColor Cyan
Write-Host "1. 访问 https://railway.app" -ForegroundColor White
Write-Host "2. 使用 GitHub 账号登录" -ForegroundColor White
Write-Host "3. 点击 'New Project' → 'Deploy from GitHub repo'" -ForegroundColor White
Write-Host "4. 选择你的仓库：Andylee56-cyber/drone-material-generator" -ForegroundColor White
Write-Host "5. 点击 'Deploy Now'" -ForegroundColor White
Write-Host "`n🎉 部署完成后，应用将 24/7 稳定运行！" -ForegroundColor Green

