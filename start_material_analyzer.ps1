# 启动无人机素材8维度分析系统
# Start Drone Material 8-Dimensional Analysis System

Write-Host "🚁 启动无人机素材8维度分析系统..." -ForegroundColor Cyan

# 激活Conda环境
Write-Host "📦 激活Conda环境..." -ForegroundColor Yellow
conda activate uav_adv

# 检查依赖
Write-Host "🔍 检查依赖..." -ForegroundColor Yellow
$missing = @()

try {
    python -c "import ultralytics" 2>$null
    if ($LASTEXITCODE -ne 0) { $missing += "ultralytics" }
} catch {
    $missing += "ultralytics"
}

try {
    python -c "import plotly" 2>$null
    if ($LASTEXITCODE -ne 0) { $missing += "plotly" }
} catch {
    $missing += "plotly"
}

if ($missing.Count -gt 0) {
    Write-Host "❌ 缺少以下依赖: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "正在安装..." -ForegroundColor Yellow
    pip install ultralytics plotly
}

# 创建必要目录
$dirs = @("reports", "temp_uploads")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✅ 创建目录: $dir" -ForegroundColor Green
    }
}

# 启动Streamlit应用
Write-Host "🌐 启动Streamlit应用..." -ForegroundColor Cyan
Write-Host "访问地址: http://localhost:8502" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor DarkYellow
Write-Host ""

streamlit run app\web\material_analyzer_app.py --server.port 8502




