"""
无人机素材批量生成器
Drone Material Batch Generator
基于8维度分析结果，自动批量生成和筛选高质量无人机视觉素材
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import shutil
from agents.image_quality_analyzer import ImageQualityAnalyzer
from agents.material_generator_agent import MaterialGeneratorAgent


class MaterialBatchGenerator:
    """无人机素材批量生成器"""
    
    def __init__(self, yolo_model_path: Optional[str] = None):
        """
        初始化批量生成器
        
        参数:
            yolo_model_path: YOLO模型路径
        """
        self.analyzer = ImageQualityAnalyzer(yolo_model_path)
        self.agent = MaterialGeneratorAgent(yolo_model_path)
        self.quality_threshold = 75.0  # 默认质量阈值
        
    def generate_high_quality_materials(
        self,
        source_dir: str,
        output_dir: str,
        min_quality: float = 75.0,
        max_count: Optional[int] = None,
        dimension_weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        从源目录批量生成高质量素材
        
        参数:
            source_dir: 源图片目录
            output_dir: 输出目录
            min_quality: 最低质量分数
            max_count: 最大生成数量（None表示不限制）
            dimension_weights: 维度权重（用于自定义评分）
            
        返回:
            生成结果字典
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_paths = [
            str(p) for p in source_path.rglob('*')
            if p.suffix.lower() in image_extensions
        ]
        
        if not image_paths:
            return {
                'success': False,
                'message': f'在 {source_dir} 中未找到图片文件',
                'total_images': 0,
                'generated_count': 0
            }
        
        print(f"📸 找到 {len(image_paths)} 张图片，开始分析...")
        
        # 批量分析
        analysis_result = self.agent.analyze_and_evaluate(image_paths)
        
        # 筛选高质量素材
        quality_scores = analysis_result['quality_evaluation']
        
        # 应用自定义权重（如果有）
        if dimension_weights:
            for item in quality_scores:
                weighted_score = sum(
                    item['dimension_scores'].get(dim, 0) * weight
                    for dim, weight in dimension_weights.items()
                ) / sum(dimension_weights.values())
                item['weighted_score'] = weighted_score
                item['average_score'] = weighted_score
        
        # 按质量排序
        quality_scores.sort(key=lambda x: x['average_score'], reverse=True)
        
        # 筛选并复制高质量素材
        high_quality = [
            q for q in quality_scores
            if q['average_score'] >= min_quality
        ]
        
        if max_count:
            high_quality = high_quality[:max_count]
        
        # 复制文件到输出目录
        generated_files = []
        metadata = []
        
        for idx, item in enumerate(high_quality, 1):
            src_path = Path(item['image_path'])
            dst_path = output_path / f"high_quality_{idx:04d}_{src_path.name}"
            
            try:
                shutil.copy2(src_path, dst_path)
                generated_files.append(str(dst_path))
                
                metadata.append({
                    'index': idx,
                    'original_path': str(src_path),
                    'generated_path': str(dst_path),
                    'quality_score': item['average_score'],
                    'quality_level': item['quality_level'],
                    'dimension_scores': item['dimension_scores']
                })
                
                print(f"✅ [{idx}/{len(high_quality)}] {src_path.name} (质量: {item['average_score']:.2f}%)")
            except Exception as e:
                print(f"❌ 复制失败 {src_path.name}: {e}")
        
        # 保存元数据
        metadata_file = output_path / f"material_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generation_time': datetime.now().isoformat(),
                'source_dir': str(source_path),
                'output_dir': str(output_path),
                'min_quality': min_quality,
                'total_analyzed': len(image_paths),
                'generated_count': len(generated_files),
                'materials': metadata
            }, f, ensure_ascii=False, indent=2)
        
        # 生成统计报告
        stats = self._generate_statistics(metadata, analysis_result)
        stats_file = output_path / f"generation_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return {
            'success': True,
            'total_images': len(image_paths),
            'generated_count': len(generated_files),
            'output_dir': str(output_path),
            'metadata_file': str(metadata_file),
            'statistics_file': str(stats_file),
            'generated_files': generated_files
        }
    
    def _generate_statistics(self, metadata: List[Dict], analysis_result: Dict) -> Dict:
        """生成统计信息"""
        if not metadata:
            return {}
        
        scores = [m['quality_score'] for m in metadata]
        dimension_scores = {}
        
        for dim in self.analyzer.dimensions:
            dim_scores = [m['dimension_scores'].get(dim, 0) for m in metadata]
            dimension_scores[dim] = {
                'mean': float(np.mean(dim_scores)),
                'std': float(np.std(dim_scores)),
                'min': float(np.min(dim_scores)),
                'max': float(np.max(dim_scores))
            }
        
        return {
            'total_materials': len(metadata),
            'quality_statistics': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores))
            },
            'dimension_statistics': dimension_scores,
            'quality_distribution': {
                'excellent (>=90)': sum(1 for s in scores if s >= 90),
                'good (80-89)': sum(1 for s in scores if 80 <= s < 90),
                'medium (70-79)': sum(1 for s in scores if 70 <= s < 80),
                'fair (60-69)': sum(1 for s in scores if 60 <= s < 70)
            }
        }
    
    def generate_material_report(self, output_dir: str) -> str:
        """
        生成素材报告
        
        参数:
            output_dir: 输出目录
            
        返回:
            报告文件路径
        """
        output_path = Path(output_dir)
        metadata_files = list(output_path.glob("material_metadata_*.json"))
        
        if not metadata_files:
            raise ValueError(f"在 {output_dir} 中未找到素材元数据文件")
        
        # 读取最新的元数据
        latest_metadata = max(metadata_files, key=lambda p: p.stat().st_mtime)
        with open(latest_metadata, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 生成Markdown报告
        report_content = f"""# 无人机素材批量生成报告

