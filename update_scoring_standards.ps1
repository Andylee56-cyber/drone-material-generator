# ============================================
# 更新8维评分标准和增强训练目标（适配VisDrone数据集）
# ============================================

Write-Host "开始更新评分标准和增强训练系统..." -ForegroundColor Cyan

# ============================================
# 步骤1: 更新8维评分标准（适配VisDrone数据集）
# ============================================
Write-Host "`n步骤1: 更新8维评分标准..." -ForegroundColor Yellow

@"
"""
8维度图片质量分析Agent（适配VisDrone数据集）
8-Dimensional Image Quality Analysis Agent (VisDrone Optimized)
用于分析无人机图片素材的8个关键维度，评分标准已调整为适配VisDrone数据集
"""

import numpy as np
import cv2
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
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
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
"@ | Set-Content "agents\image_quality_analyzer.py" -Encoding UTF8

Write-Host "✅ 步骤1完成：已更新8维评分标准（适配VisDrone数据集）" -ForegroundColor Green

# ============================================
# 步骤2: 更新增强训练器（改为基于提升幅度）
# ============================================
Write-Host "`n步骤2: 更新增强训练器（改为基于提升幅度）..." -ForegroundColor Yellow

@"
"""
GPU加速版素材自动增强训练器（基于提升幅度评估）
"""
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional
from agents.image_quality_analyzer import ImageQualityAnalyzer
from agents.material_generator_agent import MaterialGeneratorAgent
import torch
import torch.nn.functional as F

