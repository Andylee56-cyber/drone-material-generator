# 高性能启动脚本 - 支持GPU加速
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 启动高性能无人机素材生成系统" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/4] 检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# 检查PyTorch和GPU
Write-Host ""
Write-Host "[2/4] 检查PyTorch和GPU..." -ForegroundColor Yellow
$torchCheck = python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'GPU设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ PyTorch未安装" -ForegroundColor Red
    Write-Host "请先运行: .\安装依赖.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host $torchCheck -ForegroundColor Green

# 检查项目文件
Write-Host ""
Write-Host "[3/4] 检查项目文件..." -ForegroundColor Yellow
$projectPath = "d:\mlflow_learning_project"
$appFile = Join-Path $projectPath "material_generator_app_optimized.py"

if (-not (Test-Path $appFile)) {
    Write-Host "❌ 找不到应用文件: $appFile" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 找到应用文件: $appFile" -ForegroundColor Green

# 切换到项目目录
Set-Location $projectPath

# 获取本机IP（用于局域网访问）
Write-Host ""
Write-Host "[4/4] 获取网络信息..." -ForegroundColor Yellow
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📱 访问地址：" -ForegroundColor Green
Write-Host "   本地: http://localhost:8501" -ForegroundColor White
if ($ipAddress) {
    Write-Host "   局域网: http://$ipAddress:8501" -ForegroundColor White
}
Write-Host ""
Write-Host "💡 提示：" -ForegroundColor Yellow
Write-Host "   - 按 Ctrl+C 停止服务" -ForegroundColor White
Write-Host "   - 浏览器会自动打开" -ForegroundColor White
Write-Host "   - GPU加速已启用（如果可用）" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 启动Streamlit（高性能模式）
$fileName = Split-Path $appFile -Leaf
streamlit run $fileName --server.port 8501 --server.address 0.0.0.0 --server.headless false

