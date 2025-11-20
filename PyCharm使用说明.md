# 无人机视觉MLflow实验 - PyCharm使用说明

## 📋 项目概述

本项目是一个完整的无人机视觉机器学习实验平台，集成了MLflow实验跟踪、深度学习模型训练、Web UI界面和可视化功能。项目适用于无人机视觉算法开发与训练实习。

## 🚀 快速开始

### 1. 环境准备

#### 1.1 安装Python环境
- 确保已安装Python 3.8或更高版本
- 推荐使用Anaconda或Miniconda管理Python环境

#### 1.2 创建虚拟环境
```bash
# 使用conda创建环境
conda create -n drone_vision python=3.9
conda activate drone_vision

# 或使用venv创建环境
python -m venv drone_vision_env
# Windows激活
drone_vision_env\Scripts\activate
# Linux/Mac激活
source drone_vision_env/bin/activate
```

### 2. PyCharm项目配置

#### 2.1 打开项目
1. 启动PyCharm
2. 选择 `File` → `Open`
3. 选择项目根目录 `D:\mlflow_learning_project`
4. 点击 `OK`

#### 2.2 配置Python解释器
1. 打开 `File` → `Settings` (或 `Ctrl+Alt+S`)
2. 导航到 `Project: mlflow_learning_project` → `Python Interpreter`
3. 点击齿轮图标 → `Add`
4. 选择 `Conda Environment` → `Existing environment`
5. 选择之前创建的 `drone_vision` 环境
6. 点击 `OK`

#### 2.3 安装依赖包
在PyCharm终端中运行：
```bash
pip install -r requirements.txt
```

### 3. 项目结构说明

```
mlflow_learning_project/
├── main.py                 # 主实验程序
├── streamlit_app.py        # Web UI界面
├── requirements.txt        # 依赖包列表
├── PyCharm使用说明.md      # 本说明文档
└── README.md              # 项目说明
```

## 🔧 详细使用步骤

### 步骤1: 运行基础实验

#### 1.1 直接运行主程序
1. 在PyCharm中打开 `main.py`
2. 右键点击文件 → `Run 'main'`
3. 或在终端中运行：
```bash
python main.py
```

#### 1.2 查看实验结果
- 实验完成后会显示训练过程
- 生成可视化图表 `drone_vision_analysis.png`
- MLflow实验记录自动保存

### 步骤2: 启动Web UI界面

#### 2.1 启动Streamlit应用
1. 在PyCharm终端中运行：
```bash
streamlit run streamlit_app.py
```

2. 浏览器会自动打开 `http://localhost:8501`

#### 2.2 使用Web界面功能
- **运行新实验**: 设置参数并开始训练
- **查看历史实验**: 分析之前的实验结果
- **模型对比分析**: 比较不同模型性能

### 步骤3: 使用MLflow UI

#### 3.1 启动MLflow服务器
```bash
mlflow ui
```

#### 3.2 访问MLflow界面
- 打开浏览器访问 `http://localhost:5000`
- 查看实验记录、参数、指标和模型

### 步骤4: 自定义实验

#### 4.1 修改实验参数
在 `main.py` 中修改以下参数：
```python
# 数据参数
num_samples = 1000  # 样本数量
image_size = (64, 64)  # 图像尺寸

# 训练参数
num_epochs = 10  # 训练轮数
learning_rate = 0.001  # 学习率
batch_size = 32  # 批次大小
```

#### 4.2 修改模型架构
在 `DroneVisionCNN` 类中自定义网络结构：
```python
class DroneVisionCNN(nn.Module):
    def __init__(self, num_classes=5):
        # 修改网络层
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3)  # 增加通道数
        # 添加更多层...
```

#### 4.3 添加新的数据增强
在 `prepare_data` 方法中修改数据变换：
```python
transform_train = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((64, 64)),
    transforms.RandomHorizontalFlip(0.5),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),  # 添加颜色变换
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
```

## 🛠️ 高级功能

### 1. 实验跟踪和版本控制

#### 1.1 使用MLflow记录实验
```python
with mlflow.start_run():
    # 记录参数
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("num_epochs", 10)
    
    # 记录指标
    mlflow.log_metric("accuracy", 0.85)
    mlflow.log_metric("loss", 0.15)
    
    # 保存模型
    mlflow.pytorch.log_model(model, "model")
```

#### 1.2 实验对比
在MLflow UI中可以：
- 比较不同实验的参数和结果
- 查看训练曲线
- 下载最佳模型

### 2. 模型优化

#### 2.1 超参数调优
```python
import optuna

def objective(trial):
    lr = trial.suggest_float('learning_rate', 1e-5, 1e-1, log=True)
    batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
    
    # 训练模型
    accuracy = train_model(lr, batch_size)
    return accuracy

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=20)
```

