#!/bin/bash
# HTTPS部署脚本 - 一键部署HTTPS访问

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🔒 HTTPS部署脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 请使用root用户执行此脚本${NC}"
    exit 1
fi

# 步骤1: 检查Streamlit是否运行
echo -e "${YELLOW}[1/6] 检查Streamlit服务...${NC}"
if netstat -tlnp 2>/dev/null | grep -q :8501 || ss -tlnp 2>/dev/null | grep -q :8501; then
    echo -e "${GREEN}✅ Streamlit正在运行（端口8501）${NC}"
else
    echo -e "${RED}❌ Streamlit未运行，请先启动Streamlit应用${NC}"
    echo "   执行: streamlit run streamlit_app.py --server.port 8501"
    exit 1
fi

# 步骤2: 更新软件包
echo ""
echo -e "${YELLOW}[2/6] 更新软件包列表...${NC}"
apt update -y

# 步骤3: 安装Nginx和OpenSSL
echo ""
echo -e "${YELLOW}[3/6] 安装Nginx和OpenSSL...${NC}"
apt install nginx openssl -y
echo -e "${GREEN}✅ Nginx和OpenSSL安装完成${NC}"

# 步骤4: 创建SSL证书目录
echo ""
echo -e "${YELLOW}[4/6] 创建SSL证书...${NC}"
mkdir -p /etc/nginx/ssl

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/streamlit.key \
  -out /etc/nginx/ssl/streamlit.crt \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=8.129.225.152"

chmod 600 /etc/nginx/ssl/streamlit.key
chmod 644 /etc/nginx/ssl/streamlit.crt
echo -e "${GREEN}✅ SSL证书创建完成${NC}"

# 步骤5: 创建Nginx配置
echo ""
echo -e "${YELLOW}[5/6] 配置Nginx...${NC}"

cat > /etc/nginx/sites-available/streamlit << 'EOF'
# HTTP 服务器 - 自动跳转到 HTTPS
server {
    listen 80;
    server_name 8.129.225.152;

    # 自动跳转到 HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name 8.129.225.152;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/streamlit.crt;
    ssl_certificate_key /etc/nginx/ssl/streamlit.key;
    
    # SSL 协议和加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 反向代理到 Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        
        # WebSocket 支持（Streamlit 需要）
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 传递真实 IP 和主机信息
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_read_timeout 86400;
        proxy_connect_timeout 86400;
        proxy_send_timeout 86400;
        
        # 禁用缓冲（Streamlit 需要实时响应）
        proxy_buffering off;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置
echo "测试Nginx配置..."
if nginx -t; then
    echo -e "${GREEN}✅ Nginx配置正确${NC}"
else
    echo -e "${RED}❌ Nginx配置有误，请检查${NC}"
    exit 1
fi

# 步骤6: 启动Nginx
echo ""
echo -e "${YELLOW}[6/6] 启动Nginx服务...${NC}"
systemctl restart nginx
systemctl enable nginx

# 检查Nginx状态
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx已启动并设置开机自启${NC}"
else
    echo -e "${RED}❌ Nginx启动失败${NC}"
    systemctl status nginx
    exit 1
fi

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 HTTPS部署完成！${NC}"
echo "=========================================="
echo ""
echo "📝 重要提醒："
echo "1. 请到阿里云控制台 → 防火墙 → 启用80和443端口"
echo "2. 访问地址: https://8.129.225.152"
echo "3. 首次访问会提示证书不安全，点击'高级' → '继续访问'即可"
echo ""
echo "🔍 验证命令："
echo "   systemctl status nginx"
echo "   netstat -tlnp | grep -E '80|443'"
echo ""

