#!/bin/bash
# 检查服务器状态脚本

echo "=== 检查Streamlit服务状态 ==="
systemctl status streamlit-app 2>/dev/null || echo "Streamlit服务未配置为systemd服务"

echo ""
echo "=== 检查8501端口是否监听 ==="
netstat -tlnp | grep :8501 || ss -tlnp | grep :8501 || echo "8501端口未监听"

echo ""
echo "=== 检查Nginx是否安装 ==="
which nginx && nginx -v || echo "Nginx未安装"

echo ""
echo "=== 检查防火墙端口 ==="
echo "请到阿里云控制台检查80和443端口是否启用"

