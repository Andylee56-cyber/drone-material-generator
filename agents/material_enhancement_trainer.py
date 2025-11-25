"""
GPU加速版素材自动增强训练器（基于提升幅度评估）
"""
import numpy as np
try:
    import cv2
except ImportError:
    try:
        import cv2.cv2 as cv2
    except ImportError:
        try:
            import sys
            import importlib.util
            spec = importlib.util.find_spec("cv2")
            if spec is None:
                raise ImportError("cv2 module not found")
            import cv2
        except Exception:
            raise ImportError(
                "OpenCV (cv2) is not installed. "
                "Please ensure 'opencv-python-headless==4.5.4.62' is in requirements.txt. "
                "If the error persists, try: pip install opencv-python-headless"
            )
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
