# Claude Code 部署指南（国内版 - 无需梯子）

## 📋 系统要求

- **操作系统**: Windows 10/11 (64位)
- **内存**: 至少 8GB RAM（推荐 16GB）
- **存储空间**: 至少 5GB 可用空间（Node.js + 依赖包）
- **网络**: 需要稳定的互联网连接（使用国内镜像源）

---

## 🚀 完整部署流程

### 第一步：安装 Node.js（使用国内下载源）

#### 1.1 下载 Node.js

**方法一：使用淘宝镜像下载（推荐）**

1. 打开浏览器，访问：`https://npmmirror.com/mirrors/node/`
2. 选择最新 LTS 版本（例如：v20.x.x）
3. 下载 Windows 安装包：
   - 64位系统：选择 `node-v20.x.x-x64.msi`
   - 32位系统：选择 `node-v20.x.x-x86.msi`

**方法二：使用华为云镜像**

1. 访问：`https://mirrors.huaweicloud.com/nodejs/`
2. 选择 LTS 版本下载

#### 1.2 安装 Node.js

1. **双击下载的 `.msi` 安装文件**
2. **安装向导步骤**：
   - 点击 "Next"
   - 接受许可协议，点击 "Next"
   - 选择安装路径（默认：`C:\Program Files\nodejs\`），点击 "Next"
   - **重要**：勾选 "Automatically install the necessary tools"（自动安装必要工具）
   - 点击 "Install"，等待安装完成
   - 点击 "Finish"

#### 1.3 验证 Node.js 安装

1. **打开 PowerShell 或 CMD**
   - 按 `Win + X`，选择 "Windows PowerShell" 或 "命令提示符"

2. **检查版本**：
```powershell
node -v
npm -v
```

3. **预期输出**：
```
v20.x.x
10.x.x
```

如果显示版本号，说明安装成功！

---

### 第二步：配置 npm 国内镜像源

#### 2.1 设置淘宝镜像（推荐）

在 PowerShell 中执行：

```powershell
# 设置 npm 镜像源为淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证配置
npm config get registry
```

**预期输出**：`https://registry.npmmirror.com`

#### 2.2 配置其他镜像源（备用）

如果淘宝镜像有问题，可以使用：

```powershell
# 华为云镜像
npm config set registry https://repo.huaweicloud.com/repository/npm/

# 腾讯云镜像
npm config set registry https://mirrors.cloud.tencent.com/npm/

# 中科大镜像
npm config set registry https://npmreg.proxy.ustclug.org/
```

#### 2.3 配置其他工具镜像（可选，仅在需要时配置）

**注意**：这些配置不是必需的，只有在安装 Electron 或需要 Python 时才需要。

```powershell
# 方法1：使用环境变量（推荐，永久生效）
# 配置 Electron 镜像（如果需要安装 Electron 应用）
[Environment]::SetEnvironmentVariable("ELECTRON_MIRROR", "https://npmmirror.com/mirrors/electron/", "User")

# 配置 Python 镜像（如果需要编译原生模块）
[Environment]::SetEnvironmentVariable("PYTHON_MIRROR", "https://npmmirror.com/mirrors/python/", "User")

# 方法2：临时设置（仅当前会话有效）
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
$env:PYTHON_MIRROR = "https://npmmirror.com/mirrors/python/"

# 验证环境变量
Write-Host "Electron 镜像: $env:ELECTRON_MIRROR"
Write-Host "Python 镜像: $env:PYTHON_MIRROR"
```

**说明**：
- `npx` 会自动使用 npm 的镜像源，无需单独配置
- Electron 和 Python 镜像只在安装相关依赖时才需要
- 对于大多数项目，只需要配置 npm 主镜像源即可

---

### 第三步：安装 Claude Code 相关工具

#### 3.1 安装全局工具（可选）

```powershell
# 安装 yarn（可选，npm 的替代品）
npm install -g yarn --registry=https://registry.npmmirror.com

# 配置 yarn 镜像
yarn config set registry https://registry.npmmirror.com

# 安装 pnpm（可选，更快的包管理器）
npm install -g pnpm --registry=https://registry.npmmirror.com

# 配置 pnpm 镜像
pnpm config set registry https://registry.npmmirror.com
```

#### 3.2 创建项目目录

```powershell
# 创建项目文件夹
mkdir D:\claude-code-project
cd D:\claude-code-project

# 或者使用你喜欢的路径
```

#### 3.3 初始化项目

```powershell
# 初始化 npm 项目
npm init -y

# 这会创建 package.json 文件
```

---

### 第四步：安装 Claude Code 开发环境

#### 4.1 安装必要的依赖包

**基础安装（必需）**：

```powershell
# 安装基础开发工具
npm install --save-dev typescript @types/node --registry=https://registry.npmmirror.com

# 安装常用工具
npm install axios dotenv --registry=https://registry.npmmirror.com
```

**Electron 安装（可选，仅在需要构建桌面应用时）**：

如果遇到 SSL 证书错误，使用以下方法：

