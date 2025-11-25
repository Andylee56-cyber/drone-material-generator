# ========================================
# 生成二维码 - 方便老板在手机上扫描访问
# ========================================

$url = "https://drone-material-generator-ha8mscbtjeytbixqy6qtut.streamlit.app"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "生成二维码链接" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "应用链接：" -ForegroundColor White
Write-Host $url -ForegroundColor Cyan
Write-Host ""
Write-Host "二维码生成方式：" -ForegroundColor Yellow
Write-Host ""
Write-Host "方法1：在线生成（推荐）" -ForegroundColor Green
Write-Host "1. 访问：https://cli.im/" -ForegroundColor Gray
Write-Host "2. 粘贴上面的链接" -ForegroundColor Gray
Write-Host "3. 点击生成二维码" -ForegroundColor Gray
Write-Host "4. 保存二维码图片发送给老板" -ForegroundColor Gray
Write-Host ""
Write-Host "方法2：使用微信" -ForegroundColor Green
Write-Host "1. 复制链接" -ForegroundColor Gray
Write-Host "2. 在微信中发送给自己" -ForegroundColor Gray
Write-Host "3. 长按链接，选择'生成二维码'" -ForegroundColor Gray
Write-Host "4. 保存二维码图片" -ForegroundColor Gray
Write-Host ""
Write-Host "方法3：使用PowerShell生成（需要安装模块）" -ForegroundColor Green
Write-Host "Install-Module -Name QRCodeGenerator -Force" -ForegroundColor Gray
Write-Host "New-QRCode -Content '$url' -Path 'qrcode.png'" -ForegroundColor Gray
Write-Host ""

# 尝试使用在线API生成二维码
Write-Host "正在生成二维码图片..." -ForegroundColor Yellow
try {
    # 使用反引号转义&符号
    $qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=300x300`&data=$url"
    $outputPath = "qrcode.png"
    
    Invoke-WebRequest -Uri $qrUrl -OutFile $outputPath
    
    if (Test-Path $outputPath) {
        Write-Host "✅ 二维码已生成：$outputPath" -ForegroundColor Green
        Write-Host ""
        Write-Host "请将二维码图片发送给老板，用手机扫描即可访问" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  自动生成失败，请使用在线工具生成" -ForegroundColor Yellow
    Write-Host "访问：https://cli.im/ 手动生成" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "华为手机访问建议" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 使用Chrome浏览器（推荐）" -ForegroundColor White
Write-Host "2. 或使用Microsoft Edge浏览器" -ForegroundColor White
Write-Host "3. 确保网络连接正常" -ForegroundColor White
Write-Host "4. 如果还是打不开，尝试切换网络（Wi-Fi/移动数据）" -ForegroundColor White
Write-Host ""

