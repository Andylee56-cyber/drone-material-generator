# ========================================
# Deploy to GitHub and Streamlit Cloud
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Check file exists" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

cd D:\mlflow_learning_project

if (Test-Path "app\web\material_generator_app.py") {
    Write-Host "OK: material_generator_app.py exists" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "ERROR: File not found" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Push to GitHub" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Adding file to Git..." -ForegroundColor Yellow
git add app/web/material_generator_app.py

Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "Fix: 1. Move image count slider to main UI 2. Ensure detection boxes are drawn correctly 3. Add download functionality for enhanced images"

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "NOTE: Use Personal Access Token as password" -ForegroundColor Red
Write-Host "Username: Andylee56-cyber" -ForegroundColor Gray
Write-Host "Password: Enter your Personal Access Token" -ForegroundColor Gray
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Code pushed to GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository: https://github.com/Andylee56-cyber/drone-material-generator" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Streamlit Cloud will auto-deploy in 1-2 minutes" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Check status at: https://share.streamlit.io" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "ERROR: Push failed. Please check:" -ForegroundColor Red
    Write-Host "1. GitHub repository exists" -ForegroundColor Yellow
    Write-Host "2. Used Personal Access Token (not password)" -ForegroundColor Yellow
    Write-Host "3. Network connection is OK" -ForegroundColor Yellow
}




