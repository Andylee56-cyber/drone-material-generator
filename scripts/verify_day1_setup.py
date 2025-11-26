"""
Day 1 环境搭建验证脚本
验证所有依赖和项目结构是否正确配置
"""

import sys
import os
from pathlib import Path
import subprocess

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """检查Python版本"""
    print_header("1. 检查Python版本")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("[OK] Python版本符合要求 (>= 3.10)")
        return True
    else:
        print("[ERROR] Python版本不符合要求，需要 >= 3.10")
        return False

def check_conda_environment():
    """检查Conda环境"""
    print_header("2. 检查Conda环境")
    env_name = os.environ.get('CONDA_DEFAULT_ENV', '')
    print(f"当前Conda环境: {env_name}")
    
    if 'drone_vision_advanced' in env_name:
        print("[OK] Conda环境正确 (drone_vision_advanced)")
        return True
    else:
        print("[WARNING] 警告: 当前环境不是 'drone_vision_advanced'")
        print("   请运行: conda activate drone_vision_advanced")
        return False

def check_pytorch():
    """检查PyTorch安装和GPU支持"""
    print_header("3. 检查PyTorch安装")
    try:
        import torch
        print(f"[OK] PyTorch版本: {torch.__version__}")
        
        # 检查CUDA
        if torch.cuda.is_available():
            print(f"[OK] CUDA可用")
            print(f"   CUDA版本: {torch.version.cuda}")
            print(f"   GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("[WARNING] CUDA不可用（将使用CPU模式）")
            print("   如果应该有GPU，请检查CUDA安装")
            return True  # CPU模式也可以继续
    except ImportError:
        print("[ERROR] PyTorch未安装")
        return False

def check_dependencies():
    """检查关键依赖包"""
    print_header("4. 检查关键依赖包")
    
    required_packages = {
        'torch': 'PyTorch',
        'torchvision': 'TorchVision',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'albumentations': 'Albumentations',
        'skimage': 'scikit-image',
        'rasterio': 'Rasterio',
        'spectral': 'Spectral',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'streamlit': 'Streamlit',
        'redis': 'Redis',
        'psycopg2': 'PostgreSQL',
    }
    
    optional_packages = {
        'segmentation_models_pytorch': 'Segmentation Models',
        'mmseg': 'MMSegmentation',
        'mmcv': 'MMCV',
    }
    
    all_ok = True
    
    # 检查必需包
    print("\n必需依赖包:")
    for module_name, package_name in required_packages.items():
        try:
            if module_name == 'cv2':
                import cv2
                print(f"  [OK] {package_name}: {cv2.__version__}")
            elif module_name == 'skimage':
                import skimage
                print(f"  [OK] {package_name}: {skimage.__version__}")
            elif module_name == 'psycopg2':
                import psycopg2
                print(f"  [OK] {package_name}: {psycopg2.__version__}")
            else:
                module = __import__(module_name)
                version = getattr(module, '__version__', '已安装')
                print(f"  [OK] {package_name}: {version}")
        except ImportError:
            print(f"  [ERROR] {package_name}: 未安装")
            all_ok = False
    
    # 检查可选包
    print("\n可选依赖包:")
    for module_name, package_name in optional_packages.items():
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', '已安装')
            print(f"  [OK] {package_name}: {version}")
        except ImportError:
            print(f"  [WARNING] {package_name}: 未安装（可选）")
    
    return all_ok

def check_project_structure():
    """检查项目结构"""
    print_header("5. 检查项目结构")
    
    required_dirs = [
        'backend/algorithms/segmentation/models',
        'backend/algorithms/segmentation/losses',
        'backend/algorithms/tracking',
        'backend/algorithms/fusion',
        'data/datasets/road_segmentation',
        'data/datasets/farmland_segmentation',
        'models/segmentation',
        'models/tracking',
    ]
    
    all_ok = True
    base_path = Path('.')
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [ERROR] {dir_path} - 不存在")
            all_ok = False
    
    return all_ok

def test_pytorch_gpu():
    """测试PyTorch GPU功能"""
    print_header("6. 测试PyTorch GPU功能")
    try:
        import torch
        
        if torch.cuda.is_available():
            # 创建测试张量
            x = torch.randn(3, 3).cuda()
            y = torch.randn(3, 3).cuda()
            z = torch.matmul(x, y)
            print("[OK] GPU计算测试成功")
            print(f"   测试结果: {z.shape}")
            return True
        else:
            print("[WARNING] GPU不可用，跳过GPU测试")
            return True
    except Exception as e:
        print(f"[ERROR] GPU测试失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  Day 1 环境搭建验证")
    print("="*60)
    
    results = []
    
    # 执行检查
    results.append(("Python版本", check_python_version()))
    results.append(("Conda环境", check_conda_environment()))
    results.append(("PyTorch安装", check_pytorch()))
    results.append(("依赖包", check_dependencies()))
    results.append(("项目结构", check_project_structure()))
    results.append(("GPU测试", test_pytorch_gpu()))
    
    # 总结
    print_header("验证结果总结")
    
    all_passed = True
    for name, result in results:
        status = "[OK] 通过" if result else "[ERROR] 失败"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("  [SUCCESS] 所有检查通过！可以继续下一步。")
        print("\n下一步:")
        print("  1. 准备训练数据集")
        print("  2. 开始Day 2-3的语义分割模型开发")
        print("  3. 参考文档: 第7-8周实施详细步骤.md")
    else:
        print("  [WARNING] 部分检查未通过，请修复后再继续。")
        print("\n修复建议:")
        print("  1. 检查未通过的项")
        print("  2. 重新运行Day 1的安装命令")
        print("  3. 查看错误信息并解决")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

