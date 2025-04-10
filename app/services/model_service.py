"""
模型服务模块
处理模型的加载、管理和配置
"""
import os
import json
from flask import current_app
from app.yolo_detector import YOLODetector
import onnxruntime as ort

# 创建全局检测器对象，将在应用中使用
detector = None

def get_config():
    """
    获取应用配置文件
    
    Returns:
        配置字典，如果读取失败则返回空字典
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"配置读取失败: {e}")
        return {}

def save_config(config):
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        
    Returns:
        是否保存成功
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"配置保存失败: {e}")
        return False

def get_models():
    """
    获取所有模型列表
    
    Returns:
        模型列表
    """
    config = get_config()
    return config.get('models', [])

def add_model(name, path, model_type=None, description=''):
    """
    添加新模型到配置
    
    Args:
        name: 模型名称
        path: 模型路径
        model_type: 模型类型，如果为None则尝试自动检测
        description: 模型描述
        
    Returns:
        (成功标志, 模型信息或错误信息)
    """
    # 检查模型文件是否存在
    model_file_path = path
    if not os.path.isabs(model_file_path):
        model_file_path = os.path.join(current_app.config['ROOT_DIR'], path)
    
    if not os.path.exists(model_file_path):
        return False, f'模型文件不存在: {model_file_path}'
    
    # 如果未指定模型类型，尝试自动检测
    detected_type = model_type
    if not detected_type:
        detected_type = detect_model_type(model_file_path)
    
    # 创建模型记录
    new_model = {
        'name': name,
        'path': path,
        'type': detected_type or 'unknown',
        'description': description
    }
    
    # 将模型添加到配置
    config = get_config()
    if 'models' not in config:
        config['models'] = []
    
    # 检查是否已存在同名模型
    for i, model in enumerate(config['models']):
        if model['name'] == name:
            config['models'][i] = new_model
            if save_config(config):
                return True, new_model
            else:
                return False, '无法保存模型配置'
    
    # 添加新模型
    config['models'].append(new_model)
    if save_config(config):
        return True, new_model
    else:
        return False, '无法保存模型配置'

def detect_model_type(model_path):
    """
    尝试检测模型类型
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        检测到的模型类型，如果无法检测则返回None
    """
    # 首先根据文件名尝试识别
    basename = os.path.basename(model_path).lower()
    if 'yolov5' in basename:
        return 'yolov5'
    elif 'yolov8' in basename:
        return 'yolov8'
    elif 'qrcode' in basename or 'qr' in basename:
        return 'yolov8'  # QR码检测模型通常是YOLOv8架构
    
    # 尝试加载模型，从元数据判断
    try:
        session = ort.InferenceSession(model_path)
        metadata = session.get_modelmeta()
        
        if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
            # YOLOv8特有的metadata键
            yolov8_keys = ['stride', 'task', 'batch', 'imgsz']
            # YOLOv5特有的metadata键
            yolov5_keys = ['model_type', 'size', 'stride']
            
            # 统计匹配度
            yolov8_match = sum(1 for key in yolov8_keys if key in metadata.custom_metadata_map)
            yolov5_match = sum(1 for key in yolov5_keys if key in metadata.custom_metadata_map)
            
            if yolov8_match > yolov5_match:
                return 'yolov8'
            elif yolov5_match > 0:
                return 'yolov5'
    except Exception:
        pass
    
    # 如果无法检测，则返回None
    return None

def delete_model(model_name):
    """
    删除指定模型
    
    Args:
        model_name: 要删除的模型名称
        
    Returns:
        (成功标志, 成功消息或错误信息)
    """
    config = get_config()
    
    if 'models' not in config:
        return False, '没有找到模型配置'
    
    # 寻找并删除模型
    found = False
    for i, model in enumerate(config['models']):
        if model['name'] == model_name:
            del config['models'][i]
            found = True
            break
    
    if not found:
        return False, f'没有找到名为 {model_name} 的模型'
    
    # 保存配置
    if save_config(config):
        return True, f'成功删除模型: {model_name}'
    else:
        return False, '无法保存模型配置'

def set_current_model(model_name):
    """
    设置当前使用的模型
    
    Args:
        model_name: 模型名称
        
    Returns:
        (成功标志, 模型信息或错误信息, 模型对象)
    """
    global detector
    
    config = get_config()
    
    # 寻找模型配置
    found_model = None
    for model in config.get('models', []):
        if model['name'] == model_name:
            found_model = model
            break
    
    if not found_model:
        return False, f'没有找到名为 {model_name} 的模型', None
    
    # 更新当前模型配置
    if 'model' not in config:
        config['model'] = {}
    
    config['model']['current_model'] = model_name
    save_config(config)
    
    # 加载模型
    try:
        model_path = found_model['path']
        # 检查路径是否存在，如果是相对路径则转为绝对路径
        if not os.path.isabs(model_path):
            model_path = os.path.join(current_app.config['ROOT_DIR'], model_path)
            
        print(f"正在加载模型，路径: {model_path}")
        if not os.path.exists(model_path):
            return False, f'模型文件不存在: {model_path}', None
            
        detector = YOLODetector(model_path, found_model['type'])
        print(f"已加载模型: {model_name}, 路径: {model_path}")
        
        return True, found_model, detector
    except Exception as e:
        return False, f'模型加载失败: {str(e)}', None

def get_detector():
    """
    获取当前检测器实例
    
    Returns:
        检测器实例
    """
    global detector
    return detector
