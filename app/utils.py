"""
工具函数模块，提供日志记录等实用功能
"""
import time
import datetime
import os
import json

class Logger:
    """标准日志记录类"""
    
    LOG_LEVELS = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }
    
    def __init__(self, name="YOLODetector", log_level="INFO"):
        """
        初始化日志记录器
        
        Args:
            name: 日志名称
            log_level: 日志级别，可选值 DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        self.name = name
        self.level = self.LOG_LEVELS.get(log_level.upper(), 20)  # 默认INFO级别
        
        # 创建日志目录
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 日志文件名格式: logs/YYYY-MM-DD.log
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.log_file = os.path.join(self.log_dir, f"{date_str}.log")
    
    def _get_config(self):
        """获取当前配置信息"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception:
            return {}
    
    def _get_current_model(self):
        """获取当前加载的模型名称"""
        config = self._get_config()
        return config.get('model', {}).get('current_model', '未知模型')
    
    def _format_message(self, level, message):
        """格式化日志消息"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        model_name = self._get_current_model()
        return f"[{timestamp}] [{self.name}] [{level}] [模型: {model_name}] {message}"
    
    def _log(self, level, level_name, message):
        """记录日志"""
        if level >= self.level:
            formatted_message = self._format_message(level_name, message)
            print(formatted_message)
            
            # 同时写入日志文件
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(formatted_message + '\n')
            except Exception as e:
                print(f"写入日志文件失败: {str(e)}")
    
    def debug(self, message):
        """记录调试级别日志"""
        self._log(10, 'DEBUG', message)
    
    def info(self, message):
        """记录信息级别日志"""
        self._log(20, 'INFO', message)
    
    def warning(self, message):
        """记录警告级别日志"""
        self._log(30, 'WARNING', message)
    
    def error(self, message):
        """记录错误级别日志"""
        self._log(40, 'ERROR', message)
    
    def critical(self, message):
        """记录严重错误级别日志"""
        self._log(50, 'CRITICAL', message)
