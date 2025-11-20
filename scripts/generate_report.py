"""
生成分析报告脚本
Generate Analysis Report Script
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


def generate_excel_report(json_file: str, output_file: str):
    """从JSON结果生成Excel报告"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: 总体统计
        summary_data = {
            '指标': [
                '总图片数',
                '总标注数',
                '整体质量',
                '高质量图片数',
                '需要改进的维度数'
            ],
            '数值': [
                data['analysis']['total_images'],
                data['analysis']['total_annotations'],
                f"{data['recommendations']['overall_quality']:.2f}",
                len(data['recommendations']['high_quality_images']),
                len(data['recommendations']['needs_improvement'])
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='总体统计', index=False)
        
        # Sheet 2: 平均维度得分
        dimension_data = {
            '维度': list(data['analysis']['average_scores'].keys()),
            '平均得分': list(data['analysis']['average_scores'].values())
        }
        df_dimensions = pd.DataFrame(dimension_data)
        df_dimensions.to_excel(writer, sheet_name='平均维度得分', index=False)
        
        # Sheet 3: 图片质量评估
        quality_data = []
        for item in data['quality_evaluation']:
            quality_data.append({
                '图片路径': item['image_path'],
                '平均得分': item['average_score'],
                '质量等级': item['quality_level'],
                **item['dimension_scores']
            })
        df_quality = pd.DataFrame(quality_data)
        df_quality.to_excel(writer, sheet_name='图片质量评估', index=False)
        
        # Sheet 4: 改进建议
        if data['recommendations']['improvement_suggestions']:
            improvement_data = {
                '维度': list(data['recommendations']['improvement_suggestions'].keys()),
                '改进建议': list(data['recommendations']['improvement_suggestions'].values())
            }
            df_improvement = pd.DataFrame(improvement_data)
            df_improvement.to_excel(writer, sheet_name='改进建议', index=False)
    
    print(f"✅ Excel报告已生成: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="生成分析报告")
    parser.add_argument(
        "--json-file",
        type=str,
        required=True,
        help="JSON分析结果文件"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出Excel文件路径 (默认: 与JSON同目录)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=['excel', 'csv'],
        default='excel',
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    json_file = Path(args.json_file)
    if not json_file.exists():
        print(f"❌ 文件不存在: {json_file}")
        return
    
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = json_file.parent / f"{json_file.stem}_report.xlsx"
    
    if args.format == 'excel':
        try:
            generate_excel_report(str(json_file), str(output_file))
        except ImportError:
            print("❌ 需要安装 openpyxl: pip install openpyxl")
    else:
        # CSV格式
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 生成CSV
        quality_data = []
        for item in data['quality_evaluation']:
            quality_data.append({
                '图片路径': item['image_path'],
                '平均得分': item['average_score'],
                '质量等级': item['quality_level'],
                **item['dimension_scores']
            })
        df = pd.DataFrame(quality_data)
        csv_file = output_file.with_suffix('.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ CSV报告已生成: {csv_file}")


if __name__ == "__main__":
    main()




