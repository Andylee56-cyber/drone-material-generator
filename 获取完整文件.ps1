# 获取完整文件内容
ssh root@8.129.225.152 "cat /opt/drone-material-generator/app/web/material_generator_app.py" | Out-File -FilePath material_generator_app_original.py -Encoding UTF8

Write-Host "文件已保存到: material_generator_app_original.py" -ForegroundColor Green
Write-Host "请把文件内容发给我，我会提供完整的优化版本" -ForegroundColor Yellow

