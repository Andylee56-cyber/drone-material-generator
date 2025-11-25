# 第4周：完整训练流程测试 - Windows PowerShell执行计划

## 📋 执行环境准备

**前提条件：**
- ✅ 已激活 `drone_vision_clean` 环境（或 `drone_vision` 环境）
- ✅ 工作目录：`D:\mlflow_learning_project` 或 `C:\Windows\system32\drone_vision_project`
- ✅ Python版本：3.7+
- ✅ 已安装基础依赖：mlflow, matplotlib, opencv-python, pillow

---

## 🗓️ 第4周每日任务清单

### 📅 周一：小规模数据集准备

#### 🌅 上午 (9:00-12:00) - 数据集下载与预处理

**步骤1：准备工作环境（5分钟）**
```powershell
# 1. 打开PowerShell（管理员权限）
# 2. 激活conda环境
conda activate drone_vision_clean

# 3. 切换到项目目录（根据你的实际路径选择）
cd D:\mlflow_learning_project
# 或者
cd C:\Windows\system32\drone_vision_project

# 4. 创建数据集目录结构
New-Item -ItemType Directory -Force -Path data\external\visdrone
New-Item -ItemType Directory -Force -Path data\processed\visdrone
New-Item -ItemType Directory -Force -Path data\raw\images
New-Item -ItemType Directory -Force -Path data\raw\annotations

# 5. 验证目录创建成功
tree /F data
```

**步骤2：安装必要的Python包（10分钟）**
```powershell
# 安装数据处理相关包
pip install opencv-python pillow pyyaml numpy pandas

# 验证安装

```

**步骤3：下载VisDrone数据集（可选，如果网络允许）（30-60分钟）**

**选项A：从GitHub克隆（推荐用于学习）**
```powershell
cd data\external\visdrone
git clone https://github.com/VisDrone/VisDrone-Dataset.git

# 如果没有git，可以用浏览器下载zip包
# 访问：https://github.com/VisDrone/VisDrone-Dataset
# 下载后解压到 data\external\visdrone 目录
```

**选项B：创建模拟数据集（如果无法下载真实数据）**
```powershell
# 回到项目根目录
cd D:\mlflow_learning_project
# 或 cd C:\Windows\system32\drone_vision_project

# 运行之前创建的prepare_test_images.py生成测试数据
python scripts\prepare_test_images.py
```

**步骤4：创建VisDrone数据预处理脚本（30分钟）**

在PowerShell中执行：
```powershell
# 在scripts目录创建visdrone_processor.py
New-Item -ItemType File -Path scripts\visdrone_processor.py -Force
```

然后我会提供完整的脚本内容（见下方）。

---

#### 📝 脚本1：visdrone_processor.py

在PyCharm或文本编辑器中打开 `scripts/visdrone_processor.py`，输入以下代码：

