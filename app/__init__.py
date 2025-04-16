from flask import Flask
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap5
import os
import json
import sys
from flask import send_from_directory

# 创建socketio实例，用于WebSocket通信
socketio = SocketIO(async_mode='threading')
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
    # 导入路径工具模块
    from app.utils.path_utils import get_upload_dir, get_results_dir, get_logs_dir, get_config_path, setup_resource_directories, get_resource_path
    
    # 初始化资源目录结构
    resource_dir = setup_resource_directories()
    
    # 创建应用实例 - 恢复原始静态文件夹设置
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='../templates',
                static_folder='../static')
    
    # 设置项目根目录
    root_dir = get_root_dir()
    app.config['ROOT_DIR'] = root_dir
    
    # 初始化日志系统
    log_dir = get_logs_dir()  # 使用新的日志目录
    from app.yolomodel.logger import ensure_log_dir, get_logger
    ensure_log_dir(log_dir)   # 确保日志目录存在
    app_logger = get_logger("APP", "info")
    
    app_logger.info(f"应用启动，根目录: {root_dir}")
    app_logger.info(f"资源目录: {resource_dir}")
    app_logger.info(f"日志目录: {log_dir}")
    
    # 如果是打包环境，添加额外的静态文件访问规则
    if getattr(sys, 'frozen', False):
        from flask import send_from_directory
        
        # 获取外部静态资源目录
        external_static = os.path.join(get_resource_path(), 'static')
        app_logger.info(f"外部静态资源目录: {external_static}")
        
        # 注册自定义的上传文件路由
        @app.route('/static/uploads/<path:filename>')
        def serve_upload(filename):
            uploads_dir = os.path.join(external_static, 'uploads')
            app_logger.info(f"访问外部上传文件: {filename}, 路径: {uploads_dir}")
            return send_from_directory(uploads_dir, filename)
        
        # 注册自定义的结果文件路由
        @app.route('/static/results/<path:filename>')
        def serve_result(filename):
            results_dir = os.path.join(external_static, 'results')
            app_logger.info(f"访问外部结果文件: {filename}, 路径: {results_dir}")
            return send_from_directory(results_dir, filename)
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=get_upload_dir(),  # 使用外部资源目录
        RESULT_FOLDER=get_results_dir(),  # 使用外部资源目录
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB上传限制
        ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg'},
    )

    if test_config is None:
        # 如果不是测试，则尝试加载config.json
        config_path = get_config_path()  # 使用path_utils获取配置文件路径
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
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    app_logger.info("初始化Flask扩展完成")
    
    # 注册蓝图
    from app import routes
    app.register_blueprint(routes.bp)
    app_logger.info("注册路由完成")
    
    # 将socketio实例添加到app对象，以便于在app.py中使用
    app.socketio = socketio
    
    app_logger.info("应用初始化完成")
    return app
