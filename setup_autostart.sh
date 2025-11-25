#!/bin/bash
# 设置开机自启脚本

echo "=== 设置服务开机自启 ==="

# 1. 确保Nginx开机自启
systemctl enable nginx
echo "✅ Nginx已设置开机自启"

# 2. 检查Streamlit是否作为systemd服务
if systemctl list-units | grep -q streamlit; then
    systemctl enable streamlit
    echo "✅ Streamlit服务已设置开机自启"
else
    echo "⚠️  Streamlit未配置为systemd服务，需要手动设置"
    echo ""
    echo "创建Streamlit systemd服务..."
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/streamlit-app.service << 'EOF'
[Unit]
Description=Streamlit Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/mlflow_learning_project
ExecStart=/usr/bin/python3 -m streamlit run streamlit_app.py --server.port 8501 --server.headless true --server.address 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd配置
    systemctl daemon-reload
    systemctl enable streamlit-app
    systemctl start streamlit-app
    echo "✅ Streamlit服务已创建并设置开机自启"
fi

# 3. 验证服务状态
echo ""
echo "=== 服务状态 ==="
systemctl is-enabled nginx && echo "✅ Nginx: 已启用" || echo "❌ Nginx: 未启用"
systemctl is-enabled streamlit-app 2>/dev/null && echo "✅ Streamlit: 已启用" || echo "⚠️  Streamlit: 需要手动启动"

echo ""
echo "=== 完成 ==="
echo "现在服务器重启后，服务会自动启动"

