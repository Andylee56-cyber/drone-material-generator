# 🔐 配置GitHub Personal Access Token
# 你的Token已配置，此脚本用于设置Git凭据

param(
    [string]$Token = ""
)

if ([string]::IsNullOrEmpty($Token)) {
    Write-Host "请输入你的GitHub Personal Access Token:" -ForegroundColor Yellow
    $Token = Read-Host -AsSecureString
    $Token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Token))
}

Write-Host "🔐 配置GitHub Personal Access Token..." -ForegroundColor Green
Write-Host ""

# 你的GitHub信息
$GitHubUsername = "Andylee56-cyber"
$Repository = "drone-material-generator"
$RemoteUrl = "https://github.com/$GitHubUsername/$Repository.git"

Write-Host "GitHub用户名: $GitHubUsername" -ForegroundColor Cyan
Write-Host "仓库: $Repository" -ForegroundColor Cyan
Write-Host ""

# 方法1：配置Git凭据助手（推荐）
Write-Host "📝 配置Git凭据助手..." -ForegroundColor Yellow
git config --global credential.helper manager-core

# 方法2：在URL中嵌入Token（临时，用于首次推送）
Write-Host "🔗 配置远程仓库URL（包含Token）..." -ForegroundColor Yellow
$TokenUrl = "https://$GitHubUsername`:$Token@github.com/$GitHubUsername/$Repository.git"
git remote set-url origin $TokenUrl

Write-Host ""
Write-Host "✅ Token配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  安全提示：" -ForegroundColor Yellow
Write-Host "   1. Token已嵌入到Git配置中" -ForegroundColor Yellow
Write-Host "   2. 建议推送后移除URL中的Token（见下方命令）" -ForegroundColor Yellow
Write-Host "   3. 使用Git凭据管理器保存Token更安全" -ForegroundColor Yellow
Write-Host ""

# 测试连接
Write-Host "🧪 测试Git连接..." -ForegroundColor Yellow
try {
    git ls-remote --heads origin main | Out-Null
    Write-Host "✅ 连接成功！" -ForegroundColor Green
} catch {
    Write-Host "❌ 连接失败，请检查Token是否正确" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 下一步：" -ForegroundColor Green
Write-Host "   1. 执行: git push" -ForegroundColor Cyan
Write-Host "   2. 推送成功后，执行以下命令移除URL中的Token：" -ForegroundColor Cyan
Write-Host "      git remote set-url origin $RemoteUrl" -ForegroundColor Cyan
Write-Host "   3. Git凭据管理器会自动保存Token" -ForegroundColor Cyan


