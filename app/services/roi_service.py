"""
ROI服务模块
处理ROI区域的管理和操作
"""
import os
import json
from flask import current_app
import cv2
from app.yolomodel.preprocessor import ImagePreprocessor
from app.utils.file_utils import save_uploaded_file

def get_roi_configs():
    """
    获取所有ROI配置
    
    Returns:
        ROI配置字典
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('roi_configs', {})
    except Exception as e:
        print(f"ROI配置读取失败: {e}")
        return {}

def get_roi_config_detail(config_name):
    """
    获取特定ROI配置的详细信息
    
    Args:
        config_name: ROI配置名称
        
    Returns:
        ROI配置详情，包括背景图片和所有区域信息
    """
    try:
        roi_configs = get_roi_configs()
        if config_name in roi_configs:
            return {
                'success': True,
                'data': roi_configs[config_name]
            }
        else:
            return {
                'success': False,
                'message': f"未找到ROI配置: {config_name}"
            }
    except Exception as e:
        current_app.logger.error(f"获取ROI配置详情失败: {e}")
        return {
            'success': False,
            'message': f"获取ROI配置详情失败: {str(e)}"
        }

def save_roi_configs(roi_configs):
    """
    保存ROI配置
    
    Args:
        roi_configs: ROI配置字典
        
    Returns:
        是否保存成功
    """
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        # 读取原有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新ROI配置
        config['roi_configs'] = roi_configs
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"ROI配置保存失败: {e}")
        return False

def delete_roi_config(config_name):
    """
    删除指定的ROI配置
    
    Args:
        config_name: 配置名称
        
    Returns:
        (成功标志, 成功消息或错误信息)
    """
    try:
        # 获取现有配置
        roi_configs = get_roi_configs()
        
        # 检查配置是否存在
        if config_name not in roi_configs:
            return False, f'ROI配置 {config_name} 不存在'
        
        # 删除配置
        del roi_configs[config_name]
        
        # 保存更新后的配置
        if save_roi_configs(roi_configs):
            return True, f'成功删除ROI配置: {config_name}'
        else:
            return False, '无法保存ROI配置'
    except Exception as e:
        return False, f'删除ROI配置失败: {str(e)}'

def process_roi_background(file):
    """
    处理ROI背景图片上传
    
    Args:
        file: 上传的文件对象
        
    Returns:
        (成功标志, 处理后的图片URL或错误信息)
    """
    try:
        # 保存原始图片
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path, _ = save_uploaded_file(file, upload_folder, prefix='roi_bg_')
        
        # 读取并预处理图像
        image = cv2.imread(file_path)
        if image is None:
            return False, '无法读取上传的图像'
        
        # 创建预处理器并处理图像
        # 尝试获取当前检测器的输入尺寸，如果未加载则使用标准尺寸
        from app.services.model_service import get_detector
        detector = get_detector()
        
        if detector is not None:
            # 使用当前加载的模型尺寸
            input_width = detector.input_width
            input_height = detector.input_height
        else:
            # 使用默认尺寸，通常是640x640或416x416
            input_width = 640
            input_height = 640
            
        # 创建预处理器
        preprocessor = ImagePreprocessor(input_width, input_height)
        input_tensor, _ = preprocessor.preprocess(image)
        
        # 将处理后的图像保存为新文件
        processed_image = input_tensor.copy()  # 创建副本以避免修改原始张量
        processed_filename = os.path.basename(file_path).replace('roi_bg_', 'roi_bg_resized_')
        processed_path = os.path.join(upload_folder, processed_filename)
        cv2.imwrite(processed_path, processed_image)
        
        # 计算URL路径
        url_path = processed_path.replace(current_app.root_path, '')
        url_path = url_path.replace('\\', '/')  # 处理Windows路径分隔符
        
        # 确保路径以/static开头
        if not url_path.startswith('/static'):
            url_path = '/static' + url_path.split('/static')[-1]
        
        return True, url_path
    except Exception as e:
        return False, f'处理ROI背景图片失败: {str(e)}'
