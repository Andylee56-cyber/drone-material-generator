# 🔒 HTTPS 部署配置指南（阿里云服务器）

## 📋 目标

将 Streamlit 应用配置为 HTTPS 访问，实现：
- ✅ 使用 `https://8.129.225.152` 访问（无需端口号）
- ✅ 自动从 HTTP 跳转到 HTTPS
- ✅ 24/7 稳定运行
- ✅ 随时随地快速访问

---

## 🎯 第一步：配置阿里云防火墙（重要！）

### 1.1 在阿里云控制台配置

1. **登录阿里云控制台**
   - 访问：https://ecs.console.aliyun.com
   - 进入"轻量应用服务器" → 找到你的服务器

2. **打开防火墙设置**
   - 点击服务器名称进入详情页
   - 点击顶部"防火墙"标签

3. **添加端口规则**
   
   **规则1：HTTP 端口（80）**
   - 点击"添加规则"
   - 应用类型：`自定义`
   - 协议：`TCP`
   - 端口范围：`80`
   - 策略：`允许`
   - 备注：`HTTP访问`
   - 点击"确定"

   **规则2：HTTPS 端口（443）**
   - 点击"添加规则"
   - 应用类型：`自定义`
   - 协议：`TCP`
   - 端口范围：`443`
   - 策略：`允许`
   - 备注：`HTTPS访问`
   - 点击"确定"

4. **确认规则已添加**
   - 应该能看到两条规则：
     - `TCP:80` - 允许
     - `TCP:443` - 允许

---

## 🔧 第二步：连接服务器

### 方法1：使用阿里云网页终端（推荐）

1. 在阿里云控制台，点击"远程连接"
2. 选择"Workbench 一键连接"
3. 连接成功后，在终端中执行命令

### 方法2：使用本地 PowerShell

```powershell
ssh root@8.129.225.152
```

输入密码连接。

---

## 📦 第三步：安装 Nginx 和 OpenSSL

连接服务器后，执行以下命令：

```bash
# 更新软件包列表
apt update

# 安装 Nginx 和 OpenSSL
apt install nginx openssl -y
```

**执行后应该看到：**
- `nginx is already the newest version` 或安装成功
- `openssl is already the newest version` 或安装成功

---

## 🔐 第四步：创建 SSL 证书

### 方案A：自签名证书（快速，适合测试）

```bash
# 创建证书目录
mkdir -p /etc/nginx/ssl

# 生成自签名证书（有效期1年）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/streamlit.key \
  -out /etc/nginx/ssl/streamlit.crt \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=8.129.225.152"
```

**执行后应该看到：**
- `Generating a RSA private key`
- `writing new private key to '/etc/nginx/ssl/streamlit.key'`

### 方案B：Let's Encrypt 免费证书（推荐，适合生产环境）

**前提条件：需要域名**

如果你有域名（如：`yourdomain.com`），可以使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx -y

# 申请证书（替换 yourdomain.com 为你的域名）
certbot --nginx -d yourdomain.com

# 按照提示输入邮箱，选择同意协议
# Certbot 会自动配置 Nginx
```

---

## ⚙️ 第五步：配置 Nginx

### 5.1 创建 Nginx 配置文件

```bash
nano /etc/nginx/sites-available/streamlit
```

### 5.2 在 nano 中粘贴以下内容

**（直接复制整段，包括所有内容）**

```
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
```

### 5.3 保存并退出 nano

1. 按 `Ctrl + O` 保存
2. 按 `Enter` 确认文件名
3. 按 `Ctrl + X` 退出

---

## 🔗 第六步：启用 Nginx 配置

```bash
# 创建软链接（启用配置）
ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/

# 删除默认配置（避免冲突）
rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置是否正确
nginx -t
```

**执行 `nginx -t` 后应该看到：**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**如果看到错误，告诉我具体错误信息。**

---

## 🚀 第七步：启动 Nginx

```bash
# 启动 Nginx
systemctl start nginx

# 设置开机自启
systemctl enable nginx

# 检查 Nginx 状态
systemctl status nginx
```

**执行 `systemctl status nginx` 后应该看到：**
- `Active: active (running)` - 表示 Nginx 正在运行

---

## ✅ 第八步：验证 HTTPS 访问

### 8.1 测试 HTTP 自动跳转

在浏览器中访问：
```
http://8.129.225.152
```

**应该自动跳转到：**
```
https://8.129.225.152
```

### 8.2 访问 HTTPS

在浏览器中访问：
```
https://8.129.225.152
```

**如果使用自签名证书，浏览器会提示"不安全连接"：**
1. 点击"高级"或"Advanced"
2. 点击"继续访问"或"Proceed to 8.129.225.152 (unsafe)"
3. 之后即可正常使用

### 8.3 验证功能

- ✅ 应用界面正常显示
- ✅ 可以上传图片
- ✅ 可以生成多角度素材
- ✅ 所有功能正常

---

## 🔍 故障排查

### 问题1：无法访问 HTTPS

**检查步骤：**

```bash
# 1. 检查 Nginx 是否运行
systemctl status nginx

# 2. 检查防火墙规则
ufw status

# 3. 检查 Nginx 错误日志
tail -n 50 /var/log/nginx/error.log

# 4. 检查端口是否监听
netstat -tlnp | grep -E '80|443'
```

### 问题2：浏览器提示"连接被拒绝"

**可能原因：**
- 阿里云防火墙未开放 80/443 端口
- Nginx 未启动

**解决方法：**
1. 检查阿里云控制台防火墙设置
2. 执行 `systemctl restart nginx`

### 问题3：HTTP 不跳转到 HTTPS

**检查配置文件：**

```bash
cat /etc/nginx/sites-available/streamlit
```

确认第一个 `server` 块中有 `return 301 https://$server_name$request_uri;`

### 问题4：Streamlit 功能异常

**检查 Streamlit 服务：**

```bash
# 检查 Streamlit 服务状态
systemctl status streamlit-app

# 查看 Streamlit 日志
journalctl -u streamlit-app -n 50 --no-pager
```

---

## 📝 完整命令清单（一键复制）

如果你已经连接服务器，可以按顺序执行以下命令：

```bash
# 1. 安装 Nginx
apt update && apt install nginx openssl -y

# 2. 创建证书目录
mkdir -p /etc/nginx/ssl

# 3. 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/streamlit.key -out /etc/nginx/ssl/streamlit.crt -subj "/C=CN/ST=State/L=City/O=Organization/CN=8.129.225.152"

# 4. 创建 Nginx 配置（需要手动用 nano 编辑）
nano /etc/nginx/sites-available/streamlit
# （在 nano 中粘贴配置内容，保存退出）

# 5. 启用配置
ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 6. 测试配置
nginx -t

# 7. 启动 Nginx
systemctl start nginx
systemctl enable nginx

# 8. 检查状态
systemctl status nginx
```

---

## 🎉 完成！

配置完成后，你可以：

1. **访问应用：** `https://8.129.225.152`
2. **分享给老板：** 直接发送 HTTPS 链接
3. **随时随地访问：** 24/7 稳定运行

---

## 📞 需要帮助？

如果遇到问题，告诉我：
1. 具体错误信息
2. 执行到哪一步
3. 错误截图（如果有）

我会帮你解决！

