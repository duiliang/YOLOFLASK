"""
Socket控制器模块
处理WebSocket通信相关的逻辑
"""
import os
from flask import current_app
from app.services.model_service import get_config, set_current_model, get_detector
from app.services.detection_service import detect_objects

def handle_connect():
    """
    处理新的WebSocket连接
    
    Returns:
        连接状态信息
    """
    print('客户端已连接')
    message = {'status': 'connected'}
    
    # 尝试在连接时自动加载当前模型
    try:
        config = get_config()
        current_model_name = config.get('model', {}).get('current_model')
        
        if current_model_name:
            print(f"尝试自动加载模型: {current_model_name}")
            success, result, detector = set_current_model(current_model_name)
            
            if success:
                print(f"自动加载模型成功: {current_model_name}")
                message['model_loaded'] = {
                    'success': True,
                    'model': result,
                    'message': f'已自动加载模型: {current_model_name}'
                }
            else:
                print(f"自动加载模型失败: {result}")
                message['model_error'] = {'error': result}
    except Exception as e:
        print(f"检查当前模型配置失败: {str(e)}")
        message['error'] = str(e)
    
    return message

def handle_disconnect():
    """处理WebSocket断开连接"""
    print('客户端断开连接')
    return {'status': 'disconnected'}

def handle_detect(data):
    """
    处理目标检测请求
    
    Args:
        data: 包含检测请求信息的字典
        
    Returns:
        检测结果或错误信息
    """
    image_path = data.get('image_path', '')
    
    success, results, result_url = detect_objects(image_path)
    
    if success:
        return {
            'success': True,
            'results': results,
            'result_image': result_url
        }
    else:
        return {'error': results}
