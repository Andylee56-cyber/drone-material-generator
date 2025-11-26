"""
数据集划分脚本：将 COCO 格式数据集划分为训练集和验证集
"""
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List
import random


def load_coco_json(json_path: Path) -> Dict:
    """加载 COCO 格式的 JSON 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_coco_json(data: Dict, json_path: Path):
    """保存 COCO 格式的 JSON 文件"""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def split_dataset(
    input_json: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.2,
    seed: int = 42
):
    """
    划分数据集为训练集和验证集
    
    Args:
        input_json: 输入的 COCO JSON 文件路径
        output_dir: 输出目录
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        seed: 随机种子
    """
    # 设置随机种子
    random.seed(seed)
    
    # 加载原始数据
    print(f"Loading COCO JSON from: {input_json}")
    coco_data = load_coco_json(input_json)
    
    # 获取图像和标注
    images = coco_data['images']
    annotations = coco_data['annotations']
    categories = coco_data['categories']
    
    # 按图像 ID 组织标注
    image_id_to_annotations = {}
    for ann in annotations:
        image_id = ann['image_id']
        if image_id not in image_id_to_annotations:
            image_id_to_annotations[image_id] = []
        image_id_to_annotations[image_id].append(ann)
    
    # 随机打乱图像
    image_ids = list(image_id_to_annotations.keys())
    random.shuffle(image_ids)
    
    # 计算划分点
    total = len(image_ids)
    train_count = int(total * train_ratio)
    
    train_ids = set(image_ids[:train_count])
    val_ids = set(image_ids[train_count:])
    
    print(f"Total images: {total}")
    print(f"Train images: {len(train_ids)} ({len(train_ids)/total*100:.1f}%)")
    print(f"Val images: {len(val_ids)} ({len(val_ids)/total*100:.1f}%)")
    
    # 创建输出目录
    train_dir = output_dir / 'train'
    val_dir = output_dir / 'val'
    train_images_dir = train_dir / 'images'
    val_images_dir = val_dir / 'images'
    
    train_images_dir.mkdir(parents=True, exist_ok=True)
    val_images_dir.mkdir(parents=True, exist_ok=True)
    
    # 构建训练集和验证集
    train_data = {
        'images': [],
        'annotations': [],
        'categories': categories
    }
    
    val_data = {
        'images': [],
        'annotations': [],
        'categories': categories
    }
    
    # 重新映射图像 ID 和标注 ID
    train_image_id_map = {}
    val_image_id_map = {}
    train_ann_id = 1
    val_ann_id = 1
    
    # 获取原始图像目录（假设图像在 input_json 同级目录或 images 子目录）
    input_dir = input_json.parent
    possible_image_dirs = [
        input_dir / 'images',
        input_dir.parent / 'images',
        input_dir
    ]
    
    images_dir = None
    for img_dir in possible_image_dirs:
        if img_dir.exists() and any(img_dir.glob('*.jpg')) or any(img_dir.glob('*.png')):
            images_dir = img_dir
            break
    
    if images_dir is None:
        print("Warning: Could not find images directory. Please ensure images are accessible.")
        images_dir = input_dir
    
    print(f"Using images directory: {images_dir}")
    
    # 处理每张图像
    for img_info in images:
        image_id = img_info['id']
        file_name = img_info['file_name']
        
        # 查找图像文件
        img_path = None
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            candidate = images_dir / file_name
            if candidate.exists():
                img_path = candidate
                break
            # 尝试不带扩展名
            candidate = images_dir / (Path(file_name).stem + ext)
            if candidate.exists():
                img_path = candidate
                file_name = candidate.name
                break
        
        if img_path is None:
            print(f"Warning: Image not found: {file_name}, skipping...")
            continue
        
        if image_id in train_ids:
            # 训练集
            new_image_id = len(train_image_id_map) + 1
            train_image_id_map[image_id] = new_image_id
            
            new_img_info = img_info.copy()
            new_img_info['id'] = new_image_id
            new_img_info['file_name'] = file_name
            train_data['images'].append(new_img_info)
            
            # 复制图像
            shutil.copy2(img_path, train_images_dir / file_name)
            
            # 添加标注
            if image_id in image_id_to_annotations:
                for ann in image_id_to_annotations[image_id]:
                    new_ann = ann.copy()
                    new_ann['id'] = train_ann_id
                    new_ann['image_id'] = new_image_id
                    train_ann_id += 1
                    train_data['annotations'].append(new_ann)
        
        elif image_id in val_ids:
            # 验证集
            new_image_id = len(val_image_id_map) + 1
            val_image_id_map[image_id] = new_image_id
            
            new_img_info = img_info.copy()
            new_img_info['id'] = new_image_id
            new_img_info['file_name'] = file_name
            val_data['images'].append(new_img_info)
            
            # 复制图像
            shutil.copy2(img_path, val_images_dir / file_name)
            
            # 添加标注
            if image_id in image_id_to_annotations:
                for ann in image_id_to_annotations[image_id]:
                    new_ann = ann.copy()
                    new_ann['id'] = val_ann_id
                    new_ann['image_id'] = new_image_id
                    val_ann_id += 1
                    val_data['annotations'].append(new_ann)
    
    # 保存划分后的 JSON 文件
    train_json = output_dir / 'coco_train.json'
    val_json = output_dir / 'coco_val.json'
    
    save_coco_json(train_data, train_json)
    save_coco_json(val_data, val_json)
    
    print(f"\nDataset split completed!")
    print(f"Train JSON: {train_json}")
    print(f"  - Images: {len(train_data['images'])}")
    print(f"  - Annotations: {len(train_data['annotations'])}")
    print(f"Val JSON: {val_json}")
    print(f"  - Images: {len(val_data['images'])}")
    print(f"  - Annotations: {len(val_data['annotations'])}")
    print(f"Categories: {[c['name'] for c in categories]}")


def main():
    parser = argparse.ArgumentParser(description='Split COCO dataset into train/val sets')
    parser.add_argument('--input', type=str, required=True,
                        help='Input COCO JSON file path')
    parser.add_argument('--output', type=str, required=True,
                        help='Output directory for split datasets')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                        help='Training set ratio (default: 0.8)')
    parser.add_argument('--val-ratio', type=float, default=0.2,
                        help='Validation set ratio (default: 0.2)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    input_json = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_json.exists():
        print(f"Error: Input file not found: {input_json}")
        return
    
    if abs(args.train_ratio + args.val_ratio - 1.0) > 1e-6:
        print(f"Warning: train_ratio + val_ratio = {args.train_ratio + args.val_ratio}, should be 1.0")
    
    split_dataset(
        input_json=input_json,
        output_dir=output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed
    )


if __name__ == '__main__':
    main()

