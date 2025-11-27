"""
图片多角度生成器 - 增强版（带检测框）
支持真正的无人机3D视角变换，并绘制YOLO检测框
"""

# ========== 关键：在导入任何模块前设置环境变量并拦截libGL加载 ==========
import os
import sys

# 必须在导入numpy等之前设置环境变量
os.environ['OPENCV_DISABLE_OPENCL'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ''
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'

# 阻止加载libGL - 清理LD_LIBRARY_PATH
if 'LD_LIBRARY_PATH' in os.environ:
    paths = os.environ['LD_LIBRARY_PATH'].split(':')
    paths = [p for p in paths if 'libGL' not in p and 'mesa' not in p.lower()]
    os.environ['LD_LIBRARY_PATH'] = ':'.join(paths)

# 使用ctypes拦截dlopen，阻止加载libGL.so.1
try:
    import ctypes
    import ctypes.util
    
    # 获取系统的dlopen函数
    if sys.platform.startswith('linux'):
        libdl = ctypes.CDLL('libdl.so.2')
        dlopen = libdl.dlopen
        dlopen.argtypes = [ctypes.c_char_p, ctypes.c_int]
        dlopen.restype = ctypes.c_void_p
        
        # 保存原始的dlopen
        _original_dlopen = dlopen
        
        # 创建拦截函数
        def _intercept_dlopen(filename, flag):
            if filename:
                filename_str = filename.decode('utf-8', errors='ignore') if isinstance(filename, bytes) else str(filename)
                # 如果尝试加载libGL，返回None（失败但不报错）
                if 'libGL' in filename_str or 'libGL.so' in filename_str:
                    print(f"⚠️ 拦截libGL加载: {filename_str}")
                    return None  # 返回NULL，但不抛出异常
            # 其他库正常加载
            return _original_dlopen(filename, flag)
        
        # 替换dlopen（注意：这需要更复杂的实现，暂时注释）
        # libdl.dlopen = _intercept_dlopen
except:
    pass

import numpy as np

# 延迟导入 OpenCV，避免在模块级别失败
_cv2_available = None
_cv2 = None

def _get_cv2():
    """延迟导入 OpenCV，强制使用 headless 模式，完全阻止libGL加载"""
    global _cv2_available, _cv2
    if _cv2_available is None:
        try:
            # 再次确保环境变量已设置
            import os
            os.environ['OPENCV_DISABLE_OPENCL'] = '1'
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            os.environ['DISPLAY'] = ''
            os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
            
            # 使用subprocess设置环境变量后导入（更彻底的方法）
            import subprocess
            import sys
            
            # 在Linux上，使用LD_PRELOAD来阻止libGL加载
            # 但更简单的方法是：直接导入并捕获错误，然后忽略
            try:
                # 临时重定向stderr以捕获libGL错误
                import io
                import contextlib
                
                # 创建一个假的libGL.so.1模块
                class FakeLibGL:
                    pass
                
                # 在导入cv2前，拦截ImportError
                with contextlib.redirect_stderr(io.StringIO()):
                    import cv2
                    # 测试基本功能
                    _ = cv2.__version__
                    _cv2 = cv2
                    _cv2_available = True
                    print("✅ OpenCV 加载成功（已忽略libGL警告）")
            except Exception as e:
                error_str = str(e)
                # 如果是libGL错误，强制继续使用
                if 'libGL' in error_str or 'libGL.so' in error_str:
                    # 直接导入，忽略错误
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        try:
                            import cv2
                            _cv2 = cv2
                            _cv2_available = True
                            print("✅ OpenCV 加载成功（强制忽略libGL错误）")
                        except:
                            # 如果还是失败，使用PIL降级
                            _cv2_available = False
                            print("⚠️ OpenCV无法加载，将使用PIL降级方案")
                else:
                    raise
        except Exception as e:
            print(f"❌ OpenCV 导入失败: {e}")
            _cv2_available = False
    return _cv2 if _cv2_available else None
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Dict, Optional
import random
import time
from datetime import datetime
import math
import torch

# 延迟导入 YOLO，确保环境变量已设置
# 注意：YOLO在导入时会导入cv2，所以必须在环境变量设置后导入
_YOLO = None
def _get_yolo():
    """延迟导入 YOLO，确保环境变量已设置"""
    global _YOLO
    if _YOLO is None:
        try:
            # 再次确保环境变量已设置（防止ultralytics导入cv2时出错）
            os.environ['OPENCV_DISABLE_OPENCL'] = '1'
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            os.environ['DISPLAY'] = ''
            os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
            
            from ultralytics import YOLO as _YOLO_CLS
            _YOLO = _YOLO_CLS
        except Exception as e:
            # 如果导入失败，返回 None
            print(f"YOLO导入失败: {e}")
            return None
    return _YOLO


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
        self.detector = None
        self.yolo_model_path = yolo_model_path
        
        # 延迟加载YOLO模型，避免在初始化时导入失败
        # 只在真正需要时才加载
        
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
    
    def _generate_with_pil_fallback(
        self,
        input_image_path: str,
        output_dir: str,
        num_generations: int = 8,
        transformations: List[str] = None
    ) -> Dict:
        """使用 PIL 降级方案生成图片（当 OpenCV 不可用时）"""
        input_path = Path(input_image_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not input_path.exists():
            raise FileNotFoundError(f"输入图片不存在: {input_image_path}")
        
        # 使用 PIL 打开图片
        pil_img = Image.open(input_path)
        img_array = np.array(pil_img)
        h, w = img_array.shape[:2] if len(img_array.shape) == 2 else img_array.shape[:2]
        
        # 简单的变换列表（不依赖 OpenCV）
        if transformations is None:
            transformations = ['original', 'rotate_90', 'rotate_180', 'rotate_270', 
                             'flip_horizontal', 'flip_vertical', 'crop_center', 'resize']
        
        selected_transforms = random.sample(transformations, min(num_generations, len(transformations)))
        
        generated_files = []
        metadata = []
        
        for idx, transform_type in enumerate(selected_transforms, 1):
            try:
                if transform_type == 'original':
                    transformed_img = pil_img.copy()
                elif transform_type == 'rotate_90':
                    transformed_img = pil_img.rotate(-90, expand=True)
                elif transform_type == 'rotate_180':
                    transformed_img = pil_img.rotate(180, expand=False)
                elif transform_type == 'rotate_270':
                    transformed_img = pil_img.rotate(90, expand=True)
                elif transform_type == 'flip_horizontal':
                    transformed_img = pil_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                elif transform_type == 'flip_vertical':
                    transformed_img = pil_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                elif transform_type == 'crop_center':
                    crop_size = min(w, h) // 2
                    left = (w - crop_size) // 2
                    top = (h - crop_size) // 2
                    transformed_img = pil_img.crop((left, top, left + crop_size, top + crop_size))
                elif transform_type == 'resize':
                    new_size = (w // 2, h // 2)
                    transformed_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    transformed_img = pil_img.copy()
                
                output_filename = f"generated_{idx:03d}_{transform_type}.jpg"
                output_file = output_path / output_filename
                transformed_img.save(str(output_file), 'JPEG', quality=95)
                
                generated_files.append(str(output_file))
                metadata.append({
                    'index': idx,
                    'transform_type': transform_type,
                    'file_path': str(output_file)
                })
            except Exception as e:
                print(f"生成 {transform_type} 失败: {e}")
                continue
        
        return {
            'success': True,
            'num_generated': len(generated_files),
            'generated_files': generated_files,
            'metadata': metadata,
            'confidence_statistics': {}
        }

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
        # 延迟导入 OpenCV - 使用更激进的方法阻止libGL错误
        import warnings
        import io
        import contextlib
        
        # 完全忽略所有警告和错误
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stderr(io.StringIO()):
                cv2 = _get_cv2()
                if cv2 is None:
                    # 强制导入，完全忽略libGL错误
                    try:
                        import os
                        os.environ['OPENCV_DISABLE_OPENCL'] = '1'
                        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
                        os.environ['DISPLAY'] = ''
                        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
                        
                        # 直接导入，不捕获任何错误
                        import cv2
                        print("✅ OpenCV 在方法内成功加载（强制模式）")
                    except ImportError as e:
                        # ImportError不应该发生，因为opencv-python-headless已安装
                        raise RuntimeError(f"OpenCV 未安装: {e}")
                    except Exception as e:
                        error_str = str(e)
                        # 如果是libGL错误，强制继续
                        if 'libGL' in error_str or 'libGL.so' in error_str:
                            # 完全忽略错误，强制导入
                            import sys
                            old_stderr = sys.stderr
                            sys.stderr = io.StringIO()
                            try:
                                import cv2
                                print("✅ OpenCV 加载成功（已忽略libGL错误）")
                            finally:
                                sys.stderr = old_stderr
                        else:
                            raise RuntimeError(f"OpenCV 加载失败: {e}")
        
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

        # 极端变换在实际素材中过于失真，这里默认关闭
        extreme_transforms = []
        
        # 合并所有变换类型
        all_transforms = transformations + extreme_transforms
        
        # 强制选择不同的变换，确保每个都不同
        if num_generations > len(all_transforms):
            selected_transforms = all_transforms.copy()
            # 重复使用但添加唯一标识
            for i in range(num_generations - len(all_transforms)):
                base = random.choice(all_transforms)
                selected_transforms.append(f"{base}_unique_{i}")
        else:
            selected_transforms = random.sample(all_transforms, num_generations)
        
        # 强制打乱，确保顺序随机
        random.shuffle(selected_transforms)

        generated_files = []
        metadata = []
        all_detections = []  # 存储所有检测结果用于统计

        for idx, transform_type in enumerate(selected_transforms, 1):
            try:
                # 为每次变换生成唯一的随机种子，确保每次变换都不同
                # 使用更激进的随机种子生成（基于时间、索引、哈希）
                seed_base = int(time.time() * 1000000) + idx * 10000 + hash(transform_type) % 100000 + random.randint(1, 1000000)
                random.seed(seed_base)
                np.random.seed(seed_base % 2**32)
                
                # 传递索引作为额外随机因子，并添加时间戳确保唯一性
                random_factor = idx * 10000 + int(time.time() * 1000) % 100000 + hash(transform_type) % 10000
                
                # 强制应用变换（不使用copy，直接变换）
                transformed_img = self._apply_transformation(img, transform_type, h, w, random_factor=random_factor)
                
                cv2 = _get_cv2()
                if cv2 is not None and transformed_img.shape == img.shape:
                    diff = np.abs(transformed_img.astype(np.float32) - img.astype(np.float32))
                    mean_diff = np.mean(diff)
                    if mean_diff < 6.0:
                        center = (w // 2, h // 2)
                        angle = random.uniform(-15, 15)
                        scale = random.uniform(0.95, 1.05)
                        M = cv2.getRotationMatrix2D(center, angle, scale)
                        transformed_img = cv2.warpAffine(
                            transformed_img, M, (w, h),
                            borderMode=cv2.BORDER_REFLECT
                        )
                        tx = random.uniform(-w * 0.05, w * 0.05)
                        ty = random.uniform(-h * 0.05, h * 0.05)
                        M[0, 2] += tx
                        M[1, 2] += ty
                        transformed_img = cv2.warpAffine(
                            transformed_img, M, (w, h),
                            borderMode=cv2.BORDER_REFLECT
                        )
                
                # 进行目标检测并绘制检测框（每次使用不同的置信度阈值）
                detections = []
                if self.draw_boxes:
                    # 为每次检测添加随机变化，但降低阈值以检测更多目标
                    # 使用更低的置信度阈值，确保检测到更多目标
                    base_conf = 0.1 + (idx % 10) * 0.03  # 0.1-0.37之间变化，10个不同值
                    # 添加额外的随机偏移（更小的范围，避免过度变化）
                    conf_variation = random.uniform(-0.03, 0.03)
                    final_conf = max(0.08, min(0.4, base_conf + conf_variation))  # 降低最大阈值，检测更多目标
                    
                    # 检测前再次确保图片已经变换（双重验证，但使用温和变换）
                    if cv2 is not None and transformed_img.shape == img.shape:
                        diff_check = np.abs(transformed_img.astype(np.float32) - img.astype(np.float32))
                        if np.mean(diff_check) < 10.0:  # 如果差异还是太小
                            # 应用温和的变换（避免过度扭曲）
                            center = (w // 2, h // 2)
                            angle = random.uniform(-25, 25)  # 减小角度
                            scale = random.uniform(0.9, 1.1)  # 减小缩放
                            M = cv2.getRotationMatrix2D(center, angle, scale)
                            transformed_img = cv2.warpAffine(transformed_img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                            
                            # 再添加温和的透视变换
                            offset = random.uniform(0.05, 0.15)  # 减小偏移
                            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                            pts2 = np.float32([
                                [w*offset, h*offset], 
                                [w*(1-offset), h*offset], 
                                [w*0.1, h*0.9], 
                                [w*0.9, h*0.9]
                            ])
                            M2 = cv2.getPerspectiveTransform(pts1, pts2)
                            transformed_img = cv2.warpPerspective(transformed_img, M2, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                    
                    transformed_img, detections = self._detect_and_draw_boxes(transformed_img, conf_threshold=final_conf)
                    all_detections.extend(detections)
                
                output_filename = f"generated_{idx:03d}_{transform_type}.jpg"
                output_file = output_path / output_filename
                
                # 使用 OpenCV 保存，如果失败则使用 PIL
                try:
                    cv2.imwrite(str(output_file), transformed_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                except Exception:
                    # 降级方案：使用 PIL 保存
                    if len(transformed_img.shape) == 3:
                        # BGR to RGB
                        pil_img = Image.fromarray(transformed_img[:, :, ::-1])
                    else:
                        pil_img = Image.fromarray(transformed_img)
                    pil_img.save(str(output_file), 'JPEG', quality=95)

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

        # 计算平均置信度统计（确保总是返回数据）
        confidence_stats = self._calculate_confidence_stats(all_detections)
        
        # 如果没有检测数据，创建一个空的但有效的结构
        if not confidence_stats or len(confidence_stats) == 0:
            confidence_stats = {
                '_all_confidences': [],
                '_total_detections': 0
            }
        else:
            # 确保_all_confidences存在
            if '_all_confidences' not in confidence_stats:
                # 从其他统计中提取
                all_conf = []
                for key, value in confidence_stats.items():
                    if isinstance(value, dict) and 'confidences' in value:
                        all_conf.extend(value['confidences'])
                confidence_stats['_all_confidences'] = all_conf
            confidence_stats['_total_detections'] = len(confidence_stats.get('_all_confidences', []))

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
                'confidence_statistics': confidence_stats,
                'total_detections': len(all_detections)
            }, f, ensure_ascii=False, indent=2)

        return {
            'success': True,
            'original_image': str(input_path),
            'output_dir': str(output_path),
            'num_generated': len(generated_files),
            'generated_files': generated_files,
            'metadata_file': str(metadata_file),
            'confidence_statistics': confidence_stats,
            'total_detections': len(all_detections)
        }

    def _detect_and_draw_boxes(self, img: np.ndarray, conf_threshold: float = None) -> tuple:
        """
        检测目标并绘制检测框
        
        参数:
            img: 输入图片
            conf_threshold: 置信度阈值，如果为None则自动计算
        
        返回:
            (绘制后的图片, 检测结果列表)
        """
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，返回原图和空检测结果
            return img, []
        
        # 延迟加载 YOLO 模型
        if self.detector is None:
            YOLO = _get_yolo()
            if YOLO is None:
                return img, []
            try:
                if self.yolo_model_path and Path(self.yolo_model_path).exists():
                    self.detector = YOLO(self.yolo_model_path)
                else:
                    self.detector = YOLO('yolov8n.pt')
            except Exception as e:
                # 如果加载失败，返回原图
                return img, []
        
        try:
            # 改进的检测算法：使用动态置信度阈值
            if conf_threshold is None:
                base_conf = 0.25
                # 根据图片亮度调整置信度（暗图需要更低阈值）
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
                mean_brightness = np.mean(gray)
                if mean_brightness < 50:  # 暗图
                    conf_threshold = base_conf * 0.7
                elif mean_brightness > 200:  # 亮图
                    conf_threshold = base_conf * 1.2
                else:
                    conf_threshold = base_conf
            
            # 使用动态NMS和置信度阈值（每次检测都不同）
            # 根据图片内容动态调整IOU
            iou_threshold = 0.4 + (hash(str(img.shape)) % 3) * 0.05  # 0.4-0.5之间
            results = self.detector(img, verbose=False, conf=conf_threshold, iou=iou_threshold)
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
        """计算各类别的置信度统计（包含所有置信度值）"""
        if not all_detections:
            return {}
        
        # 按类别分组统计，保留所有置信度值
        class_stats = {}
        all_confidences = []  # 存储所有置信度值
        
        for det in all_detections:
            class_name = det['class_name']
            confidence = det['confidence']
            all_confidences.append(confidence)
            
            if class_name not in class_stats:
                class_stats[class_name] = {
                    'count': 0,
                    'confidences': [],  # 保留所有置信度值
                    'avg_confidence': 0.0
                }
            class_stats[class_name]['count'] += 1
            class_stats[class_name]['confidences'].append(confidence)
        
        # 计算平均置信度（但保留所有置信度值）
        for class_name, stats in class_stats.items():
            stats['avg_confidence'] = np.mean(stats['confidences'])
            stats['max_confidence'] = np.max(stats['confidences'])
            stats['min_confidence'] = np.min(stats['confidences'])
            # 不删除confidences，保留所有值用于饼图显示
        
        # 添加全局统计
        class_stats['_all_confidences'] = all_confidences
        
        # 按平均置信度排序
        sorted_stats = dict(sorted(
            {k: v for k, v in class_stats.items() if k != '_all_confidences'}.items(),
            key=lambda x: x[1]['avg_confidence'],
            reverse=True
        ))
        
        # 添加全局统计到结果
        sorted_stats['_all_confidences'] = all_confidences
        
        return sorted_stats

    def _apply_transformation(self, img: np.ndarray, transform_type: str, h: int, w: int, random_factor: int = 1) -> np.ndarray:
        """应用指定的3D视角变换（改进版：添加随机参数变化，确保每次变换都不同）"""
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，返回原图
            return img.copy()
        
        result = img.copy()
        
        # 处理带变体后缀的变换类型
        base_transform = transform_type.split('_var')[0].split('_extra')[0]
        has_extra = '_extra' in transform_type
        
        # 强制所有变换都使用随机参数（除了original）
        # 使用random_factor确保每次变换都不同
        rng = np.random.RandomState(random_factor * 1000 + hash(transform_type) % 10000)
        
        if base_transform == 'original':
            # 即使是original，也添加随机变化
            center = (w // 2, h // 2)
            angle = rng.uniform(-8, 8)
            scale = rng.uniform(0.95, 1.05)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            return result
        
        # ========== 真正的3D视角变换 ==========
        
        elif base_transform == 'top_down_90':
            # 强制使用随机参数，让角度更刁钻
            offset1 = rng.uniform(0.02, 0.18)  # 更大的变化范围
            offset2 = rng.uniform(0.02, 0.18)
            rotation = rng.uniform(-10, 10)  # 更大的旋转角度
            # 添加额外的倾斜
            tilt_x = rng.uniform(-0.1, 0.1)
            tilt_y = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset1 + tilt_x), h*(offset1 + tilt_y)], 
                [w*(1-offset1 + tilt_x), h*(offset1 - tilt_y)], 
                [w*(offset2 - tilt_x), h*(1-offset2 + tilt_y)], 
                [w*(1-offset2 - tilt_x), h*(1-offset2 - tilt_y)]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            # 应用旋转
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'top_down_60':
            offset = rng.uniform(0.02, 0.2)
            rotation = rng.uniform(-12, 12)
            tilt = rng.uniform(-0.08, 0.08)
            top_y = rng.uniform(0.02, 0.1)
            bottom_y = rng.uniform(0.9, 0.98)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*top_y], 
                [w*(1-offset + tilt), h*top_y], 
                [w*(0.05 - tilt), h*bottom_y], 
                [w*(0.95 - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'top_down_45':
            offset = rng.uniform(0.05, 0.25)
            rotation = rng.uniform(-15, 15)
            tilt = rng.uniform(-0.1, 0.1)
            top_y = rng.uniform(0.05, 0.15)
            bottom_y = rng.uniform(0.85, 0.95)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*top_y], 
                [w*(1-offset + tilt), h*top_y], 
                [w*(0.1 - tilt), h*bottom_y], 
                [w*(0.9 - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'low_angle_30':
            offset = rng.uniform(0.02, 0.2)
            rotation = rng.uniform(-15, 15)
            top_y = rng.uniform(0.2, 0.4)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*top_y], 
                [w*(1-offset + tilt), h*top_y], 
                [w*(0.05 - tilt), h*0.95], 
                [w*(0.95 - tilt), h*0.95]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'low_angle_45':
            offset = rng.uniform(0.05, 0.25)
            rotation = rng.uniform(-18, 18)
            top_y = rng.uniform(0.3, 0.5)
            tilt = rng.uniform(-0.12, 0.12)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*top_y], 
                [w*(1-offset + tilt), h*top_y], 
                [w*(0.0 - tilt), h*1.0], 
                [w*(1.0 - tilt), h*1.0]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'side_view_left':
            offset = rng.uniform(0.6, 0.8)
            rotation = rng.uniform(-20, 20)
            top_y = rng.uniform(0.05, 0.15)
            bottom_y = rng.uniform(0.85, 0.95)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(0.0 + tilt), h*top_y], 
                [w*(offset + tilt), h*top_y], 
                [w*(0.0 - tilt), h*bottom_y], 
                [w*(offset - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'side_view_right':
            offset = rng.uniform(0.2, 0.4)
            rotation = rng.uniform(-20, 20)
            top_y = rng.uniform(0.05, 0.15)
            bottom_y = rng.uniform(0.85, 0.95)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*top_y], 
                [w*(1.0 + tilt), h*top_y], 
                [w*(offset - tilt), h*bottom_y], 
                [w*(1.0 - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'oblique_30':
            angle = rng.uniform(20, 40)
            scale = rng.uniform(0.9, 1.1)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.02, 0.2)
            tilt = rng.uniform(-0.12, 0.12)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*(offset - tilt)], 
                [w*(1-offset + tilt), h*(offset + tilt)], 
                [w*(0.0 - tilt), h*0.9], 
                [w*(1.0 - tilt), h*0.9]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'oblique_45':
            angle = rng.uniform(35, 55)
            scale = rng.uniform(0.85, 1.15)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.05, 0.25)
            tilt = rng.uniform(-0.15, 0.15)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*(offset - tilt)], 
                [w*(1-offset + tilt), h*(offset + tilt)], 
                [w*(0.05 - tilt), h*0.95], 
                [w*(0.95 - tilt), h*0.95]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'oblique_60':
            angle = rng.uniform(50, 70)
            scale = rng.uniform(0.8, 1.2)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.1, 0.3)
            tilt = rng.uniform(-0.18, 0.18)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*(offset - tilt)], 
                [w*(1-offset + tilt), h*(offset + tilt)], 
                [w*(0.1 - tilt), h*0.9], 
                [w*(0.9 - tilt), h*0.9]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'bird_eye' or transform_type == 'bird_eye':
            offset = rng.uniform(0.02, 0.12)
            rotation = rng.uniform(-25, 25)
            scale = rng.uniform(0.85, 0.95)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*offset, h*offset], 
                [w*(1-offset), h*offset], 
                [w*offset, h*(1-offset)], 
                [w*(1-offset), h*(1-offset)]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w/2, h/2)
            M_scale = cv2.getRotationMatrix2D(center, rotation, scale)
            result = cv2.warpAffine(result, M_scale, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'worm_eye' or transform_type == 'worm_eye':
            offset_x = rng.uniform(0.15, 0.25)
            center_y = rng.uniform(0.45, 0.55)
            rotation = rng.uniform(-30, 30)
            tilt = rng.uniform(-0.15, 0.15)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset_x + tilt), h*center_y], 
                [w*(1-offset_x + tilt), h*center_y], 
                [w*(0.0 - tilt), h*1.0], 
                [w*(1.0 - tilt), h*1.0]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'diagonal_up' or transform_type == 'diagonal_up':
            top_y = rng.uniform(0.1, 0.3)
            bottom_y = rng.uniform(0.7, 0.9)
            left_x = rng.uniform(0.0, 0.2)
            right_x = rng.uniform(0.8, 1.0)
            rotation = rng.uniform(-20, 20)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*left_x, h*top_y], 
                [w*right_x, h*0.0], 
                [w*(left_x + 0.2), h*bottom_y], 
                [w*1.0, h*(bottom_y - 0.1)]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'diagonal_down' or transform_type == 'diagonal_down':
            top_y = rng.uniform(0.0, 0.2)
            bottom_y = rng.uniform(0.7, 0.9)
            left_x = rng.uniform(0.0, 0.2)
            right_x = rng.uniform(0.8, 1.0)
            rotation = rng.uniform(-20, 20)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(left_x + 0.2), h*top_y], 
                [w*1.0, h*(top_y + 0.1)], 
                [w*left_x, h*bottom_y], 
                [w*right_x, h*1.0]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'tilt_left' or transform_type == 'tilt_left':
            angle = rng.uniform(-25, -5)
            rotation2 = rng.uniform(-10, 10)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.05, 0.15)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*0.0], 
                [w*(1-offset + tilt), h*0.1], 
                [w*(offset - tilt), h*1.0], 
                [w*(1-offset - tilt), h*0.9]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            M_rot2 = cv2.getRotationMatrix2D(center, rotation2, 1.0)
            result = cv2.warpAffine(result, M_rot2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'tilt_right' or transform_type == 'tilt_right':
            angle = rng.uniform(5, 25)
            rotation2 = rng.uniform(-10, 10)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.05, 0.15)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*0.1], 
                [w*(1-offset + tilt), h*0.0], 
                [w*(offset - tilt), h*0.9], 
                [w*(1-offset - tilt), h*1.0]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            M_rot2 = cv2.getRotationMatrix2D(center, rotation2, 1.0)
            result = cv2.warpAffine(result, M_rot2, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'panoramic_wide' or transform_type == 'panoramic_wide':
            top_y = rng.uniform(0.1, 0.2)
            bottom_y = rng.uniform(0.8, 0.9)
            rotation = rng.uniform(-15, 15)
            tilt = rng.uniform(-0.08, 0.08)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(0.0 + tilt), h*top_y], 
                [w*(1.0 + tilt), h*top_y], 
                [w*(0.0 - tilt), h*bottom_y], 
                [w*(1.0 - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'panoramic_narrow' or transform_type == 'panoramic_narrow':
            offset = rng.uniform(0.05, 0.15)
            rotation = rng.uniform(-20, 20)
            tilt = rng.uniform(-0.1, 0.1)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*0.0], 
                [w*(1-offset + tilt), h*0.0], 
                [w*(offset - tilt), h*1.0], 
                [w*(1-offset - tilt), h*1.0]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'zoom_extreme' or transform_type == 'zoom_extreme':
            scale = rng.uniform(1.3, 1.8)
            rotation = rng.uniform(-30, 30)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotation, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        
        elif base_transform == 'rotate_3d_45' or transform_type == 'rotate_3d_45':
            angle = rng.uniform(35, 55)
            scale = rng.uniform(0.9, 1.1)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            offset = rng.uniform(0.05, 0.15)
            tilt = rng.uniform(-0.12, 0.12)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(offset + tilt), h*(offset - tilt)], 
                [w*(1-offset + tilt), h*(offset + tilt)], 
                [w*(offset - tilt), h*(1-offset + tilt)], 
                [w*(1-offset - tilt), h*(1-offset - tilt)]
            ])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'rotate_3d_90' or transform_type == 'rotate_3d_90':
            angle = rng.uniform(80, 100)
            scale = rng.uniform(0.85, 1.15)
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, scale)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        
        elif base_transform == 'perspective_strong' or transform_type == 'perspective_strong':
            top_offset = rng.uniform(0.15, 0.25)
            bottom_y = rng.uniform(0.95, 1.0)
            rotation = rng.uniform(-25, 25)
            tilt = rng.uniform(-0.15, 0.15)
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*(top_offset + tilt), h*top_offset], 
                [w*(1-top_offset + tilt), h*top_offset], 
                [w*(0.0 - tilt), h*bottom_y], 
                [w*(1.0 - tilt), h*bottom_y]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            center = (w // 2, h // 2)
            M_rot = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'fisheye_effect' or transform_type == 'fisheye_effect':
            h, w = result.shape[:2]
            center_x, center_y = w // 2, h // 2
            max_radius = min(center_x, center_y)
            # 使用随机强度
            strength = rng.uniform(0.5, 0.9)
            offset_x = rng.uniform(-w*0.05, w*0.05)
            offset_y = rng.uniform(-h*0.05, h*0.05)
            map_x = np.zeros((h, w), dtype=np.float32)
            map_y = np.zeros((h, w), dtype=np.float32)
            for y in range(h):
                for x in range(w):
                    dx = x - center_x + offset_x
                    dy = y - center_y + offset_y
                    r = math.sqrt(dx*dx + dy*dy) / max_radius
                    if r > 0:
                        theta = math.atan2(dy, dx)
                        r_new = r * r * strength
                        map_x[y, x] = center_x + r_new * max_radius * math.cos(theta)
                        map_y[y, x] = center_y + r_new * max_radius * math.sin(theta)
                    else:
                        map_x[y, x] = x
                        map_y[y, x] = y
            result = cv2.remap(result, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        # 添加极端变换类型
        elif base_transform.startswith('extreme_'):
            # 所有极端变换都使用极端参数
            if 'top_down' in base_transform:
                offset1 = rng.uniform(0.0, 0.25)
                offset2 = rng.uniform(0.0, 0.25)
                rotation = rng.uniform(-60, 60)
                tilt = rng.uniform(-0.2, 0.2)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                pts2 = np.float32([
                    [w*(offset1 + tilt), h*(offset1 - tilt)], 
                    [w*(1-offset1 + tilt), h*(offset1 + tilt)], 
                    [w*(offset2 - tilt), h*(1-offset2 - tilt)], 
                    [w*(1-offset2 - tilt), h*(1-offset2 + tilt)]
                ])
                M = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
                center = (w // 2, h // 2)
                M_rot = cv2.getRotationMatrix2D(center, rotation, rng.uniform(0.7, 1.3))
                result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
                
            elif 'low_angle' in base_transform:
                offset = rng.uniform(0.0, 0.3)
                rotation = rng.uniform(-60, 60)
                top_y = rng.uniform(0.1, 0.5)
                tilt = rng.uniform(-0.25, 0.25)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                pts2 = np.float32([
                    [w*(offset + tilt), h*top_y], 
                    [w*(1-offset + tilt), h*top_y], 
                    [w*0.0, h*1.0], 
                    [w*1.0, h*1.0]
                ])
                M = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
                center = (w // 2, h // 2)
                M_rot = cv2.getRotationMatrix2D(center, rotation, rng.uniform(0.6, 1.4))
                result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
                
            elif 'side' in base_transform:
                offset = rng.uniform(0.1, 0.9) if 'left' in base_transform else rng.uniform(0.1, 0.9)
                rotation = rng.uniform(-60, 60)
                tilt = rng.uniform(-0.3, 0.3)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                if 'left' in base_transform:
                    pts2 = np.float32([
                        [w*0.0, h*0.0], 
                        [w*offset, h*0.0], 
                        [w*0.0, h*1.0], 
                        [w*offset, h*1.0]
                    ])
                else:
                    pts2 = np.float32([
                        [w*offset, h*0.0], 
                        [w*1.0, h*0.0], 
                        [w*offset, h*1.0], 
                        [w*1.0, h*1.0]
                    ])
                M = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
                center = (w // 2, h // 2)
                M_rot = cv2.getRotationMatrix2D(center, rotation, rng.uniform(0.7, 1.3))
                result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
                
            elif 'oblique' in base_transform or 'diagonal' in base_transform:
                angle = rng.uniform(0, 90)
                scale = rng.uniform(0.5, 1.5)
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, scale)
                result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                offset = rng.uniform(0.0, 0.3)
                tilt = rng.uniform(-0.3, 0.3)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                pts2 = np.float32([
                    [w*(offset + tilt), h*(offset - tilt)], 
                    [w*(1-offset + tilt), h*(offset + tilt)], 
                    [w*(0.0 - tilt), h*0.9], 
                    [w*(1.0 - tilt), h*0.9]
                ])
                M2 = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
                
            elif 'tilt' in base_transform:
                angle = rng.uniform(-60, 60)
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, rng.uniform(0.7, 1.3))
                result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                offset = rng.uniform(0.0, 0.2)
                tilt = rng.uniform(-0.25, 0.25)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                pts2 = np.float32([
                    [w*(offset + tilt), h*0.0], 
                    [w*(1-offset + tilt), h*0.1], 
                    [w*(offset - tilt), h*1.0], 
                    [w*(1-offset - tilt), h*0.9]
                ])
                M2 = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
                
            elif 'zoom' in base_transform:
                scale = rng.uniform(1.5, 2.5) if 'in' in base_transform else rng.uniform(0.4, 0.7)
                rotation = rng.uniform(-45, 45)
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, rotation, scale)
                result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                
            elif 'rotate' in base_transform:
                angle = rng.uniform(0, 180)
                scale = rng.uniform(0.6, 1.4)
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, scale)
                result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
                
            elif 'perspective' in base_transform:
                offset = rng.uniform(0.0, 0.3)
                rotation = rng.uniform(-45, 45)
                tilt = rng.uniform(-0.3, 0.3)
                pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
                pts2 = np.float32([
                    [w*(offset + tilt), h*offset], 
                    [w*(1-offset + tilt), h*offset], 
                    [w*0.0, h*1.0], 
                    [w*1.0, h*1.0]
                ])
                M = cv2.getPerspectiveTransform(pts1, pts2)
                result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
                center = (w // 2, h // 2)
                M_rot = cv2.getRotationMatrix2D(center, rotation, rng.uniform(0.7, 1.3))
                result = cv2.warpAffine(result, M_rot, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        # 最后添加小幅变换，但不要过度扭曲（使用更温和的参数）
        # 只对非original变换添加，且使用更小的参数范围
        if base_transform != 'original':
            final_rotation = rng.uniform(-5, 5)  # 减小旋转范围
            final_scale = rng.uniform(0.98, 1.02)  # 减小缩放范围
            center = (w // 2, h // 2)
            M_final = cv2.getRotationMatrix2D(center, final_rotation, final_scale)
            result = cv2.warpAffine(result, M_final, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        
        return result


if __name__ == "__main__":
    generator = ImageMultiAngleGenerator()
    result = generator.generate_multi_angle_images(
        input_image_path="test_image.jpg",
        output_dir="generated",
        num_generations=8
    )
    print(f"生成了 {result['num_generated']} 张图片")


