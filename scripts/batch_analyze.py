"""
批量图片分析脚本
Batch Image Analysis Script
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from agents.material_generator_agent import MaterialGeneratorAgent


def main():
    parser = argparse.ArgumentParser(description="批量分析无人机图片素材")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="输入图片目录"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="输出结果目录"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=70.0,
        help="最低质量分数阈值 (默认: 70.0)"
    )
    parser.add_argument(
        "--yolo-model",
        type=str,
        default=None,
        help="YOLO模型路径 (可选)"
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有图片
    input_dir = Path(args.input_dir)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    image_paths = [
        str(p) for p in input_dir.rglob('*')
        if p.suffix.lower() in image_extensions
    ]
    
    if not image_paths:
        print(f"❌ 在 {input_dir} 中未找到图片文件")
        return
    
    print(f"📸 找到 {len(image_paths)} 张图片")
    print("🚀 开始批量分析...")
    
    # 初始化Agent
    agent = MaterialGeneratorAgent(yolo_model_path=args.yolo_model)
    
    # 执行分析
    result = agent.analyze_and_evaluate(image_paths)
    
    # 保存完整结果
    result_file = output_dir / f"analysis_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 完整结果已保存到: {result_file}")
    
    # 筛选高质量素材
    high_quality = agent.filter_high_quality_materials(image_paths, args.min_quality)
    
    # 保存高质量素材列表
    high_quality_file = output_dir / f"high_quality_materials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(high_quality_file, 'w', encoding='utf-8') as f:
        for path in high_quality:
            f.write(f"{path}\n")
    print(f"✅ 高质量素材列表已保存到: {high_quality_file}")
    print(f"📊 高质量素材数量: {len(high_quality)} / {len(image_paths)}")
    
    # 生成报告
    report_path = agent.generate_material_report(result, str(output_dir))
    print(f"✅ 详细报告已保存到: {report_path}")
    
    # 打印统计信息
    print("\n📈 统计信息:")
    print(f"  总图片数: {result['analysis']['total_images']}")
    print(f"  总标注数: {result['analysis']['total_annotations']}")
    print(f"  整体质量: {result['recommendations']['overall_quality']:.2f}")
    print(f"  高质量图片: {len(high_quality)}")
    
    # 打印平均维度得分
    print("\n📊 平均维度得分:")
    for dim, score in result['analysis']['average_scores'].items():
        print(f"  {dim}: {score:.2f}%")
    
    # 打印改进建议
    if result['recommendations']['needs_improvement']:
        print("\n💡 需要改进的维度:")
        for dim in result['recommendations']['needs_improvement']:
            suggestion = result['recommendations']['improvement_suggestions'].get(dim, "暂无建议")
            print(f"  - {dim}: {suggestion}")


if __name__ == "__main__":
    main()




