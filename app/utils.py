"""
工具函数模块，提供通用功能和日志记录的桥接
"""
import time
import datetime
import os
import json
from app.yolomodel.logger import get_logger, ensure_log_dir

# 导出日志获取函数，保持向后兼容性
get_logger = get_logger

# 创建一个应用级别的默认记录器
app_logger = get_logger(name="APP", level="INFO")

def get_config_path():
    """
    获取配置文件路径
    支持正常运行和打包后的场景
    
    Returns:
        配置文件的绝对路径
    """
    import sys
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的情况
        base_dir = os.path.dirname(sys.executable)
    else:
        # 正常运行的情况
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_dir, 'config.json')

def load_config():
    """
    加载配置文件
    
    Returns:
        配置字典，如果加载失败则返回默认配置
    """
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False
        },
        "model": {
            "conf_threshold": 0.25,
            "iou_threshold": 0.45,
            "current_model": ""
        },
        "models": [],
        "upload": {
            "allowed_extensions": ["jpg", "jpeg", "png", "bmp"],
            "max_size_mb": 10
        }
    }
    
    try:
        config_path = get_config_path()
        app_logger.info(f"加载配置文件: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            app_logger.info("配置文件加载成功")
            return config
    except Exception as e:
        app_logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
        return default_config

def get_current_model_name():
    """
    获取当前加载的模型名称
    
    Returns:
        当前模型名称，如果未设置则返回'未知模型'
    """
    config = load_config()
    return config.get('model', {}).get('current_model', '未知模型')

def format_timestamp(timestamp=None):
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳，如果为None则使用当前时间
        
    Returns:
        格式化的时间字符串
    """
    if timestamp is None:
        timestamp = time.time()
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
