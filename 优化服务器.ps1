# 服务器优化脚本 - PowerShell版本
# 使用方法：在PowerShell中执行: .\优化服务器.ps1

$serverIP = "8.129.225.152"
$serverUser = "root"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 开始优化服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查SSH连接
Write-Host "[1/5] 检查SSH连接..." -ForegroundColor Yellow
$testConnection = ssh -o ConnectTimeout=5 -o BatchMode=yes $serverUser@$serverIP "echo '连接成功'" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH连接失败，请先手动连接一次：" -ForegroundColor Red
    Write-Host "   ssh $serverUser@$serverIP" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "连接成功后，再运行此脚本" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ SSH连接正常" -ForegroundColor Green
Write-Host ""

# 步骤1: 验证Swap空间
Write-Host "[2/5] 验证Swap空间..." -ForegroundColor Yellow
ssh $serverUser@$serverIP @"
free -h
"@

Write-Host ""
Write-Host "如果Swap显示0B，需要添加Swap空间" -ForegroundColor Yellow
$addSwap = Read-Host "是否添加Swap空间？(y/n)"

if ($addSwap -eq "y" -or $addSwap -eq "Y") {
    Write-Host "正在添加Swap空间..." -ForegroundColor Yellow
    ssh $serverUser@$serverIP @"
# 创建2GB swap文件
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
free -h
"@
    Write-Host "✅ Swap空间已添加" -ForegroundColor Green
}

Write-Host ""

# 步骤2: 查找项目路径
Write-Host "[3/5] 查找项目路径..." -ForegroundColor Yellow
$projectPath = ssh $serverUser@$serverIP @"
# 查找streamlit_app.py
STREAMLIT_PATH=\$(find /root -name "streamlit_app.py" -type f 2>/dev/null | head -1)
if [ -z "\$STREAMLIT_PATH" ]; then
    STREAMLIT_PATH=\$(find /home -name "streamlit_app.py" -type f 2>/dev/null | head -1)
fi

if [ -n "\$STREAMLIT_PATH" ]; then
    echo "\$STREAMLIT_PATH"
    dirname "\$STREAMLIT_PATH"
else
    # 检查Streamlit进程的工作目录
    PID=\$(ps aux | grep streamlit | grep -v grep | awk '{print \$2}' | head -1)
    if [ -n "\$PID" ]; then
        ls -la /proc/\$PID/cwd 2>/dev/null | awk '{print \$NF}'
    else
        echo "/root/mlflow_learning_project"
    fi
fi
"@

$projectPath = $projectPath.Trim()
Write-Host "项目路径: $projectPath" -ForegroundColor Green

if ([string]::IsNullOrEmpty($projectPath)) {
    Write-Host "❌ 无法找到项目路径，请手动输入：" -ForegroundColor Red
    $projectPath = Read-Host "请输入项目完整路径（如：/root/mlflow_learning_project）"
}

Write-Host ""

# 步骤3: 备份并优化代码
Write-Host "[4/5] 备份并优化代码..." -ForegroundColor Yellow

$optimizeCode = @"
#!/bin/bash
cd $projectPath

# 检查文件是否存在
if [ ! -f streamlit_app.py ]; then
    echo "❌ 找不到streamlit_app.py"
    echo "当前目录：\$(pwd)"
    ls -la *.py 2>/dev/null
    exit 1
fi

# 备份原文件
cp streamlit_app.py streamlit_app.py.backup.\$(date +%Y%m%d_%H%M%S)
echo "✅ 已备份原文件"

# 检查是否已经优化
if grep -q "@st.cache_resource" streamlit_app.py; then
    echo "⚠️  文件可能已经优化过了"
else
    echo "📝 需要在文件开头添加优化代码"
fi

# 显示文件前20行
echo ""
echo "=== 文件前20行 ==="
head -20 streamlit_app.py
"@

ssh $serverUser@$serverIP $optimizeCode

Write-Host ""
$continue = Read-Host "是否继续添加优化代码？(y/n)"