class MaterialEnhancementTrainer:
    """支持GPU并行的素材自动增强训练器（基于提升幅度评估）"""

    def __init__(self, yolo_model_path: Optional[str] = None,
                 fast_mode: bool = True, analysis_max_side: int = 960):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.analyzer = ImageQualityAnalyzer(yolo_model_path)
        self.agent = MaterialGeneratorAgent(yolo_model_path)
        # 改为基于提升幅度的目标
        self.target_improvement = 5.0  # 目标提升5分（优秀）
        self.excellent_threshold = 8.0  # 提升8分以上为优秀
        self.good_threshold = 5.0  # 提升5-8分为良好
        self.fair_threshold = 3.0  # 提升3-5分为一般
        self.max_iterations = 10
        self.fast_mode = fast_mode
        self.analysis_max_side = analysis_max_side
        self.temp_dir = Path("temp_enhancement_cache")
        self.temp_dir.mkdir(exist_ok=True)

    def enhance_to_excellent(self, image_path: str, output_dir: str,
                             target_improvement: float = 5.0, max_iterations: int = 10) -> Dict:
        """
        增强图片质量，目标为提升指定分数
        
        参数:
            image_path: 输入图片路径
            output_dir: 输出目录
            target_improvement: 目标提升分数（默认5分）
            max_iterations: 最大迭代次数
        """
        input_path = Path(image_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        if not input_path.exists():
            raise FileNotFoundError(f"输入图片不存在: {image_path}")

        img = cv2.imread(str(input_path))
        if img is None:
            pil_img = Image.open(input_path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # 获取初始分数
        temp_path = self._write_temp_image(img, "initial.jpg")
        initial_analysis = self.analyzer.analyze_single_image(str(temp_path))
        if temp_path.exists():
            temp_path.unlink()
        
        initial_scores = [initial_analysis[dim] for dim in self.analyzer.dimensions]
        initial_score = float(np.mean(initial_scores))

        current_img = img.copy()
        iteration_history = []

        for iteration in range(max_iterations):
            temp_path = self._write_temp_image(current_img, f"iter_{iteration}.jpg")
            analysis_result = self.analyzer.analyze_single_image(str(temp_path))
            if temp_path.exists():
                temp_path.unlink()

            scores = [analysis_result[dim] for dim in self.analyzer.dimensions]
            current_score = float(np.mean(scores))
            improvement = current_score - initial_score
            
            iteration_history.append({
                'iteration': iteration + 1,
                'score': current_score,
                'improvement': improvement,
                'dimension_scores': analysis_result.copy()
            })

            # 判断提升等级
            if improvement >= self.excellent_threshold:
                quality_level = "优秀"
                target_achieved = True
            elif improvement >= self.good_threshold:
                quality_level = "良好"
                target_achieved = True
            elif improvement >= self.fair_threshold:
                quality_level = "一般"
                target_achieved = False
            else:
                quality_level = "较差"
                target_achieved = False

            # 如果达到目标提升幅度，提前结束
            if improvement >= target_improvement:
                final_path = output_path / f"enhanced_final_{input_path.stem}.jpg"
                cv2.imwrite(str(final_path), current_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                return {
                    'success': True,
                    'target_achieved': True,
                    'initial_score': initial_score,
                    'final_score': current_score,
                    'improvement': improvement,
                    'quality_level': quality_level,
                    'iterations': iteration + 1,
                    'final_image_path': str(final_path),
                    'enhancement_history': iteration_history
                }

            strategies = self._select_enhancement_strategy(analysis_result)
            current_img = self._apply_enhancements(current_img, strategies)

        # 达到最大迭代次数
        final_path = output_path / f"enhanced_final_{input_path.stem}.jpg"
        cv2.imwrite(str(final_path), current_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        final_improvement = iteration_history[-1]['improvement']
        
        if final_improvement >= self.excellent_threshold:
            quality_level = "优秀"
        elif final_improvement >= self.good_threshold:
            quality_level = "良好"
        elif final_improvement >= self.fair_threshold:
            quality_level = "一般"
        else:
            quality_level = "较差"
        
        return {
            'success': True,
            'target_achieved': final_improvement >= target_improvement,
            'initial_score': initial_score,
            'final_score': iteration_history[-1]['score'],
            'improvement': final_improvement,
            'quality_level': quality_level,
            'iterations': max_iterations,
            'final_image_path': str(final_path),
            'enhancement_history': iteration_history
        }

    def enhance_batch_to_excellent(self, image_paths: List[str], output_dir: str,
                                   target_improvement: float = 5.0, max_iterations: int = 10) -> Dict:
        """
        批量增强图片质量
        
        参数:
            image_paths: 图片路径列表
            output_dir: 输出目录
            target_improvement: 目标提升分数
            max_iterations: 最大迭代次数
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        batch_results = []
        for img_path in image_paths:
            try:
                img_output_dir = output_path / Path(img_path).stem
                result = self.enhance_to_excellent(img_path, str(img_output_dir),
                                                   target_improvement, max_iterations)
                result['original_path'] = img_path
                batch_results.append(result)
            except Exception as e:
                batch_results.append({'success': False, 'original_path': img_path, 'error': str(e)})

        successful = [r for r in batch_results if r.get('success', False)]
        achieved = [r for r in successful if r.get('target_achieved', False)]
        
        # 统计提升等级
        excellent_count = sum(1 for r in successful if r.get('improvement', 0) >= self.excellent_threshold)
        good_count = sum(1 for r in successful if self.good_threshold <= r.get('improvement', 0) < self.excellent_threshold)
        fair_count = sum(1 for r in successful if self.fair_threshold <= r.get('improvement', 0) < self.good_threshold)
        poor_count = sum(1 for r in successful if r.get('improvement', 0) < self.fair_threshold)
        
        # 计算平均提升幅度
        avg_improvement = np.mean([r.get('improvement', 0) for r in successful]) if successful else 0.0
        
        return {
            'total_images': len(image_paths),
            'successful': len(successful),
            'target_achieved': len(achieved),
            'excellent_count': excellent_count,
            'good_count': good_count,
            'fair_count': fair_count,
            'poor_count': poor_count,
            'average_improvement': avg_improvement,
            'results': batch_results,
            'success_rate': len(successful) / len(image_paths) * 100 if image_paths else 0,
            'achievement_rate': len(achieved) / len(successful) * 100 if successful else 0
        }

    def _bgr_to_tensor(self, img: np.ndarray) -> torch.Tensor:
        tensor = torch.from_numpy(img[:, :, ::-1].copy()).float() / 255.0
        tensor = tensor.permute(2, 0, 1).unsqueeze(0).to(self.device)
        return tensor

    def _tensor_to_bgr(self, tensor: torch.Tensor) -> np.ndarray:
        tensor = tensor.squeeze(0).clamp(0, 1)
        img = (tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        return img[:, :, ::-1]

    def _write_temp_image(self, img: np.ndarray, filename: str) -> Path:
        temp_path = self.temp_dir / filename
        processed = img
        if self.fast_mode and self.analysis_max_side:
            h, w = img.shape[:2]
            max_side = max(h, w)
            if max_side > self.analysis_max_side:
                scale = self.analysis_max_side / max_side
                new_size = (int(w * scale), int(h * scale))
                processed = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        quality = 85 if self.fast_mode else 95
        cv2.imwrite(str(temp_path), processed, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return temp_path

    def _select_enhancement_strategy(self, scores: Dict) -> List[str]:
        th = 50.0  # 降低阈值，因为VisDrone数据集分数本身较低
        strategies = []
        if scores.get('图片数据量', 100) < th:
            strategies.append('super_resolution')
        if scores.get('拍摄光照质量', 100) < th:
            strategies.append('lighting_correction')
            strategies.append('contrast_enhancement')
        if scores.get('目标尺寸', 100) < th:
            strategies.append('sharpen')
            strategies.append('edge_enhancement')
        if scores.get('目标完整性', 100) < th:
            strategies.append('denoise')
            strategies.append('sharpen')
        if scores.get('数据均衡度', 100) < th:
            strategies.append('color_enhancement')
        if scores.get('产品丰富度', 100) < th:
            strategies.append('contrast_enhancement')
            strategies.append('sharpen')
        if scores.get('目标密集度', 100) < th:
            strategies.append('overall_enhancement')
        if scores.get('场景复杂度', 100) < th:
            strategies.append('texture_enhancement')
            strategies.append('sharpen')
        if not strategies:
            strategies = ['overall_enhancement', 'sharpen', 'contrast_enhancement']
        return strategies

    def _apply_enhancements(self, img: np.ndarray, strategies: List[str]) -> np.ndarray:
        tensor = self._bgr_to_tensor(img)
        for strategy in strategies:
            if strategy == 'super_resolution' and self.fast_mode:
                continue
            if strategy == 'super_resolution':
                tensor = self._super_resolution(tensor)
            elif strategy == 'lighting_correction':
                tensor = self._lighting_correction(tensor)
            elif strategy == 'contrast_enhancement':
                tensor = self._contrast_enhancement(tensor)
            elif strategy == 'sharpen':
                tensor = self._sharpen(tensor)
            elif strategy == 'edge_enhancement':
                tensor = self._edge_enhancement(tensor)
            elif strategy == 'denoise':
                tensor = self._denoise(tensor)
            elif strategy == 'color_enhancement':
                tensor = self._color_enhancement(tensor)
            elif strategy == 'texture_enhancement':
                tensor = self._texture_enhancement(tensor)
            elif strategy == 'overall_enhancement':
                tensor = self._overall_enhancement(tensor)
        return self._tensor_to_bgr(tensor)

    def _super_resolution(self, tensor):
        up = F.interpolate(tensor, scale_factor=1.2, mode='bilinear', align_corners=False)
        _, _, h, w = up.shape
        target_h, target_w = tensor.shape[2:]
        y0 = (h - target_h) // 2
        x0 = (w - target_w) // 2
        return up[:, :, y0:y0 + target_h, x0:x0 + target_w]

    def _lighting_correction(self, tensor):
        gamma = 0.9 if tensor.mean().item() < 0.5 else 1.1
        return torch.clamp(tensor ** gamma, 0, 1)

    def _contrast_enhancement(self, tensor):
        return torch.clamp(tensor * 1.2 + 0.05, 0, 1)

    def _sharpen(self, tensor):
        kernel = torch.tensor([[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
                              device=self.device, dtype=torch.float32)
        kernel = kernel.view(1, 1, 3, 3).repeat(3, 1, 1, 1)
        return torch.clamp(F.conv2d(tensor, kernel, padding=1, groups=3), 0, 1)

    def _edge_enhancement(self, tensor):
        sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                               device=self.device, dtype=torch.float32)
        sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                               device=self.device, dtype=torch.float32)
        sobel_x = sobel_x.view(1, 1, 3, 3).repeat(3, 1, 1, 1)
        sobel_y = sobel_y.view(1, 1, 3, 3).repeat(3, 1, 1, 1)
        grad = torch.abs(F.conv2d(tensor, sobel_x, padding=1, groups=3)) + \
               torch.abs(F.conv2d(tensor, sobel_y, padding=1, groups=3))
        return torch.clamp(tensor + 0.3 * grad, 0, 1)

    def _denoise(self, tensor):
        kernel = torch.ones((1, 1, 3, 3), device=self.device) / 9.0
        kernel = kernel.repeat(3, 1, 1, 1)
        return torch.clamp(F.conv2d(tensor, kernel, padding=1, groups=3), 0, 1)

    def _color_enhancement(self, tensor):
        mean = tensor.mean(dim=(2, 3), keepdim=True)
        return torch.clamp((tensor - mean) * 1.3 + mean, 0, 1)

    def _texture_enhancement(self, tensor):
        blur = F.avg_pool2d(tensor, kernel_size=3, stride=1, padding=1)
        high_freq = tensor - blur
        return torch.clamp(tensor + 0.5 * high_freq, 0, 1)

    def _overall_enhancement(self, tensor):
        tensor = self._lighting_correction(tensor)
        tensor = self._contrast_enhancement(tensor)
        tensor = self._sharpen(tensor)
        return tensor


if __name__ == "__main__":
    trainer = MaterialEnhancementTrainer()
    result = trainer.enhance_to_excellent(
        "test_image.jpg",
        "enhanced_output",
        target_improvement=5.0,
        max_iterations=10
    )
    print(f"增强完成: {result}")
"@ | Set-Content "agents\material_enhancement_trainer.py" -Encoding UTF8

Write-Host "✅ 步骤2完成：已更新增强训练器（改为基于提升幅度）" -ForegroundColor Green

# ============================================
# 步骤3: 更新Streamlit界面（显示提升幅度）
# ============================================
Write-Host "`n步骤3: 更新Streamlit界面..." -ForegroundColor Yellow

# 读取现有文件
$appContent = Get-Content "app\web\material_generator_app.py" -Raw -Encoding UTF8

# 替换增强训练设置部分（第55行）
$appContent = $appContent -replace '        target_score = st\.slider\("目标质量分数", 80, 100, 90, 1\)', '        target_improvement = st.slider("目标提升分数", 3, 10, 5, 1)'

# 替换判断是否需要增强训练的部分（第230行）
$appContent = $appContent -replace '        needs_enhancement = overall_quality < 60\.0', '        needs_enhancement = overall_quality < 50.0  # VisDrone数据集标准降低'

# 替换增强训练调用部分（第297行）
$appContent = $appContent -replace '                                target_score=target_score,', '                                target_improvement=target_improvement,'

# 替换显示增强结果的部分（第307行）
$oldInfo = '                            st.info(f"📊 成功率: {enhancement_result[''success_rate'']:.2f}% | 达标率: {enhancement_result[''achievement_rate'']:.2f}%")'
$newInfo = @'
                            st.info(f"📊 成功率: {enhancement_result['success_rate']:.2f}% | 达标率: {enhancement_result['achievement_rate']:.2f}%")
                            st.info(f"📈 平均提升幅度: {enhancement_result.get('average_improvement', 0):.2f}分")
                            st.info(f"⭐ 优秀({enhancement_result.get('excellent_count', 0)}) | 良好({enhancement_result.get('good_count', 0)}) | 一般({enhancement_result.get('fair_count', 0)}) | 较差({enhancement_result.get('poor_count', 0)})")
'@
$appContent = $appContent -replace [regex]::Escape($oldInfo), $newInfo

# 替换增强历史记录显示部分（第376行）
$oldHistory = "'初始分数': f\"{result.get('enhancement_history', [{}])[0].get('score', 0):.2f}%\" if result.get('enhancement_history') else \"N/A\","
$newHistory = "'初始分数': f\"{result.get('initial_score', 0):.2f}%\","
$appContent = $appContent -replace [regex]::Escape($oldHistory), $newHistory

# 替换提升幅度显示（第378行）
$oldImprovement = "'提升幅度': f\"+{result.get('improvement', 0):.2f}%\","
$newImprovement = "'提升幅度': f\"+{result.get('improvement', 0):.2f}分\","
$appContent = $appContent -replace [regex]::Escape($oldImprovement), $newImprovement

# 替换是否达标显示（第380行）
$oldTarget = "'是否达标': \"✅\" if result.get('target_achieved', False) else \"❌\""
$newTarget = "'质量等级': result.get('quality_level', 'N/A'),"
$appContent = $appContent -replace [regex]::Escape($oldTarget), $newTarget

# 替换图表Y轴标签（第398行）
$appContent = $appContent -replace '                    yaxis_title="提升幅度 \(%\)",', '                    yaxis_title="提升幅度 (分)",'

# 替换图表数据解析（第390行）
$oldYData = "y=[float(item['提升幅度'].lstrip('+').rstrip('%')) for item in enhancement_history_data],"
$newYData = "y=[float(item['提升幅度'].lstrip('+').rstrip('分')) for item in enhancement_history_data],"
$appContent = $appContent -replace [regex]::Escape($oldYData), $newYData

# 保存更新后的文件
$appContent | Set-Content "app\web\material_generator_app.py" -Encoding UTF8

Write-Host "✅ 步骤3完成：已更新Streamlit界面（显示提升幅度）" -ForegroundColor Green

Write-Host "`n✅ 所有更新完成！" -ForegroundColor Green
Write-Host "`n主要改进：" -ForegroundColor Cyan
Write-Host "1. 8维评分标准已降低，适配VisDrone数据集" -ForegroundColor White
Write-Host "2. 增强训练改为基于提升幅度评估（优秀≥8分，良好≥5分，一般≥3分）" -ForegroundColor White
Write-Host "3. UI界面已更新，显示提升幅度和质量等级" -ForegroundColor White
Write-Host "`n现在可以重新运行Streamlit应用测试新标准！" -ForegroundColor Yellow