```powershell
# 方法1：配置 Electron 镜像源（推荐）
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
npm install --save-dev electron electron-builder --registry=https://registry.npmmirror.com

# 方法2：如果方法1不行，临时禁用 SSL 验证（不推荐，仅用于测试）
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
npm install --save-dev electron electron-builder --registry=https://registry.npmmirror.com
$env:NODE_TLS_REJECT_UNAUTHORIZED = "1"  # 安装后恢复

# 方法3：如果不需要 Electron，直接跳过这一步
```

**说明**：
- Electron 用于构建桌面应用程序，对于大多数 Web 开发项目不需要
- 如果只是学习 Node.js 开发，可以完全跳过 Electron 安装
- 基础工具（TypeScript、axios、dotenv）已经足够开始开发

#### 4.2 配置 package.json

编辑 `package.json` 文件，添加以下配置：

```json
{
  "name": "claude-code-project",
  "version": "1.0.0",
  "description": "Claude Code Development Environment",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "node index.js",
    "build": "tsc"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
```

---

### 第五步：验证安装

#### 5.1 创建测试文件

创建 `test.js` 文件：

```javascript
console.log('Node.js 版本:', process.version);
console.log('npm 版本:', process.env.npm_version || '已安装');
console.log('当前工作目录:', process.cwd());
console.log('✅ Claude Code 开发环境配置成功！');
```

#### 5.2 运行测试

```powershell
node test.js
```

**预期输出**：
```
Node.js 版本: v20.x.x
npm 版本: 已安装
当前工作目录: D:\claude-code-project
✅ Claude Code 开发环境配置成功！
```

---

## ⚙️ 常用配置命令

### 查看当前配置

```powershell
# 查看 npm 配置
npm config list

# 查看镜像源
npm config get registry

# 查看全局安装路径
npm config get prefix
```

### 清除缓存

```powershell
# 清除 npm 缓存
npm cache clean --force

# 如果下载失败，先清除缓存再重试
```

### 更新 npm

```powershell
# 更新 npm 到最新版本
npm install -g npm@latest --registry=https://registry.npmmirror.com
```

---

## 📝 使用说明

### 基本操作

1. **创建新项目**
```powershell
mkdir my-project
cd my-project
npm init -y
```

2. **安装依赖包**
```powershell
# 安装生产依赖
npm install package-name --registry=https://registry.npmmirror.com

# 安装开发依赖
npm install package-name --save-dev --registry=https://registry.npmmirror.com
```

3. **运行项目**
```powershell
npm start
# 或
node index.js
```

### 常用 npm 命令

| 命令 | 说明 |
|------|------|
| `npm install` | 安装所有依赖 |
| `npm install package` | 安装指定包 |
| `npm uninstall package` | 卸载包 |
| `npm update` | 更新所有包 |
| `npm list` | 查看已安装的包 |
| `npm search keyword` | 搜索包 |
| `npm run script-name` | 运行脚本 |

---

## ❓ 常见问题解决

### 问题1: npm install 速度慢或失败

**解决方案**：
```powershell
# 1. 确认镜像源配置正确
npm config get registry

# 2. 如果不对，重新设置
npm config set registry https://registry.npmmirror.com

# 3. 清除缓存
npm cache clean --force

# 4. 使用详细模式查看错误
npm install --verbose
```

### 问题2: 权限错误（EACCES）

**解决方案**：
```powershell
# Windows 下以管理员身份运行 PowerShell
# 或者修改 npm 全局安装路径
npm config set prefix "C:\Users\你的用户名\AppData\Roaming\npm"
```

### 问题3: Node.js 命令找不到（"无法将'node'项识别为 cmdlet"）

**错误提示**：
```
node : 无法将"node"项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

**原因**：Node.js 已安装，但未添加到系统 PATH 环境变量中。

**详细解决步骤**：

#### 步骤1：确认 Node.js 安装位置

在 PowerShell 中执行：

```powershell
# 检查默认安装路径是否存在
Test-Path "C:\Program Files\nodejs\node.exe"
Test-Path "C:\Program Files (x86)\nodejs\node.exe"

# 或者搜索 node.exe
Get-ChildItem -Path "C:\Program Files" -Filter "node.exe" -Recurse -ErrorAction SilentlyContinue
```

#### 步骤2：找到 Node.js 安装路径

常见安装路径：
- `C:\Program Files\nodejs\`
- `C:\Program Files (x86)\nodejs\`
- `C:\Users\你的用户名\AppData\Roaming\npm\`

如果找不到，检查安装程序日志或重新安装时注意安装路径。

#### 步骤3：手动添加到 PATH（方法一：图形界面）

1. **打开环境变量设置**：
   - 按 `Win + R`，输入 `sysdm.cpl`，回车
   - 或：右键 "此电脑" → "属性" → "高级系统设置" → "环境变量"

2. **编辑 PATH 变量**：
   - 在 "系统变量" 区域找到 `Path`
   - 点击 "编辑"
   - 点击 "新建"
   - 输入 Node.js 安装路径（例如：`C:\Program Files\nodejs\`）
   - 点击 "确定" 保存所有窗口

#### 步骤4：手动添加到 PATH（方法二：PowerShell 命令）

**以管理员身份运行 PowerShell**，然后执行：

```powershell
# 获取当前 PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