if ($continue -eq "y" -or $continue -eq "Y") {
    Write-Host "正在添加优化代码..." -ForegroundColor Yellow
    
    # 创建优化代码片段
    $optimizationCode = @"
import streamlit as st
import torch
import gc

# ========== 性能优化设置 ==========
# 限制CPU线程，避免过载
if not torch.cuda.is_available():
    torch.set_num_threads(1)
    torch.set_grad_enabled(False)  # 推理时不需要梯度

# ========== 模型缓存（关键优化） ==========
@st.cache_resource  # 这个装饰器确保模型只加载一次
def load_model():
    \"\"\"加载模型，只执行一次，后续请求复用\"\"\"
    from main import DroneVisionCNN
    model = DroneVisionCNN(num_classes=5)
    model.eval()  # 设置为评估模式
    gc.collect()  # 清理内存
    return model

# ========== 数据预处理缓存 ==========
@st.cache_data(max_entries=20)  # 缓存最近20张图片的预处理结果
def preprocess_image(image, target_size=(64, 64)):
    \"\"\"预处理图片，带缓存\"\"\"
    # 你的图片预处理代码
    import numpy as np
    from PIL import Image
    if isinstance(image, Image.Image):
        image = image.resize(target_size)
        image_array = np.array(image)
    else:
        image_array = image
    return image_array

# ========== 推理函数（带缓存） ==========
@st.cache_data(max_entries=10)  # 缓存最近10次推理结果
def predict_image(model, image_tensor):
    \"\"\"预测图片，相同输入直接返回缓存结果\"\"\"
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.softmax(output, dim=1)
        return probabilities.cpu().numpy()

"@

    # 将优化代码写入临时文件
    $tempFile = "optimization_code.txt"
    $optimizationCode | Out-File -FilePath $tempFile -Encoding UTF8
    
    # 上传并插入到文件开头
    ssh $serverUser@$serverIP @"
cd $projectPath
# 读取优化代码（需要手动添加）
echo "请手动在streamlit_app.py开头添加以下代码："
echo ""
echo "import streamlit as st"
echo "import torch"
echo "import gc"
echo ""
echo "if not torch.cuda.is_available():"
echo "    torch.set_num_threads(1)"
echo "    torch.set_grad_enabled(False)"
echo ""
echo "@st.cache_resource"
echo "def load_model():"
echo "    from main import DroneVisionCNN"
echo "    model = DroneVisionCNN(num_classes=5)"
echo "    model.eval()"
echo "    gc.collect()"
echo "    return model"
"@
    
    Write-Host ""
    Write-Host "⚠️  由于SSH限制，需要手动添加优化代码" -ForegroundColor Yellow
    Write-Host "请按照上面的提示，在streamlit_app.py文件开头添加优化代码" -ForegroundColor Yellow
}

Write-Host ""

# 步骤4: 优化系统参数
Write-Host "[5/5] 优化系统参数..." -ForegroundColor Yellow
$optimizeSystem = Read-Host "是否优化系统参数？(y/n)"

if ($optimizeSystem -eq "y" -or $optimizeSystem -eq "Y") {
    ssh $serverUser@$serverIP @"
# 优化内核参数
cat >> /etc/sysctl.conf << 'EOF'
# 优化内存管理
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2

# 优化网络
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
EOF

sysctl -p
echo "✅ 系统参数已优化"
"@
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎉 优化完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 下一步操作：" -ForegroundColor Yellow
Write-Host "1. 手动编辑 streamlit_app.py，添加优化代码" -ForegroundColor White
Write-Host "2. 重启Streamlit服务" -ForegroundColor White
Write-Host "3. 测试访问: https://8.129.225.152" -ForegroundColor White
Write-Host ""
Write-Host "💡 手动编辑文件方法：" -ForegroundColor Yellow
Write-Host "   ssh $serverUser@$serverIP" -ForegroundColor White
Write-Host "   cd $projectPath" -ForegroundColor White
Write-Host "   nano streamlit_app.py" -ForegroundColor White
Write-Host ""

