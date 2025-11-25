#!/bin/bash
# 一键应用所有优化

set -e

echo "=========================================="
echo "🚀 开始应用优化方案"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查是否为root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 请使用root用户执行${NC}"
    exit 1
fi

# 步骤1: 添加Swap空间
echo -e "${YELLOW}[1/4] 添加Swap空间...${NC}"
if [ -f /swapfile ]; then
    echo "Swap文件已存在，跳过创建"
else
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    echo -e "${GREEN}✅ Swap空间已添加（2GB）${NC}"
fi

# 验证Swap
echo ""
echo "当前内存状态："
free -h

# 步骤2: 优化系统参数
echo ""
echo -e "${YELLOW}[2/4] 优化系统参数...${NC}"
# 增加文件描述符限制
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

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
echo -e "${GREEN}✅ 系统参数已优化${NC}"

# 步骤3: 检查Streamlit配置
echo ""
echo -e "${YELLOW}[3/4] 检查Streamlit配置...${NC}"
STREAMLIT_CONFIG_DIR="/root/.streamlit"
if [ ! -d "$STREAMLIT_CONFIG_DIR" ]; then
    mkdir -p "$STREAMLIT_CONFIG_DIR"
fi

cat > "$STREAMLIT_CONFIG_DIR/config.toml" << 'EOF'
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[runner]
fastReruns = true
magicEnabled = true

[client]
showErrorDetails = false
EOF

echo -e "${GREEN}✅ Streamlit配置已优化${NC}"

# 步骤4: 创建优化后的启动脚本
echo ""
echo -e "${YELLOW}[4/4] 创建优化启动脚本...${NC}"

cat > /root/start_streamlit_optimized.sh << 'EOF'
#!/bin/bash
# 优化后的Streamlit启动脚本

# 设置环境变量
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# 限制Python内存
export PYTHONHASHSEED=0

# 启动Streamlit
cd /root/mlflow_learning_project  # 修改为你的项目路径
python3 -m streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 127.0.0.1 \
    --server.maxUploadSize 200 \
    --server.maxMessageSize 200
EOF

chmod +x /root/start_streamlit_optimized.sh
echo -e "${GREEN}✅ 优化启动脚本已创建${NC}"

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 优化完成！${NC}"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo "1. 重启Streamlit服务（使用优化脚本）"
echo "2. 测试访问: https://8.129.225.152"
echo "3. 检查性能: free -h"
echo ""
echo "💡 使用优化启动脚本："
echo "   /root/start_streamlit_optimized.sh"
echo ""

