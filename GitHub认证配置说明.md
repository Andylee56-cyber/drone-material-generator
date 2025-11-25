# 🔐 GitHub认证配置说明

## ⚠️ 重要提示

**GitHub已不再支持密码推送！** 从2021年8月13日起，GitHub要求使用 **Personal Access Token (PAT)** 代替密码进行Git操作。

---

## 🎯 你的GitHub信息

- **用户名**: `Andylee56-cyber`
- **仓库**: `https://github.com/Andylee56-cyber/drone-material-generator.git`

---

## 📝 创建Personal Access Token（5分钟）

### 步骤1：访问Token设置页面

1. 登录GitHub：https://github.com
2. 点击右上角头像 → **Settings**
3. 左侧菜单 → **Developer settings**
4. 左侧菜单 → **Personal access tokens** → **Tokens (classic)**
5. 或直接访问：https://github.com/settings/tokens

### 步骤2：生成新Token

1. 点击 **"Generate new token"** → **"Generate new token (classic)"**
2. 填写信息：
   - **Note**: `Streamlit Cloud部署`（描述用途）
   - **Expiration**: 选择过期时间（建议90天或No expiration）
   - **Select scopes**: 勾选 **`repo`**（全部权限）
     - 这会自动勾选所有repo相关权限
3. 点击 **"Generate token"**

### 步骤3：复制Token

⚠️ **重要**：Token只显示一次，请立即复制保存！

```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**保存位置建议**：
- 密码管理器（推荐）
- 或本地加密文件
- **不要**提交到Git仓库！

---

## 🔧 使用Token推送代码

### 方法1：在推送时输入Token

```powershell
cd D:\mlflow_learning_project
git push
```

当提示输入密码时：
- **Username**: `Andylee56-cyber`
- **Password**: 输入你的 **Personal Access Token**（不是GitHub密码）

### 方法2：配置Git凭据（推荐，只需一次）

#### Windows（使用Git Credential Manager）

```powershell
# 推送时输入Token，Git会自动保存
git push
# Username: Andylee56-cyber
# Password: 你的Token
```

Git会自动保存凭据，下次推送不需要再输入。

#### 手动配置（如果自动保存失败）

```powershell
# 配置Git使用Token
git config --global credential.helper wincred

# 或者使用Git Credential Manager
git config --global credential.helper manager-core
```

### 方法3：在URL中嵌入Token（不推荐，但可用）

```powershell
# 临时使用（不保存到配置）
git remote set-url origin https://Andylee56-cyber:你的Token@github.com/Andylee56-cyber/drone-material-generator.git

# 推送
git push

# 推送后，建议改回普通URL（安全）
git remote set-url origin https://github.com/Andylee56-cyber/drone-material-generator.git
```

---

## ✅ 验证配置

```powershell
# 测试推送（如果有更改）
cd D:\mlflow_learning_project
git status
git add .
git commit -m "测试Token配置"
git push
```

如果推送成功，说明Token配置正确！

---

## 🔄 更新Token

如果Token过期或需要更换：

1. 访问：https://github.com/settings/tokens
2. 找到旧Token → **Revoke**（撤销）
3. 创建新Token（重复上面的步骤）
4. 使用新Token重新配置

---

## 🛡️ 安全建议

1. **不要分享Token**
   - Token等同于密码，不要告诉任何人
   - 不要提交到代码仓库

2. **定期更换Token**
   - 建议每90天更换一次
   - 如果怀疑泄露，立即撤销

3. **使用最小权限**
   - 只勾选必要的权限（`repo`）
   - 不要勾选不必要的权限

4. **使用环境变量（高级）**
   ```powershell
   # 设置环境变量（仅当前会话）
   $env:GITHUB_TOKEN = "你的Token"
   
   # 在脚本中使用
   git push https://Andylee56-cyber:$env:GITHUB_TOKEN@github.com/Andylee56-cyber/drone-material-generator.git
   ```

---

## 🐛 常见问题

### Q1: 推送时提示 "Authentication failed"

**原因**：使用了GitHub密码而不是Token

**解决**：
1. 确认使用的是Token，不是密码
2. 检查Token是否过期
3. 检查Token权限是否包含`repo`

### Q2: 提示 "remote: Support for password authentication was removed"

**原因**：GitHub已禁用密码认证

**解决**：必须使用Personal Access Token

### Q3: Token在哪里查看？

**注意**：Token创建后只显示一次，无法再次查看！

**如果忘记**：
1. 撤销旧Token
2. 创建新Token
3. 使用新Token重新配置

---

## 📞 需要帮助？

如果遇到问题：
1. 检查Token是否正确复制（没有多余空格）
2. 确认Token权限包含`repo`
3. 确认Token未过期
4. 尝试撤销并重新创建Token

---

## ✅ 配置完成检查清单

- [ ] 已创建Personal Access Token
- [ ] Token已保存到安全位置
- [ ] 已测试推送代码（成功）
- [ ] 了解如何更新Token
- [ ] 了解安全注意事项

**配置完成后，就可以正常推送代码到GitHub了！** 🎉


