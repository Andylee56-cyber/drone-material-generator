# 修复 Streamlit Cloud 部署问题
# 自动提交修复到 GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Streamlit Cloud Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查 Git 状态
Write-Host "`n[1/4] Checking Git status..." -ForegroundColor Yellow
git status

# 添加修改的文件
Write-Host "`n[2/4] Staging changes..." -ForegroundColor Yellow
git add requirements.txt
git add agents/image_multi_angle_generator.py

# 提交更改
Write-Host "`n[3/4] Committing changes..." -ForegroundColor Yellow
$commitMessage = "Fix OpenCV dependency for Streamlit Cloud compatibility"
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "Commit successful!" -ForegroundColor Green
} else {
    Write-Host "No changes to commit or commit failed" -ForegroundColor Yellow
}

# 推送到 GitHub
Write-Host "`n[4/4] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Changes pushed to GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nStreamlit Cloud will automatically redeploy in 1-2 minutes." -ForegroundColor Cyan
    Write-Host "Please wait and then refresh your app." -ForegroundColor Cyan
} else {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "Push failed. Please check your Git configuration." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

