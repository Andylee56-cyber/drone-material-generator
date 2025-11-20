# 启动 MLflow 和 Streamlit 服务
# Start MLflow and Streamlit Services

Write-Host "🚀 正在启动服务..." -ForegroundColor Green

# 激活 Conda 环境
Write-Host "📦 激活 Conda 环境..." -ForegroundColor Yellow
conda activate uav_adv

# 启动 MLflow UI (后台)
Write-Host "📊 启动 MLflow UI..." -ForegroundColor Cyan
$projectPath = (Get-Location).Path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "conda activate uav_adv; Set-Location '$projectPath'; mlflow ui --port 5000" -WindowStyle Normal

# 等待一下
Start-Sleep -Seconds 2

# 启动 Streamlit (后台)
Write-Host "🌐 启动 Streamlit..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "conda activate uav_adv; streamlit run app\web\streamlit_app_simple.py --server.port 8501" -WindowStyle Normal

# 等待服务启动
Start-Sleep -Seconds 3

Write-Host "`n✅ 服务启动完成！" -ForegroundColor Green
Write-Host "📊 MLflow UI: http://localhost:5000" -ForegroundColor Yellow
Write-Host "🌐 Streamlit: http://localhost:8501" -ForegroundColor Yellow
Write-Host "`n💡 提示: 两个服务窗口已打开，关闭窗口即可停止对应服务" -ForegroundColor Cyan