```python
"""
VisDrone数据集预处理脚本
用于将VisDrone格式转换为COCO格式并调整图像尺寸
"""
import os
import json
from pathlib import Path
from PIL import Image


class VisDroneProcessor:
    def __init__(self, data_path="data/external/visdrone"):
        self.data_path = Path(data_path)
        self.output_path = Path("data/processed/visdrone")
        self.class_names = [
            'ignored regions', 'pedestrian', 'people', 'bicycle', 'car', 
            'van', 'truck', 'tricycle', 'awning-tricycle', 'bus', 'motor'
        ]
    
    def process_dataset(self):
        """处理整个数据集"""
        print("开始处理VisDrone数据集...")
        
        # 创建输出目录
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # 处理训练集
        self.process_split("train")
        
        # 处理验证集
        self.process_split("val")
        
        print("数据集处理完成！")
    
    def process_split(self, split_name):
        """处理特定分割的数据"""
        print(f"\n处理{split_name}集...")
        
        # 创建分割目录
        split_dir = self.output_path / split_name
        split_dir.mkdir(exist_ok=True)
        
        # 处理图像
        images_dir = split_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # 处理标注
        annotations_dir = split_dir / "annotations"
        annotations_dir.mkdir(exist_ok=True)
        
        # 查找源数据目录（适配多种可能的路径）
        possible_paths = [
            self.data_path / f"VisDrone2019-DET-{split_name}",
            self.data_path / f"VisDrone-Dataset" / f"VisDrone2019-DET-{split_name}",
            Path("data/raw/images")  # 如果使用测试数据
        ]
        
        source_images_dir = None
        for path in possible_paths:
            if path.exists():
                source_images_dir = path / "images"
                source_annotations_dir = path / "annotations"
                break
        
        if source_images_dir and source_images_dir.exists():
            print(f"  找到源图像目录: {source_images_dir}")
            # 处理图像
            image_count = 0
            for img_file in source_images_dir.glob("*.jpg"):
                try:
                    # 调整图像大小
                    processed_img = self.resize_image(img_file, max_size=(640, 640))
                    processed_img.save(images_dir / img_file.name)
                    image_count += 1
                except Exception as e:
                    print(f"  处理图像失败 {img_file.name}: {e}")
            print(f"  已处理 {image_count} 张图像")
        else:
            print(f"  警告: 未找到{split_name}集的源图像目录")
            print(f"  尝试的路径: {[str(p) for p in possible_paths]}")
        
        # 转换标注格式
        source_annotations_dir = self.data_path / f"VisDrone2019-DET-{split_name}" / "annotations"
        if not source_annotations_dir.exists():
            source_annotations_dir = Path("data/raw/annotations")
        
        if source_annotations_dir.exists():
            coco_annotations = self.convert_to_coco_format(
                source_annotations_dir, images_dir, split_name
            )
            
            # 保存COCO格式标注
            output_file = annotations_dir / "annotations.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(coco_annotations, f, indent=2, ensure_ascii=False)
            print(f"  已保存COCO格式标注: {output_file}")
        else:
            print(f"  警告: 未找到标注目录，创建空标注文件")
            # 创建空的COCO格式文件
            empty_coco = {
                "images": [],
                "annotations": [],
                "categories": []
            }
            for i, class_name in enumerate(self.class_names):
                empty_coco["categories"].append({
                    "id": i,
                    "name": class_name,
                    "supercategory": "object"
                })
            with open(annotations_dir / "annotations.json", 'w', encoding='utf-8') as f:
                json.dump(empty_coco, f, indent=2, ensure_ascii=False)
    
    def resize_image(self, image_path, max_size=(640, 640)):
        """调整图像大小"""
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    
    def convert_to_coco_format(self, annotations_dir, images_dir, split_name):
        """转换为COCO格式"""
        coco_data = {
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # 添加类别信息
        for i, class_name in enumerate(self.class_names):
            coco_data["categories"].append({
                "id": i,
                "name": class_name,
                "supercategory": "object"
            })
        
        image_id = 0
        annotation_id = 0
        
        # 处理每个图像
        for img_file in images_dir.glob("*.jpg"):
            try:
                # 添加图像信息
                img = Image.open(img_file)
                coco_data["images"].append({
                    "id": image_id,
                    "file_name": img_file.name,
                    "width": img.size[0],
                    "height": img.size[1]
                })
                
                # 处理对应的标注文件（VisDrone格式：每张图对应一个.txt文件）
                annotation_file = annotations_dir / (img_file.stem + ".txt")
                if annotation_file.exists():
                    with open(annotation_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(',')
                            if len(parts) >= 8:
                                try:
                                    # VisDrone格式: <bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,<score>,<object_category>,<truncation>,<occlusion>
                                    bbox_left = int(parts[0])
                                    bbox_top = int(parts[1])
                                    bbox_width = int(parts[2])
                                    bbox_height = int(parts[3])
                                    category_id = int(parts[5])  # VisDrone类别ID
                                    
                                    # 跳过忽略区域
                                    if category_id == 0:
                                        continue
                                    
                                    # 转换为COCO格式（COCO格式：bbox = [x, y, width, height]）
                                    coco_data["annotations"].append({
                                        "id": annotation_id,
                                        "image_id": image_id,
                                        "category_id": category_id,
                                        "bbox": [bbox_left, bbox_top, bbox_width, bbox_height],
                                        "area": bbox_width * bbox_height,
                                        "iscrowd": 0
                                    })
                                    annotation_id += 1
                                except (ValueError, IndexError) as e:
                                    print(f"  解析标注行失败: {line[:50]}... - {e}")
                                    continue
                
                image_id += 1
            except Exception as e:
                print(f"  处理图像失败 {img_file.name}: {e}")
                continue
        
        print(f"  转换完成: {len(coco_data['images'])} 张图像, {len(coco_data['annotations'])} 个标注")
        return coco_data


if __name__ == "__main__":
    processor = VisDroneProcessor()
    processor.process_dataset()
    print("\n✅ VisDrone数据预处理完成！")
```

