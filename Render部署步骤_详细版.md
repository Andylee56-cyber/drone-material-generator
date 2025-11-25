# 🚀 Render 部署步骤（详细版）

## 📋 问题说明

Railway 免费版现在只能部署数据库，不能部署应用。改用 **Render** 部署，免费版可用。

---

## 🎯 Render 部署步骤

### 第一步：注册 Render 账号

1. 访问：https://render.com
2. 点击右上角 "Get Started for Free"
3. 选择 "Sign up with GitHub"
4. 使用你的 GitHub 账号登录并授权

### 第二步：创建 Web Service

1. 登录后，点击 "New +" 按钮（右上角）
2. 选择 "Web Service"
3. 在 "Connect a repository" 部分：
   - 点击 "Connect account"（如果还没连接 GitHub）
   - 搜索并选择：`Andylee56-cyber/drone-material-generator`
   - 点击 "Connect"

### 第三步：配置服务

填写以下配置：

**基本信息**：
- **Name**: `drone-material-generator`（或任意名称）
- **Region**: 选择 `Singapore`（离中国最近，速度最快）
- **Branch**: `main`
- **Root Directory**: 留空（使用根目录）

**构建和启动**：
- **Environment**: `Python 3`
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  streamlit run app/web/material_generator_app.py --server.port $PORT --server.address 0.0.0.0
  ```

**实例类型**：
- **Instance Type**: `Free`（免费版）

### 第四步：部署

1. 点击 "Create Web Service"
2. Render 会自动开始部署（约 3-5 分钟）
3. 等待部署完成

### 第五步：获取访问链接

部署完成后：
- Render 会生成一个 URL（如：`https://drone-material-generator.onrender.com`）
- 在服务页面可以看到 "Your service is live at: [URL]"

---

## ⚠️ 注意事项

### 免费版限制

1. **Sleep 机制**：
   - 免费版在 15 分钟无活动后会进入 sleep 状态
   - 首次访问需要等待约 30 秒唤醒
   - 之后访问速度正常

2. **资源限制**：
   - CPU: 0.1-0.5 vCPU
   - 内存: 512MB RAM
   - 对于你的应用应该足够

### 如果需要 24/7 运行（不 sleep）

可以升级到 **Starter Plan**（$7/月）：
- 不会 sleep
- 24/7 运行
- 更多资源

---

## 🔧 如果部署失败

### 检查日志

1. 在 Render 服务页面，点击 "Logs" 标签
2. 查看错误信息
3. 常见问题：
   - OpenCV 导入错误 → 已修复
   - 端口配置错误 → 使用 `$PORT` 环境变量
   - 依赖安装失败 → 检查 `requirements.txt`

### 手动触发重新部署

1. 点击 "Manual Deploy"
2. 选择 "Deploy latest commit"

---

## 📝 部署后验证

部署完成后，访问你的应用 URL，检查：
- [ ] 页面可以正常加载
- [ ] 可以上传图片
- [ ] 可以生成素材
- [ ] 增强训练功能正常

---

## 🎉 完成！

部署成功后，应用将可以通过 Render 提供的 URL 访问。

**免费版**：15 分钟无活动后会 sleep，首次访问需等待约 30 秒
**付费版**（$7/月）：24/7 运行，不会 sleep

