# 修复 OpenCV 导入问题 - 提交到 GitHub
Write-Host "🔧 修复 OpenCV 导入问题..." -ForegroundColor Cyan

# 检查 Git 状态
Write-Host "`n📋 检查 Git 状态..." -ForegroundColor Yellow
git status

# 添加修改的文件
Write-Host "`n➕ 添加修改的文件..." -ForegroundColor Yellow
git add requirements.txt
git add agents/image_multi_angle_generator.py
git add agents/image_quality_analyzer.py
git add agents/material_enhancement_trainer.py

# 提交更改
Write-Host "`n💾 提交更改..." -ForegroundColor Yellow
git commit -m "Fix OpenCV import error: Add error handling and update requirements.txt"

# 推送到 GitHub
Write-Host "`n🚀 推送到 GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`n✅ 修复已完成！Streamlit Cloud 将自动重新部署（约 1-2 分钟）" -ForegroundColor Green
Write-Host "`n📝 修复内容：" -ForegroundColor Cyan
Write-Host "  1. 更新 requirements.txt，指定 opencv-python-headless==4.8.1.78" -ForegroundColor Gray
Write-Host "  2. 在所有使用 cv2 的文件中添加导入错误处理" -ForegroundColor Gray
Write-Host "  3. 添加 scipy 依赖" -ForegroundColor Gray

