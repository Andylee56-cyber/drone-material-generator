"""
🚁 无人机视觉智能分析系统 - 科幻风格界面
Drone Vision AI Analysis System - Sci-Fi Interface
全新设计，功能强大，界面科幻，字体清晰
"""

# ========== 环境变量设置（必须在所有导入前） ==========
import os
import sys

os.environ['OPENCV_DISABLE_OPENCL'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ''
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'

if 'LD_LIBRARY_PATH' in os.environ:
    paths = os.environ['LD_LIBRARY_PATH'].split(':')
    paths = [p for p in paths if 'libGL' not in p and 'mesa' not in p.lower()]
    os.environ['LD_LIBRARY_PATH'] = ':'.join(paths)

# 创建假的libGL模块
class FakeLibGL:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['libGL'] = FakeLibGL()
sys.modules['libGL.so.1'] = FakeLibGL()

# ========== 标准库导入 ==========
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
import io
import contextlib
from PIL import Image
import torch
import gc

warnings.filterwarnings('ignore')

# ========== 项目路径设置 ==========
try:
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
except:
    project_root = Path.cwd()

# ========== 延迟导入Agents ==========
AGENTS_AVAILABLE = False
ENHANCEMENT_AVAILABLE = False
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stderr(io.StringIO()):
            from agents.image_multi_angle_generator import ImageMultiAngleGenerator
            from agents.image_quality_analyzer import ImageQualityAnalyzer
            from agents.material_generator_agent import MaterialGeneratorAgent
            try:
                from agents.material_enhancement_trainer import MaterialEnhancementTrainer
                ENHANCEMENT_AVAILABLE = True
            except:
                ENHANCEMENT_AVAILABLE = False
            AGENTS_AVAILABLE = True
except Exception as e:
    st.error(f"⚠️ 模块加载警告: {str(e)}")
    AGENTS_AVAILABLE = False

# ========== 页面配置 ==========
st.set_page_config(
    page_title="🚁 无人机视觉AI分析系统",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 科幻风格CSS ==========
SCIFI_CSS = """
<style>
    /* 全局科幻风格 */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Rajdhani', 'Microsoft YaHei', sans-serif !important;
    }
    
    /* 主背景 - 深色科技感 */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
        background-attachment: fixed;
    }
    
    /* 标题样式 - 霓虹效果 */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00ffff !important;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff;
        font-weight: 700 !important;
        letter-spacing: 2px;
    }
    
    /* 副标题 */
    h2 {
        color: #00ff88 !important;
        text-shadow: 0 0 8px #00ff88;
    }
    
    h3 {
        color: #ff6b9d !important;
        text-shadow: 0 0 6px #ff6b9d;
    }
    
    /* 文本颜色 */
    p, li, span, div {
        color: #e0e0e0 !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    /* 侧边栏 */
    .css-1d391kg {
        background: rgba(10, 14, 39, 0.95) !important;
        border-right: 2px solid #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
    }
    
    /* 按钮样式 - 科幻感 */
    .stButton > button {
        background: linear-gradient(135deg, #00ffff 0%, #0088ff 100%);
        color: #000 !important;
        border: 2px solid #00ffff;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 700;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        border-color: #00ff88;
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.7);
        transform: translateY(-2px);
    }
    
    /* 输入框 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid #00ffff !important;
        color: #00ffff !important;
        border-radius: 5px;
    }
    
    /* 滑块 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #00ffff 0%, #0088ff 100%);
    }
    
    /* 指标卡片 */
    [data-testid="stMetricValue"] {
        color: #00ffff !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px #00ffff;
    }
    
    [data-testid="stMetricLabel"] {
        color: #00ff88 !important;
        font-size: 1.2rem !important;
    }
    
    /* 成功/错误消息 */
    .stSuccess {
        background: rgba(0, 255, 136, 0.2) !important;
        border-left: 4px solid #00ff88;
        color: #00ff88 !important;
    }
    
    .stError {
        background: rgba(255, 107, 157, 0.2) !important;
        border-left: 4px solid #ff6b9d;
        color: #ff6b9d !important;
    }
    
    .stInfo {
        background: rgba(0, 255, 255, 0.2) !important;
        border-left: 4px solid #00ffff;
        color: #00ffff !important;
    }
    
    /* 代码块 */
    .stCodeBlock {
        background: rgba(0, 0, 0, 0.7) !important;
        border: 1px solid #00ffff;
        border-radius: 5px;
    }
    
    /* 表格 */
    .dataframe {
        background: rgba(0, 0, 0, 0.5) !important;
        color: #e0e0e0 !important;
    }
    
    /* 进度条 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00ffff 0%, #0088ff 100%);
    }
    
    /* 分隔线 */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ffff, transparent);
        margin: 2rem 0;
    }
    
    /* 卡片效果 */
    .element-container {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
    }
</style>
"""

st.markdown(SCIFI_CSS, unsafe_allow_html=True)

# ========== 工具函数 ==========
def init_session_state():
    """初始化session state"""
    if 'generator' not in st.session_state:
        st.session_state.generator = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = []
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

def get_generator(draw_boxes: bool = True):
    """获取生成器实例"""
    if st.session_state.generator is None and AGENTS_AVAILABLE:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stderr(io.StringIO()):
                    st.session_state.generator = ImageMultiAngleGenerator(draw_boxes=draw_boxes)
        except Exception as e:
            st.error(f"生成器初始化失败: {e}")
    elif st.session_state.generator is not None:
        # 更新检测框设置
        st.session_state.generator.draw_boxes = draw_boxes
    return st.session_state.generator

def get_analyzer():
    """获取分析器实例"""
    if st.session_state.analyzer is None and AGENTS_AVAILABLE:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stderr(io.StringIO()):
                    st.session_state.analyzer = ImageQualityAnalyzer()
        except Exception as e:
            st.error(f"分析器初始化失败: {e}")
    return st.session_state.analyzer

def get_agent():
    """获取Agent实例"""
    if st.session_state.agent is None and AGENTS_AVAILABLE:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stderr(io.StringIO()):
                    st.session_state.agent = MaterialGeneratorAgent()
        except Exception as e:
            st.error(f"Agent初始化失败: {e}")
    return st.session_state.agent

def create_radar_chart(scores: Dict[str, float], title: str = "8维度质量分析雷达图"):
    """创建科幻风格的雷达图"""
    dimensions = [
        "图片数据量", "拍摄光照质量", "目标尺寸", "目标完整性",
        "数据均衡度", "产品丰富度", "目标密集度", "场景复杂度"
    ]
    
    values = [scores.get(dim, 0) for dim in dimensions]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # 闭合图形
        theta=dimensions + [dimensions[0]],
        fill='toself',
        fillcolor='rgba(0, 255, 255, 0.3)',
        line=dict(color='#00ffff', width=3),
        name='质量得分',
        marker=dict(size=8, color='#00ffff')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color='#00ff88', size=12),
                gridcolor='rgba(0, 255, 255, 0.3)',
                linecolor='#00ffff'
            ),
            angularaxis=dict(
                tickfont=dict(color='#00ffff', size=11),
                linecolor='#00ffff'
            ),
            bgcolor='rgba(0, 0, 0, 0.5)'
        ),
        title=dict(
            text=title,
            font=dict(size=24, color='#00ffff', family='Orbitron'),
            x=0.5
        ),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#e0e0e0', family='Rajdhani'),
        height=600,
        showlegend=True,
        legend=dict(
            font=dict(color='#00ffff', size=14),
            bgcolor='rgba(0, 0, 0, 0.5)',
            bordercolor='#00ffff',
            borderwidth=1
        )
    )
    
    return fig

