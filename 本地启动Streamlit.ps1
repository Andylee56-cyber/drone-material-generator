# 本地启动Streamlit演示脚本
# 使用方法：在PowerShell中执行 .\本地启动Streamlit.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 启动无人机素材生成系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/4] 检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或未添加到PATH" -ForegroundColor Red
    Write-Host "请先安装Python或激活conda环境" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# 检查Streamlit
Write-Host ""
Write-Host "[2/4] 检查Streamlit..." -ForegroundColor Yellow
$streamlitCheck = python -m streamlit --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Streamlit未安装" -ForegroundColor Red
    Write-Host "正在安装Streamlit..." -ForegroundColor Yellow
    pip install streamlit
}
Write-Host "✅ Streamlit已安装" -ForegroundColor Green

# 检查项目文件
Write-Host ""
Write-Host "[3/4] 检查项目文件..." -ForegroundColor Yellow
$projectPath = "d:\mlflow_learning_project"
$appFile = Join-Path $projectPath "material_generator_app_optimized.py"

if (-not (Test-Path $appFile)) {
    Write-Host "⚠️  优化文件不存在，查找其他文件..." -ForegroundColor Yellow
    # 查找可能的文件
    $possibleFiles = @(
        Join-Path $projectPath "streamlit_app.py",
        Join-Path $projectPath "app\web\material_generator_app.py",
        Join-Path $projectPath "material_generator_app.py"
    )
    
    $found = $false
    foreach ($file in $possibleFiles) {
        if (Test-Path $file) {
            $appFile = $file
            $found = $true
            Write-Host "✅ 找到文件: $appFile" -ForegroundColor Green
            break
        }
    }
    
    if (-not $found) {
        Write-Host "❌ 找不到Streamlit应用文件" -ForegroundColor Red
        Write-Host "请确认项目路径: $projectPath" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✅ 找到优化文件: $appFile" -ForegroundColor Green
}

# 切换到项目目录
Set-Location $projectPath
Write-Host ""
Write-Host "[4/4] 启动Streamlit..." -ForegroundColor Yellow
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📱 访问地址：" -ForegroundColor Green
Write-Host "   本地: http://localhost:8501" -ForegroundColor White
Write-Host "   局域网: http://你的IP:8501" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示：" -ForegroundColor Yellow
Write-Host "   - 按 Ctrl+C 停止服务" -ForegroundColor White
Write-Host "   - 浏览器会自动打开" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 启动Streamlit（允许局域网访问）
$fileName = Split-Path $appFile -Leaf
streamlit run $fileName --server.port 8501 --server.address 0.0.0.0 --server.headless false

