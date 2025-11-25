# 🚀 Fly.io 免费部署步骤（详细版）

## 📋 为什么选择 Fly.io？

- ✅ **完全免费**：有充足的免费额度
- ✅ **不会 sleep**：24/7 运行
- ✅ **性能好**：全球部署
- ✅ **无需信用卡**：不需要支付方式
- ✅ **国内访问**：速度较好

---

## 🎯 部署步骤

### 第一步：注册 Fly.io 账号

1. 访问：https://fly.io
2. 点击 "Get Started" 或 "Sign Up"
3. 使用 **GitHub 账号登录**（推荐，最简单）
4. 授权 Fly.io 访问 GitHub

### 第二步：安装 Fly CLI

#### Windows PowerShell 安装：

```powershell
# 在 PowerShell 中执行（管理员权限）
iwr https://fly.io/install.ps1 -useb | iex
```

#### 或者手动下载：

1. 访问：https://fly.io/docs/getting-started/installing-flyctl/
2. 下载 Windows 版本
3. 解压到任意目录
4. 将目录添加到 PATH 环境变量

### 第三步：登录 Fly.io

```powershell
# 在 PowerShell 中执行
fly auth login
```

会打开浏览器，完成登录。

### 第四步：创建 Fly.io 应用

```powershell
# 切换到项目目录
cd D:\mlflow_learning_project

# 创建 Fly.io 应用
fly launch
```

**按提示操作**：
1. 应用名称：输入 `drone-material-generator`（或任意名称）
2. 选择区域：选择 `sin`（新加坡，离中国最近）
3. 是否创建 Postgres：选择 `No`
4. 是否创建 Redis：选择 `No`
5. 是否立即部署：选择 `Yes`

### 第五步：创建配置文件

如果 `fly launch` 没有自动创建，手动创建 `fly.toml`：

```powershell
# 创建 fly.toml
@"
app = "drone-material-generator"
primary_region = "sin"

[build]

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [services.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[[services.http_checks]]
  interval = "10s"
  timeout = "2s"
  grace_period = "5s"
  method = "GET"
  path = "/_stcore/health"
"@ | Out-File -FilePath fly.toml -Encoding utf8
```

### 第六步：创建 Dockerfile

```powershell
# 创建 Dockerfile
@"
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（OpenCV 需要）
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["streamlit", "run", "app/web/material_generator_app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
"@ | Out-File -FilePath Dockerfile -Encoding utf8
```

### 第七步：创建 .dockerignore

```powershell
# 创建 .dockerignore
@"
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv
.git
.gitignore
*.md
.DS_Store
test_*
generated_materials/
temp_*
"@ | Out-File -FilePath .dockerignore -Encoding utf8
```

### 第八步：提交到 GitHub

```powershell
# 添加新文件
git add Dockerfile fly.toml .dockerignore
git commit -m "Add Fly.io deployment configuration"
git push origin main
```

### 第九步：部署到 Fly.io

```powershell
# 部署应用
fly deploy
```

等待部署完成（约 3-5 分钟）。

### 第十步：获取访问链接

部署完成后，Fly.io 会显示：
```
App is available at: https://drone-material-generator.fly.dev
```

---

## 🔧 如果遇到问题

### 问题 1：fly 命令找不到

**解决**：
```powershell
# 检查是否安装成功
fly version

# 如果找不到，检查 PATH 环境变量
# 或将 fly.exe 所在目录添加到 PATH
```

### 问题 2：部署失败

**解决**：
```powershell
# 查看日志
fly logs

# 查看应用状态
fly status

# 重新部署
fly deploy
```

### 问题 3：OpenCV 导入错误

**解决**：
- Dockerfile 中已包含系统依赖
- 如果还有问题，检查 `requirements.txt` 中的 opencv-python-headless

---

## 📝 部署后验证

部署完成后，访问你的应用 URL，检查：
- [ ] 页面可以正常加载
- [ ] 可以上传图片
- [ ] 可以生成素材
- [ ] 增强训练功能正常

---

## 🎉 完成！

部署成功后，应用将：
- ✅ 24/7 运行（不会 sleep）
- ✅ 完全免费
- ✅ 随时随地可访问
- ✅ 适合给老板展示

---

## 💡 其他免费替代方案

如果 Fly.io 也有问题，还可以考虑：

### 方案 2：国内云服务器（需要付费但便宜）

- **阿里云轻量服务器**：¥24/月起
- **腾讯云轻量服务器**：¥24/月起
- 国内访问速度最快
- 需要备案（如果用域名）

### 方案 3：继续用 Streamlit Cloud（免费但会 sleep）

- 免费版会 sleep
- 首次访问需等待
- 但完全免费

---

## 🚀 立即开始

**推荐从 Fly.io 开始**，完全免费且不会 sleep！

```powershell
# 1. 安装 Fly CLI
iwr https://fly.io/install.ps1 -useb | iex

# 2. 登录
fly auth login

# 3. 创建应用
cd D:\mlflow_learning_project
fly launch
```

