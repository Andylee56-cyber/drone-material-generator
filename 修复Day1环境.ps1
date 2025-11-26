# 修复Day 1环境问题

Write-Host "`n开始修复Day 1环境问题...`n" -ForegroundColor Cyan

# 1. 激活正确的Conda环境
Write-Host "1. 激活Conda环境..." -ForegroundColor Yellow
Write-Host "   请手动运行: conda activate drone_vision_advanced" -ForegroundColor Yellow
Write-Host "   如果环境不存在，运行: conda create -n drone_vision_advanced python=3.10 -y" -ForegroundColor Yellow

# 2. 安装缺失的依赖包
Write-Host "`n2. 安装缺失的依赖包..." -ForegroundColor Yellow
$missingPackages = @(
    "albumentations",
    "rasterio",
    "spectral",
    "redis",
    "psycopg2-binary"
)

foreach ($pkg in $missingPackages) {
    Write-Host "   安装 $pkg..." -ForegroundColor Gray
    pip install $pkg
}

# 3. 创建项目结构
Write-Host "`n3. 创建项目结构..." -ForegroundColor Yellow
$dirs = @(
    "backend\algorithms\segmentation\models",
    "backend\algorithms\segmentation\losses",
    "backend\algorithms\tracking",
    "backend\algorithms\fusion",
    "data\datasets\road_segmentation",
    "data\datasets\farmland_segmentation",
    "models\segmentation",
    "models\tracking"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   [OK] 创建: $dir" -ForegroundColor Green
    } else {
        Write-Host "   [OK] 已存在: $dir" -ForegroundColor Gray
    }
}

# 4. 创建__init__.py文件
Write-Host "`n4. 创建Python包文件..." -ForegroundColor Yellow
$initFiles = @(
    "backend\__init__.py",
    "backend\algorithms\__init__.py",
    "backend\algorithms\segmentation\__init__.py",
    "backend\algorithms\segmentation\models\__init__.py",
    "backend\algorithms\segmentation\losses\__init__.py",
    "backend\algorithms\tracking\__init__.py",
    "backend\algorithms\fusion\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
        Write-Host "   [OK] 创建: $file" -ForegroundColor Green
    }
}

Write-Host "`n修复完成！请运行验证脚本检查：" -ForegroundColor Green
Write-Host "   python scripts\verify_day1_setup.py" -ForegroundColor Cyan
Write-Host "`n"


