"""
无人机视觉MLflow实验 - Streamlit Web UI
Drone Vision MLflow Experiment - Streamlit Web Interface
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import torch
import mlflow
import mlflow.pytorch
from mlflow.tracking import MlflowClient
import json
from datetime import datetime
import os
import sys

# 导入主程序模块
from main import DroneVisionExperiment, DroneVisionCNN

# 设置页面配置
st.set_page_config(
    page_title="无人机视觉MLflow实验",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_mlflow_data():
    """加载MLflow实验数据"""
    try:
        client = MlflowClient()
        experiments = client.search_experiments()
        
        experiment_data = []
        for exp in experiments:
            runs = client.search_runs([exp.experiment_id])
            for run in runs:
                experiment_data.append({
                    'experiment_id': exp.experiment_id,
                    'experiment_name': exp.name,
                    'run_id': run.info.run_id,
                    'status': run.info.status,
                    'start_time': run.info.start_time,
                    'end_time': run.info.end_time,
                    'metrics': run.data.metrics,
                    'params': run.data.params
                })
        
        return experiment_data
    except Exception as e:
        st.error(f"加载MLflow数据时出错: {str(e)}")
        return []

def create_metrics_plot(experiment_data):
    """创建指标图表"""
    if not experiment_data:
        return None
    
    # 提取训练和验证准确率
    train_accs = []
    val_accs = []
    epochs = []
    
    for run in experiment_data:
        metrics = run.get('metrics', {})
        if 'final_train_accuracy' in metrics and 'final_val_accuracy' in metrics:
            train_accs.append(metrics['final_train_accuracy'])
            val_accs.append(metrics['final_val_accuracy'])
            epochs.append(len([k for k in metrics.keys() if 'train_accuracy' in k and k != 'final_train_accuracy']))
    
    if not train_accs:
        return None
    
    # 创建图表
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('训练vs验证准确率', '训练vs验证损失', '实验对比', '模型性能分布'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 准确率对比
    fig.add_trace(
        go.Scatter(x=epochs, y=train_accs, mode='lines+markers', name='训练准确率', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=epochs, y=val_accs, mode='lines+markers', name='验证准确率', line=dict(color='red')),
        row=1, col=1
    )
    
    # 实验对比
    fig.add_trace(
        go.Bar(x=[f"实验{i+1}" for i in range(len(train_accs))], y=train_accs, name='训练准确率', marker_color='lightblue'),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=[f"实验{i+1}" for i in range(len(val_accs))], y=val_accs, name='验证准确率', marker_color='lightcoral'),
        row=2, col=1
    )
    
    # 性能分布
    fig.add_trace(
        go.Histogram(x=train_accs, name='训练准确率分布', marker_color='blue', opacity=0.7),
        row=2, col=2
    )
    fig.add_trace(
        go.Histogram(x=val_accs, name='验证准确率分布', marker_color='red', opacity=0.7),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=True, title_text="无人机视觉实验分析")
    return fig

def create_confusion_matrix_plot():
    """创建混淆矩阵"""
    # 模拟混淆矩阵数据
    class_names = ['建筑物', '道路', '植被', '水体', '车辆']
    confusion_data = np.array([
        [85, 5, 3, 2, 5],
        [3, 90, 2, 1, 4],
        [2, 1, 88, 4, 5],
        [1, 2, 3, 89, 5],
        [4, 3, 2, 1, 90]
    ])
    
    fig = px.imshow(
        confusion_data,
        labels=dict(x="预测类别", y="真实类别", color="样本数量"),
        x=class_names,
        y=class_names,
        color_continuous_scale='Blues',
        title="混淆矩阵"
    )
    
    # 添加数值标注
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            fig.add_annotation(
                x=j, y=i,
                text=str(confusion_data[i, j]),
                showarrow=False,
                font=dict(color="white" if confusion_data[i, j] > 50 else "black")
            )
    
    return fig

def create_class_distribution_plot():
    """创建类别分布图"""
    class_names = ['建筑物', '道路', '植被', '水体', '车辆']
    train_counts = [200, 200, 200, 200, 200]
    test_counts = [50, 50, 50, 50, 50]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='训练集',
        x=class_names,
        y=train_counts,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='测试集',
        x=class_names,
        y=test_counts,
        marker_color='lightcoral'
    ))
    
    fig.update_layout(
        title='数据集类别分布',
        xaxis_title='类别',
        yaxis_title='样本数量',
        barmode='group'
    )
    
    return fig

def main():
    """主函数"""
    st.title("🚁 无人机视觉MLflow实验平台")
    st.markdown("---")
    
    # 侧边栏
    st.sidebar.title("实验控制面板")
    
    # 实验选择
    experiment_option = st.sidebar.selectbox(
        "选择实验类型",
        ["运行新实验", "查看历史实验", "模型对比分析"]
    )
    
    if experiment_option == "运行新实验":
        st.header("🔄 运行新的无人机视觉实验")
        
        # 实验参数设置
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("实验参数")
            num_samples = st.slider("样本数量", 100, 2000, 1000)
            num_epochs = st.slider("训练轮数", 5, 50, 10)
            learning_rate = st.slider("学习率", 0.0001, 0.01, 0.001, format="%.4f")
            batch_size = st.selectbox("批次大小", [16, 32, 64, 128])
        
        with col2:
            st.subheader("模型配置")
            model_architecture = st.selectbox("模型架构", ["CNN", "ResNet", "VGG"])
            optimizer = st.selectbox("优化器", ["Adam", "SGD", "RMSprop"])
            activation = st.selectbox("激活函数", ["ReLU", "LeakyReLU", "ELU"])
        
        # 运行实验按钮
        if st.button("🚀 开始实验", type="primary"):
            with st.spinner("正在运行实验..."):
                try:
                    # 创建实验
                    experiment = DroneVisionExperiment("无人机视觉实验")
                    
                    # 生成数据
                    images, labels, class_names = experiment.generate_synthetic_data(num_samples)
                    
                    # 准备数据
                    train_dataset, val_dataset, test_dataset = experiment.prepare_data(images, labels)
                    
                    # 训练模型
                    history, test_accuracy = experiment.train_model(num_epochs, learning_rate)
                    
                    # 显示结果
                    st.success(f"✅ 实验完成！测试准确率: {test_accuracy:.2f}%")
                    
                    # 显示训练历史
                    st.subheader("📊 训练历史")
                    
                    # 创建训练历史图表
                    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
                    
                    # 损失曲线
                    axes[0].plot(history['train_losses'], label='训练损失', color='blue')
                    axes[0].plot(history['val_losses'], label='验证损失', color='red')
                    axes[0].set_title('模型损失')
                    axes[0].set_xlabel('Epoch')
                    axes[0].set_ylabel('损失')
                    axes[0].legend()
                    axes[0].grid(True)
                    
                    # 准确率曲线
                    axes[1].plot(history['train_accuracies'], label='训练准确率', color='blue')
                    axes[1].plot(history['val_accuracies'], label='验证准确率', color='red')
                    axes[1].set_title('模型准确率')
                    axes[1].set_xlabel('Epoch')
                    axes[1].set_ylabel('准确率 (%)')
                    axes[1].legend()
                    axes[1].grid(True)
                    
                    st.pyplot(fig)
                    
                except Exception as e:
                    st.error(f"实验运行失败: {str(e)}")
    
    elif experiment_option == "查看历史实验":
        st.header("📈 历史实验分析")
        
        # 加载MLflow数据
        experiment_data = load_mlflow_data()
        
        if experiment_data:
            st.subheader("实验概览")
            
            # 创建实验概览表格
            df = pd.DataFrame(experiment_data)
            st.dataframe(df[['experiment_name', 'status', 'start_time', 'end_time']].head(10))
            
            # 显示指标图表
            st.subheader("实验指标分析")
            metrics_plot = create_metrics_plot(experiment_data)
            if metrics_plot:
                st.plotly_chart(metrics_plot, use_container_width=True)
            
            # 显示混淆矩阵
            st.subheader("模型性能分析")
            col1, col2 = st.columns(2)
            
            with col1:
                confusion_fig = create_confusion_matrix_plot()
                st.plotly_chart(confusion_fig, use_container_width=True)
            
            with col2:
                distribution_fig = create_class_distribution_plot()
                st.plotly_chart(distribution_fig, use_container_width=True)
        
        else:
            st.warning("没有找到历史实验数据。请先运行一些实验。")
    
    elif experiment_option == "模型对比分析":
        st.header("🔍 模型对比分析")
        
        st.subheader("不同模型架构对比")
        
        # 模拟不同模型的性能数据
        models = ['CNN', 'ResNet18', 'VGG16', 'EfficientNet']
        train_accs = [85.2, 88.7, 87.1, 90.3]
        val_accs = [82.1, 85.4, 83.8, 87.6]
        test_accs = [81.5, 84.2, 82.9, 86.8]
        
        # 创建对比图表
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='训练准确率',
            x=models,
            y=train_accs,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='验证准确率',
            x=models,
            y=val_accs,
            marker_color='lightgreen'
        ))
        
        fig.add_trace(go.Bar(
            name='测试准确率',
            x=models,
            y=test_accs,
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title='不同模型架构性能对比',
            xaxis_title='模型架构',
            yaxis_title='准确率 (%)',
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 模型推荐
        st.subheader("🎯 模型推荐")
        best_model_idx = np.argmax(test_accs)
        st.success(f"推荐使用: **{models[best_model_idx]}** (测试准确率: {test_accs[best_model_idx]:.1f}%)")
        
        # 性能分析
        st.subheader("📊 性能分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("最佳训练准确率", f"{max(train_accs):.1f}%")
            st.metric("最佳验证准确率", f"{max(val_accs):.1f}%")
        
        with col2:
            st.metric("最佳测试准确率", f"{max(test_accs):.1f}%")
            st.metric("平均准确率", f"{np.mean(test_accs):.1f}%")
    
    # 底部信息
    st.markdown("---")
    st.markdown("### 📝 实验说明")
    st.info("""
    本平台支持以下功能：
    - 🚀 运行新的无人机视觉实验
    - 📈 查看和分析历史实验
    - 🔍 对比不同模型架构
    - 📊 可视化实验结果
    - 🎯 模型性能评估
    """)
    
    st.markdown("### 🔗 相关链接")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("[MLflow UI](http://localhost:5000)")
    
    with col2:
        st.markdown("[项目文档](./README.md)")
    
    with col3:
        st.markdown("[GitHub仓库](https://github.com/your-repo)")

if __name__ == "__main__":
    main()
