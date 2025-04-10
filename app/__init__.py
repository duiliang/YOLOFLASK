from flask import Flask
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap5
import os
import json
import sys

# 创建socketio实例，用于WebSocket通信
socketio = SocketIO()
bootstrap = Bootstrap5()

def get_root_dir():
    """
    获取应用根目录
    支持正常运行和打包后的场景
    
    Returns:
        应用根目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的情况
        return os.path.dirname(sys.executable)
    else:
        # 正常运行的情况
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def create_app(test_config=None):
    """
    应用工厂函数，创建并配置Flask应用
    
    Args:
        test_config: 测试配置，如果有
        
    Returns:
        配置好的Flask应用实例
    """
    # 创建应用实例
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='../templates',
                static_folder='../static')
    
    # 设置项目根目录
    root_dir = get_root_dir()
    app.config['ROOT_DIR'] = root_dir
    
    # 初始化日志系统
    from app.yolomodel.logger import ensure_log_dir, get_logger
    log_dir = ensure_log_dir()
    app_logger = get_logger("APP", "info")
    app_logger.info(f"应用启动，根目录: {root_dir}")
    app_logger.info(f"日志目录: {log_dir}")
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=os.path.join(root_dir, 'static/uploads'),
        RESULT_FOLDER=os.path.join(root_dir, 'static/results'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB上传限制
        ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    )

    if test_config is None:
        # 如果不是测试，则尝试加载config.json
        config_path = os.path.join(root_dir, 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新应用配置
                if 'server' in config_data:
                    server_config = config_data['server']
                    app.config['HOST'] = server_config.get('host', '0.0.0.0')
                    app.config['PORT'] = server_config.get('port', 5000)
                    app.config['DEBUG'] = server_config.get('debug', True)
                
                if 'model' in config_data:
                    model_config = config_data['model']
                    app.config['MODEL_CONF_THRESHOLD'] = model_config.get('conf_threshold', 0.25)
                    app.config['MODEL_IOU_THRESHOLD'] = model_config.get('iou_threshold', 0.45)
                
                if 'upload' in config_data:
                    upload_config = config_data['upload']
                    app.config['MAX_CONTENT_LENGTH'] = upload_config.get('max_size_mb', 16) * 1024 * 1024
                    app.config['ALLOWED_EXTENSIONS'] = set(upload_config.get('allowed_extensions', 
                                                                         ['jpg', 'jpeg', 'png']))
                
                app_logger.info(f"从 {config_path} 加载配置成功")
            except Exception as e:
                app_logger.error(f"加载配置文件失败: {str(e)}")
        
        # 也从实例配置文件加载配置（如果存在）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 否则，加载测试配置
        app.config.from_mapping(test_config)
    
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 确保上传文件夹和结果文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app_logger.info(f"创建上传文件夹: {app.config['UPLOAD_FOLDER']}")
    
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    app_logger.info(f"创建结果文件夹: {app.config['RESULT_FOLDER']}")
    
    # 初始化扩展
    bootstrap.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    app_logger.info("初始化Flask扩展完成")
    
    # 注册蓝图
    from app import routes
    app.register_blueprint(routes.bp)
    app_logger.info("注册路由完成")
    
    # 将socketio实例添加到app对象，以便于在app.py中使用
    app.socketio = socketio
    
    app_logger.info("应用初始化完成")
    return app
