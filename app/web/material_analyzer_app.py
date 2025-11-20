"""
8维度图片质量分析 - Streamlit Web界面
8-Dimensional Image Quality Analysis - Streamlit Web Interface
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from agents.image_quality_analyzer import ImageQualityAnalyzer
from agents.material_generator_agent import MaterialGeneratorAgent


# 页面配置
st.set_page_config(
    page_title="无人机素材8维度分析系统",
    page_icon="🚁",
    layout="wide"
)

# 标题
st.title("🚁 无人机素材8维度智能分析系统")
st.markdown("---")

# 初始化session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = ImageQualityAnalyzer()
if 'agent' not in st.session_state:
    st.session_state.agent = MaterialGeneratorAgent()
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# 侧边栏
with st.sidebar:
    st.header("⚙️ 系统配置")
    
    # 模型路径设置
    model_path = st.text_input(
        "YOLO模型路径 (可选)",
        value="",
        help="留空则使用默认预训练模型"
    )
    
    # 质量阈值
    quality_threshold = st.slider(
        "质量阈值",
        min_value=0.0,
        max_value=100.0,
        value=70.0,
        step=1.0,
        help="用于筛选高质量素材的阈值"
    )
    
    st.markdown("---")
    st.markdown("### 📊 8个分析维度")
    dimensions = [
        "1. 图片数据量",
        "2. 拍摄光照质量",
        "3. 目标尺寸",
        "4. 目标完整性",
        "5. 数据均衡度",
        "6. 产品丰富度",
        "7. 目标密集度",
        "8. 场景复杂度"
    ]
    for dim in dimensions:
        st.markdown(f"- {dim}")

# 主界面
tab1, tab2, tab3 = st.tabs(["📸 单图分析", "📁 批量分析", "📊 结果报告"])

# Tab 1: 单图分析
with tab1:
    st.header("单张图片分析")
    
    uploaded_file = st.file_uploader(
        "上传图片",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="支持JPG、PNG、BMP格式"
    )
    
    if uploaded_file is not None:
        # 保存上传的图片
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 显示图片
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption="上传的图片", use_container_width=True)
        
        with col2:
            if st.button("🔍 开始分析", type="primary"):
                with st.spinner("正在分析图片..."):
                    try:
                        result = st.session_state.analyzer.analyze_single_image(str(temp_path))
                        
                        # 显示8维度雷达图
                        fig = create_radar_chart(result)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 显示详细分数
                        st.subheader("📊 维度得分详情")
                        score_df = pd.DataFrame([
                            {"维度": dim, "得分": score, "等级": get_score_level(score)}
                            for dim, score in result.items()
                        ])
                        st.dataframe(score_df, use_container_width=True)
                        
                        # 保存结果
                        st.session_state.analysis_results = {
                            'single_image': result,
                            'image_path': str(temp_path)
                        }
                        
                    except Exception as e:
                        st.error(f"分析出错: {e}")

# Tab 2: 批量分析
with tab2:
    st.header("批量图片分析")
    
    uploaded_files = st.file_uploader(
        "上传多张图片",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        accept_multiple_files=True,
        help="可以同时上传多张图片进行批量分析"
    )
    
    if uploaded_files:
        st.info(f"已上传 {len(uploaded_files)} 张图片")
        
        if st.button("🚀 开始批量分析", type="primary"):
            # 保存所有上传的图片
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            image_paths = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                temp_path = temp_dir / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(str(temp_path))
                progress_bar.progress((i + 1) / len(uploaded_files))
                status_text.text(f"正在保存图片 {i+1}/{len(uploaded_files)}")
            
            # 执行批量分析
            with st.spinner("正在进行批量分析，请稍候..."):
                try:
                    result = st.session_state.agent.analyze_and_evaluate(image_paths)
                    
                    # 显示平均维度雷达图
                    st.subheader("📊 平均维度得分")
                    avg_scores = result['analysis']['average_scores']
                    fig = create_radar_chart(avg_scores)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示质量评估表格
                    st.subheader("📋 图片质量评估")
                    quality_df = pd.DataFrame([
                        {
                            "图片": Path(q['image_path']).name,
                            "平均得分": f"{q['average_score']:.2f}",
                            "质量等级": q['quality_level']
                        }
                        for q in result['quality_evaluation']
                    ])
                    st.dataframe(quality_df, use_container_width=True)
                    
                    # 显示推荐建议
                    st.subheader("💡 改进建议")
                    recommendations = result['recommendations']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("整体质量", f"{recommendations['overall_quality']:.2f}")
                        st.metric("高质量图片数", len(recommendations['high_quality_images']))
                    
                    with col2:
                        if recommendations['needs_improvement']:
                            st.warning("需要改进的维度:")
                            for dim in recommendations['needs_improvement']:
                                st.write(f"- {dim}")
                    
                    # 显示改进建议详情
                    if recommendations['improvement_suggestions']:
                        st.markdown("#### 具体改进建议:")
                        for dim, suggestion in recommendations['improvement_suggestions'].items():
                            st.info(f"**{dim}**: {suggestion}")
                    
                    # 保存结果
                    st.session_state.analysis_results = result
                    
                except Exception as e:
                    st.error(f"批量分析出错: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# Tab 3: 结果报告
with tab3:
    st.header("分析结果报告")
    
    if st.session_state.analysis_results is None:
        st.info("请先进行图片分析")
    else:
        result = st.session_state.analysis_results
        
        # 生成报告
        if st.button("📄 生成详细报告", type="primary"):
            report_path = st.session_state.agent.generate_material_report(
                result,
                "reports"
            )
            st.success(f"报告已生成: {report_path}")
            
            # 下载报告
            with open(report_path, 'r', encoding='utf-8') as f:
                st.download_button(
                    label="📥 下载报告 (JSON)",
                    data=f.read(),
                    file_name=Path(report_path).name,
                    mime="application/json"
                )
        
        # 显示统计信息
        if 'analysis' in result:
            st.subheader("📈 统计信息")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总图片数", result['analysis']['total_images'])
            with col2:
                st.metric("总标注数", result['analysis']['total_annotations'])
            with col3:
                st.metric("平均质量", f"{result['recommendations']['overall_quality']:.2f}")
            with col4:
                high_quality_count = len(result['recommendations']['high_quality_images'])
                st.metric("高质量图片", high_quality_count)


def create_radar_chart(scores: dict) -> go.Figure:
    """创建8维度雷达图"""
    dimensions = [
        "图片数据量",
        "拍摄光照质量",
        "目标尺寸",
        "目标完整性",
        "数据均衡度",
        "产品丰富度",
        "目标密集度",
        "场景复杂度"
    ]
    
    values = [scores.get(dim, 0) for dim in dimensions]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=dimensions,
        fill='toself',
        name='维度得分',
        line=dict(color='rgb(31, 119, 180)'),
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=11)
            )
        ),
        showlegend=True,
        title="8维度质量分析雷达图",
        height=500
    )
    
    return fig


def get_score_level(score: float) -> str:
    """获取分数等级"""
    if score >= 90:
        return "优秀 ⭐⭐⭐"
    elif score >= 80:
        return "良好 ⭐⭐"
    elif score >= 70:
        return "中等 ⭐"
    elif score >= 60:
        return "一般"
    else:
        return "较差"


if __name__ == "__main__":
    st.run()




