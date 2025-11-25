# PowerShell 优化命令（分步执行）

## 📋 使用方法

在PowerShell中，**按顺序**复制粘贴执行以下命令。

---

## 第一步：连接服务器

```powershell
ssh root@8.129.225.152
```

输入密码连接。

---

## 第二步：验证Swap空间

连接成功后，在SSH终端执行：

```bash
free -h
```

**如果Swap显示0B，执行以下命令添加：**

```bash
# 创建2GB swap文件
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab

# 验证
free -h
```

应该看到Swap有约2GB。

---

## 第三步：查找项目路径

```bash
# 查找streamlit_app.py
find /root -name "streamlit_app.py" -type f 2>/dev/null
find /home -name "streamlit_app.py" -type f 2>/dev/null

# 或者检查Streamlit进程的工作目录
ps aux | grep streamlit | grep -v grep
```

**记住找到的路径**（如：`/root/mlflow_learning_project`）

---

## 第四步：备份并查看文件

```bash
# 进入项目目录（替换为你的实际路径）
cd /root/mlflow_learning_project  # 修改为你的路径

# 备份原文件
cp streamlit_app.py streamlit_app.py.backup

# 查看文件前30行
head -30 streamlit_app.py
```

---

## 第五步：添加优化代码

使用nano编辑文件：

```bash
nano streamlit_app.py
```

**在文件开头（import语句之后）添加以下代码：**

```python
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
    """加载模型，只执行一次，后续请求复用"""
    from main import DroneVisionCNN
    model = DroneVisionCNN(num_classes=5)
    model.eval()  # 设置为评估模式
    gc.collect()  # 清理内存
    return model
```

**保存并退出nano：**
1. 按 `Ctrl + O` 保存
2. 按 `Enter` 确认
3. 按 `Ctrl + X` 退出

---

## 第六步：优化系统参数（可选）

```bash
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

# 应用参数
sysctl -p
```

---

## 第七步：重启Streamlit

```bash
# 停止当前Streamlit
pkill -f streamlit

# 等待2秒
sleep 2

# 使用优化设置启动
cd /root/mlflow_learning_project  # 修改为你的路径
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
nohup streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 127.0.0.1 \
    --server.maxUploadSize 200 \
    > /tmp/streamlit.log 2>&1 &

# 检查是否启动成功
sleep 3
ps aux | grep streamlit | grep -v grep
```

---

## 第八步：验证优化效果

```bash
# 检查内存
free -h

# 检查服务
systemctl status nginx
ps aux | grep streamlit

# 测试访问
curl -k https://127.0.0.1 | head -20
```

---

## ✅ 完成！

现在可以：
1. 访问：`https://8.129.225.152`
2. 测试性能是否提升
3. 准备演示给老板

---

## 💡 提示

- 如果遇到问题，查看日志：`tail -f /tmp/streamlit.log`
- 如果需要恢复原文件：`cp streamlit_app.py.backup streamlit_app.py`
- 演示前记得预热：提前访问一次系统，让模型加载完成

