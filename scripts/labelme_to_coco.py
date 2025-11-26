"""
自定义 LabelMe 转 COCO 格式转换脚本
不依赖 labelme2coco 包，直接使用 Python 实现
"""
import json
import argparse
from pathlib import Path
from typing import Dict, List
import base64
import io
from PIL import Image


def load_labelme_json(json_path: Path) -> Dict:
    """加载 LabelMe JSON 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_labelme_to_coco(input_dir: Path, output_json: Path):
    """
    将 LabelMe 格式转换为 COCO 格式
    
    Args:
        input_dir: 包含 LabelMe JSON 文件的目录（递归搜索）
        output_json: 输出的 COCO JSON 文件路径
    """
    # 收集所有 JSON 文件
    json_files = list(input_dir.rglob('*.json'))
    
    if len(json_files) == 0:
        print(f"Error: No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files")
    
    # 初始化 COCO 数据结构
    coco_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }
    
    # 收集所有类别
    all_categories = set()
    for json_file in json_files:
        labelme_data = load_labelme_json(json_file)
        for shape in labelme_data.get('shapes', []):
            label = shape.get('label', '')
            if label:
                all_categories.add(label)
    
    # 创建类别映射
    categories = sorted(list(all_categories))
    category_id_map = {cat: idx + 1 for idx, cat in enumerate(categories)}
    
    # 添加类别到 COCO 数据
    for cat_name, cat_id in category_id_map.items():
        coco_data["categories"].append({
            "id": cat_id,
            "name": cat_name,
            "supercategory": "none"
        })
    
    print(f"Found {len(categories)} categories: {categories}")
    
    # 处理每个 JSON 文件
    image_id = 1
    annotation_id = 1
    
    for json_file in json_files:
        try:
            labelme_data = load_labelme_json(json_file)
            
            # 获取图像信息
            image_path = json_file.parent / labelme_data.get('imagePath', '')
            if not image_path.exists():
                # 尝试查找同名图像文件（不同扩展名）
                stem = json_file.stem
                for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    candidate = json_file.parent / (stem + ext)
                    if candidate.exists():
                        image_path = candidate
                        break
                
                if not image_path.exists():
                    print(f"Warning: Image not found for {json_file.name}, skipping...")
                    continue
            
            # 读取图像尺寸
            try:
                img = Image.open(image_path)
                width, height = img.size
            except Exception as e:
                print(f"Warning: Could not read image {image_path}: {e}, skipping...")
                continue
            
            # 添加图像信息
            image_info = {
                "id": image_id,
                "file_name": image_path.name,
                "width": width,
                "height": height
            }
            coco_data["images"].append(image_info)
            
            # 处理标注
            for shape in labelme_data.get('shapes', []):
                label = shape.get('label', '')
                if not label or label not in category_id_map:
                    continue
                
                shape_type = shape.get('shape_type', '')
                points = shape.get('points', [])
                
                if shape_type == 'polygon' and len(points) >= 3:
                    # 转换为 COCO segmentation 格式
                    # COCO 格式：[[x1, y1, x2, y2, ...]]
                    segmentation = []
                    for point in points:
                        segmentation.extend([float(point[0]), float(point[1])])
                    
                    # 计算边界框
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    x_min = max(0, min(xs))
                    y_min = max(0, min(ys))
                    x_max = min(width, max(xs))
                    y_max = min(height, max(ys))
                    
                    bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                    area = (x_max - x_min) * (y_max - y_min)
                    
                    # 添加标注
                    annotation = {
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": category_id_map[label],
                        "segmentation": [segmentation],
                        "area": area,
                        "bbox": bbox,
                        "iscrowd": 0
                    }
                    coco_data["annotations"].append(annotation)
                    annotation_id += 1
            
            image_id += 1
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    # 保存 COCO JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(coco_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nConversion completed!")
    print(f"Output: {output_json}")
    print(f"Total images: {len(coco_data['images'])}")
    print(f"Total annotations: {len(coco_data['annotations'])}")
    print(f"Categories: {[c['name'] for c in coco_data['categories']]}")


def main():
    parser = argparse.ArgumentParser(description='Convert LabelMe JSON to COCO format')
    parser.add_argument('input_dir', type=str,
                        help='Input directory containing LabelMe JSON files')
    parser.add_argument('--output', type=str, required=True,
                        help='Output COCO JSON file path')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_json = Path(args.output)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    convert_labelme_to_coco(input_dir, output_json)


if __name__ == '__main__':
    main()

