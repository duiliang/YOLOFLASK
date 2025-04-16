import os
from app import create_app
from app.utils.path_utils import setup_resource_directories, get_upload_dir, get_results_dir

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 设置资源目录
    setup_resource_directories()
    
    # 确保上传目录存在
    os.makedirs(get_upload_dir(), exist_ok=True)
    os.makedirs(get_results_dir(), exist_ok=True)
    
    # 启动应用，使用socketio提供WebSocket支持
    app.socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
