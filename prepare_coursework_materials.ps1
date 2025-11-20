# 无人机信安课设素材整理脚本
# 自动复制所有实验数据、图片和报告到课设素材文件夹

$targetDir = "D:\无人机信安课设素材截图"
$projectRoot = "D:\UAV_Adversarial_Security"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "无人机信安课设素材整理" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 创建目标目录结构
Write-Host "`n[1/6] 创建目录结构..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$targetDir\01_训练结果图片" | Out-Null
New-Item -ItemType Directory -Force -Path "$targetDir\02_对抗样本示例" | Out-Null
New-Item -ItemType Directory -Force -Path "$targetDir\03_检测报告数据" | Out-Null
New-Item -ItemType Directory -Force -Path "$targetDir\04_模型文件" | Out-Null
New-Item -ItemType Directory -Force -Path "$targetDir\05_截图说明文档" | Out-Null
Write-Host "✅ 目录结构创建完成" -ForegroundColor Green

# 步骤2：复制训练结果图片
Write-Host "`n[2/6] 复制训练结果图片..." -ForegroundColor Yellow
$artifactsBase = Join-Path $projectRoot "logs\mlflow\artifacts"

if (Test-Path $artifactsBase) {
    # 查找并复制训练结果图片
    $resultsFiles = Get-ChildItem $artifactsBase -Recurse -Filter "results.png" | Select-Object -First 1
    if ($resultsFiles) {
        Copy-Item $resultsFiles.FullName -Destination "$targetDir\01_训练结果图片\01_训练曲线_results.png" -Force
        Write-Host "  ✅ 训练曲线图" -ForegroundColor Green
    }
    
    $confusionFiles = Get-ChildItem $artifactsBase -Recurse -Filter "confusion_matrix.png" | Select-Object -First 1
    if ($confusionFiles) {
        Copy-Item $confusionFiles.FullName -Destination "$targetDir\01_训练结果图片\02_混淆矩阵_confusion_matrix.png" -Force
        Write-Host "  ✅ 混淆矩阵图" -ForegroundColor Green
    }
    
    $f1Files = Get-ChildItem $artifactsBase -Recurse -Filter "F1_curve.png" | Select-Object -First 1
    if ($f1Files) {
        Copy-Item $f1Files.FullName -Destination "$targetDir\01_训练结果图片\03_F1曲线_F1_curve.png" -Force
        Write-Host "  ✅ F1曲线图" -ForegroundColor Green
    }
    
    $prFiles = Get-ChildItem $artifactsBase -Recurse -Filter "PR_curve.png" | Select-Object -First 1
    if ($prFiles) {
        Copy-Item $prFiles.FullName -Destination "$targetDir\01_训练结果图片\04_PR曲线_PR_curve.png" -Force
        Write-Host "  ✅ PR曲线图" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  未找到 MLflow artifacts 目录" -ForegroundColor Yellow
}

# 步骤3：复制对抗样本示例图片
Write-Host "`n[3/6] 复制对抗样本示例图片..." -ForegroundColor Yellow
$adversarialDir = Join-Path $projectRoot "data\adversarial\fgsm"
if (Test-Path $adversarialDir) {
    $adversarialSamples = Get-ChildItem $adversarialDir -Filter "*.jpg" | Select-Object -First 10
    $index = 1
    foreach ($sample in $adversarialSamples) {
        $newName = "对抗样本_{0:D2}_{1}" -f $index, $sample.Name
        Copy-Item $sample.FullName -Destination "$targetDir\02_对抗样本示例\$newName" -Force
        $index++
    }
    Write-Host "  ✅ 已复制 $($adversarialSamples.Count) 个对抗样本示例" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  未找到对抗样本目录" -ForegroundColor Yellow
}

# 步骤4：复制检测报告数据
Write-Host "`n[4/6] 复制检测报告数据..." -ForegroundColor Yellow
$attackEvalDir = Join-Path $projectRoot "runs\attack_eval"
if (Test-Path $attackEvalDir) {
    # 复制 JSON 报告
    $jsonFiles = Get-ChildItem $attackEvalDir -Filter "*.json"
    foreach ($file in $jsonFiles) {
        $newName = $file.Name -replace "fgsm_consistency", "检测报告_FGSM一致性"
        Copy-Item $file.FullName -Destination "$targetDir\03_检测报告数据\$newName" -Force
        Write-Host "  ✅ $newName" -ForegroundColor Green
    }
    
    # 从 MLflow 复制 CSV（如果存在）
    $csvFiles = Get-ChildItem $artifactsBase -Recurse -Filter "fgsm_consistency.csv" | Select-Object -First 1
    if ($csvFiles) {
        Copy-Item $csvFiles.FullName -Destination "$targetDir\03_检测报告数据\检测报告_FGSM一致性详细数据.csv" -Force
        Write-Host "  ✅ 检测报告 CSV" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  未找到检测报告目录" -ForegroundColor Yellow
}

# 步骤5：复制模型文件（可选，文件较大）
Write-Host "`n[5/6] 复制模型文件..." -ForegroundColor Yellow
$modelFiles = Get-ChildItem $artifactsBase -Recurse -Filter "best.pt" | Select-Object -First 1
if ($modelFiles) {
    Copy-Item $modelFiles.FullName -Destination "$targetDir\04_模型文件\YOLOv8_最佳模型_best.pt" -Force
    Write-Host "  ✅ 最佳模型文件 (大小: $([math]::Round($modelFiles.Length/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  未找到模型文件" -ForegroundColor Yellow
}

# 步骤6：创建截图说明文档
Write-Host "`n[6/6] 创建截图说明文档..." -ForegroundColor Yellow
$screenshotGuide = @"
# 无人机信安课设 - 截图清单

## 📸 需要手动截图的页面

### 一、MLflow UI 截图（http://localhost:5000）

#### 1. 实验列表页面
- **文件名**: `MLflow_01_实验列表.png`
- **说明**: 显示所有实验（训练、攻击、防御）的列表
- **截图内容**: 
  - 左侧实验列表
  - 右侧实验运行列表
  - 显示实验名称、创建时间、状态等

#### 2. 训练实验详情 - Parameters
- **文件名**: `MLflow_02_训练实验_参数.png`
- **说明**: 显示训练实验的所有参数
- **截图内容**: Parameters 标签页，包含 epochs, learning_rate, batch_size 等

#### 3. 训练实验详情 - Metrics
- **文件名**: `MLflow_03_训练实验_指标.png`
- **说明**: 显示训练实验的所有指标
- **截图内容**: Metrics 标签页，包含 mAP, accuracy, loss 等指标曲线

#### 4. 训练实验详情 - Artifacts
- **文件名**: `MLflow_04_训练实验_模型文件.png`
- **说明**: 显示训练实验保存的模型和文件
- **截图内容**: Artifacts 标签页，显示 weights/best.pt, plots/ 等文件

#### 5. 攻击实验详情
- **文件名**: `MLflow_05_攻击实验_FGSM.png`
- **说明**: 显示 FGSM 攻击实验的详细信息
- **截图内容**: 包含攻击参数（eps, attack_type 等）和指标

#### 6. 检测实验详情 - Artifacts
- **文件名**: `MLflow_06_检测实验_报告文件.png`
- **说明**: 显示检测实验生成的报告文件
- **截图内容**: Artifacts 标签页，显示 fgsm_consistency.csv, fgsm_consistency.json 等

#### 7. 指标对比图
- **文件名**: `MLflow_07_指标对比.png`
- **说明**: 对比多个实验的指标
- **截图内容**: 在 MLflow 中选择多个实验，查看指标对比图表

### 二、Streamlit Dashboard 截图（http://localhost:8501）

#### 8. 对抗样本统计表格
- **文件名**: `Streamlit_01_对抗样本统计表格.png`
- **说明**: 显示对抗样本的详细统计数据
- **截图内容**: 包含 image, attack, eps, delta_l1, delta_l2, delta_linf 等列的数据表格

#### 9. 可视化图表
- **文件名**: `Streamlit_02_可视化图表.png`
- **说明**: 显示对抗攻击的可视化图表
- **截图内容**: 如果有数据，截图显示 delta_l1, delta_l2, delta_linf 的曲线图

#### 10. 图片对比（如果有）
- **文件名**: `Streamlit_03_原始vs对抗样本对比.png`
- **说明**: 显示原始图片和对抗样本的对比
- **截图内容**: 如果有此功能，截图显示对比效果

### 三、训练过程截图（可选）

#### 11. 训练命令行输出
- **文件名**: `训练_命令行输出.png`
- **说明**: 训练过程中的命令行输出
- **截图内容**: 显示训练进度、loss、accuracy 等实时输出

---

## 📋 截图操作步骤

1. **打开 MLflow UI**: 访问 http://localhost:5000
2. **打开 Streamlit**: 访问 http://localhost:8501
3. **按顺序截图**: 按照上述清单，依次截图并保存到 `05_截图说明文档` 文件夹
4. **命名规范**: 严格按照文件名命名，便于后续整理

---

## ✅ 完成检查清单

- [ ] MLflow_01_实验列表.png
- [ ] MLflow_02_训练实验_参数.png
- [ ] MLflow_03_训练实验_指标.png
- [ ] MLflow_04_训练实验_模型文件.png
- [ ] MLflow_05_攻击实验_FGSM.png
- [ ] MLflow_06_检测实验_报告文件.png
- [ ] MLflow_07_指标对比.png
- [ ] Streamlit_01_对抗样本统计表格.png
- [ ] Streamlit_02_可视化图表.png
- [ ] Streamlit_03_原始vs对抗样本对比.png（如果有）
- [ ] 训练_命令行输出.png（可选）

---

## 📝 注意事项

1. 截图时确保窗口最大化，显示完整内容
2. 截图清晰，文字可读
3. 保存为 PNG 格式，保持高质量
4. 按照文件名严格命名，不要修改
5. 所有截图保存在 `05_截图说明文档` 文件夹中

---

生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

$screenshotGuide | Out-File -FilePath "$targetDir\05_截图说明文档\截图清单和操作指南.md" -Encoding UTF8
Write-Host "  ✅ 截图说明文档已创建" -ForegroundColor Green

# 创建文件清单
Write-Host "`n[完成] 生成文件清单..." -ForegroundColor Yellow
$fileList = @"
# 无人机信安课设素材文件清单

生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## 📁 文件结构

"@

# 统计各目录文件
$dirs = @(
    "01_训练结果图片",
    "02_对抗样本示例", 
    "03_检测报告数据",
    "04_模型文件",
    "05_截图说明文档"
)

foreach ($dir in $dirs) {
    $dirPath = Join-Path $targetDir $dir
    if (Test-Path $dirPath) {
        $files = Get-ChildItem $dirPath -File
        $fileList += "`n### $dir`n"
        if ($files.Count -gt 0) {
            foreach ($file in $files) {
                $size = if ($file.Length -lt 1MB) { 
                    "$([math]::Round($file.Length/1KB, 2)) KB" 
                } else { 
                    "$([math]::Round($file.Length/1MB, 2)) MB" 
                }
                $fileList += "- $($file.Name) ($size)`n"
            }
        } else {
            $fileList += "- （暂无文件）`n"
        }
    }
}

$fileList | Out-File -FilePath "$targetDir\文件清单.txt" -Encoding UTF8

# 显示总结
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ 素材整理完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n目标目录: $targetDir" -ForegroundColor Yellow
Write-Host "`n已整理内容:" -ForegroundColor Yellow
Write-Host "  📊 训练结果图片" -ForegroundColor White
Write-Host "  🎯 对抗样本示例" -ForegroundColor White
Write-Host "  📄 检测报告数据" -ForegroundColor White
Write-Host "  🤖 模型文件" -ForegroundColor White
Write-Host "  📸 截图说明文档" -ForegroundColor White
Write-Host "`n⚠️  请按照 '05_截图说明文档\截图清单和操作指南.md' 完成手动截图" -ForegroundColor Yellow
Write-Host "`n打开文件夹: " -NoNewline
Write-Host "explorer `"$targetDir`"" -ForegroundColor Cyan

