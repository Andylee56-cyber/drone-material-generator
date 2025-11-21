"""
图片多角度生成器 - 增强版（带检测框）
支持真正的无人机3D视角变换，并绘制YOLO检测框
"""

import numpy as np
try:
    import cv2
except ImportError:
    raise ImportError(
        "OpenCV (cv2) is not installed. "
        "This is required for the drone vision system. "
        "Please ensure 'opencv-python-headless==4.8.1.78' is in requirements.txt and Streamlit Cloud has installed it correctly."
    )
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Dict, Optional
import random
from datetime import datetime
import math
from ultralytics import YOLO
import torch


class ImageMultiAngleGenerator:
    """图片多角度生成器 - 支持真实3D视角变换和检测框绘制"""

    def __init__(self, yolo_model_path: Optional[str] = None, draw_boxes: bool = True):
        """
        初始化生成器
        
        参数:
            yolo_model_path: YOLO模型路径，None则使用默认模型
            draw_boxes: 是否绘制检测框
        """
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.draw_boxes = draw_boxes
        
        # 加载YOLO模型用于目标检测
        if draw_boxes:
            if yolo_model_path and Path(yolo_model_path).exists():
                self.detector = YOLO(yolo_model_path)
            else:
                self.detector = YOLO('yolov8n.pt')
            
            # COCO类别名称（YOLOv8默认使用COCO数据集）
            self.class_names = [
                'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
                'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
                'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
                'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
                'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
                'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
                'toothbrush'
            ]
            
            # 为每个类别分配颜色（BGR格式）
            self.colors = self._generate_colors(len(self.class_names))

    def _generate_colors(self, num_colors: int) -> List[tuple]:
        """生成不同颜色用于不同类别"""
        colors = []
        np.random.seed(42)  # 固定随机种子，确保颜色一致
        for i in range(num_colors):
            color = tuple(np.random.randint(0, 255, 3).tolist())
            colors.append(color)
        return colors

    def generate_multi_angle_images(
        self,
        input_image_path: str,
        output_dir: str,
        num_generations: int = 8,
        transformations: List[str] = None
    ) -> Dict:
        """
        从单张图片生成多角度素材（真正的3D视角变换 + 检测框）
        """
        input_path = Path(input_image_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not input_path.exists():
            raise FileNotFoundError(f"输入图片不存在: {input_image_path}")

        img = cv2.imread(str(input_path))
        if img is None:
            pil_img = Image.open(input_path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        h, w = img.shape[:2]

        # 真正的无人机视角变换列表
        if transformations is None:
            transformations = [
                'top_down_90', 'top_down_60', 'top_down_45',
                'low_angle_30', 'low_angle_45',
                'side_view_left', 'side_view_right',
                'oblique_30', 'oblique_45', 'oblique_60',
                'bird_eye', 'worm_eye',
                'diagonal_up', 'diagonal_down',
                'tilt_left', 'tilt_right',
                'panoramic_wide', 'panoramic_narrow',
                'zoom_extreme', 'rotate_3d_45', 'rotate_3d_90',
                'perspective_strong', 'fisheye_effect', 'original'
            ]

        # 随机选择变换（允许重复）
        if num_generations > len(transformations):
            selected_transforms = transformations.copy()
            for _ in range(num_generations - len(transformations)):
                selected_transforms.append(random.choice(transformations))
            random.shuffle(selected_transforms)
        else:
            selected_transforms = random.sample(transformations, num_generations)

        generated_files = []
        metadata = []
        all_detections = []  # 存储所有检测结果用于统计

        for idx, transform_type in enumerate(selected_transforms, 1):
            try:
                transformed_img = self._apply_transformation(img, transform_type, h, w)
                
                # 进行目标检测并绘制检测框
                detections = []
                if self.draw_boxes:
                    transformed_img, detections = self._detect_and_draw_boxes(transformed_img)
                    all_detections.extend(detections)
                
                output_filename = f"generated_{idx:03d}_{transform_type}.jpg"
                output_file = output_path / output_filename
                cv2.imwrite(str(output_file), transformed_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

                generated_files.append(str(output_file))
                metadata.append({
                    'index': idx,
                    'original_path': str(input_path),
                    'generated_path': str(output_file),
                    'transformation': transform_type,
                    'filename': output_filename,
                    'detections': detections
                })
            except Exception as e:
                print(f"⚠️ 生成失败 {transform_type}: {e}")
                continue

        # 计算平均置信度统计
        confidence_stats = self._calculate_confidence_stats(all_detections)

        metadata_file = output_path / f"generation_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generation_time': datetime.now().isoformat(),
                'original_image': str(input_path),
                'output_dir': str(output_path),
                'num_requested': num_generations,
                'num_generated': len(generated_files),
                'generated_images': metadata,
                'confidence_statistics': confidence_stats
            }, f, ensure_ascii=False, indent=2)

        return {
            'success': True,
            'original_image': str(input_path),
            'output_dir': str(output_path),
            'num_generated': len(generated_files),
            'generated_files': generated_files,
            'metadata_file': str(metadata_file),
            'confidence_statistics': confidence_stats
        }

    def _detect_and_draw_boxes(self, img: np.ndarray) -> tuple:
        """
        检测目标并绘制检测框
        
        返回:
            (绘制后的图片, 检测结果列表)
        """
        try:
            results = self.detector(img, verbose=False, conf=0.25)
            detections = []
            annotated_img = img.copy()
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 获取检测信息
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                    
                    # 获取类别名称和颜色
                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f'class_{cls_id}'
                    color = self.colors[cls_id % len(self.colors)]
                    
                    # 绘制检测框
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
                    
                    # 绘制标签背景
                    label = f'{class_name} {confidence:.2f}'
                    (label_width, label_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                    )
                    cv2.rectangle(
                        annotated_img,
                        (x1, y1 - label_height - baseline - 5),
                        (x1 + label_width, y1),
                        color,
                        -1
                    )
                    
                    # 绘制标签文字
                    cv2.putText(
                        annotated_img,
                        label,
                        (x1, y1 - baseline - 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                        cv2.LINE_AA
                    )
                    
                    # 记录检测结果
                    detections.append({
                        'class_id': cls_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2]
                    })
            
            return annotated_img, detections
        except Exception as e:
            print(f"检测出错: {e}")
            return img, []

    def _calculate_confidence_stats(self, all_detections: List[Dict]) -> Dict:
        """计算各类别的平均置信度统计"""
        if not all_detections:
            return {}
        
        # 按类别分组统计
        class_stats = {}
        for det in all_detections:
            class_name = det['class_name']
            if class_name not in class_stats:
                class_stats[class_name] = {
                    'count': 0,
                    'confidences': [],
                    'avg_confidence': 0.0
                }
            class_stats[class_name]['count'] += 1
            class_stats[class_name]['confidences'].append(det['confidence'])
        
        # 计算平均置信度
        for class_name, stats in class_stats.items():
            stats['avg_confidence'] = np.mean(stats['confidences'])
            stats['max_confidence'] = np.max(stats['confidences'])
            stats['min_confidence'] = np.min(stats['confidences'])
            del stats['confidences']  # 删除详细列表，只保留统计值
        
        # 按平均置信度排序
        sorted_stats = dict(sorted(
            class_stats.items(),
            key=lambda x: x[1]['avg_confidence'],
            reverse=True
        ))
        
        return sorted_stats

    def _apply_transformation(self, img: np.ndarray, transform_type: str, h: int, w: int) -> np.ndarray:
        """应用指定的3D视角变换"""
        result = img.copy()
        
        if transform_type == 'original':
            return result
        
        # ========== 真正的3D视角变换 ==========
        
        elif transform_type == 'top_down_90':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.1], [w*0.9, h*0.1], [w*0.1, h*0.9], [w*0.9, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'top_down_60':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.15, h*0.05], [w*0.85, h*0.05], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'top_down_45':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.2, h*0.1], [w*0.8, h*0.1], [w*0.1, h*0.9], [w*0.9, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'low_angle_30':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.3], [w*0.9, h*0.3], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'low_angle_45':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.15, h*0.4], [w*0.85, h*0.4], [w*0.0, h*1.0], [w*1.0, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'side_view_left':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.0, h*0.1], [w*0.7, h*0.1], [w*0.0, h*0.9], [w*0.7, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'side_view_right':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.3, h*0.1], [w*1.0, h*0.1], [w*0.3, h*0.9], [w*1.0, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'oblique_30':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 30, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.1], [w*0.9, h*0.1], [w*0.0, h*0.9], [w*1.0, h*0.9]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'oblique_45':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 45, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.15, h*0.15], [w*0.85, h*0.15], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'oblique_60':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 60, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.2, h*0.2], [w*0.8, h*0.2], [w*0.1, h*0.9], [w*0.9, h*0.9]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'bird_eye':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.05, h*0.05], [w*0.95, h*0.05], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            M_scale = cv2.getRotationMatrix2D((w/2, h/2), 0, 0.9)
            result = cv2.warpAffine(result, M_scale, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'worm_eye':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.2, h*0.5], [w*0.8, h*0.5], [w*0.0, h*1.0], [w*1.0, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'diagonal_up':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.0, h*0.2], [w*0.8, h*0.0], [w*0.2, h*1.0], [w*1.0, h*0.8]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'diagonal_down':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.2, h*0.0], [w*1.0, h*0.2], [w*0.0, h*0.8], [w*0.8, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'tilt_left':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, -15, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.0], [w*0.9, h*0.1], [w*0.1, h*1.0], [w*0.9, h*0.9]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'tilt_right':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 15, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.1], [w*0.9, h*0.0], [w*0.1, h*0.9], [w*0.9, h*1.0]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'panoramic_wide':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.0, h*0.15], [w*1.0, h*0.15], [w*0.0, h*0.85], [w*1.0, h*0.85]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'panoramic_narrow':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.0], [w*0.9, h*0.0], [w*0.1, h*1.0], [w*0.9, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'zoom_extreme':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 0, 1.5)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'rotate_3d_45':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 45, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.1, h*0.1], [w*0.9, h*0.1], [w*0.1, h*0.9], [w*0.9, h*0.9]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif transform_type == 'rotate_3d_90':
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, 90, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'perspective_strong':
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.2, h*0.2], [w*0.8, h*0.2], [w*0.0, h*1.0], [w*1.0, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif transform_type == 'fisheye_effect':
            h, w = result.shape[:2]
            center_x, center_y = w // 2, h // 2
            max_radius = min(center_x, center_y)
            map_x = np.zeros((h, w), dtype=np.float32)
            map_y = np.zeros((h, w), dtype=np.float32)
            for y in range(h):
                for x in range(w):
                    dx = x - center_x
                    dy = y - center_y
                    r = math.sqrt(dx*dx + dy*dy) / max_radius
                    if r > 0:
                        theta = math.atan2(dy, dx)
                        r_new = r * r * 0.7
                        map_x[y, x] = center_x + r_new * max_radius * math.cos(theta)
                        map_y[y, x] = center_y + r_new * max_radius * math.sin(theta)
                    else:
                        map_x[y, x] = x
                        map_y[y, x] = y
            result = cv2.remap(result, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        return result


if __name__ == "__main__":
    generator = ImageMultiAngleGenerator()
    result = generator.generate_multi_angle_images(
        input_image_path="test_image.jpg",
        output_dir="generated",
        num_generations=8
    )
    print(f"生成了 {result['num_generated']} 张图片")


