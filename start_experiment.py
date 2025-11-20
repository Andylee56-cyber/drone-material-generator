"""
无人机视觉MLflow实验启动脚本
Drone Vision MLflow Experiment Launcher
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        'torch', 'torchvision', 'mlflow', 'streamlit', 
        'numpy', 'pandas', 'matplotlib', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def start_mlflow_ui():
    """启动MLflow UI"""
    print("🚀 启动MLflow UI...")
    try:
        subprocess.Popen([sys.executable, "-m", "mlflow", "ui"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ MLflow UI已启动: http://localhost:5000")
        return True
    except Exception as e:
        print(f"❌ 启动MLflow UI失败: {e}")
        return False

def start_streamlit_app():
    """启动Streamlit应用"""
    print("🚀 启动Streamlit应用...")
    try:
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("✅ Streamlit应用已启动: http://localhost:8501")
        return True
    except Exception as e:
        print(f"❌ 启动Streamlit应用失败: {e}")
        return False

def run_experiment():
    """运行实验"""
    print("🚀 运行无人机视觉实验...")
    try:
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 实验运行成功")
            return True
        else:
            print(f"❌ 实验运行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 运行实验失败: {e}")
        return False

def open_browsers():
    """打开浏览器"""
    time.sleep(5)  # 等待服务启动
    
    try:
        webbrowser.open("http://localhost:5000")  # MLflow UI
        time.sleep(1)
        webbrowser.open("http://localhost:8501")  # Streamlit
        print("🌐 已打开浏览器窗口")
    except Exception as e:
        print(f"❌ 打开浏览器失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚁 无人机视觉MLflow实验平台")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    print("\n请选择操作:")
    print("1. 运行实验")
    print("2. 启动Web界面")
    print("3. 启动MLflow UI")
    print("4. 启动所有服务")
    print("5. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            print("\n" + "="*40)
            print("运行实验")
            print("="*40)
            run_experiment()
            break
            
        elif choice == "2":
            print("\n" + "="*40)
            print("启动Web界面")
            print("="*40)
            if start_streamlit_app():
                print("\nStreamlit应用正在运行...")
                print("按 Ctrl+C 停止服务")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n👋 服务已停止")
            break
            
        elif choice == "3":
            print("\n" + "="*40)
            print("启动MLflow UI")
            print("="*40)
            if start_mlflow_ui():
                print("\nMLflow UI正在运行...")
                print("按 Ctrl+C 停止服务")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n👋 服务已停止")
            break
            
        elif choice == "4":
            print("\n" + "="*40)
            print("启动所有服务")
            print("="*40)
            
            # 启动MLflow UI
            mlflow_success = start_mlflow_ui()
            
            # 启动Streamlit
            streamlit_success = start_streamlit_app()
            
            if mlflow_success and streamlit_success:
                print("\n🎉 所有服务已启动!")
                print("📊 MLflow UI: http://localhost:5000")
                print("🌐 Streamlit: http://localhost:8501")
                
                # 在后台打开浏览器
                browser_thread = Thread(target=open_browsers)
                browser_thread.daemon = True
                browser_thread.start()
                
                print("\n按 Ctrl+C 停止所有服务")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n👋 所有服务已停止")
            else:
                print("❌ 部分服务启动失败")
            break
            
        elif choice == "5":
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择，请输入1-5")

if __name__ == "__main__":
    main()
