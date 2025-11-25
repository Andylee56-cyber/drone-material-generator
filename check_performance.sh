#!/bin/bash
# 性能诊断脚本

echo "=== 服务器性能诊断 ==="
echo ""

# 1. 检查CPU信息
echo "【CPU信息】"
lscpu | grep -E 'Model name|CPU\(s\)|Thread|Core'
echo ""

# 2. 检查内存使用
echo "【内存使用】"
free -h
echo ""

# 3. 检查磁盘使用
echo "【磁盘使用】"
df -h
echo ""

# 4. 检查当前资源占用
echo "【当前资源占用】"
top -bn1 | head -20
echo ""

# 5. 检查Python进程资源占用
echo "【Python/Streamlit进程】"
ps aux | grep -E 'python|streamlit' | grep -v grep
echo ""

# 6. 检查是否有GPU
echo "【GPU信息】"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi
else
    echo "未检测到NVIDIA GPU或驱动未安装"
fi
echo ""

# 7. 检查网络延迟
echo "【网络测试】"
ping -c 3 8.8.8.8 | tail -2
echo ""

# 8. 检查系统负载
echo "【系统负载】"
uptime
echo ""

echo "=== 诊断完成 ==="