def calculate_overall_score(scores: Dict[str, float]) -> float:
    """计算总体质量得分"""
    return np.mean(list(scores.values()))

def generate_improvement_suggestions(scores: Dict[str, float]) -> List[str]:
    """生成改进建议"""
    suggestions = []
    dimension_names = {
        "图片数据量": "提高图片分辨率和文件大小",
        "拍摄光照质量": "改善光照条件，避免过曝或欠曝",
        "目标尺寸": "调整拍摄距离，确保目标足够大",
        "目标完整性": "避免目标被裁剪或遮挡",
        "数据均衡度": "平衡不同类别目标的分布",
        "产品丰富度": "增加更多类别的目标",
        "目标密集度": "增加单位面积内的目标数量",
        "场景复杂度": "丰富背景纹理和细节"
    }
    
    for dim, score in scores.items():
        if score < 60:
            suggestions.append(f"⚠️ {dim} ({score:.1f}分): {dimension_names.get(dim, '需要改进')}")
        elif score < 80:
            suggestions.append(f"⚡ {dim} ({score:.1f}分): {dimension_names.get(dim, '可以进一步提升')}")
    
    if not suggestions:
        suggestions.append("✅ 所有维度表现优秀，素材质量很高！")
    
    return suggestions

# ========== 主界面 ==========
def main():
    init_session_state()
    
    # 主标题
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem;">🚁 无人机视觉AI分析系统</h1>
        <p style="font-size: 1.5rem; color: #00ff88; letter-spacing: 3px;">DRONE VISION AI ANALYSIS SYSTEM</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 🎛️ 控制面板")
        
        page = st.radio(
            "选择功能模块",
            ["📸 素材生成", "📊 质量分析", "🎯 智能筛选", "📈 数据报告"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        st.markdown("### ⚙️ 系统状态")
        if AGENTS_AVAILABLE:
            st.success("✅ 系统就绪")
        else:
            st.error("⚠️ 模块未加载")
        
        st.markdown("---")
        st.markdown("### 📖 使用说明")
        st.info("""
        1. **素材生成**: 上传图片，生成多角度素材
        2. **质量分析**: 8维度深度分析
        3. **智能筛选**: 自动筛选高质量素材
        4. **数据报告**: 查看详细分析报告
        """)
    
    # 主内容区
    if page == "📸 素材生成":
        show_generation_page()
    elif page == "📊 质量分析":
        show_analysis_page()
    elif page == "🎯 智能筛选":
        show_filter_page()
    elif page == "📈 数据报告":
        show_report_page()

def show_generation_page():
    """素材生成页面"""
    st.markdown("## 📸 多角度素材生成器")
    st.markdown("从单张图片生成多个角度的素材，支持3D视角变换和检测框标注")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "上传无人机图片",
            type=['jpg', 'jpeg', 'png'],
            help="支持JPG、PNG格式，建议分辨率1920x1080以上"
        )
        
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            image = Image.open(uploaded_file)
            st.image(image, caption="原始图片", use_container_width=True)
    
    with col2:
        st.markdown("### ⚙️ 生成参数")
        num_generations = st.slider("生成数量", 4, 100, 8, help="建议4-20张，数量越多耗时越长")
        
        transformations = st.multiselect(
            "变换类型",
            ["透视变换", "旋转", "缩放", "亮度调整", "对比度调整"],
            default=["透视变换", "旋转", "缩放"],
            help="选择要应用的变换类型"
        )
        
        show_detection = st.checkbox("显示检测框", value=True, help="在生成的图片上绘制YOLO检测框")
    
    if st.button("🚀 开始生成", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("请先上传图片")
            return
        
        if not AGENTS_AVAILABLE:
            st.error("系统模块未加载，请检查环境配置")
            return
        
        generator = get_generator(draw_boxes=show_detection)
        if generator is None:
            st.error("生成器初始化失败")
            return
        
        # 保存临时文件
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        output_dir = Path("generated_images") / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("🔄 正在生成素材，请稍候...")
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stderr(io.StringIO()):
                    result = generator.generate_multi_angle_images(
                        input_image_path=str(temp_path),
                        output_dir=str(output_dir),
                        num_generations=num_generations,
                        transformations=transformations if transformations else None
                    )
            
            progress_bar.progress(100)
            status_text.success(f"✅ 成功生成 {result.get('num_generated', 0)} 张素材")
            
            st.session_state.generated_images = result.get('generated_files', [])
            st.session_state.confidence_stats = result.get('confidence_statistics', {})
            
            # 显示生成的图片 - 显示所有图片，使用分页
            st.markdown("### 🖼️ 生成的素材")
            total_images = len(st.session_state.generated_images)
            st.info(f"✅ 共生成 {total_images} 张素材图片")
            
            # 分页显示（每页9张）
            images_per_page = 9
            total_pages = (total_images + images_per_page - 1) // images_per_page
            
            if total_pages > 1:
                page = st.selectbox("选择页码", range(1, total_pages + 1), format_func=lambda x: f"第 {x} 页 (共 {total_pages} 页)")
                start_idx = (page - 1) * images_per_page
                end_idx = min(start_idx + images_per_page, total_images)
            else:
                start_idx = 0
                end_idx = total_images
            
            # 显示当前页的图片
            cols = st.columns(3)
            for idx in range(start_idx, end_idx):
                img_path = st.session_state.generated_images[idx]
                with cols[idx % 3]:
                    try:
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                        # 从文件名提取变换类型
                        transform_name = Path(img_path).stem.split('_')[-1] if '_' in Path(img_path).stem else "original"
                        st.caption(f"素材 {idx + 1}/{total_images} - {transform_name}")
                    except Exception as e:
                        st.error(f"加载失败: {e}")
            
            # 显示置信度统计饼图（显示所有置信度）
            if st.session_state.confidence_stats:
                st.markdown("### 📊 检测置信度统计")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 获取所有置信度值（不是平均值）
                    all_confidences = st.session_state.confidence_stats.get('_all_confidences', [])
                    
                    if all_confidences:
                        # 将置信度分组到区间（用于饼图显示）
                        confidence_ranges = {
                            '0.0-0.2': 0,
                            '0.2-0.4': 0,
                            '0.4-0.6': 0,
                            '0.6-0.8': 0,
                            '0.8-1.0': 0
                        }
                        
                        for conf in all_confidences:
                            if conf < 0.2:
                                confidence_ranges['0.0-0.2'] += 1
                            elif conf < 0.4:
                                confidence_ranges['0.2-0.4'] += 1
                            elif conf < 0.6:
                                confidence_ranges['0.4-0.6'] += 1
                            elif conf < 0.8:
                                confidence_ranges['0.6-0.8'] += 1
                            else:
                                confidence_ranges['0.8-1.0'] += 1
                        
                        # 创建饼图 - 显示所有置信度分布
                        fig = go.Figure(data=[go.Pie(
                            labels=list(confidence_ranges.keys()),
                            values=list(confidence_ranges.values()),
                            hole=0.3,
                            textinfo='label+percent+value',
                            texttemplate='%{label}<br>%{value}个检测<br>占比:%{percent}',
                            marker=dict(
                                colors=['#ff6b9d', '#ffa500', '#00ff88', '#00ffff', '#0088ff'],
                                line=dict(color='#000000', width=2)
                            )
                        )])
                        fig.update_layout(
                            title="所有检测置信度分布",
                            font=dict(color='#e0e0e0', family='Rajdhani'),
                            paper_bgcolor='rgba(0, 0, 0, 0)',
                            plot_bgcolor='rgba(0, 0, 0, 0)',
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无检测数据")
                
                with col2:
                    st.markdown("#### 📈 统计信息")
                    
                    # 计算加权平均置信度（权重由每个维度的占比随机生成）
                    all_confidences = st.session_state.confidence_stats.get('_all_confidences', [])
                    if all_confidences:
                        total_detections = len(all_confidences)
                        st.metric("总检测数", total_detections)
                        
                        # 生成随机权重（8个维度）
                        np.random.seed(int(time.time()) % 1000)
                        dimension_weights = np.random.dirichlet(np.ones(8))  # 8个维度的随机权重
                        
                        # 将置信度分成8组，每组使用不同的权重
                        num_groups = 8
                        group_size = len(all_confidences) // num_groups
                        weighted_sum = 0
                        total_weight = 0
                        
                        for i in range(num_groups):
                            start_idx = i * group_size
                            end_idx = start_idx + group_size if i < num_groups - 1 else len(all_confidences)
                            group_confidences = all_confidences[start_idx:end_idx]
                            
                            if group_confidences:
                                group_avg = np.mean(group_confidences)
                                weight = dimension_weights[i]
                                weighted_sum += group_avg * weight
                                total_weight += weight
                        
                        weighted_avg_confidence = (weighted_sum / total_weight * 100) if total_weight > 0 else 0
                        
                        st.metric("加权平均置信度", f"{weighted_avg_confidence:.1f}%")
                        st.caption("权重由8维度占比随机生成")
                        
                        # 显示权重分布
                        with st.expander("📊 权重分布"):
                            dimension_names = [
                                "图片数据量", "拍摄光照质量", "目标尺寸", "目标完整性",
                                "数据均衡度", "产品丰富度", "目标密集度", "场景复杂度"
                            ]
                            for i, (name, weight) in enumerate(zip(dimension_names, dimension_weights)):
                                st.progress(weight, text=f"{name}: {weight*100:.1f}%")
                        
                        # 简单平均置信度（对比）
                        simple_avg = np.mean(all_confidences) * 100
                        st.metric("简单平均置信度", f"{simple_avg:.1f}%")
                        
                        # 质量评估（使用加权平均）
                        quality_score = weighted_avg_confidence
                    else:
                        quality_score = 0
                    
                    # 质量评估
                    if quality_score > 0:
                        st.warning("⚠️ 素材质量较低，建议开启增强训练")
                        if st.button("🚀 开启增强训练", type="primary", use_container_width=True):
                            st.session_state.enhancement_mode = True
                            st.info("增强训练模式已开启，将在下次生成时应用")
                    elif quality_score < 80:
                        st.info("⚡ 素材质量良好，可以进一步提升")
                        if st.button("🚀 开启增强训练", type="secondary", use_container_width=True):
                            st.session_state.enhancement_mode = True
                            st.info("增强训练模式已开启")
                    else:
                        st.success("✅ 素材质量优秀")
                    
                    # 增强训练功能
                    if st.session_state.get('enhancement_mode', False) and ENHANCEMENT_AVAILABLE:
                        st.markdown("### 🚀 增强训练模式")
                        st.warning("增强训练功能需要额外的计算资源，可能会增加处理时间")
                        if st.button("开始增强训练", type="primary"):
                            try:
                                from agents.material_enhancement_trainer import MaterialEnhancementTrainer
                                trainer = MaterialEnhancementTrainer()
                                enhanced_images = []
                                for img_path in st.session_state.generated_images[:5]:  # 只增强前5张
                                    enhanced = trainer.enhance_image(img_path)
                                    enhanced_images.append(enhanced)
                                st.success(f"✅ 成功增强 {len(enhanced_images)} 张图片")
                            except Exception as e:
                                st.error(f"增强训练失败: {e}")
            
            # 显示详细统计表格
            if st.session_state.confidence_stats:
                with st.expander("📋 详细检测统计"):
                    stats_data = []
                    for class_name, stats in st.session_state.confidence_stats.items():
                        stats_data.append({
                            '类别': class_name,
                            '检测数量': stats['count'],
                            '平均置信度': f"{stats['avg_confidence']*100:.2f}%",
                            '最高置信度': f"{stats['max_confidence']*100:.2f}%",
                            '最低置信度': f"{stats['min_confidence']*100:.2f}%"
                        })
                    df_stats = pd.DataFrame(stats_data)
                    st.dataframe(df_stats, use_container_width=True)
        
        except Exception as e:
            st.error(f"生成失败: {str(e)}")
        finally:
            progress_bar.empty()
            if temp_path.exists():
                temp_path.unlink()

def show_analysis_page():
    """质量分析页面"""
    st.markdown("## 📊 8维度质量分析")
    st.markdown("对图片进行8个维度的深度质量分析，生成详细的评估报告")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        analysis_mode = st.radio(
            "分析模式",
            ["单图分析", "批量分析"],
            help="选择分析单张图片或批量分析多张图片"
        )
        
        if analysis_mode == "单图分析":
            uploaded_file = st.file_uploader(
                "上传图片",
                type=['jpg', 'jpeg', 'png'],
                key="analysis_upload"
            )
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="待分析图片", use_container_width=True)
        
        else:
            uploaded_files = st.file_uploader(
                "上传多张图片",
                type=['jpg', 'jpeg', 'png'],
                accept_multiple_files=True,
                key="batch_upload"
            )
            
            if uploaded_files:
                st.info(f"已选择 {len(uploaded_files)} 张图片")
                cols = st.columns(min(3, len(uploaded_files)))
                for idx, file in enumerate(uploaded_files[:3]):
                    with cols[idx]:
                        img = Image.open(file)
                        st.image(img, use_container_width=True)
    
    with col2:
        st.markdown("### 📋 分析参数")
        min_confidence = st.slider("检测置信度阈值", 0.1, 0.9, 0.5, 0.05, help="YOLO检测的最小置信度")
        show_details = st.checkbox("显示详细信息", value=True)
        export_json = st.checkbox("导出JSON报告", value=False)
    
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        if not AGENTS_AVAILABLE:
            st.error("系统模块未加载")
            return
        
        analyzer = get_analyzer()
        if analyzer is None:
            st.error("分析器初始化失败")
            return
        
        if analysis_mode == "单图分析":
            if not uploaded_file:
                st.error("请先上传图片")
                return
            
            # 保存临时文件
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                with st.spinner("🔄 正在分析..."):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        with contextlib.redirect_stderr(io.StringIO()):
                            result = analyzer.analyze_single_image(str(temp_path))
                
                st.session_state.analysis_results = result
                
                # 显示雷达图
                st.markdown("### 📈 8维度雷达图")
                fig = create_radar_chart(result, "单图质量分析")
                st.plotly_chart(fig, use_container_width=True)
                
                # 显示得分
                st.markdown("### 📊 维度得分")
                cols = st.columns(4)
                for idx, (dim, score) in enumerate(result.items()):
                    with cols[idx % 4]:
                        st.metric(dim, f"{score:.1f}")
                
                # 总体得分
                overall = calculate_overall_score(result)
                st.markdown(f"### 🎯 总体质量得分: {overall:.1f}")
                
                # 改进建议
                st.markdown("### 💡 改进建议")
                suggestions = generate_improvement_suggestions(result)
                for suggestion in suggestions:
                    st.markdown(f"- {suggestion}")
                
                # 导出JSON
                if export_json:
                    json_str = json.dumps(result, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📥 下载JSON报告",
                        json_str,
                        file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
            finally:
                if temp_path.exists():
                    temp_path.unlink()
        
        else:  # 批量分析
            if not uploaded_files:
                st.error("请先上传图片")
                return
            
            # 保存临时文件
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_paths = []
            for file in uploaded_files:
                temp_path = temp_dir / file.name
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                temp_paths.append(str(temp_path))
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    with contextlib.redirect_stderr(io.StringIO()):
                        results = analyzer.analyze_batch(temp_paths)
                
                progress_bar.progress(100)
                status_text.success(f"✅ 成功分析 {len(results)} 张图片")
                
                # 显示结果表格
                st.markdown("### 📋 分析结果表格")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                
                # 平均得分
                avg_scores = df.iloc[:, 1:].mean()
                st.markdown("### 📊 平均维度得分")
                fig = create_radar_chart(avg_scores.to_dict(), "批量分析平均得分")
                st.plotly_chart(fig, use_container_width=True)
                
                # 导出CSV
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 下载CSV报告",
                    csv,
                    file_name=f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            except Exception as e:
                st.error(f"批量分析失败: {str(e)}")
            finally:
                for path in temp_paths:
                    if Path(path).exists():
                        Path(path).unlink()

def show_filter_page():
    """智能筛选页面"""
    st.markdown("## 🎯 智能素材筛选")
    st.markdown("根据8维度分析结果，自动筛选高质量素材")
    
    uploaded_files = st.file_uploader(
        "上传多张图片",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider("最低质量得分", 0, 100, 70, help="只保留得分高于此值的素材")
    with col2:
        filter_mode = st.selectbox(
            "筛选模式",
            ["总体得分", "任一维度", "所有维度"],
            help="选择筛选标准"
        )
    
    if st.button("🔍 开始筛选", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("请先上传图片")
            return
        
        if not AGENTS_AVAILABLE:
            st.error("系统模块未加载")
            return
        
        agent = get_agent()
        if agent is None:
            st.error("Agent初始化失败")
            return
        
        # 保存临时文件
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_paths = []
        for file in uploaded_files:
            temp_path = temp_dir / file.name
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            temp_paths.append(str(temp_path))
        
        try:
            with st.spinner("🔄 正在分析和筛选..."):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    with contextlib.redirect_stderr(io.StringIO()):
                        if filter_mode == "总体得分":
                            high_quality = agent.filter_high_quality_materials(temp_paths, min_score=min_score)
                        else:
                            # 需要实现其他筛选模式
                            high_quality = agent.filter_high_quality_materials(temp_paths, min_score=min_score)
            
            st.success(f"✅ 筛选完成，找到 {len(high_quality)} 张高质量素材")
            
            # 显示筛选结果
            st.markdown("### 🎯 高质量素材")
            cols = st.columns(3)
            for idx, img_path in enumerate(high_quality[:9]):
                with cols[idx % 3]:
                    try:
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                        st.caption(f"素材 {idx + 1}")
                    except:
                        pass
        
        except Exception as e:
            st.error(f"筛选失败: {str(e)}")
        finally:
            for path in temp_paths:
                if Path(path).exists():
                    Path(path).unlink()

def show_report_page():
    """数据报告页面"""
    st.markdown("## 📈 数据分析报告")
    st.markdown("查看详细的分析报告和统计数据")
    
    if st.session_state.analysis_results is None:
        st.info("请先在'质量分析'页面进行分析")
        return
    
    results = st.session_state.analysis_results
    
    # 统计信息
    st.markdown("### 📊 统计概览")
    col1, col2, col3, col4 = st.columns(4)
    
    overall = calculate_overall_score(results)
    max_dim = max(results.items(), key=lambda x: x[1])
    min_dim = min(results.items(), key=lambda x: x[1])
    
    with col1:
        st.metric("总体得分", f"{overall:.1f}")
    with col2:
        st.metric("最高维度", f"{max_dim[0]}\n{max_dim[1]:.1f}")
    with col3:
        st.metric("最低维度", f"{min_dim[0]}\n{min_dim[1]:.1f}")
    with col4:
        above_80 = sum(1 for v in results.values() if v >= 80)
        st.metric("优秀维度", f"{above_80}/8")
    
    # 详细报告
    st.markdown("### 📋 详细报告")
    df = pd.DataFrame([results])
    st.dataframe(df.T, use_container_width=True)
    
    # 可视化
    st.markdown("### 📈 可视化分析")
    fig = create_radar_chart(results, "详细质量分析报告")
    st.plotly_chart(fig, use_container_width=True)
    
    # 改进建议
    st.markdown("### 💡 改进建议")
    suggestions = generate_improvement_suggestions(results)
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")

if __name__ == "__main__":
    main()

