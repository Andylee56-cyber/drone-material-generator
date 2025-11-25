"""
优化版本的Streamlit应用示例
展示如何添加缓存和优化性能
"""

import streamlit as st
import torch
import torch.nn as nn
import gc
from PIL import Image
import numpy as np
from main import DroneVisionCNN, DroneVisionExperiment

# ========== 性能优化设置 ==========

# 限制CPU线程，避免过载
if not torch.cuda.is_available():
    torch.set_num_threads(1)
    torch.set_grad_enabled(False)  # 推理时不需要梯度

# 设置页面配置
st.set_page_config(
    page_title="无人机素材生成系统（优化版）",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 模型缓存（关键优化） ==========

@st.cache_resource  # 这个装饰器确保模型只加载一次
def load_model():
    """加载模型，只执行一次，后续请求复用"""
    st.info("🔄 首次加载模型，请稍候...")
    
    # 创建模型
    model = DroneVisionCNN(num_classes=5)
    
    # 如果有预训练权重，加载它
    # model.load_state_dict(torch.load('model.pth', map_location='cpu'))
    
    # 设置为评估模式（推理模式）
    model.eval()
    
    # 清理内存
    gc.collect()
    
    return model

# ========== 数据预处理缓存 ==========

@st.cache_data(max_entries=20)  # 缓存最近20张图片的预处理结果
def preprocess_image(image, target_size=(64, 64)):
    """预处理图片，带缓存"""
    # 你的图片预处理代码
    if isinstance(image, Image.Image):
        image = image.resize(target_size)
        image_array = np.array(image)
    else:
        image_array = image
    
    # 转换为tensor
    # tensor = torch.from_numpy(image_array).float()
    return image_array

# ========== 推理函数（带缓存） ==========

@st.cache_data(max_entries=10)  # 缓存最近10次推理结果
def predict_image(model, image_tensor):
    """预测图片，相同输入直接返回缓存结果"""
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.softmax(output, dim=1)
        return probabilities.cpu().numpy()

# ========== 主界面 ==========

def main():
    st.title("🚁 无人机素材生成系统")
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("系统配置")
        
        auto_analyze = st.checkbox("生成后自动分析", value=True)
        
        st.header("增强训练设置")
        enable_training = st.checkbox("启用自动增强训练", value=False)
        
        if enable_training:
            target_score = st.slider("目标提升分数", 1, 10, 5)
            max_iterations = st.slider("最大迭代次数", 1, 20, 10)
    
    # 主内容区
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("上传图片")
        uploaded_file = st.file_uploader(
            "选择图片文件",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="支持JPG、PNG、BMP格式，最大200MB"
        )
        
        if uploaded_file is not None:
            # 显示原始图片
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的原始图片", use_container_width=True)
            
            # 加载模型（只加载一次）
            if 'model' not in st.session_state:
                with st.spinner("正在加载模型..."):
                    st.session_state.model = load_model()
            
            # 生成按钮
            if st.button("生成多角度素材并分析", type="primary"):
                with st.spinner("正在生成多角度素材,请稍候..."):
                    # 预处理图片
                    processed_image = preprocess_image(image)
                    
                    # 这里添加你的生成逻辑
                    # ...
                    
                    st.success("✅ 生成完成！")
                    
                    # 如果启用自动分析
                    if auto_analyze:
                        with st.spinner("步骤2/2: 正在分析生成的素材..."):
                            # 使用缓存的模型进行推理
                            # predictions = predict_image(st.session_state.model, image_tensor)
                            # ...
                            
                            st.success("✅ 分析完成！")
                            
                            # 显示结果
                            st.header("分析结果")
                            # 显示你的分析结果
                            
                            # 清理内存
                            gc.collect()
    
    with col2:
        st.header("系统状态")
        st.info("✅ 系统运行正常")
        st.info(f"📊 模型已加载: {'是' if 'model' in st.session_state else '否'}")
        
        # 显示内存使用（如果可能）
        try:
            import psutil
            memory = psutil.virtual_memory()
            st.metric("内存使用", f"{memory.percent}%")
        except:
            pass

# ========== 清理函数 ==========

def clear_cache():
    """清理缓存"""
    st.cache_resource.clear()
    st.cache_data.clear()
    gc.collect()
    st.success("✅ 缓存已清理")

# 运行主函数
if __name__ == "__main__":
    main()
    
    # 在侧边栏添加清理按钮（调试用）
    with st.sidebar:
        if st.button("清理缓存（调试用）"):
            clear_cache()