**步骤5：运行预处理脚本（10分钟）**
```powershell
# 确保在项目根目录
python scripts\visdrone_processor.py

# 检查输出
tree /F data\processed\visdrone
```

---

#### 🌆 下午 (14:00-18:00) - 数据验证与质量检查

**步骤6：创建数据验证脚本（60分钟）**

在PowerShell中创建文件：
```powershell
New-Item -ItemType File -Path scripts\data_validation.py -Force
```

---

#### 📝 脚本2：data_validation.py

```python
"""
数据验证脚本
用于验证处理后的数据集质量和完整性
"""
import json
from pathlib import Path
import cv2
import numpy as np
from collections import Counter


class DataValidator:
    def __init__(self, data_path="data/processed/visdrone"):
        self.data_path = Path(data_path)
        self.validation_report = {}
    
    def validate_dataset(self):
        """验证整个数据集"""
        print("=" * 60)
        print("开始验证数据集...")
        print("=" * 60)
        
        for split in ["train", "val", "test"]:
            split_path = self.data_path / split
            if split_path.exists():
                print(f"\n验证 {split} 集...")
                self.validation_report[split] = self.validate_split(split_path)
            else:
                print(f"\n跳过 {split} 集（目录不存在）")
        
        # 生成验证报告
        self.generate_validation_report()
        
        return self.validation_report
    
    def validate_split(self, split_path):
        """验证特定分割的数据"""
        images_dir = split_path / "images"
        annotations_file = split_path / "annotations" / "annotations.json"
        
        validation_result = {
            "total_images": 0,
            "valid_images": 0,
            "total_annotations": 0,
            "image_issues": [],
            "annotation_issues": [],
            "class_distribution": {},
            "size_distribution": {}
        }
        
        # 验证图像
        if images_dir.exists():
            image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
            validation_result["total_images"] = len(image_files)
            
            for img_file in image_files:
                try:
                    img = cv2.imread(str(img_file))
                    if img is None:
                        validation_result["image_issues"].append(f"无法读取图像: {img_file.name}")
                    else:
                        validation_result["valid_images"] += 1
                        # 记录图像尺寸分布
                        h, w = img.shape[:2]
                        size_key = f"{w}x{h}"
                        validation_result["size_distribution"][size_key] = \
                            validation_result["size_distribution"].get(size_key, 0) + 1
                except Exception as e:
                    validation_result["image_issues"].append(f"图像处理错误: {img_file.name} - {e}")
        else:
            validation_result["image_issues"].append("图像目录不存在")
        
        # 验证标注
        if annotations_file.exists():
            try:
                with open(annotations_file, 'r', encoding='utf-8') as f:
                    coco_data = json.load(f)
                
                validation_result["total_annotations"] = len(coco_data.get("annotations", []))
                
                # 检查标注质量
                for annotation in coco_data.get("annotations", []):
                    bbox = annotation.get("bbox", [])
                    if len(bbox) != 4:
                        validation_result["annotation_issues"].append(
                            f"标注格式错误 (ID: {annotation.get('id', 'unknown')})"
                        )
                    elif bbox[2] <= 0 or bbox[3] <= 0:
                        validation_result["annotation_issues"].append(
                            f"标注尺寸错误 (ID: {annotation.get('id', 'unknown')})"
                        )
                    
                    # 统计类别分布
                    category_id = annotation.get("category_id", 0)
                    cat_str = str(category_id)
                    validation_result["class_distribution"][cat_str] = \
                        validation_result["class_distribution"].get(cat_str, 0) + 1
                
                print(f"  ✅ 图像: {validation_result['valid_images']}/{validation_result['total_images']} 有效")
                print(f"  ✅ 标注: {validation_result['total_annotations']} 个")
                if validation_result["image_issues"]:
                    print(f"  ⚠️  图像问题: {len(validation_result['image_issues'])} 个")
                if validation_result["annotation_issues"]:
                    print(f"  ⚠️  标注问题: {len(validation_result['annotation_issues'])} 个")
                
            except Exception as e:
                validation_result["annotation_issues"].append(f"读取标注文件失败: {e}")
        else:
            validation_result["annotation_issues"].append("标注文件不存在")
        
        return validation_result
    
    def generate_validation_report(self):
        """生成验证报告"""
        report_file = self.data_path / "validation_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_report, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("数据集验证摘要")
        print("=" * 60)
        
        for split, result in self.validation_report.items():
            print(f"\n{split.upper()} 集:")
            print(f"  图像数量: {result['total_images']}")
            print(f"  有效图像: {result['valid_images']}")
            print(f"  标注数量: {result['total_annotations']}")
            print(f"  图像问题: {len(result['image_issues'])}")
            print(f"  标注问题: {len(result['annotation_issues'])}")
            
            if result['class_distribution']:
                print(f"  类别分布: {dict(list(result['class_distribution'].items())[:5])}...")
        
        print(f"\n✅ 验证报告已保存: {report_file}")


if __name__ == "__main__":
    validator = DataValidator()
    validator.validate_dataset()
    print("\n✅ 数据验证完成！")
```

