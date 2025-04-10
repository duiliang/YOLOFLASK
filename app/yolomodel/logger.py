"""
日志模块，提供统一的日志记录功能
"""
import logging
import time
from datetime import datetime
import os
import sys

# 日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

class Logger:
    """日志记录器类，提供统一的日志记录功能"""
    
    def __init__(self, name="YOLO", level="info", log_file=None):
        """
        初始化日志记录器
        
        Args:
            name: 日志名称，默认为"YOLO"
            level: 日志级别，可选值为debug, info, warning, error, critical
            log_file: 日志文件路径，如果为None则输出到控制台
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
        self.name = name
        
        # 清除现有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 如果指定了日志文件，添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
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
        log_file: 日志文件路径
    
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