#### 2.2 模型集成
```python
# 创建多个模型
models = [DroneVisionCNN() for _ in range(5)]

# 集成预测
def ensemble_predict(models, x):
    predictions = []
    for model in models:
        pred = model(x)
        predictions.append(pred)
    return torch.mean(torch.stack(predictions), dim=0)
```

### 3. 数据管理

#### 3.1 真实数据加载
```python
def load_real_data(data_path):
    """加载真实无人机数据"""
    images = []
    labels = []
    
    for class_name in os.listdir(data_path):
        class_path = os.path.join(data_path, class_name)
        for img_file in os.listdir(class_path):
            img_path = os.path.join(class_path, img_file)
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            images.append(img)
            labels.append(class_name)
    
    return images, labels
```

#### 3.2 数据预处理管道
```python
class DataPreprocessor:
    def __init__(self):
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def preprocess(self, image):
        return self.transform(image)
```

## 📊 可视化和分析

### 1. 训练过程可视化
```python
def plot_training_history(history):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 损失曲线
    axes[0, 0].plot(history['train_losses'], label='训练损失')
    axes[0, 0].plot(history['val_losses'], label='验证损失')
    axes[0, 0].set_title('模型损失')
    axes[0, 0].legend()
    
    # 准确率曲线
    axes[0, 1].plot(history['train_accuracies'], label='训练准确率')
    axes[0, 1].plot(history['val_accuracies'], label='验证准确率')
    axes[0, 1].set_title('模型准确率')
    axes[0, 1].legend()
    
    plt.tight_layout()
    plt.show()
```

### 2. 模型性能分析
```python
def analyze_model_performance(model, test_loader):
    model.eval()
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for data, target in test_loader:
            output = model(data)
            _, predicted = torch.max(output, 1)
            all_predictions.extend(predicted.cpu().numpy())
            all_targets.extend(target.cpu().numpy())
    
    # 生成分类报告
    report = classification_report(all_targets, all_predictions)
    print(report)
    
    # 绘制混淆矩阵
    cm = confusion_matrix(all_targets, all_predictions)
    sns.heatmap(cm, annot=True, fmt='d')
    plt.title('混淆矩阵')
    plt.show()
```

## 🐛 常见问题和解决方案

### 问题1: 内存不足
**解决方案:**
```python
# 减少批次大小
batch_size = 16  # 从32减少到16

# 使用梯度累积
accumulation_steps = 2
for i, (data, target) in enumerate(train_loader):
    output = model(data)
    loss = criterion(output, target) / accumulation_steps
    loss.backward()
    
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### 问题2: 训练速度慢
**解决方案:**
```python
# 使用GPU加速
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    output = model(data)
    loss = criterion(output, target)
```

### 问题3: 过拟合
**解决方案:**
```python
# 增加正则化
model = nn.Sequential(
    nn.Conv2d(3, 32, 3),
    nn.BatchNorm2d(32),
    nn.ReLU(),
    nn.Dropout(0.5),  # 增加Dropout
    # ... 更多层
)

# 使用数据增强
transform_train = transforms.Compose([
    transforms.RandomHorizontalFlip(0.5),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
])
```

## 📈 性能优化建议

### 1. 数据加载优化
```python
# 使用多进程数据加载
train_loader = DataLoader(
    dataset, 
    batch_size=32, 
    shuffle=True, 
    num_workers=4,  # 使用4个进程
    pin_memory=True  # 固定内存
)
```

### 2. 模型优化
```python
# 使用预训练模型
import torchvision.models as models
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, num_classes)

# 冻结早期层
for param in model.parameters():
    param.requires_grad = False
for param in model.fc.parameters():
    param.requires_grad = True
```

### 3. 训练策略
```python
# 使用学习率调度器
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5
)

# 早停机制
class EarlyStopping:
    def __init__(self, patience=7, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
    
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
        
        return self.counter >= self.patience
```

## 🔗 相关资源

### 学习资源
- [PyTorch官方文档](https://pytorch.org/docs/)
- [MLflow官方文档](https://mlflow.org/docs/)
- [Streamlit官方文档](https://docs.streamlit.io/)

### 数据集资源
- [COCO数据集](https://cocodataset.org/)
- [ImageNet数据集](https://www.image-net.org/)
- [无人机数据集](https://www.kaggle.com/datasets)

### 模型资源
- [PyTorch模型库](https://pytorch.org/vision/stable/models.html)
- [Hugging Face模型库](https://huggingface.co/models)

## 📞 技术支持

如果在使用过程中遇到问题，可以：

1. 查看PyCharm控制台输出的错误信息
2. 检查MLflow UI中的实验记录
3. 查看生成的日志文件
4. 参考本文档的常见问题部分

## 🎯 下一步计划

1. **数据增强**: 实现更多数据增强技术
2. **模型集成**: 实现多模型集成
3. **实时推理**: 添加实时图像分类功能
4. **模型部署**: 使用FastAPI部署模型服务
5. **移动端应用**: 开发移动端无人机视觉应用

---

**祝您实验顺利！** 🚁✨
