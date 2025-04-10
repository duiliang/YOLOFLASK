"""
模型配置加载模块
负责从配置文件加载各种参数
"""
import os
import json
from pathlib import Path

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self):
        """初始化配置加载器"""
        self.default_config = {
            "model": {
                "conf_threshold": 0.25,
                "iou_threshold": 0.45,
                "current_model": ""
            }
        }
        self.config = None
        self.config_path = self._get_config_path()
        
    def _get_config_path(self):
        """获取配置文件路径"""
        # 从当前文件所在目录推算项目根目录
        base_dir = Path(__file__).resolve().parent.parent.parent
        return os.path.join(base_dir, 'config.json')
    
    def load_config(self):
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                print(f"从 {self.config_path} 加载配置成功")
                return self.config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}，使用默认配置")
            self.config = self.default_config
            return self.config
    
    def get_model_params(self):
        """
        获取模型参数
        
        Returns:
            模型参数字典
        """
        if self.config is None:
            self.load_config()
        
        return self.config.get('model', self.default_config['model'])
    
    def get_conf_threshold(self):
        """获取置信度阈值"""
        model_params = self.get_model_params()
        return model_params.get('conf_threshold', 0.25)
    
    def get_iou_threshold(self):
        """获取IOU阈值"""
        model_params = self.get_model_params()
        return model_params.get('iou_threshold', 0.45)
    
    def get_current_model(self):
        """获取当前模型名称"""
        model_params = self.get_model_params()
        return model_params.get('current_model', '')
    
    def get_models_list(self):
        """获取模型列表"""
        if self.config is None:
            self.load_config()
        
        return self.config.get('models', [])
