"""
启动器脚本，用于启动Flask应用并防止控制台窗口闪退
"""
import os
import sys
import time
import traceback
import shutil

def main():
    """主函数，执行应用启动逻辑并处理异常"""
    try:
        print("=" * 60)
        print("    YOLO目标检测系统启动器")
        print("=" * 60)
        print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"工作目录: {os.getcwd()}")
        
        # 检查config.json是否在当前目录，如果不在则复制一份
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_in_dist = os.path.join(base_dir, 'config.json')
        resources_config = os.path.join(base_dir, 'resources', 'config', 'config.json')
        
        if not os.path.exists(config_in_dist) and os.path.exists(resources_config):
            print(f"复制配置文件到执行目录: {resources_config} -> {config_in_dist}")
            shutil.copy2(resources_config, config_in_dist)
        
        # 导入app模块中的app对象
        print("正在导入应用程序...")
        from app import create_app
        from app.utils.path_utils import setup_resource_directories, get_upload_dir, get_results_dir
        
        # 设置资源目录
        print("正在设置资源目录...")
        setup_resource_directories()
        
        # 确保上传和结果目录存在
        os.makedirs(get_upload_dir(), exist_ok=True)
        os.makedirs(get_results_dir(), exist_ok=True)
        
        # 创建应用实例
        app = create_app()
        
        print("正在启动Web服务器...")
        print("=" * 60)
        print("应用已启动，请在浏览器中访问: http://localhost:5000")
        print("按Ctrl+C可停止服务器")
        print("=" * 60)
        
        # 使用threading模式启动应用
        app.socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
        
    except KeyboardInterrupt:
        print("\n接收到退出信号，正在关闭服务器...")
        time.sleep(1)
        print("服务器已关闭。")
    except Exception as e:
        print("\n" + "!" * 60)
        print("应用程序出现错误:")
        print(str(e))
        print("\n详细错误信息:")
        traceback.print_exc()
        print("!" * 60)
        
        # 程序出错时，保持控制台窗口显示，不会立即关闭
        print("\n按回车键退出程序...")
        input()

if __name__ == "__main__":
    main()
