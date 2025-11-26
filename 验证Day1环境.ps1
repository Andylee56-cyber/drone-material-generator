# Day 1 环境搭建验证脚本 (PowerShell版本)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Day 1 环境搭建验证" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# 1. 检查Python版本
Write-Host "1. 检查Python版本..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   $pythonVersion" -ForegroundColor Green

# 2. 检查Conda环境
Write-Host "`n2. 检查Conda环境..." -ForegroundColor Yellow
$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv -like "*drone_vision_advanced*") {
    Write-Host "   ✅ 当前环境: $condaEnv" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  当前环境: $condaEnv" -ForegroundColor Yellow
    Write-Host "   请运行: conda activate drone_vision_advanced" -ForegroundColor Yellow
}

# 3. 检查PyTorch
Write-Host "`n3. 检查PyTorch安装..." -ForegroundColor Yellow
python -c "import torch; print(f'   ✅ PyTorch版本: {torch.__version__}'); print(f'   CUDA可用: {torch.cuda.is_available()}'); print(f'   CUDA版本: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" 2>&1

# 4. 检查关键依赖
Write-Host "`n4. 检查关键依赖包..." -ForegroundColor Yellow
$packages = @("torch", "torchvision", "cv2", "numpy", "pandas", "albumentations", "fastapi", "streamlit")
foreach ($pkg in $packages) {
    $result = python -c "import $pkg; print('OK')" 2>&1
    if ($result -like "*OK*") {
        Write-Host "   ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $pkg - 未安装" -ForegroundColor Red
    }
}

# 5. 检查项目结构
Write-Host "`n5. 检查项目结构..." -ForegroundColor Yellow
$requiredDirs = @(
    "backend\algorithms\segmentation\models",
    "backend\algorithms\segmentation\losses",
    "backend\algorithms\tracking",
    "backend\algorithms\fusion",
    "data\datasets\road_segmentation",
    "data\datasets\farmland_segmentation",
    "models\segmentation",
    "models\tracking"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "   ✅ $dir" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir - 不存在" -ForegroundColor Red
    }
}

# 6. 运行Python验证脚本
Write-Host "`n6. 运行详细验证..." -ForegroundColor Yellow
python scripts\verify_day1_setup.py

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  验证完成！" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan


