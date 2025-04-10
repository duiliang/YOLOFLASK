"""
日志模块，提供统一的日志记录功能
支持打包成单文件后，在exe同级目录创建日志文件夹
"""
import logging
import time
from datetime import datetime
import os
import sys
import traceback

# 日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

def get_application_path():
    """
    获取应用程序路径
    支持正常运行和PyInstaller打包后的场景
    
    Returns:
        应用程序目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的情况
        return os.path.dirname(sys.executable)
    else:
        # 正常运行的情况
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ensure_log_dir():
    """
    确保日志目录存在
    在应用程序目录下创建logger文件夹
    
    Returns:
        日志目录的绝对路径
    """
    app_path = get_application_path()
    log_dir = os.path.join(app_path, 'logger')
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return log_dir
    except Exception as e:
        print(f"创建日志目录失败: {str(e)}")
        # 如果无法创建日志目录，则使用临时目录
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), 'yolo_logger')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

class Logger:
    """日志记录器类，提供统一的日志记录功能"""
    
    def __init__(self, name="YOLO", level="info", log_file=None):
        """
        初始化日志记录器
        
        Args:
            name: 日志名称，默认为"YOLO"
            level: 日志级别，可选值为debug, info, warning, error, critical
            log_file: 日志文件路径，如果为None则自动创建
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
        self.name = name
        
        # 清除现有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', 
                                     datefmt='%Y-%m-%d %H:%M:%S')
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        try:
            # 如果没有指定日志文件，则创建默认日志文件
            if not log_file:
                log_dir = ensure_log_dir()
                date_str = datetime.now().strftime('%Y-%m-%d')
                log_file = os.path.join(log_dir, f"{name}_{date_str}.log")
            
            # 确保日志文件的目录存在
            log_parent_dir = os.path.dirname(log_file)
            if log_parent_dir and not os.path.exists(log_parent_dir):
                os.makedirs(log_parent_dir)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.log_file = log_file
            self.info(f"日志初始化成功，日志文件: {log_file}")
        except Exception as e:
            self.error(f"创建日志文件失败: {str(e)}")
            self.error(traceback.format_exc())
            self.log_file = None
    
    def debug(self, message):
        """记录调试级别日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录信息级别日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录警告级别日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录错误级别日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录严重错误级别日志"""
        self.logger.critical(message)

# 日志记录器缓存
_loggers = {}

def get_logger(name="YOLO", level="info", log_file=None):
    """
    获取或创建日志记录器
    
    Args:
        name: 日志名称
        level: 日志级别
        log_file: 日志文件路径，如果为None则自动创建
    
    Returns:
        Logger实例
    """
    global _loggers
    # 如果日志记录器已存在，则直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 否则创建新的日志记录器
    logger = Logger(name, level, log_file)
    _loggers[name] = logger
    return logger

# 创建默认记录器
default_logger = get_logger("YOLO")
