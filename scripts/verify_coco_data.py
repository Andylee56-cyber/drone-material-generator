"""
验证 COCO 格式数据集的质量
"""
import json
import argparse
from pathlib import Path
from collections import Counter


def verify_coco_json(json_path: Path):
    """验证 COCO JSON 文件"""
    print(f"\n{'='*60}")
    print(f"Verifying: {json_path}")
    print(f"{'='*60}")
    
    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        return False
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load file: {e}")
        return False
    
    # 检查必需字段
    required_keys = ['images', 'annotations', 'categories']
    for key in required_keys:
        if key not in data:
            print(f"ERROR: Missing required key: {key}")
            return False
    
    # 统计信息
    images = data['images']
    annotations = data['annotations']
    categories = data['categories']
    
    print(f"\nBasic Statistics:")
    print(f"  Images: {len(images)}")
    print(f"  Annotations: {len(annotations)}")
    print(f"  Categories: {len(categories)}")
    
    # 检查图像
    if len(images) == 0:
        print("WARNING: No images found!")
    else:
        # 检查图像尺寸
        widths = [img.get('width', 0) for img in images]
        heights = [img.get('height', 0) for img in images]
        print(f"\nImage Dimensions:")
        print(f"  Width range: {min(widths)} - {max(widths)}")
        print(f"  Height range: {min(heights)} - {max(heights)}")
        print(f"  Average: {sum(widths)/len(widths):.1f} x {sum(heights)/len(heights):.1f}")
    
    # 检查标注
    if len(annotations) == 0:
        print("WARNING: No annotations found!")
    else:
        # 统计每个类别的标注数量
        category_counts = Counter([ann.get('category_id', -1) for ann in annotations])
        print(f"\nAnnotation Statistics:")
        print(f"  Total annotations: {len(annotations)}")
        print(f"  Annotations per image: {len(annotations)/len(images):.2f}")
        
        # 检查标注格式
        has_segmentation = sum(1 for ann in annotations if 'segmentation' in ann)
        has_bbox = sum(1 for ann in annotations if 'bbox' in ann)
        print(f"  With segmentation: {has_segmentation}")
        print(f"  With bbox: {has_bbox}")
        
        # 类别分布
        print(f"\nCategory Distribution:")
        category_names = {cat['id']: cat['name'] for cat in categories}
        for cat_id, count in sorted(category_counts.items()):
            cat_name = category_names.get(cat_id, f"Unknown({cat_id})")
            print(f"  {cat_name}: {count} ({count/len(annotations)*100:.1f}%)")
    
    # 检查类别
    print(f"\nCategories:")
    for cat in categories:
        print(f"  ID {cat['id']}: {cat.get('name', 'N/A')}")
    
    # 检查图像 ID 和标注 ID 的一致性
    image_ids = set(img['id'] for img in images)
    annotation_image_ids = set(ann['image_id'] for ann in annotations)
    
    missing_images = annotation_image_ids - image_ids
    if missing_images:
        print(f"\nWARNING: {len(missing_images)} annotations reference non-existent images")
    
    images_without_annotations = image_ids - annotation_image_ids
    if images_without_annotations:
        print(f"WARNING: {len(images_without_annotations)} images have no annotations")
    
    print(f"\n{'='*60}")
    print("Verification completed!")
    print(f"{'='*60}\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Verify COCO format dataset')
    parser.add_argument('json_path', type=str,
                        help='Path to COCO JSON file')
    
    args = parser.parse_args()
    
    json_path = Path(args.json_path)
    verify_coco_json(json_path)


if __name__ == '__main__':
    main()