## 生成信息
- **生成时间**: {data['generation_time']}
- **源目录**: {data['source_dir']}
- **输出目录**: {data['output_dir']}
- **最低质量要求**: {data['min_quality']}%

## 统计信息
- **分析图片总数**: {data['total_analyzed']}
- **生成高质量素材数**: {data['generated_count']}
- **生成率**: {data['generated_count'] / data['total_analyzed'] * 100:.2f}%

## 素材列表

| 序号 | 文件名 | 质量分数 | 质量等级 | 主要优势维度 |
|------|--------|----------|----------|--------------|
"""
        
        for material in data['materials']:
            # 找出得分最高的3个维度
            dim_scores = material['dimension_scores']
            top_dims = sorted(dim_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_dims_str = ', '.join([f"{dim}({score:.1f}%)" for dim, score in top_dims])
            
            filename = Path(material['generated_path']).name
            report_content += f"| {material['index']} | {filename} | {material['quality_score']:.2f}% | {material['quality_level']} | {top_dims_str} |\n"
        
        report_content += f"""
## 详细维度分析

"""
        
        # 读取统计文件
        stats_files = list(output_path.glob("generation_statistics_*.json"))
        if stats_files:
            latest_stats = max(stats_files, key=lambda p: p.stat().st_mtime)
            with open(latest_stats, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            report_content += f"""
### 质量分布
- 优秀 (>=90%): {stats['quality_distribution']['excellent (>=90)']} 张
- 良好 (80-89%): {stats['quality_distribution']['good (80-89)']} 张
- 中等 (70-79%): {stats['quality_distribution']['medium (70-79)']} 张
- 一般 (60-69%): {stats['quality_distribution']['fair (60-69)']} 张

### 平均维度得分
"""
            for dim, stat in stats['dimension_statistics'].items():
                report_content += f"- **{dim}**: {stat['mean']:.2f}% (范围: {stat['min']:.1f}% - {stat['max']:.1f}%)\n"
        
        # 保存报告
        report_file = output_path / f"material_generation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_file)


if __name__ == "__main__":
    # 测试代码
    generator = MaterialBatchGenerator()
    
    result = generator.generate_high_quality_materials(
        source_dir="test_images",
        output_dir="generated_materials",
        min_quality=75.0,
        max_count=10
    )
    
    print("\n生成结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))




