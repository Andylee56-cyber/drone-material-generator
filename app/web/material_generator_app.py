"""
无人机素材多角度生成与分析系统 - Streamlit Web界面（带增强训练功能）
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from PIL import Image
import time
import shutil
from datetime import datetime

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from agents.image_multi_angle_generator import ImageMultiAngleGenerator
from agents.image_quality_analyzer import ImageQualityAnalyzer
from agents.material_generator_agent import MaterialGeneratorAgent
from agents.material_enhancement_trainer import MaterialEnhancementTrainer

st.set_page_config(page_title="无人机素材生成系统", page_icon="🚁", layout="wide", initial_sidebar_state="collapsed")


# ========== 移动端优化 ==========
st.markdown("""
<style>
    /* 移动端按钮优化 */
    @media screen and (max-width: 768px) {
        .stButton > button {
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
        }
        
        /* 输入框优化（防止iOS自动缩放） */
        .stTextInput > div > div > input {
            font-size: 16px !important;
        }
        
        /* 文件上传优化 */
        .stFileUploader {
            font-size: 16px !important;
        }
        
        /* 表格优化 */
        .dataframe {
            font-size: 14px !important;
            overflow-x: auto !important;
        }
        
        /* 图表容器 */
        .js-plotly-plot {
            width: 100% !important;
            height: auto !important;
        }
        
        /* 侧边栏优化 */
        .css-1d391kg {
            padding-top: 1rem !important;
        }
    }
    
    /* 隐藏Streamlit默认元素（移动端） */
    @media screen and (max-width: 768px) {
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    }
    
    /* 通用优化 */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)



