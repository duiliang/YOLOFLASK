import os
from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 使用eventlet作为socketio的异步后端
    # 确保上传目录存在
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/results', exist_ok=True)
    # 启动应用，使用socketio提供WebSocket支持
    app.socketio.run(app, debug=True, host='0.0.0.0', port=5000)
