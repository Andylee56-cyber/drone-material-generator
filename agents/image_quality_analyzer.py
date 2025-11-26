"""
8维度图片质量分析Agent（适配VisDrone数据集）
8-Dimensional Image Quality Analysis Agent (VisDrone Optimized)
用于分析无人机图片素材的8个关键维度，评分标准已调整为适配VisDrone数据集
"""

import numpy as np
import os

# 设置环境变量避免 OpenGL 依赖（必须在导入前设置）
os.environ['OPENCV_DISABLE_OPENCL'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ''
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'

# 延迟导入 OpenCV，避免在模块级别失败
_cv2_available = None
_cv2 = None

def _get_cv2():
    """延迟导入 OpenCV，如果失败返回 None"""
    global _cv2_available, _cv2
    if _cv2_available is None:
        try:
            import cv2
            _cv2 = cv2
            _cv2_available = True
        except (ImportError, OSError) as e:
            # OSError 包括 libGL.so.1 缺失等系统库问题
            _cv2_available = False
            print(f"警告: OpenCV 导入失败: {e}")
    return _cv2 if _cv2_available else None
from PIL import Image
import torch
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO
import json
from datetime import datetime


class ImageQualityAnalyzer:
    """8维度图片质量分析器（VisDrone优化版）"""
    
    def __init__(self, yolo_model_path: Optional[str] = None):
        """
        初始化分析器
        
        参数:
            yolo_model_path: YOLO模型路径，如果为None则使用默认模型
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 加载YOLO模型用于目标检测
        if yolo_model_path and Path(yolo_model_path).exists():
            self.detector = YOLO(yolo_model_path)
        else:
            # 使用预训练的YOLOv8n模型
            self.detector = YOLO('yolov8n.pt')
        
        # 8个维度的名称
        self.dimensions = [
            "图片数据量",
            "拍摄光照质量",
            "目标尺寸",
            "目标完整性",
            "数据均衡度",
            "产品丰富度",
            "目标密集度",
            "场景复杂度"
        ]
        
    def analyze_single_image(self, image_path: str) -> Dict:
        """
        分析单张图片的8个维度
        
        参数:
            image_path: 图片路径
            
        返回:
            包含8个维度分数的字典
        """
        # 延迟导入 OpenCV
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，使用 PIL 降级方案
            return self._analyze_with_pil(image_path)
        
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            # 如果 cv2.imread 失败，尝试用 PIL 读取
            return self._analyze_with_pil(image_path)
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # 1. 图片数据量 (基于图片分辨率和文件大小)
        data_quantity = self._calculate_data_quantity(image_path, h, w)
        
        # 2. 拍摄光照质量 (基于亮度、对比度、直方图分析)
        lighting_quality = self._calculate_lighting_quality(img_rgb)
        
        # 3. 目标尺寸 (基于检测到的目标平均尺寸)
        target_size = self._calculate_target_size(img_rgb)
        
        # 4. 目标完整性 (基于目标是否被裁剪或遮挡)
        target_completeness = self._calculate_target_completeness(img_rgb)
        
        # 5. 数据均衡度 (基于不同类别目标的分布)
        data_balance = self._calculate_data_balance(img_rgb)
        
        # 6. 产品丰富度 (基于检测到的目标类别数量)
        product_richness = self._calculate_product_richness(img_rgb)
        
        # 7. 目标密集度 (基于单位面积内的目标数量)
        target_density = self._calculate_target_density(img_rgb, h, w)
        
        # 8. 场景复杂度 (基于背景复杂度、纹理丰富度)
        scene_complexity = self._calculate_scene_complexity(img_rgb)
        
        return {
            "图片数据量": data_quantity,
            "拍摄光照质量": lighting_quality,
            "目标尺寸": target_size,
            "目标完整性": target_completeness,
            "数据均衡度": data_balance,
            "产品丰富度": product_richness,
            "目标密集度": target_density,
            "场景复杂度": scene_complexity
        }
    
    def _analyze_with_pil(self, image_path: str) -> Dict:
        """
        使用 PIL 进行基础分析（OpenCV 不可用时的降级方案）
        """
        try:
            pil_img = Image.open(image_path).convert("RGB")
            w, h = pil_img.size
            img_array = np.array(pil_img)
            
            # 1. 图片数据量
            file_size = Path(image_path).stat().st_size / (1024 * 1024)  # MB
            pixel_count = h * w
            resolution_score = min(100, (pixel_count / (1280 * 720)) * 100)
            size_score = min(100, (file_size / 1.0) * 100)
            if pixel_count >= 640 * 480 and file_size >= 0.5:
                resolution_score = max(30, resolution_score)
                size_score = max(30, size_score)
            data_quantity = (resolution_score * 0.6 + size_score * 0.4)
            
            # 2. 拍摄光照质量（基于亮度）
            brightness = np.mean(img_array)
            lighting_quality = min(100, max(20, (brightness / 128.0) * 100))
            
            # 3-8. 其他维度使用基础估算
            contrast = np.std(img_array)
            target_size = min(100, max(30, (contrast / 50.0) * 100))
            target_completeness = 70.0
            data_balance = 60.0
            product_richness = 50.0
            target_density = min(100, max(20, (pixel_count / 1000000) * 10))
            scene_complexity = min(100, max(30, contrast / 2.0))
            
            return {
                "图片数据量": data_quantity,
                "拍摄光照质量": lighting_quality,
                "目标尺寸": target_size,
                "目标完整性": target_completeness,
                "数据均衡度": data_balance,
                "产品丰富度": product_richness,
                "目标密集度": target_density,
                "场景复杂度": scene_complexity
            }
        except Exception as e:
            print(f"PIL 分析失败: {e}")
            # 返回默认值
            return {
                "图片数据量": 50.0,
                "拍摄光照质量": 50.0,
                "目标尺寸": 50.0,
                "目标完整性": 50.0,
                "数据均衡度": 50.0,
                "产品丰富度": 50.0,
                "目标密集度": 50.0,
                "场景复杂度": 50.0
            }
    
    def analyze_batch(self, image_paths: List[str]) -> Dict:
        """
        批量分析多张图片
        
        参数:
            image_paths: 图片路径列表
            
        返回:
            包含所有图片分析结果的字典
        """
        results = []
        for img_path in image_paths:
            try:
                result = self.analyze_single_image(img_path)
                result['image_path'] = img_path
                results.append(result)
            except Exception as e:
                print(f"分析图片 {img_path} 时出错: {e}")
                continue
        
        # 计算平均维度分数
        avg_scores = {}
        for dim in self.dimensions:
            scores = [r[dim] for r in results if dim in r]
            avg_scores[dim] = np.mean(scores) if scores else 0.0
        
        return {
            "individual_results": results,
            "average_scores": avg_scores,
            "total_images": len(results),
            "total_annotations": sum(len(self._detect_objects(r['image_path'])) for r in results)
        }
    
    def _calculate_data_quantity(self, image_path: str, height: int, width: int) -> float:
        """计算图片数据量维度 (0-100) - VisDrone优化：降低标准"""
        # 基于分辨率和文件大小
        file_size = Path(image_path).stat().st_size / (1024 * 1024)  # MB
        pixel_count = height * width
        
        # 归一化到0-100
        # VisDrone优化：理想值降低为 分辨率 >= 1280x720, 文件大小 >= 1MB
        resolution_score = min(100, (pixel_count / (1280 * 720)) * 100)
        size_score = min(100, (file_size / 1.0) * 100)
        
        # 如果达到最低标准（640x480, 0.5MB），至少给30分
        if pixel_count >= 640 * 480 and file_size >= 0.5:
            resolution_score = max(30, resolution_score)
            size_score = max(30, size_score)
        
        return (resolution_score * 0.6 + size_score * 0.4)
    
    def _calculate_lighting_quality(self, img: np.ndarray) -> float:
        """计算拍摄光照质量维度 (0-100) - VisDrone优化：放宽标准"""
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，使用基础亮度计算
            brightness = np.mean(img)
            return min(100, max(20, (brightness / 128.0) * 100))
        
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        v_channel = hsv[:, :, 2]  # 亮度通道
        
        # 计算亮度统计
        mean_brightness = np.mean(v_channel)
        std_brightness = np.std(v_channel)
        
        # VisDrone优化：理想亮度范围放宽为 80-220 (0-255范围)
        brightness_score = 100 - abs(mean_brightness - 150) / 150 * 100
        brightness_score = max(0, min(100, brightness_score))
        
        # 对比度评分 (标准差越大，对比度越好) - 降低要求
        contrast_score = min(100, std_brightness / 2.0)  # 从2.55降到2.0
        
        # 检查是否有过曝或欠曝 - 减少惩罚
        overexposed = np.sum(v_channel > 240) / v_channel.size
        underexposed = np.sum(v_channel < 15) / v_channel.size
        exposure_penalty = (overexposed + underexposed) * 30  # 从50降到30
        
        final_score = (brightness_score * 0.4 + contrast_score * 0.4) - exposure_penalty
        # 最低保证20分（VisDrone数据集通常光照不理想）
        return max(20, min(100, final_score))
    
    def _detect_objects(self, img: np.ndarray) -> List[Dict]:
        """使用YOLO检测目标"""
        try:
            results = self.detector(img, verbose=False)
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detections.append({
                        'class': int(box.cls[0]),
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                    })
            return detections
        except Exception as e:
            print(f"目标检测出错: {e}")
            return []
    
    def _calculate_target_size(self, img: np.ndarray) -> float:
        """计算目标尺寸维度 (0-100) - VisDrone优化：降低理想占比"""
        detections = self._detect_objects(img)
        if not detections:
            return 0.0
        
        h, w = img.shape[:2]
        total_area = h * w
        
        # 计算所有检测框的平均面积占比
        area_ratios = []
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            box_area = (x2 - x1) * (y2 - y1)
            area_ratio = box_area / total_area
            area_ratios.append(area_ratio)
        
        avg_ratio = np.mean(area_ratios) if area_ratios else 0
        
        # VisDrone优化：理想目标尺寸占比降低为 2-10%（从5-15%降低）
        if 0.02 <= avg_ratio <= 0.10:
            return 100.0
        elif avg_ratio < 0.02:
            return (avg_ratio / 0.02) * 100
        else:
            return max(0, 100 - ((avg_ratio - 0.10) / 0.10) * 100)
    
    def _calculate_target_completeness(self, img: np.ndarray) -> float:
        """计算目标完整性维度 (0-100) - VisDrone优化：减少边缘惩罚"""
        detections = self._detect_objects(img)
        if not detections:
            return 0.0
        
        h, w = img.shape[:2]
        completeness_scores = []
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            
            # 检查目标是否靠近边缘 (可能被裁剪) - VisDrone优化：放宽边距
            margin = 0.03  # 从5%降到3%
            near_left = x1 < w * margin
            near_right = x2 > w * (1 - margin)
            near_top = y1 < h * margin
            near_bottom = y2 > h * (1 - margin)
            
            # 如果目标在边缘，可能不完整 - 减少惩罚
            edge_penalty = (near_left + near_right + near_top + near_bottom) * 5  # 从10降到5
            
            # 检查置信度 (低置信度可能表示目标不完整)
            confidence_score = det['confidence'] * 100
            
            completeness = max(0, confidence_score - edge_penalty)
            completeness_scores.append(completeness)
        
        result = np.mean(completeness_scores) if completeness_scores else 0.0
        # 最低保证15分
        return max(15, result)
    
    def _calculate_data_balance(self, img: np.ndarray) -> float:
        """计算数据均衡度维度 (0-100) - VisDrone优化：保持但放宽"""
        detections = self._detect_objects(img)
        if not detections:
            return 0.0
        
        # 统计各类别的数量
        class_counts = {}
        for det in detections:
            cls = det['class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
        
        if len(class_counts) == 0:
            return 0.0
        
        # 计算类别分布的均衡度 (使用熵)
        total = sum(class_counts.values())
        probs = [count / total for count in class_counts.values()]
        entropy = -sum(p * np.log2(p + 1e-10) for p in probs)
        max_entropy = np.log2(len(class_counts))
        
        # 归一化到0-100
        balance_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        # 最低保证20分（即使不均衡也有基础分）
        return max(20, balance_score)
    
    def _calculate_product_richness(self, img: np.ndarray) -> float:
        """计算产品丰富度维度 (0-100) - VisDrone优化：降低理想类别数"""
        detections = self._detect_objects(img)
        unique_classes = len(set(det['class'] for det in detections))
        
        # VisDrone优化：理想情况降低为 3-6个不同类别（从5-10降低）
        if unique_classes == 0:
            return 0.0
        elif unique_classes <= 6:
            return (unique_classes / 6) * 100
        else:
            # 超过6个类别，给予额外奖励但不超过100
            return min(100, 100 + (unique_classes - 6) * 3)
    
    def _calculate_target_density(self, img: np.ndarray, height: int, width: int) -> float:
        """计算目标密集度维度 (0-100) - VisDrone优化：降低理想密集度"""
        detections = self._detect_objects(img)
        num_targets = len(detections)
        
        if num_targets == 0:
            return 0.0
        
        # 计算单位面积内的目标数量
        area = height * width / (1000 * 1000)  # 转换为百万像素
        density = num_targets / (area + 1e-6)
        
        # VisDrone优化：理想密集度降低为 每百万像素2-8个目标（从5-15降低）
        if 2 <= density <= 8:
            return 100.0
        elif density < 2:
            return (density / 2) * 100
        else:
            # 过于密集可能影响质量
            return max(0, 100 - ((density - 8) / 8) * 50)
    
    def _calculate_scene_complexity(self, img: np.ndarray) -> float:
        """计算场景复杂度维度 (0-100) - VisDrone优化：稍微放宽"""
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，使用基础复杂度计算
            contrast = np.std(img)
            return min(100, max(30, contrast / 2.0))
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 使用拉普拉斯算子计算图像清晰度/复杂度
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 计算纹理复杂度 (使用局部二值模式或边缘检测)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 计算颜色复杂度
        unique_colors = len(np.unique(img.reshape(-1, img.shape[-1]), axis=0))
        color_complexity = min(100, (unique_colors / 800) * 100)  # 从1000降到800
        
        # 综合评分
        sharpness_score = min(100, (laplacian_var / 400) * 100)  # 从500降到400
        texture_score = min(100, edge_density * 1200)  # 从1000提高到1200
        
        complexity = (sharpness_score * 0.3 + texture_score * 0.3 + color_complexity * 0.4)
        # 最低保证25分（VisDrone通常有一定复杂度）
        return max(25, min(100, complexity))


if __name__ == "__main__":
    # 测试代码
    analyzer = ImageQualityAnalyzer()
    test_image = "test_image.jpg"  # 替换为实际图片路径
    
    if Path(test_image).exists():
        result = analyzer.analyze_single_image(test_image)
        print("8维度分析结果:")
        for dim, score in result.items():
            print(f"{dim}: {score:.2f}%")

