# LabelMe 转 COCO 格式转换脚本
# 使用方法：根据你的实际数据路径修改下面的路径

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LabelMe to COCO Conversion Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查是否在正确的环境中
Write-Host "`n[1/5] Checking environment..." -ForegroundColor Yellow
$envName = "drone_vision_advanced"
$currentEnv = conda info --envs | Select-String "\*" | ForEach-Object { $_.ToString().Split()[0] }

if ($currentEnv -notlike "*$envName*") {
    Write-Host "Activating conda environment: $envName" -ForegroundColor Yellow
    conda activate $envName
} else {
    Write-Host "Environment OK: $currentEnv" -ForegroundColor Green
}

# 安装 labelme2coco（如果未安装）
Write-Host "`n[2/5] Installing labelme2coco..." -ForegroundColor Yellow
pip install labelme2coco --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "labelme2coco installed successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to install labelme2coco" -ForegroundColor Red
    exit 1
}

# 提示用户输入数据路径
Write-Host "`n[3/5] Data path configuration..." -ForegroundColor Yellow
Write-Host "Please provide the path to your LabelMe JSON files:" -ForegroundColor Cyan
Write-Host "Example: C:\Windows\System32\data\raw\roads" -ForegroundColor Gray
Write-Host "Or: D:\mlflow_learning_project\data\raw\roads" -ForegroundColor Gray

$roadsPath = Read-Host "Enter path to roads data (or press Enter to skip)"
$farmlandPath = Read-Host "Enter path to farmland data (or press Enter to skip)"

# 创建输出目录
$roadOutput = "data\datasets\road_segmentation"
$farmlandOutput = "data\datasets\farmland_segmentation"

New-Item -ItemType Directory -Force -Path $roadOutput | Out-Null
New-Item -ItemType Directory -Force -Path $farmlandOutput | Out-Null

# 转换道路数据
if ($roadsPath -and (Test-Path $roadsPath)) {
    Write-Host "`n[4/5] Converting roads data..." -ForegroundColor Yellow
    $roadJson = Join-Path $roadOutput "coco.json"
    
    Write-Host "Input: $roadsPath" -ForegroundColor Gray
    Write-Host "Output: $roadJson" -ForegroundColor Gray
    
    labelme2coco $roadsPath --output $roadJson
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Roads conversion completed!" -ForegroundColor Green
    } else {
        Write-Host "Roads conversion failed!" -ForegroundColor Red
    }
} else {
    Write-Host "`n[4/5] Skipping roads conversion (path not provided or invalid)" -ForegroundColor Yellow
}

# 转换农田数据
if ($farmlandPath -and (Test-Path $farmlandPath)) {
    Write-Host "`n[5/5] Converting farmland data..." -ForegroundColor Yellow
    $farmlandJson = Join-Path $farmlandOutput "coco.json"
    
    Write-Host "Input: $farmlandPath" -ForegroundColor Gray
    Write-Host "Output: $farmlandJson" -ForegroundColor Gray
    
    labelme2coco $farmlandPath --output $farmlandJson
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Farmland conversion completed!" -ForegroundColor Green
    } else {
        Write-Host "Farmland conversion failed!" -ForegroundColor Red
    }
} else {
    Write-Host "`n[5/5] Skipping farmland conversion (path not provided or invalid)" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Conversion completed!" -ForegroundColor Green
Write-Host "Next step: Run split_dataset.py to split train/val sets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

