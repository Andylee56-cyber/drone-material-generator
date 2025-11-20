# ============================================
# 大疆无人机视觉智能Agent系统 - 继续安装步骤
# 从第七步开始（数据库初始化）
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🚁 大疆无人机视觉智能Agent系统" -ForegroundColor Cyan
Write-Host "   继续安装步骤（从第七步开始）" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. 确认当前工作目录
Write-Host "[步骤0] 确认工作目录..." -ForegroundColor Yellow
$currentDir = Get-Location
Write-Host "当前目录: $currentDir" -ForegroundColor Green
Write-Host ""

# 2. 检查虚拟环境
Write-Host "[步骤1] 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "✅ 找到虚拟环境，正在激活..." -ForegroundColor Green
    .\venv\Scripts\activate
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "❌ 未找到虚拟环境！" -ForegroundColor Red
    Write-Host "请先执行前面的步骤创建虚拟环境" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. 创建必要的目录
Write-Host "[步骤2] 创建必要的目录..." -ForegroundColor Yellow
$dirs = @("database", "outputs", "outputs\models", "data\raw", "data\processed")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  ✅ 创建目录: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ 目录已存在: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

# 4. 第七步：创建数据库初始化脚本
Write-Host "[步骤3] 创建数据库初始化脚本..." -ForegroundColor Yellow
$setupDbScript = @"
import sqlite3
import sys
from pathlib import Path

def init_database(db_path="database/drone_vision.db"):
    \"\"\"初始化SQLite数据库\"\"\"
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📊 初始化数据库: {db_path}")
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    # 1. 数据版本表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_count INTEGER DEFAULT 0,
            total_size_mb REAL DEFAULT 0
        )
    ''')
    
    # 2. 实验记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_name TEXT NOT NULL,
            run_id TEXT UNIQUE,
            status TEXT DEFAULT 'running',
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            metrics TEXT,
            params TEXT,
            model_path TEXT
        )
    ''')
    
    # 3. 模型版本表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            version TEXT,
            file_path TEXT,
            accuracy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            experiment_id INTEGER,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    ''')
    
    # 4. 分析任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_type TEXT,
            status TEXT DEFAULT 'pending',
            input_path TEXT,
            output_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result_summary TEXT
        )
    ''')
    
    # 5. 用户操作日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            resource TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            result TEXT
        )
    ''')
    
    # 6. 系统配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入默认配置
    cursor.execute('''
        INSERT OR IGNORE INTO system_config (config_key, config_value)
        VALUES ('system_version', '1.0.0')
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ 数据库初始化完成！")
    print(f"   数据库位置: {db_file.absolute()}")
    print("   已创建表: data_versions, experiments, models, analysis_tasks, audit_logs, system_config")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/drone_vision.db"
    init_database(db_path)
"@

$setupDbScript | Out-File -FilePath "scripts\setup_database.py" -Encoding utf8
Write-Host "✅ 数据库初始化脚本已创建: scripts\setup_database.py" -ForegroundColor Green
Write-Host ""

# 5. 运行数据库初始化
Write-Host "[步骤4] 运行数据库初始化..." -ForegroundColor Yellow
python scripts\setup_database.py
Write-Host ""

