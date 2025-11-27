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

        # 改进的随机选择算法：确保角度多样化和刁钻
        # 优先选择不同的变换类型，避免重复
        if num_generations > len(transformations):
            selected_transforms = transformations.copy()
            # 添加更多随机变化
            for _ in range(num_generations - len(transformations)):
                # 随机选择基础变换，然后添加随机参数变化
                base_transform = random.choice(transformations)
                # 添加随机后缀表示参数变化
                selected_transforms.append(f"{base_transform}_var{random.randint(1, 5)}")
            random.shuffle(selected_transforms)
        else:
            # 确保选择不同的变换
            selected_transforms = random.sample(transformations, num_generations)
            random.shuffle(selected_transforms)
        
        # 添加随机旋转和缩放变化，让角度更刁钻
        for i in range(len(selected_transforms)):
            if random.random() < 0.3:  # 30%概率添加额外变换
                selected_transforms[i] = f"{selected_transforms[i]}_extra"

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
            # 根据图片质量调整置信度阈值，让检测更准确
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
            
            # 使用更严格的NMS和置信度阈值
            results = self.detector(img, verbose=False, conf=conf_threshold, iou=0.45)
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
        """应用指定的3D视角变换（改进版：添加随机参数变化）"""
        cv2 = _get_cv2()
        if cv2 is None:
            # 如果 OpenCV 不可用，返回原图
            return img.copy()
        
        result = img.copy()
        
        # 处理带变体后缀的变换类型
        base_transform = transform_type.split('_var')[0].split('_extra')[0]
        has_extra = '_extra' in transform_type
        
        if base_transform == 'original':
            if has_extra:
                # 添加轻微的随机旋转和缩放
                center = (w // 2, h // 2)
                angle = random.uniform(-5, 5)
                scale = random.uniform(0.98, 1.02)
                M = cv2.getRotationMatrix2D(center, angle, scale)
                result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            return result
        
        # ========== 真正的3D视角变换 ==========
        
        elif base_transform == 'top_down_90':
            # 添加随机变化，让角度更刁钻
            if has_extra:
                offset1 = random.uniform(0.05, 0.15)
                offset2 = random.uniform(0.05, 0.15)
            else:
                offset1, offset2 = 0.1, 0.1
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([
                [w*offset1, h*offset1], 
                [w*(1-offset1), h*offset1], 
                [w*offset2, h*(1-offset2)], 
                [w*(1-offset2), h*(1-offset2)]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'top_down_60':
            offset = random.uniform(0.05, 0.15) if has_extra else 0.1
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*0.05], [w*(1-offset), h*0.05], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'top_down_45':
            offset = random.uniform(0.1, 0.2) if has_extra else 0.15
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*0.1], [w*(1-offset), h*0.1], [w*0.1, h*0.9], [w*0.9, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'low_angle_30':
            offset = random.uniform(0.05, 0.15) if has_extra else 0.1
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*0.3], [w*(1-offset), h*0.3], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'low_angle_45':
            offset = random.uniform(0.1, 0.2) if has_extra else 0.15
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*0.4], [w*(1-offset), h*0.4], [w*0.0, h*1.0], [w*1.0, h*1.0]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'side_view_left':
            offset = random.uniform(0.65, 0.75) if has_extra else 0.7
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*0.0, h*0.1], [w*offset, h*0.1], [w*0.0, h*0.9], [w*offset, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'side_view_right':
            offset = random.uniform(0.25, 0.35) if has_extra else 0.3
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*0.1], [w*1.0, h*0.1], [w*offset, h*0.9], [w*1.0, h*0.9]])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        elif base_transform == 'oblique_30':
            angle = random.uniform(25, 35) if has_extra else 30
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            offset = random.uniform(0.05, 0.15) if has_extra else 0.1
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*offset], [w*(1-offset), h*offset], [w*0.0, h*0.9], [w*1.0, h*0.9]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'oblique_45':
            angle = random.uniform(40, 50) if has_extra else 45
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            offset = random.uniform(0.1, 0.2) if has_extra else 0.15
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*offset], [w*(1-offset), h*offset], [w*0.05, h*0.95], [w*0.95, h*0.95]])
            M2 = cv2.getPerspectiveTransform(pts1, pts2)
            result = cv2.warpPerspective(result, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
            
        elif base_transform == 'oblique_60':
            angle = random.uniform(55, 65) if has_extra else 60
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            offset = random.uniform(0.15, 0.25) if has_extra else 0.2
            pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
            pts2 = np.float32([[w*offset, h*offset], [w*(1-offset), h*offset], [w*0.1, h*0.9], [w*0.9, h*0.9]])
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


