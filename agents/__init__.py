"""
Agents包 - 无人机视觉智能Agent系统
"""

# 延迟导入，避免在模块级别失败
try:
    from agents.image_multi_angle_generator import ImageMultiAngleGenerator
except Exception as e:
    ImageMultiAngleGenerator = None
    _import_error = str(e)

try:
    from agents.image_quality_analyzer import ImageQualityAnalyzer
except Exception as e:
    ImageQualityAnalyzer = None

try:
    from agents.material_generator_agent import MaterialGeneratorAgent
except Exception as e:
    MaterialGeneratorAgent = None

try:
    from agents.material_enhancement_trainer import MaterialEnhancementTrainer
except Exception as e:
    MaterialEnhancementTrainer = None

__all__ = [
    'ImageMultiAngleGenerator',
    'ImageQualityAnalyzer',
    'MaterialGeneratorAgent',
    'MaterialEnhancementTrainer'
]