# ========== 移动端优化 ==========
st.markdown("""
<style>
    /* 移动端按钮优化 */
    @media screen and (max-width: 768px) {
        .stButton > button {
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
            margin: 8px 0 !important;
        }
        
        /* 输入框优化（防止iOS自动缩放） */
        .stTextInput > div > div > input {
            font-size: 16px !important;
        }
        
        /* 文件上传优化 */
        .stFileUploader {
            font-size: 16px !important;
        }
        
        /* 表格优化 */
        .dataframe {
            font-size: 14px !important;
            overflow-x: auto !important;
        }
        
        /* 图表容器 */
        .js-plotly-plot {
            width: 100% !important;
            height: auto !important;
        }
        
        /* 侧边栏优化 */
        .css-1d391kg {
            padding-top: 1rem !important;
        }
    }
    
    /* 隐藏Streamlit默认元素（移动端） */
    @media screen and (max-width: 768px) {
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    }
    
    /* 通用优化 */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚁 无人机素材多角度生成与分析系统")
st.markdown("**功能**: 输入一张图片，自动生成多角度素材（带检测框），并生成8维度雷达图分析和置信度统计")
st.markdown("**新增**: 质量较差素材自动增强训练功能")
st.markdown("---")

if 'generator' not in st.session_state:
    st.session_state.generator = ImageMultiAngleGenerator(draw_boxes=True)
if 'agent' not in st.session_state:
    st.session_state.agent = MaterialGeneratorAgent()
if 'enhancement_trainer' not in st.session_state:
    st.session_state.enhancement_trainer = MaterialEnhancementTrainer()
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'confidence_stats' not in st.session_state:
    st.session_state.confidence_stats = {}
if 'enhancement_results' not in st.session_state:
    st.session_state.enhancement_results = None

with st.sidebar:
    st.header("⚙️ 系统配置")
    num_generations = st.slider("生成图片数量", 4, 100, 18, 1)
    auto_analyze = st.checkbox("生成后自动分析", value=True)
    draw_detection_boxes = st.checkbox("绘制检测框", value=True)
    
    st.markdown("---")
    st.markdown("### 🎯 增强训练设置")
    enable_enhancement = st.checkbox("启用自动增强训练", value=True)
    if enable_enhancement:
        target_improvement = st.slider("目标提升分数", 3, 10, 5, 1)
        max_iterations = st.slider("最大迭代次数", 5, 20, 10, 1)
    
    st.markdown("---")
    st.markdown("### 💾 保存设置")
    save_enabled = st.checkbox("启用保存功能", value=True)
    if save_enabled:
        save_folder = st.text_input("保存文件夹路径", value="D:\\无人机生成素材")
        save_name = st.text_input("保存文件夹名称（可选）", value="")
    
    st.markdown("---")
    st.markdown("### 📊 8个分析维度（点击查看详情）")
    
    dimensions_list = [
        ("图片数据量", "基于图片分辨率和文件大小评估"),
        ("拍摄光照质量", "基于亮度、对比度、曝光度评估"),
        ("目标尺寸", "基于检测到的目标平均尺寸评估"),
        ("目标完整性", "基于目标是否被裁剪或遮挡评估"),
        ("数据均衡度", "基于不同类别目标的分布均衡性评估"),
        ("产品丰富度", "基于检测到的目标类别数量评估"),
        ("目标密集度", "基于单位面积内的目标数量评估"),
        ("场景复杂度", "基于背景复杂度、纹理丰富度评估")
    ]
    
    for dim_name, dim_desc in dimensions_list:
        with st.expander(f"📌 {dim_name}", expanded=False):
            st.markdown(f"**说明**: {dim_desc}")
            if st.session_state.analysis_results:
                avg_scores = st.session_state.analysis_results['analysis']['average_scores']
                score = avg_scores.get(dim_name, 0)
                st.metric("平均得分", f"{score:.2f}%")
                
                individual_scores = []
                for result in st.session_state.analysis_results['analysis']['individual_results']:
                    individual_scores.append({
                        '图片': Path(result['image_path']).name,
                        '得分': f"{result.get(dim_name, 0):.2f}%"
                    })
                if individual_scores:
                    st.dataframe(pd.DataFrame(individual_scores), use_container_width=True, hide_index=True)

st.header("📸 上传图片并生成多角度素材")
uploaded_file = st.file_uploader("上传一张无人机图片", type=['jpg','jpeg','png','bmp'])

if uploaded_file is not None:
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("📷 原始图片")
        st.image(uploaded_file, caption="上传的原始图片", use_column_width=True)

    with col2:
        st.subheader("🎯 操作")
        if st.button("🚀 生成多角度素材并分析", type="primary", use_container_width=True):
            with st.spinner("正在生成多角度素材，请稍候..."):
                try:
                    # 更新生成器配置
                    if draw_detection_boxes != st.session_state.generator.draw_boxes:
                        st.session_state.generator = ImageMultiAngleGenerator(draw_boxes=draw_detection_boxes)
                    
                    # 确定输出目录
                    if save_enabled and save_folder:
                        base_dir = Path(save_folder)
                        base_dir.mkdir(parents=True, exist_ok=True)
                        if save_name:
                            output_dir = base_dir / save_name
                        else:
                            output_dir = base_dir / f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    else:
                        output_dir = Path("generated_materials") / f"generation_{int(time.time())}"
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("步骤1/2: 正在生成多角度素材（带检测框）...")
                    result = st.session_state.generator.generate_multi_angle_images(
                        input_image_path=str(temp_path),
                        output_dir=str(output_dir),
                        num_generations=num_generations
                    )
                    progress_bar.progress(50)
                    status_text.text(f"✅ 已生成 {result['num_generated']} 张素材")
                    st.session_state.generated_images = result['generated_files']
                    st.session_state.confidence_stats = result.get('confidence_statistics', {})

                    if auto_analyze:
                        status_text.text("步骤2/2: 正在分析生成的素材...")
                        analysis_result = st.session_state.agent.analyze_and_evaluate(
                            result['generated_files']
                        )
                        st.session_state.analysis_results = analysis_result
                        progress_bar.progress(100)
                        status_text.text("✅ 分析完成！")
                    else:
                        progress_bar.progress(100)
                        status_text.text("✅ 生成完成！")

                    st.success(f"✅ 成功生成 {result['num_generated']} 张多角度素材！")
                    if save_enabled:
                        st.info(f"💾 素材已保存至: {output_dir}")
                except Exception as e:
                    st.error(f"❌ 处理出错: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # 显示生成结果和分析
    if st.session_state.generated_images:
        st.markdown("---")
        st.subheader("🎨 生成的多角度素材（带检测框）")
        num_cols = 4
        images = st.session_state.generated_images
        for i in range(0, len(images), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(images):
                    img_path = Path(images[i + j])
                    if img_path.exists():
                        col.image(Image.open(img_path), caption=img_path.name, use_column_width=True)

        # 显示置信度统计
        if st.session_state.confidence_stats:
            st.markdown("---")
            st.subheader("📊 各类别平均置信度统计")
            
            confidence_data = []
            for class_name, stats in st.session_state.confidence_stats.items():
                confidence_data.append({
                    '类别': class_name,
                    '检测数量': stats['count'],
                    '平均置信度': f"{stats['avg_confidence']*100:.2f}%",
                    '最高置信度': f"{stats['max_confidence']*100:.2f}%",
                    '最低置信度': f"{stats['min_confidence']*100:.2f}%"
                })
            
            if confidence_data:
                df_confidence = pd.DataFrame(confidence_data)
                st.dataframe(df_confidence, use_container_width=True, hide_index=True)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[item['类别'] for item in confidence_data],
                    y=[float(item['平均置信度'].rstrip('%')) for item in confidence_data],
                    text=[item['平均置信度'] for item in confidence_data],
                    textposition='auto',
                    marker=dict(
                        color=[float(item['平均置信度'].rstrip('%')) for item in confidence_data],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="置信度 (%)")
                    )
                ))
                fig.update_layout(
                    title="各类别平均置信度对比",
                    xaxis_title="类别",
                    yaxis_title="平均置信度 (%)",
                    height=500,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)

    # 显示8维度分析结果
    if st.session_state.analysis_results:
        st.markdown("---")
        st.subheader("📊 8维度雷达图分析")
        avg_scores = st.session_state.analysis_results['analysis']['average_scores']
        overall_quality = st.session_state.analysis_results['recommendations']['overall_quality']
        
        # 判断是否需要增强训练
        needs_enhancement = overall_quality < 50.0  # VisDrone数据集标准降低
        
        fig = go.Figure()
        dimensions = [
            "图片数据量","拍摄光照质量","目标尺寸","目标完整性",
            "数据均衡度","产品丰富度","目标密集度","场景复杂度"
        ]
        values = [avg_scores.get(dim,0) for dim in dimensions]
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=dimensions + [dimensions[0]],
            fill='toself',
            name='维度得分',
            line=dict(color='rgb(31,119,180)', width=3),
            fillcolor='rgba(31,119,180,0.25)'
        ))
        avg_score = np.mean(values)
        fig.add_trace(go.Scatterpolar(
            r=[avg_score]*(len(dimensions)+1),
            theta=dimensions + [dimensions[0]],
            name=f'平均线 ({avg_score:.1f}%)',
            line=dict(color='rgb(255,127,14)', width=2, dash='dash')
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0,100]),
                angularaxis=dict(rotation=90, direction='counterclockwise')
            ),
            showlegend=True,
            title="8维度质量分析雷达图",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown("#### 📈 维度得分详情")
            score_df = pd.DataFrame([
                {"维度": dim, "得分": f"{score:.2f}%", "等级": "优秀 ⭐⭐⭐" if score>=90 else "良好 ⭐⭐" if score>=80 else "中等 ⭐" if score>=70 else "一般" if score>=60 else "较差"}
                for dim, score in avg_scores.items()
            ])
            st.dataframe(score_df, use_container_width=True, hide_index=True)
            
            # 增强训练提示
            if needs_enhancement and enable_enhancement:
                st.warning(f"⚠️ **素材质量较差（{overall_quality:.2f}%），建议进行增强训练**")
                if st.button("🎯 开始增强训练", type="primary", use_container_width=True):
                    with st.spinner("正在进行增强训练，请稍候..."):
                        try:
                            # 确定增强输出目录
                            if save_enabled and save_folder:
                                base_dir = Path(save_folder)
                                base_dir.mkdir(parents=True, exist_ok=True)
                                enhancement_dir = base_dir / f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            else:
                                enhancement_dir = Path("enhanced_materials") / f"enhancement_{int(time.time())}"
                            
                            enhancement_dir.mkdir(parents=True, exist_ok=True)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # 批量增强
                            status_text.text("正在对质量较差的素材进行增强训练...")
                            enhancement_result = st.session_state.enhancement_trainer.enhance_batch_to_excellent(
                                image_paths=st.session_state.generated_images,
                                output_dir=str(enhancement_dir),
                                target_improvement=target_improvement,
                                max_iterations=max_iterations
                            )
                            
                            st.session_state.enhancement_results = enhancement_result
                            progress_bar.progress(100)
                            status_text.text("✅ 增强训练完成！")
                            
                            # 显示增强结果
                            st.success(f"✅ 增强训练完成！")
                            st.info(f"📊 成功率: {enhancement_result['success_rate']:.2f}% | 达标率: {enhancement_result['achievement_rate']:.2f}%")
                            st.info(f"📈 平均提升幅度: {enhancement_result.get('average_improvement', 0):.2f}分")
                            st.info(f"⭐ 优秀({enhancement_result.get('excellent_count', 0)}) | 良好({enhancement_result.get('good_count', 0)}) | 一般({enhancement_result.get('fair_count', 0)}) | 较差({enhancement_result.get('poor_count', 0)})")
                            
                            if save_enabled:
                                st.info(f"💾 增强素材已保存至: {enhancement_dir}")
                        except Exception as e:
                            st.error(f"❌ 增强训练出错: {e}")
                            import traceback
                            st.code(traceback.format_exc())
            
            # 数据表现分析
            st.markdown("#### 🔍 数据表现客观分析")
            low_score_dims = [dim for dim, score in avg_scores.items() if score < 60 and dim != "场景复杂度"]
            if low_score_dims:
                st.warning("**以下维度得分较低，可能原因：**")
                analysis_text = {
                    "图片数据量": "• 图片分辨率可能较低（<1920x1080）\n• 文件大小可能较小（<2MB）\n• 建议：使用更高分辨率相机拍摄",
                    "拍摄光照质量": "• 光照条件可能不理想（过暗/过亮）\n• 对比度可能不足\n• 可能存在过曝或欠曝区域\n• 建议：在光线充足、均匀的环境下拍摄",
                    "目标尺寸": "• 检测到的目标在画面中占比可能过小（<5%）\n• 拍摄距离可能过远\n• 建议：调整拍摄角度和距离，使目标占比在5-15%",
                    "目标完整性": "• 目标可能被裁剪或部分遮挡\n• 目标可能靠近画面边缘\n• 检测置信度可能较低\n• 建议：确保目标完整出现在画面中央",
                    "数据均衡度": "• 不同类别目标分布可能不均衡\n• 某些类别目标数量过多或过少\n• 建议：增加不同类别目标的多样性",
                    "产品丰富度": "• 检测到的目标类别数量可能较少（<5类）\n• 场景中目标类型单一\n• 建议：在同一场景中包含5-10个不同类别的目标",
                    "目标密集度": "• 单位面积内的目标数量可能过少（<5个/百万像素）\n• 场景可能过于空旷\n• 建议：增加场景中的目标密度"
                }
                for dim in low_score_dims:
                    st.markdown(f"**{dim}** ({avg_scores[dim]:.2f}%):")
                    st.markdown(analysis_text.get(dim, "暂无具体分析"))
            else:
                st.success("✅ 所有维度得分均在合理范围内")
        with col2:
            st.markdown("#### 📊 统计信息")
            st.metric("整体质量", f"{overall_quality:.2f}%")
            st.metric("生成素材数", len(st.session_state.generated_images))
            st.metric("分析素材数", st.session_state.analysis_results['analysis']['total_images'])
            
            if needs_enhancement:
                st.warning("⚠️ 质量较差")
            elif overall_quality >= 90:
                st.success("✅ 优秀")
            elif overall_quality >= 80:
                st.info("✅ 良好")
            elif overall_quality >= 70:
                st.info("✅ 中等")
            else:
                st.info("✅ 一般")

        # 显示增强训练结果
        if st.session_state.enhancement_results:
            st.markdown("---")
            st.subheader("🎯 增强训练结果")
            
            enhancement_result = st.session_state.enhancement_results
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总素材数", enhancement_result['total_images'])
            with col2:
                st.metric("成功增强", enhancement_result['successful'])
            with col3:
                st.metric("达到目标", enhancement_result['target_achieved'])
            with col4:
                st.metric("成功率", f"{enhancement_result['success_rate']:.2f}%")
            
            # 显示增强历史
            st.markdown("#### 📈 增强历史记录")
            enhancement_history_data = []
            for result in enhancement_result['results']:
                if result.get('success', False):
                    enhancement_history_data.append({
                        '素材': Path(result.get('original_path', '')).name,
                        '初始分数': f"{result.get('initial_score', 0):.2f}%",
                        '最终分数': f"{result.get('final_score', 0):.2f}%",
                        '提升幅度': f"+{result.get('improvement', 0):.2f}分",
                        '迭代次数': result.get('iterations', 0),
                        '质量等级': result.get('quality_level', 'N/A'),
                    })
            
            if enhancement_history_data:
                st.dataframe(pd.DataFrame(enhancement_history_data), use_container_width=True, hide_index=True)
                
                # 绘制提升幅度图表
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[item['素材'] for item in enhancement_history_data],
                    y=[float(item['提升幅度'].lstrip('+').rstrip('分')) for item in enhancement_history_data],
                    text=[item['提升幅度'] for item in enhancement_history_data],
                    textposition='auto',
                    marker=dict(color='green')
                ))
                fig.update_layout(
                    title="素材质量提升幅度",
                    xaxis_title="素材",
                    yaxis_title="提升幅度 (分)",
                    height=400,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 📋 素材质量评估")
        quality_data = []
        for item in st.session_state.analysis_results['quality_evaluation']:
            quality_data.append({
                "素材": Path(item['image_path']).name,
                "平均得分": f"{item['average_score']:.2f}%",
                "质量等级": item['quality_level']
            })
        st.dataframe(pd.DataFrame(quality_data), use_container_width=True, hide_index=True)