**步骤7：运行验证脚本（10分钟）**
```powershell
python scripts\data_validation.py

# 查看验证报告
type data\processed\visdrone\validation_report.json
```

---http://127.0.0.1:5000

**步骤8：创建数据统计分析脚本（可选，如果时间允许）**

```powershell
New-Item -ItemType File -Path scripts\dataset_stats.py -Force
```

---

### 📅 周二：DVC数据版本管理测试

#### 🌅 上午 (9:00-12:00)

**步骤1：检查DVC环境（5分钟）**
```powershell
# 检查DVC是否安装
dvc --version

# 如果未安装，则安装
pip install dvc

# 检查DVC状态
dvc status
```

**步骤2：添加数据到DVC（30分钟）**
```powershell
# 确保在项目根目录
# 如果还没有初始化DVC
dvc init

# 添加处理后数据到DVC
dvc add data\processed\visdrone

# 查看DVC文件
git status
dir data*.dvc
```

**步骤3：提交到Git（10分钟）**
```powershell
# 添加DVC文件到Git
git add data\processed\visdrone.dvc
git add .dvc\config

# 提交
git commit -m "Add processed VisDrone dataset v1.0"

# 查看DVC跟踪的数据
dvc list data\processed\visdrone
```

---

### 📅 周三：MLflow实验跟踪集成

#### 🌅 上午 (9:00-12:00)

**步骤1：创建MLflow与DVC集成脚本（30分钟）**

```powershell
New-Item -ItemType File -Path scripts\train_with_mlflow.py -Force
```

---

#### 📝 脚本3：train_with_mlflow.py

```python
"""
带MLflow跟踪的训练脚本
集成DVC数据版本和MLflow实验跟踪
"""
import mlflow
import mlflow.pytorch
from pathlib import Path
import json
from datetime import datetime


def main():
    # 设置MLflow实验
    experiment_name = "drone_vision_week4"
    mlflow.set_experiment(experiment_name)
    
    # 开始MLflow运行
    with mlflow.start_run(run_name=f"week4_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        
        # 1. 记录数据信息
        data_path = Path("data/processed/visdrone")
        mlflow.log_param("data_path", str(data_path))
        mlflow.log_param("data_version", "v1.0")
        
        # 记录数据集统计
        validation_report_path = data_path / "validation_report.json"
        if validation_report_path.exists():
            with open(validation_report_path, 'r') as f:
                validation_report = json.load(f)
            
            for split, stats in validation_report.items():
                mlflow.log_metric(f"{split}_images", stats.get("total_images", 0))
                mlflow.log_metric(f"{split}_annotations", stats.get("total_annotations", 0))
        
        # 2. 记录模型参数（示例）
        params = {
            "model": "yolov5",
            "epochs": 10,
            "batch_size": 16,
            "learning_rate": 0.001,
            "image_size": 640
        }
        
        for key, value in params.items():
            mlflow.log_param(key, value)
        
        # 3. 模拟训练过程（记录指标）
        print("开始模拟训练过程...")
        import time
        import random
        
        for epoch in range(1, params["epochs"] + 1):
            # 模拟训练指标
            train_loss = 1.0 / epoch + random.uniform(0, 0.1)
            val_loss = 1.0 / epoch + random.uniform(0.05, 0.15)
            
            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            
            print(f"Epoch {epoch}/{params['epochs']}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
            time.sleep(0.2)
        
        # 4. 记录最终指标
        final_accuracy = 0.85 + random.uniform(-0.05, 0.05)
        mlflow.log_metric("final_accuracy", final_accuracy)
        mlflow.log_metric("final_val_loss", val_loss)
        
        # 5. 保存验证报告作为artifact
        if validation_report_path.exists():
            mlflow.log_artifact(str(validation_report_path), "reports")
        
        print(f"\n✅ 训练完成！最终准确率: {final_accuracy:.4f}")
        print(f"📊 查看MLflow UI: mlflow ui")


if __name__ == "__main__":
    main()
```

