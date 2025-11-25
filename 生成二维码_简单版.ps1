$url = "https://drone-material-generator-ha8mscbtjeytbixqy6qtut.streamlit.app"
$qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=$url"
$outputPath = "qrcode.png"

Write-Host "正在生成二维码..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri $qrUrl -OutFile $outputPath -ErrorAction Stop
    
    if (Test-Path $outputPath) {
        $fullPath = (Resolve-Path $outputPath).Path
        Write-Host "成功！二维码已生成：" -ForegroundColor Green
        Write-Host $fullPath -ForegroundColor Cyan
        Write-Host ""
        Write-Host "正在打开二维码图片..." -ForegroundColor Yellow
        Start-Process $fullPath
    } else {
        Write-Host "生成失败：文件未创建" -ForegroundColor Red
    }
} catch {
    Write-Host "生成失败：" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "请使用在线工具生成：" -ForegroundColor Yellow
    Write-Host "1. 访问：https://cli.im/" -ForegroundColor Gray
    Write-Host "2. 粘贴链接：$url" -ForegroundColor Gray
    Write-Host "3. 生成并保存二维码" -ForegroundColor Gray
}




