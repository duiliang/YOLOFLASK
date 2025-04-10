"""
模型控制器模块
处理与模型相关的路由请求
"""
from flask import request, jsonify, current_app
import os
from app.services.model_service import (
    get_config, get_models, add_model, 
    delete_model as service_delete_model, 
    set_current_model as service_set_current_model
)

def handle_get_config():
    """处理获取配置文件请求"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = get_config()
            return jsonify(config)
    except Exception as e:
        return jsonify({'error': f'无法读取配置文件: {str(e)}'}), 500

def handle_get_models():
    """处理获取所有模型列表请求"""
    try:
        models = get_models()
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': f'无法读取模型配置: {str(e)}'}), 500

def handle_add_model():
    """处理添加新模型请求"""
    data = request.json
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    name = data.get('name')
    path = data.get('path')
    model_type = data.get('type')
    description = data.get('description', '')
    
    if not name or not path:
        return jsonify({'error': '模型名称和路径为必填项'}), 400
    
    success, result = add_model(name, path, model_type, description)
    
    if success:
        return jsonify({'success': True, 'model': result})
    else:
        return jsonify({'error': result}), 400

def handle_delete_model(model_name):
    """处理删除指定模型请求"""
    success, message = service_delete_model(model_name)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 404

def handle_set_current_model():
    """处理设置当前模型请求"""
    data = request.json
    model_name = data.get('model_name')
    
    if not model_name:
        return jsonify({'error': '必须提供模型名称'}), 400
    
    success, result, detector = service_set_current_model(model_name)
    
    if success:
        # 使用socketio广播，通知所有客户端模型已更新
        # 注意：因为不想在控制器中引入socketio，所以这部分逻辑后续会在routes.py中处理
        return jsonify({
            'success': True, 
            'model': result,
            'message': f'成功加载模型: {model_name}'
        })
    else:
        return jsonify({'error': result}), 500
