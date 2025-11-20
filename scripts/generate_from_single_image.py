"""
从单张图片生成多角度素材并分析
Generate Multi-Angle Materials from Single Image and Analyze
"""

import argparse
import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from agents.image_multi_angle_generator import ImageMultiAngleGenerator
from agents.image_quality_analyzer import ImageQualityAnalyzer
from agents.material_generator_agent import MaterialGeneratorAgent


def main():
    parser = argparse.ArgumentParser(description="从单张图片生成多角度素材并分析")
    parser.add_argument("--input-image", type=str, required=True, help="输入图片路径")
    parser.add_argument("--output-dir", type=str, default="generated_materials", help="输出目录")
    parser.add_argument("--num-generations", type=int, default=8, help="生成图片数量")
    parser.add_argument("--analyze", action="store_true", help="生成后自动分析")
    parser.add_argument("--yolo-model", type=str, default=None, help="YOLO模型路径（可选）")
    args = parser.parse_args()

    input_path = Path(args.input_image)
    if not input_path.exists():
        print(f"❌ 输入图片不存在: {args.input_image}")
        return

    print("=" * 60)
    print("从单张图片生成多角度素材")
    print("=" * 60)
    print(f"输入图片: {args.input_image}")
    print(f"输出目录: {args.output_dir}")
    print(f"生成数量: {args.num_generations}")
    print("=" * 60)

    print("\n步骤1: 生成多角度图片...")
    generator = ImageMultiAngleGenerator()
    try:
        result = generator.generate_multi_angle_images(
            input_image_path=str(input_path),
            output_dir=args.output_dir,
            num_generations=args.num_generations
        )
        if result['success']:
            print(f"✅ 成功生成 {result['num_generated']} 张图片")
            print(f"输出目录: {result['output_dir']}")
        else:
            print("❌ 生成失败")
            return
    except Exception as e:
        print(f"❌ 生成过程出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤2: 分析生成的图片（如果启用）
    if args.analyze:
        print("\n步骤2: 分析生成的图片...")
        analyzer = ImageQualityAnalyzer(yolo_model_path=args.yolo_model)
        agent = MaterialGeneratorAgent(yolo_model_path=args.yolo_model)
        try:
            # 分析所有生成的图片
            analysis_result = agent.analyze_and_evaluate(result['generated_files'])
            
            # 保存分析结果
            analysis_file = Path(args.output_dir) / f"analysis_result_{Path(result['metadata_file']).stem.split('_')[-1]}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 分析完成，结果保存到: {analysis_file}")
            print(f"平均质量: {analysis_result['recommendations']['overall_quality']:.2f}%")
            
        except Exception as e:
            print(f"⚠️ 分析过程出错: {e}")
            import traceback
            traceback.print_exc()

    print("\n✅ 处理完成！")


if __name__ == "__main__":
    main()



