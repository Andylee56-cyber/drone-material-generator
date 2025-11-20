"""
批量生成高质量无人机素材脚本
Batch Generate High-Quality Drone Materials Script
"""

import argparse
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from agents.material_batch_generator import MaterialBatchGenerator


def main():
    parser = argparse.ArgumentParser(description="批量生成高质量无人机素材")
    parser.add_argument(
        "--source-dir",
        type=str,
        required=True,
        help="源图片目录（包含待筛选的无人机图片）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="输出目录（生成的高质量素材将保存到这里）"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=75.0,
        help="最低质量分数阈值 (默认: 75.0)"
    )
    parser.add_argument(
        "--max-count",
        type=int,
        default=None,
        help="最大生成数量 (默认: 不限制)"
    )
    parser.add_argument(
        "--yolo-model",
        type=str,
        default=None,
        help="YOLO模型路径 (可选)"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="生成Markdown格式的报告"
    )
    
    args = parser.parse_args()
    
    # 检查源目录
    source_path = Path(args.source_dir)
    if not source_path.exists():
        print(f"❌ 源目录不存在: {args.source_dir}")
        return
    
    # 创建输出目录
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("无人机素材批量生成器")
    print("=" * 60)
    print(f"源目录: {args.source_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"最低质量: {args.min_quality}%")
    if args.max_count:
        print(f"最大数量: {args.max_count}")
    print("=" * 60)
    
    # 初始化生成器
    generator = MaterialBatchGenerator(yolo_model_path=args.yolo_model)
    
    # 执行生成
    try:
        result = generator.generate_high_quality_materials(
            source_dir=str(source_path),
            output_dir=str(output_path),
            min_quality=args.min_quality,
            max_count=args.max_count
        )
        
        if result['success']:
            print("\n" + "=" * 60)
            print("✅ 素材生成完成！")
            print("=" * 60)
            print(f"分析图片总数: {result['total_images']}")
            print(f"生成高质量素材: {result['generated_count']} 张")
            print(f"生成率: {result['generated_count'] / result['total_images'] * 100:.2f}%")
            print(f"\n输出目录: {result['output_dir']}")
            print(f"元数据文件: {result['metadata_file']}")
            print(f"统计文件: {result['statistics_file']}")
            
            # 生成报告
            if args.generate_report:
                print("\n正在生成报告...")
                report_file = generator.generate_material_report(str(output_path))
                print(f"✅ 报告已生成: {report_file}")
        else:
            print(f"\n❌ 生成失败: {result.get('message', '未知错误')}")
            
    except Exception as e:
        print(f"\n❌ 生成过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()




