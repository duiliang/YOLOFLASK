"""
打包脚本，将Flask YOLO应用打包成单个可执行文件
支持在断网环境下运行，会在exe同级目录创建资源文件夹
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def clear_directory(directory):
    """清空目录内容"""
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            try:
                os.unlink(item_path)
            except Exception as e:
                print(f"无法删除文件 {item_path}: {str(e)}")
        elif os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
            except Exception as e:
                print(f"无法删除目录 {item_path}: {str(e)}")

def main():
    """主函数，执行打包流程"""
    # 获取项目根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 打印信息
    print(f"项目目录: {project_dir}")
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    # 创建打包临时目录
    build_dir = os.path.join(project_dir, "build")
    dist_dir = os.path.join(project_dir, "dist")
    
    # 清理打包目录
    if os.path.exists(build_dir):
        print(f"清理build目录: {build_dir}")
        clear_directory(build_dir)
    
    if os.path.exists(dist_dir):
        print(f"清理dist目录: {dist_dir}")
        clear_directory(dist_dir)
    
    # 创建spec文件内容
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'engineio.async_drivers.eventlet',
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue',
        'eventlet.hubs.selects',
        'dns.rdtypes.ANY.SSHFP',
        'dns.rdtypes.IN.SSHFP',
        'flask_socketio',
        'app.utils.path_utils',
        'gevent',
        'gevent.ssl',
        'gevent.builtins',
        'engineio.async_drivers.threading',
        'socketio',
        'engineio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YOLO目标检测系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/favicon.ico' if os.path.exists('static/img/favicon.ico') else None,
)
"""
    
    # 写入spec文件
    spec_file = os.path.join(project_dir, "app.spec")
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print(f"已创建spec文件: {spec_file}")
    
    # 执行打包命令
    print("开始执行PyInstaller打包...")
    try:
        subprocess.run(["pyinstaller", "--clean", "app.spec"], check=True)
        print("PyInstaller打包成功！")
    except subprocess.CalledProcessError as e:
        print(f"打包失败，错误码: {e.returncode}")
        return
    except Exception as e:
        print(f"打包过程中出现异常: {str(e)}")
        return
    
    # 创建示例资源目录结构
    dist_resources_dir = os.path.join(dist_dir, "resources")
    os.makedirs(dist_resources_dir, exist_ok=True)
    
    # 创建资源子目录
    resource_dirs = [
        os.path.join(dist_resources_dir, "static", "uploads"),
        os.path.join(dist_resources_dir, "static", "results"),
        os.path.join(dist_resources_dir, "models"),
        os.path.join(dist_resources_dir, "logs"),
        os.path.join(dist_resources_dir, "config"),
    ]
    
    for dir_path in resource_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"创建资源目录: {dir_path}")
    
    # 复制配置文件到资源目录
    config_src = os.path.join(project_dir, "config.json")
    config_dest = os.path.join(dist_resources_dir, "config", "config.json")
    
    if os.path.exists(config_src):
        shutil.copy2(config_src, config_dest)
        print(f"已复制配置文件到: {config_dest}")
        
        # 复制到dist目录根目录下
        dist_config = os.path.join(dist_dir, "config.json")
        shutil.copy2(config_src, dist_config)
        print(f"已复制配置文件到: {dist_config}")
    
    # 复制当前的模型文件到模型目录
    models_dir = os.path.join(dist_resources_dir, "models")
    try:
        import json
        with open(config_src, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
            if 'models' in config_data:
                for model_info in config_data['models']:
                    if 'path' in model_info and os.path.exists(model_info['path']):
                        model_filename = os.path.basename(model_info['path'])
                        model_dest = os.path.join(models_dir, model_filename)
                        shutil.copy2(model_info['path'], model_dest)
                        print(f"已复制模型文件: {model_info['path']} -> {model_dest}")
    except Exception as e:
        print(f"复制模型文件失败: {str(e)}")
    
    # 创建一个简单的说明文件
    readme_content = """# YOLO目标检测系统 - 离线版

## 系统说明
本系统是基于Flask和YOLO模型的目标检测Web应用，支持离线部署和使用。

## 目录结构
- YOLO目标检测系统.exe - 主程序
- config.json - 配置文件 (重要：必须与主程序放在同一目录)
- resources/ - 资源目录（必须与主程序放在同一目录）
  - config/ - 配置文件目录（备份）
  - models/ - 模型文件目录
  - logs/ - 日志文件目录
  - static/ - 静态资源目录
    - uploads/ - 上传图片目录
    - results/ - 检测结果目录

## 使用方法
1. 直接双击"YOLO目标检测系统.exe"运行程序
2. 在浏览器中访问 http://localhost:5000
3. 如需更换模型，请将模型文件放入resources/models/目录

## 注意事项
- 首次运行可能需要等待较长时间
- 请勿删除resources目录及其子目录
- 如需查看日志，请查看resources/logs/目录
- 如果程序出现问题，控制台窗口会显示错误信息，按回车键可退出程序
- config.json文件必须保留在程序根目录下
"""
    
    readme_file = os.path.join(dist_dir, "README.txt")
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"已创建说明文件: {readme_file}")
    print("\n打包完成！打包结果在dist目录中。")

if __name__ == "__main__":
    main()
