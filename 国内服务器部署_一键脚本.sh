#!/bin/bash
# 国内云服务器一键部署脚本
# 适用于 Ubuntu 20.04/22.04

set -e

echo "🚀 开始部署无人机视觉系统..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 更新系统
echo -e "${YELLOW}📦 更新系统...${NC}"
apt update && apt upgrade -y

# 2. 安装 Python 3.11
echo -e "${YELLOW}🐍 安装 Python 3.11...${NC}"
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install python3.11 python3.11-venv python3.11-dev python3-pip git -y

# 3. 安装系统依赖
echo -e "${YELLOW}📚 安装系统依赖...${NC}"
apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev -y

# 4. 克隆项目
echo -e "${YELLOW}📥 克隆项目...${NC}"
cd /opt
if [ -d "drone-material-generator" ]; then
    echo "项目已存在，更新中..."
    cd drone-material-generator
    git pull origin main
else
    git clone https://github.com/Andylee56-cyber/drone-material-generator.git
    cd drone-material-generator
fi

# 5. 创建虚拟环境
echo -e "${YELLOW}🔧 创建虚拟环境...${NC}"
python3.11 -m venv venv
source venv/bin/activate

# 6. 安装 Python 依赖
echo -e "${YELLOW}📦 安装 Python 依赖（这可能需要几分钟）...${NC}"
pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 7. 创建 Streamlit 配置
echo -e "${YELLOW}⚙️ 配置 Streamlit...${NC}"
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << 'EOF'
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF

# 8. 配置防火墙
echo -e "${YELLOW}🔥 配置防火墙...${NC}"
ufw allow 8501/tcp
ufw --force enable

# 9. 创建系统服务
echo -e "${YELLOW}🚀 创建系统服务...${NC}"
cat > /etc/systemd/system/streamlit-app.service << 'EOF'
[Unit]
Description=Streamlit Drone Material Generator App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/drone-material-generator
Environment="PATH=/opt/drone-material-generator/venv/bin"
ExecStart=/opt/drone-material-generator/venv/bin/streamlit run app/web/material_generator_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 10. 启动服务
echo -e "${YELLOW}▶️ 启动服务...${NC}"
systemctl daemon-reload
systemctl enable streamlit-app
systemctl start streamlit-app

# 11. 等待服务启动
sleep 5

# 12. 检查服务状态
echo -e "${YELLOW}✅ 检查服务状态...${NC}"
if systemctl is-active --quiet streamlit-app; then
    echo -e "${GREEN}✅ 服务运行成功！${NC}"
    echo -e "${GREEN}📱 访问地址: http://$(curl -s ifconfig.me):8501${NC}"
else
    echo -e "${RED}❌ 服务启动失败，查看日志: sudo journalctl -u streamlit-app -f${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 部署完成！${NC}"