**步骤2：运行训练脚本（20分钟）**
```powershell
python scripts\train_with_mlflow.py

# 启动MLflow UI查看结果
mlflow ui --port 5000

# 在浏览器打开: http://127.0.0.1:5000
```

---

### 📅 周四：完整训练流程测试

#### 🌅 上午 (9:00-12:00)

**步骤1：创建完整训练流程脚本**

整合所有组件，创建一个端到端的训练流程。

**步骤2：测试完整流程（60分钟）**
```powershell
# 1. 数据预处理
python scripts\visdrone_processor.py

# 2. 数据验证
python scripts\data_validation.py

# 3. 运行训练（带MLflow跟踪）
python scripts\train_with_mlflow.py

# 4. 查看结果
mlflow ui
```

---

### 📅 周五：文档编写与总结

#### 🌅 上午 (9:00-12:00)

**步骤1：创建工作总结文档**
```powershell
New-Item -ItemType File -Path 第4周工作总结.md -Force
```

**步骤2：运行最终测试**
```powershell
# 完整流程测试
python scripts\visdrone_processor.py
python scripts\data_validation.py
python scripts\train_with_mlflow.py

# 检查所有输出
tree /F data\processed
dir outputs
```

---

## ✅ 每日检查清单

### 周一检查
- [ ] 数据集目录结构已创建
- [ ] 预处理脚本运行成功
- [ ] 验证脚本运行成功
- [ ] 生成了验证报告

### 周二检查
- [ ] DVC已初始化
- [ ] 数据已添加到DVC
- [ ] Git提交成功

### 周三检查
- [ ] MLflow脚本运行成功
- [ ] MLflow UI可以访问
- [ ] 实验记录已保存

### 周四检查
- [ ] 完整流程测试通过
- [ ] 所有组件正常工作

### 周五检查
- [ ] 文档已编写
- [ ] 所有任务已完成

---

## 🚨 常见问题解决

### 问题1：PowerShell命令执行策略限制
```powershell
# 如果遇到"无法加载文件，因为在此系统上禁止运行脚本"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题2：找不到conda环境
```powershell
# 查找conda安装路径
where.exe conda

# 手动激活环境
C:\Users\你的用户名\.conda\envs\drone_vision_clean\python.exe
```

### 问题3：模块导入错误
```powershell
# 安装缺失的包
pip install 包名

# 检查已安装的包
pip list
```

### 问题4：路径问题
```powershell
# 使用绝对路径
cd D:\mlflow_learning_project

# 或使用相对路径（确保在正确目录）
pwd  # 查看当前目录
```

---

## 📊 预期输出

完成第4周任务后，你应该有：

1. **数据结构**：
   ```
   data/
   ├── processed/
   │   └── visdrone/
   │       ├── train/
   │       │   ├── images/
   │       │   └── annotations/
   │       └── validation_report.json
   ```

2. **脚本文件**：
   - `scripts/visdrone_processor.py`
   - `scripts/data_validation.py`
   - `scripts/train_with_mlflow.py`

3. **MLflow实验结果**：
   - 实验记录在 `mlruns/` 目录
   - 可以通过 `mlflow ui` 查看

---

## 🎯 成功标准

- ✅ 数据集预处理完成，输出到 `data/processed/visdrone`
- ✅ 数据验证通过，生成了验证报告
- ✅ MLflow实验成功运行，记录了训练过程
- ✅ 所有脚本可以独立运行
- ✅ 文档完整，可以复现整个流程

---

**祝你第4周工作顺利！** 🚀

