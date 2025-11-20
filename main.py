"""
无人机视觉MLflow实验主程序
Drone Vision MLflow Experiment
作者: 无人机视觉算法实习生
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import mlflow
import mlflow.pytorch
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class DroneDataset(Dataset):
    """无人机数据集类"""
    def __init__(self, images, labels, transform=None):
        self.images = images
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image = self.images[idx]
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

class DroneVisionCNN(nn.Module):
    """无人机视觉CNN模型"""
    def __init__(self, num_classes=5):
        super(DroneVisionCNN, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        
        # 批归一化
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        self.bn4 = nn.BatchNorm2d(256)
        
        # 池化层
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.5)
        
        # 全连接层
        self.fc1 = nn.Linear(256 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, num_classes)
        
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # 卷积层1
        x = self.pool(self.relu(self.bn1(self.conv1(x))))
        
        # 卷积层2
        x = self.pool(self.relu(self.bn2(self.conv2(x))))
        
        # 卷积层3
        x = self.pool(self.relu(self.bn3(self.conv3(x))))
        
        # 卷积层4
        x = self.pool(self.relu(self.bn4(self.conv4(x))))
        
        # 展平
        x = x.view(x.size(0), -1)
        
        # 全连接层
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        
        return x

class DroneVisionExperiment:
    """无人机视觉MLflow实验类"""
    
    def __init__(self, experiment_name="无人机视觉实验"):
        self.experiment_name = experiment_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.test_loader = None
        
        # 设置MLflow实验
        mlflow.set_experiment(experiment_name)
        
    def generate_synthetic_data(self, num_samples=1000, image_size=(64, 64)):
        """生成合成无人机数据"""
        print("正在生成合成无人机数据...")
        
        images = []
        labels = []
        class_names = ['建筑物', '道路', '植被', '水体', '车辆']
        
        for i in range(num_samples):
            # 生成随机图像
            if i % 5 == 0:  # 建筑物
                img = np.random.randint(50, 150, (image_size[0], image_size[1], 3), dtype=np.uint8)
                # 添加建筑物特征
                img[20:40, 10:30] = [100, 100, 100]  # 灰色建筑
                label = 0
            elif i % 5 == 1:  # 道路
                img = np.random.randint(80, 120, (image_size[0], image_size[1], 3), dtype=np.uint8)
                # 添加道路特征
                img[30:34, :] = [60, 60, 60]  # 灰色道路
                label = 1
            elif i % 5 == 2:  # 植被
                img = np.random.randint(0, 100, (image_size[0], image_size[1], 3), dtype=np.uint8)
                img[:, :, 1] = np.random.randint(100, 255, (image_size[0], image_size[1]))  # 绿色
                label = 2
            elif i % 5 == 3:  # 水体
                img = np.random.randint(0, 50, (image_size[0], image_size[1], 3), dtype=np.uint8)
                img[:, :, 2] = np.random.randint(100, 255, (image_size[0], image_size[1]))  # 蓝色
                label = 3
            else:  # 车辆
                img = np.random.randint(100, 200, (image_size[0], image_size[1], 3), dtype=np.uint8)
                # 添加车辆特征
                img[25:35, 20:40] = [200, 0, 0]  # 红色车辆
                label = 4
            
            images.append(img)
            labels.append(label)
        
        return np.array(images), np.array(labels), class_names
    
    def prepare_data(self, images, labels, test_size=0.2, val_size=0.2):
        """准备训练、验证和测试数据"""
        print("正在准备数据集...")
        
        # 分割数据
        X_temp, X_test, y_temp, y_test = train_test_split(
            images, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size/(1-test_size), random_state=42, stratify=y_temp
        )
        
        # 数据变换
        transform_train = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((64, 64)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        transform_val = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 创建数据集
        train_dataset = DroneDataset(X_train, y_train, transform_train)
        val_dataset = DroneDataset(X_val, y_val, transform_val)
        test_dataset = DroneDataset(X_test, y_test, transform_val)
        
        # 创建数据加载器
        self.train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        self.val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
        self.test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
        
        print(f"训练集大小: {len(train_dataset)}")
        print(f"验证集大小: {len(val_dataset)}")
        print(f"测试集大小: {len(test_dataset)}")
        
        return train_dataset, val_dataset, test_dataset
    
    def train_model(self, num_epochs=10, learning_rate=0.001):
        """训练模型"""
        print("开始训练模型...")
        
        # 创建模型
        self.model = DroneVisionCNN(num_classes=5).to(self.device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
        
        # 训练历史
        train_losses = []
        val_losses = []
        train_accuracies = []
        val_accuracies = []
        
        with mlflow.start_run():
            # 记录参数
            mlflow.log_param("num_epochs", num_epochs)
            mlflow.log_param("learning_rate", learning_rate)
            mlflow.log_param("batch_size", 32)
            mlflow.log_param("model_architecture", "CNN")
            
            for epoch in range(num_epochs):
                # 训练阶段
                self.model.train()
                train_loss = 0.0
                train_correct = 0
                train_total = 0
                
                for batch_idx, (data, target) in enumerate(self.train_loader):
                    data, target = data.to(self.device), target.to(self.device)
                    
                    optimizer.zero_grad()
                    output = self.model(data)
                    loss = criterion(output, target)
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                    _, predicted = torch.max(output.data, 1)
                    train_total += target.size(0)
                    train_correct += (predicted == target).sum().item()
                
                # 验证阶段
                self.model.eval()
                val_loss = 0.0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for data, target in self.val_loader:
                        data, target = data.to(self.device), target.to(self.device)
                        output = self.model(data)
                        loss = criterion(output, target)
                        
                        val_loss += loss.item()
                        _, predicted = torch.max(output.data, 1)
                        val_total += target.size(0)
                        val_correct += (predicted == target).sum().item()
                
                # 计算准确率
                train_acc = 100. * train_correct / train_total
                val_acc = 100. * val_correct / val_total
                
                train_losses.append(train_loss / len(self.train_loader))
                val_losses.append(val_loss / len(self.val_loader))
                train_accuracies.append(train_acc)
                val_accuracies.append(val_acc)
                
                print(f'Epoch {epoch+1}/{num_epochs}:')
                print(f'  训练损失: {train_loss/len(self.train_loader):.4f}, 训练准确率: {train_acc:.2f}%')
                print(f'  验证损失: {val_loss/len(self.val_loader):.4f}, 验证准确率: {val_acc:.2f}%')
                
                # 记录到MLflow
                mlflow.log_metric("train_loss", train_loss/len(self.train_loader), step=epoch)
                mlflow.log_metric("val_loss", val_loss/len(self.val_loader), step=epoch)
                mlflow.log_metric("train_accuracy", train_acc, step=epoch)
                mlflow.log_metric("val_accuracy", val_acc, step=epoch)
                
                scheduler.step()
            
            # 测试模型
            test_accuracy, _, _ = self.evaluate_model()
            
            # 记录最终指标
            mlflow.log_metric("final_test_accuracy", test_accuracy)
            mlflow.log_metric("final_train_accuracy", train_accuracies[-1])
            mlflow.log_metric("final_val_accuracy", val_accuracies[-1])
            
            # 保存模型
            mlflow.pytorch.log_model(self.model, "model")
            
            # 保存训练历史
            history = {
                'train_losses': train_losses,
                'val_losses': val_losses,
                'train_accuracies': train_accuracies,
                'val_accuracies': val_accuracies
            }
            
            return history, test_accuracy
    
    def evaluate_model(self):
        """评估模型"""
        print("正在评估模型...")
        
        self.model.eval()
        correct = 0
        total = 0
        all_predictions = []
        all_targets = []
        
        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
                
                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend(target.cpu().numpy())
        
        accuracy = 100. * correct / total
        print(f'测试准确率: {accuracy:.2f}%')
        
        return accuracy, all_predictions, all_targets
    
    def create_visualizations(self, history, class_names):
        """创建可视化图表"""
        print("正在创建可视化图表...")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 训练和验证损失
        axes[0, 0].plot(history['train_losses'], label='训练损失', color='blue')
        axes[0, 0].plot(history['val_losses'], label='验证损失', color='red')
        axes[0, 0].set_title('模型损失')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('损失')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 训练和验证准确率
        axes[0, 1].plot(history['train_accuracies'], label='训练准确率', color='blue')
        axes[0, 1].plot(history['val_accuracies'], label='验证准确率', color='red')
        axes[0, 1].set_title('模型准确率')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('准确率 (%)')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # 类别分布
        class_counts = [200, 200, 200, 200, 200]  # 假设每个类别200个样本
        axes[1, 0].bar(class_names, class_counts, color=['skyblue', 'lightgreen', 'lightcoral', 'lightblue', 'orange'])
        axes[1, 0].set_title('数据集类别分布')
        axes[1, 0].set_ylabel('样本数量')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 模型架构可视化
        axes[1, 1].text(0.5, 0.5, 'CNN架构:\n\nConv2d(3→32)\nConv2d(32→64)\nConv2d(64→128)\nConv2d(128→256)\n\nFC(256→512)\nFC(512→256)\nFC(256→5)', 
                       ha='center', va='center', fontsize=12, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        axes[1, 1].set_title('模型架构')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig('drone_vision_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return fig

def main():
    """主函数"""
    print("=" * 50)
    print("无人机视觉MLflow实验")
    print("=" * 50)
    
    # 创建实验
    experiment = DroneVisionExperiment("无人机视觉实验")
    
    # 生成数据
    images, labels, class_names = experiment.generate_synthetic_data(num_samples=1000)
    print(f"生成了 {len(images)} 个样本，包含 {len(class_names)} 个类别")
    
    # 准备数据
    train_dataset, val_dataset, test_dataset = experiment.prepare_data(images, labels)
    
    # 训练模型
    history, test_accuracy = experiment.train_model(num_epochs=10, learning_rate=0.001)
    
    # 评估模型
    accuracy, predictions, targets = experiment.evaluate_model()
    
    # 创建可视化
    fig = experiment.create_visualizations(history, class_names)
    
    print("\n实验完成！")
    print(f"最终测试准确率: {test_accuracy:.2f}%")
    print("可视化图表已保存为 'drone_vision_analysis.png'")
    print("MLflow实验记录已保存，可通过MLflow UI查看")

if __name__ == "__main__":
    main()

