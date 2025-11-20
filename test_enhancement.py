"""
测试素材增强训练功能
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from agents.material_enhancement_trainer import MaterialEnhancementTrainer

# 初始化训练器
trainer = MaterialEnhancementTrainer()

# 测试单张图片增强（需要替换为实际图片路径）
test_image = "test_images/test_input.jpg"
if Path(test_image).exists():
    print(f"开始增强测试: {test_image}")
    result = trainer.enhance_to_excellent(
        test_image,
        "test_enhanced_output",
        target_score=90.0,
        max_iterations=5
    )
    print(f"\n增强结果:")
    print(f"  成功: {result['success']}")
    print(f"  达到目标: {result['target_achieved']}")
    print(f"  最终分数: {result['final_score']:.2f}%")
    print(f"  迭代次数: {result['iterations']}")
    print(f"  提升幅度: +{result['improvement']:.2f}%")
    print(f"  输出路径: {result['final_image_path']}")
else:
    print(f"测试图片不存在: {test_image}")
    print("请先准备测试图片")
