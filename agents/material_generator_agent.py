"""
无人机素材生成Agent
Drone Material Generator Agent
基于8维度分析结果，智能生成和推荐无人机素材
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from agents.image_quality_analyzer import ImageQualityAnalyzer


class MaterialGeneratorAgent:
    """无人机素材生成Agent"""
    
    def __init__(self, yolo_model_path: Optional[str] = None):
        """
        初始化素材生成Agent
        
        参数:
            yolo_model_path: YOLO模型路径
        """
        self.analyzer = ImageQualityAnalyzer(yolo_model_path)
        self.material_database = []  # 素材数据库
        self.quality_threshold = 70.0  # 质量阈值
        
    def analyze_and_evaluate(self, image_paths: List[str]) -> Dict:
        """
        分析图片并评估质量
        
        参数:
            image_paths: 图片路径列表
            
        返回:
            分析结果和质量评估
        """
        # 批量分析
        analysis_results = self.analyzer.analyze_batch(image_paths)
        
        # 评估每张图片的综合质量
        quality_scores = []
        for result in analysis_results['individual_results']:
            scores = [result[dim] for dim in self.analyzer.dimensions]
            avg_score = np.mean(scores)
            quality_scores.append({
                'image_path': result['image_path'],
                'average_score': avg_score,
                'dimension_scores': {dim: result[dim] for dim in self.analyzer.dimensions},
                'quality_level': self._get_quality_level(avg_score)
            })
        
        # 按质量排序
        quality_scores.sort(key=lambda x: x['average_score'], reverse=True)
        
        return {
            'analysis': analysis_results,
            'quality_evaluation': quality_scores,
            'recommendations': self._generate_recommendations(quality_scores)
        }
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "一般"
        else:
            return "较差"
    
    def _generate_recommendations(self, quality_scores: List[Dict]) -> Dict:
        """生成素材推荐建议"""
        if not quality_scores:
            return {}
        
        # 统计各维度平均分
        avg_dimensions = {}
        for dim in self.analyzer.dimensions:
            scores = [q['dimension_scores'][dim] for q in quality_scores]
            avg_dimensions[dim] = np.mean(scores)
        
        # 找出需要改进的维度
        weak_dimensions = [
            dim for dim, score in avg_dimensions.items() 
            if score < self.quality_threshold
        ]
        
        # 生成改进建议
        recommendations = {
            'high_quality_images': [
                q['image_path'] for q in quality_scores[:5] 
                if q['average_score'] >= self.quality_threshold
            ],
            'needs_improvement': weak_dimensions,
            'improvement_suggestions': self._get_improvement_suggestions(weak_dimensions),
            'overall_quality': np.mean([q['average_score'] for q in quality_scores])
        }
        
        return recommendations
    
    def _get_improvement_suggestions(self, weak_dimensions: List[str]) -> Dict[str, str]:
        """获取改进建议"""
        suggestions = {
            "图片数据量": "建议使用更高分辨率的相机拍摄，确保图片文件大小在2MB以上",
            "拍摄光照质量": "建议在光线充足的环境下拍摄，避免过曝或欠曝，保持良好对比度",
            "目标尺寸": "建议调整拍摄角度和距离，使目标在画面中占比5-15%",
            "目标完整性": "确保目标完整出现在画面中，避免被裁剪或遮挡",
            "数据均衡度": "建议增加不同类别目标的多样性，保持类别分布均衡",
            "产品丰富度": "建议在同一场景中包含5-10个不同类别的目标",
            "目标密集度": "建议每百万像素包含5-15个目标，避免过于稀疏或密集",
            "场景复杂度": "建议在纹理丰富、细节清晰的场景下拍摄"
        }
        
        return {dim: suggestions.get(dim, "暂无具体建议") for dim in weak_dimensions}
    
    def generate_material_report(self, analysis_result: Dict, output_path: str) -> str:
        """
        生成素材分析报告
        
        参数:
            analysis_result: 分析结果
            output_path: 输出路径
            
        返回:
            报告文件路径
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_images': analysis_result['analysis']['total_images'],
            'total_annotations': analysis_result['analysis']['total_annotations'],
            'average_dimension_scores': analysis_result['analysis']['average_scores'],
            'quality_evaluation': analysis_result['quality_evaluation'],
            'recommendations': analysis_result['recommendations']
        }
        
        # 保存JSON报告
        report_path = Path(output_path) / f"material_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return str(report_path)
    
    def filter_high_quality_materials(self, image_paths: List[str], 
                                      min_score: float = 70.0) -> List[str]:
        """
        筛选高质量素材
        
        参数:
            image_paths: 图片路径列表
            min_score: 最低质量分数
            
        返回:
            高质量图片路径列表
        """
        results = self.analyze_and_evaluate(image_paths)
        high_quality = [
            q['image_path'] for q in results['quality_evaluation']
            if q['average_score'] >= min_score
        ]
        return high_quality


if __name__ == "__main__":
    # 测试代码
    agent = MaterialGeneratorAgent()
    test_images = ["test1.jpg", "test2.jpg"]  # 替换为实际图片路径
    
    if all(Path(img).exists() for img in test_images):
        result = agent.analyze_and_evaluate(test_images)
        print("素材分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))




