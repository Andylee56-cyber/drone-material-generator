# 无人机视觉AI系统 - 快速启动脚本
# 全新科幻风格界面

Write-Host "🚁 无人机视觉AI系统启动中..." -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "📋 检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# 检查依赖
Write-Host ""
Write-Host "📦 检查依赖包..." -ForegroundColor Yellow
$requiredPackages = @("streamlit", "plotly", "pandas", "numpy", "Pillow", "torch")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $installed = pip show $package 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "⚠️ 缺少以下依赖包: $($missingPackages -join ', ')" -ForegroundColor Yellow
    Write-Host "正在安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ 所有依赖已安装" -ForegroundColor Green
}

# 创建必要目录
Write-Host ""
Write-Host "📁 创建必要目录..." -ForegroundColor Yellow
$directories = @("temp_uploads", "generated_images", "reports")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✅ 创建目录: $dir" -ForegroundColor Green
    }
}

# 启动应用
Write-Host ""
Write-Host "🚀 启动应用..." -ForegroundColor Cyan
Write-Host "应用将在浏览器中自动打开: http://localhost:8501" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止应用" -ForegroundColor Yellow
Write-Host ""

# 启动Streamlit
streamlit run drone_vision_ai_system.py --server.port 8501

