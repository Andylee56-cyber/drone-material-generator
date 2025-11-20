"""
快速测试实验 - 生成MLflow数据
Quick Test Experiment - Generate MLflow Data
"""
import os
import sys
from main import DroneVisionExperiment

def main():
    print("=" * 60)
    print("🚀 快速测试实验 - 生成MLflow数据")
    print("=" * 60)
    
    # 确保在项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"📁 工作目录: {os.getcwd()}")
    
    # 创建实验（使用少量数据快速测试）
    print("\n📊 创建实验...")
    experiment = DroneVisionExperiment("无人机视觉实验")
    
    # 生成少量数据（快速测试）
    print("\n🔄 生成测试数据（100个样本）...")
    images, labels, class_names = experiment.generate_synthetic_data(num_samples=100)
    print(f"✅ 生成了 {len(images)} 个样本，包含 {len(class_names)} 个类别")
    
    # 准备数据
    print("\n📦 准备数据集...")
    train_dataset, val_dataset, test_dataset = experiment.prepare_data(images, labels)
    
    # 训练模型（少量epoch快速测试）
    print("\n🎯 开始训练（3个epoch，快速测试）...")
    history, test_accuracy = experiment.train_model(num_epochs=3, learning_rate=0.001)
    
    print("\n" + "=" * 60)
    print("✅ 实验完成！")
    print(f"📊 最终测试准确率: {test_accuracy:.2f}%")
    print(f"📁 MLflow数据保存在: {os.path.join(os.getcwd(), 'mlruns')}")
    print("\n💡 现在可以在MLflow UI中查看实验数据了！")
    print("   MLflow UI: http://localhost:5000")
    print("=" * 60)

if __name__ == "__main__":
    main()





