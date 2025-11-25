"""
准备测试图片用于标注
Prepare test images for annotation
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

def create_test_images(output_dir, num_images=5):
    """创建测试图片"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"正在创建 {num_images} 张测试图片...")
    
    for i in range(num_images):
        # 创建随机图片
        width, height = 800, 600
        img = Image.new('RGB', (width, height), color=(73, 109, 137))
        
        # 绘制一些简单的形状（模拟目标对象）
        draw = ImageDraw.Draw(img)
        
        # 绘制矩形（模拟汽车、人等）
        for j in range(3):
            x1 = np.random.randint(50, width-150)
            y1 = np.random.randint(50, height-150)
            x2 = x1 + np.random.randint(50, 150)
            y2 = y1 + np.random.randint(50, 150)
             
            color = (
                np.random.randint(0, 255),
                np.random.randint(0, 255),
                np.random.randint(0, 255)
            )
            draw.rectangle([x1, y1, x2, y2], fill=color, outline=(255, 255, 255), width=2)
        
        # 保存图片
        img_path = os.path.join(output_dir, f"test_image_{i+1:03d}.jpg")
        img.save(img_path, 'JPEG', quality=85)
        print(f"  ✓ 创建: {img_path}")
    
    print(f"\n测试图片创建完成！共 {num_images} 张")
    print(f"图片保存在: {output_dir}")

if __name__ == "__main__":
    # 创建测试图片
    images_dir = Path("data/raw/images")
    if not images_dir.exists():
        images_dir.mkdir(parents=True, exist_ok=True)
    
    create_test_images(str(images_dir), num_images=5)