# Node.js 安装路径（根据实际情况修改）
$nodePath = "C:\Program Files\nodejs"

# 检查是否已存在
if ($currentPath -notlike "*$nodePath*") {
    # 添加到 PATH
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$nodePath", "Machine")
    Write-Host "✅ 已添加 Node.js 到 PATH: $nodePath" -ForegroundColor Green
} else {
    Write-Host "⚠️ Node.js 路径已存在于 PATH 中" -ForegroundColor Yellow
}
```

#### 步骤5：刷新环境变量

**重要**：修改 PATH 后必须刷新才能生效！

```powershell
# 方法1：关闭并重新打开 PowerShell（推荐）
# 直接关闭当前 PowerShell 窗口，重新打开

# 方法2：在当前会话中刷新（临时生效）
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 方法3：重启电脑（最彻底，但通常不需要）
```

#### 步骤6：验证修复

```powershell
# 检查 node 命令
node -v

# 检查 npm 命令
npm -v

# 检查完整路径
where.exe node
where.exe npm
```

**预期输出**：
```
v20.x.x
10.x.x
C:\Program Files\nodejs\node.exe
C:\Program Files\nodejs\npm.cmd
```

#### 步骤7：如果还是不行

1. **完全重启 PowerShell**：
   - 关闭所有 PowerShell 窗口
   - 重新打开新的 PowerShell

2. **检查用户 PATH**：
```powershell
# 查看用户 PATH
[Environment]::GetEnvironmentVariable("Path", "User")

# 如果需要，也添加到用户 PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;C:\Program Files\nodejs", "User")
```

3. **重新安装 Node.js**：
   - 卸载现有版本
   - 重新下载安装
   - **安装时确保勾选 "Add to PATH" 选项**

#### 快速修复脚本（一键执行）

将以下代码保存为 `fix-nodejs-path.ps1`，**以管理员身份运行**：

```powershell
# 检查并修复 Node.js PATH
$nodePaths = @(
    "C:\Program Files\nodejs",
    "C:\Program Files (x86)\nodejs"
)

$found = $false
foreach ($path in $nodePaths) {
    if (Test-Path "$path\node.exe") {
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($currentPath -notlike "*$path*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$path", "Machine")
            Write-Host "✅ 已添加: $path" -ForegroundColor Green
        }
        $found = $true
        break
    }
}

if (-not $found) {
    Write-Host "❌ 未找到 Node.js 安装，请先安装 Node.js" -ForegroundColor Red
} else {
    Write-Host "`n⚠️ 请关闭并重新打开 PowerShell 使更改生效！" -ForegroundColor Yellow
    Write-Host "然后运行: node -v" -ForegroundColor Cyan
}
```

### 问题4: 下载 Electron 失败

**解决方案**：
```powershell
# 设置 Electron 镜像
npm config set electron_mirror https://npmmirror.com/mirrors/electron/

# 或者使用环境变量
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
```

### 问题5: Python 相关错误

**解决方案**：
```powershell
# 某些包需要 Python，设置 Python 镜像
npm config set python_mirror https://npmmirror.com/mirrors/python/

# 或者安装 Python（从 https://www.python.org/downloads/）
```

---

## 🔧 高级配置（可选）

### 使用 .npmrc 文件配置

在项目根目录创建 `.npmrc` 文件：

```
registry=https://registry.npmmirror.com
electron_mirror=https://npmmirror.com/mirrors/electron/
python_mirror=https://npmmirror.com/mirrors/python/
```

### 配置代理（如果需要）

```powershell
# 设置代理（如果有公司代理）
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080

# 取消代理
npm config delete proxy
npm config delete https-proxy
```

---

## ✅ 部署检查清单

- [ ] Node.js 安装成功（`node -v` 有输出）
- [ ] npm 安装成功（`npm -v` 有输出）
- [ ] npm 镜像源配置为国内镜像（`npm config get registry` 显示国内地址）
- [ ] 能够成功安装包（`npm install` 无错误）
- [ ] 测试文件运行成功（`node test.js` 正常输出）
- [ ] 项目目录创建成功
- [ ] package.json 文件存在

---

## 📞 获取帮助

- **npm 官方文档（中文）**: https://www.npmjs.cn/
- **Node.js 中文网**: http://nodejs.cn/
- **淘宝 npm 镜像**: https://npmmirror.com/
- **常见问题**: 使用 `npm help` 查看帮助

---

## 🎯 快速命令参考

```powershell
# 一键配置（复制粘贴到 PowerShell）
npm config set registry https://registry.npmmirror.com
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set python_mirror https://npmmirror.com/mirrors/python/
npm cache clean --force
npm config list
```

---

**部署完成后，你的开发环境已配置完成，可以开始使用 Node.js 和 npm 进行开发工作！**