# 6. 验证数据库创建
Write-Host "[步骤5] 验证数据库创建..." -ForegroundColor Yellow
if (Test-Path "database\drone_vision.db") {
    Write-Host "✅ 数据库文件已创建" -ForegroundColor Green
} else {
    Write-Host "❌ 数据库文件创建失败！" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 7. 第八步：创建配置文件
Write-Host "[步骤6] 创建配置文件..." -ForegroundColor Yellow
$configYaml = @"
# 大疆无人机视觉智能Agent系统配置文件
# 海南博悦科技有限公司

system:
  name: "大疆无人机视觉智能Agent系统"
  version: "1.0.0"
  company: "海南博悦科技有限公司"

database:
  type: "sqlite"
  sqlite_path: "database/drone_vision.db"

mlflow:
  tracking_uri: "file:./mlruns"
  experiment_name: "dji_drone_vision"

model:
  default_model_path: "outputs/models/drone_vision_model.pth"
  num_classes: 5
  image_size: [640, 640]
  class_names:
    - "建筑物"
    - "道路"
    - "植被"
    - "水体"
    - "车辆"

paths:
  raw_data: "data/raw"
  processed_data: "data/processed"
  output_dir: "outputs"
"@

$configYaml | Out-File -FilePath "config.yaml" -Encoding utf8
Write-Host "✅ 配置文件已创建: config.yaml" -ForegroundColor Green
Write-Host ""

# 8. 验证配置文件
Write-Host "[步骤7] 验证配置文件..." -ForegroundColor Yellow
python -c "import yaml; yaml.safe_load(open('config.yaml', 'r', encoding='utf-8')); print('✅ 配置文件有效')"
Write-Host ""

# 9. 第九步：创建启动脚本
Write-Host "[步骤8] 创建启动脚本..." -ForegroundColor Yellow
$startSystemScript = @"
import subprocess
import time
import webbrowser
from pathlib import Path
import sys

def check_dependencies():
    \"\"\"检查必要的依赖\"\"\"
    print("🔍 检查系统依赖...")
    required_packages = ['streamlit', 'mlflow', 'torch', 'sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements_agent.txt")
        return False
    
    return True

def init_database():
    \"\"\"初始化数据库\"\"\"
    print("📊 初始化数据库...")
    try:
        from scripts.setup_database import init_database as db_init
        db_init()
        return True
    except Exception as e:
        print(f"  ⚠️  数据库初始化失败: {e}")
        return True

def start_streamlit():
    \"\"\"启动Streamlit Web界面\"\"\"
    print("\n🚀 启动Web界面...")
    streamlit_app = Path("app/web/streamlit_app_simple.py")
    
    if not streamlit_app.exists():
        print(f"  ❌ 找不到Streamlit应用: {streamlit_app}")
        print("  请确保文件存在")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             str(streamlit_app), "--server.port", "8501"],
            cwd=Path.cwd()
        )
        print("  ✅ Streamlit已启动")
        return process
    except Exception as e:
        print(f"  ❌ 启动失败: {e}")
        return None

def main():
    print("=" * 60)
    print("🚁 大疆无人机视觉智能Agent系统")
    print("   海南博悦科技有限公司")
    print("=" * 60)
    print()
    
    if not check_dependencies():
        return
    
    init_database()
    
    streamlit_process = start_streamlit()
    if not streamlit_process:
        return
    
    print("\n⏳ 等待服务启动...")
    time.sleep(3)
    
    try:
        webbrowser.open("http://localhost:8501")
        print("  ✅ 已自动打开浏览器")
    except:
        print("  ⚠️  无法自动打开浏览器，请手动访问: http://localhost:8501")
    
    print("\n" + "=" * 60)
    print("✅ 系统启动成功！")
    print("=" * 60)
    print("\n📱 访问地址: http://localhost:8501")
    print("\n⚠️  按 Ctrl+C 停止服务")
    
    try:
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n\n正在关闭服务...")
        streamlit_process.terminate()
        streamlit_process.wait()
        print("✅ 所有服务已停止")

if __name__ == "__main__":
    main()
"@

$startSystemScript | Out-File -FilePath "scripts\start_system.py" -Encoding utf8
Write-Host "✅ 启动脚本已创建: scripts\start_system.py" -ForegroundColor Green
Write-Host ""

# 10. 检查是否需要创建Streamlit应用
Write-Host "[步骤9] 检查Streamlit应用..." -ForegroundColor Yellow
if (-not (Test-Path "app\web\streamlit_app_simple.py")) {
    Write-Host "⚠️  未找到 streamlit_app_simple.py" -ForegroundColor Yellow
    Write-Host "   需要创建这个文件才能启动系统" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请告诉我是否需要创建这个文件，或者从其他地方复制" -ForegroundColor Cyan
} else {
    Write-Host "✅ Streamlit应用文件已存在" -ForegroundColor Green
}
Write-Host ""

# 11. 总结
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✅ 安装步骤执行完成！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 确保已安装所有依赖包（如果还没安装）" -ForegroundColor White
Write-Host "   pip install -r requirements_agent.txt -i https://pypi.tuna.tsinghua.edu.cn/simple" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 确保 streamlit_app_simple.py 文件存在" -ForegroundColor White
Write-Host "   如果不存在，需要创建或复制该文件到 app\web\ 目录" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 启动系统：" -ForegroundColor White
Write-Host "   python scripts\start_system.py" -ForegroundColor Gray
Write-Host ""



