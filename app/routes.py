from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit
import os
from app import socketio

# 导入控制器模块
from app.controllers.model_controller import (
    handle_get_config, handle_get_models, handle_add_model,
    handle_delete_model, handle_set_current_model
)
from app.controllers.roi_controller import (
    handle_get_roi_configs, handle_save_roi_configs,
    handle_delete_roi_config, handle_upload_roi_background,
    handle_get_roi_config_detail
)
from app.controllers.file_controller import handle_upload_file
from app.controllers.logic_controller import (
    handle_get_logic_rules, handle_save_logic_rule, handle_delete_logic_rule
)
from app.controllers.socket_controller import (
    handle_connect as socket_handle_connect,
    handle_disconnect as socket_handle_disconnect,
    handle_detect as socket_handle_detect
)

# 创建蓝图
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """主页路由"""
    return render_template('index.html')

@bp.route('/model-management')
def model_management():
    """模型管理页面路由"""
    return render_template('model-management.html')

@bp.route('/roi-management')
def roi_management():
    """ROI区域管理页面路由"""
    return render_template('roi-management.html')

@bp.route('/logic-rules')
def logic_rules():
    """逻辑规则管理页面路由"""
    return render_template('logic-rules.html')

@bp.route('/config.json')
def get_config():
    """获取配置文件内容"""
    return handle_get_config()

@bp.route('/api/models', methods=['GET'])
def get_models():
    """获取所有模型列表"""
    return handle_get_models()

@bp.route('/api/models', methods=['POST'])
def add_model():
    """添加新模型到配置"""
    return handle_add_model()

@bp.route('/api/models/<model_name>', methods=['DELETE'])
def delete_model(model_name):
    """删除指定模型"""
    return handle_delete_model(model_name)

@bp.route('/api/models/current', methods=['POST'])
def set_current_model():
    """设置当前使用的模型"""
    result = handle_set_current_model()
    
    # 处理socketio广播通知
    if isinstance(result, tuple):
        # 处理错误情况
        return result
    
    # 从JSON响应中提取数据
    response_data = result.get_json()
    if response_data.get('success'):
        # 使用socketio广播，通知所有客户端模型已更新
        socketio.emit('model_loaded', {
            'success': True, 
            'model': response_data.get('model'),
            'message': response_data.get('message')
        })
    
    return result

@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    处理文件上传请求
    
    Returns:
        包含上传文件信息的JSON响应
    """
    return handle_upload_file()

@bp.route('/api/roi-configs', methods=['GET'])
def get_roi_configs():
    """获取所有ROI配置"""
    return handle_get_roi_configs()

@bp.route('/api/roi-config/<config_name>', methods=['GET'])
def get_roi_config_detail(config_name):
    """获取特定ROI配置的详情"""
    return handle_get_roi_config_detail(config_name)

@bp.route('/api/roi-configs', methods=['POST'])
def save_roi_configs():
    """保存ROI配置"""
    return handle_save_roi_configs()

@bp.route('/api/roi-config/<config_name>', methods=['DELETE'])
def delete_roi_config(config_name):
    """删除指定的ROI配置"""
    return handle_delete_roi_config(config_name)

@bp.route('/api/upload-roi-background', methods=['POST'])
def upload_roi_background():
    """处理ROI背景图片上传"""
    return handle_upload_roi_background()

@bp.route('/api/logic-rules', methods=['GET'])
def get_logic_rules():
    """获取所有逻辑规则配置"""
    return handle_get_logic_rules()

@bp.route('/api/logic-rules', methods=['POST'])
def save_logic_rule():
    """保存逻辑规则配置"""
    return handle_save_logic_rule()

@bp.route('/api/logic-rules', methods=['DELETE'])
def delete_logic_rule():
    """删除指定的逻辑规则配置"""
    return handle_delete_logic_rule()

@socketio.on('connect')
def handle_connect():
    """处理新的WebSocket连接"""
    response = socket_handle_connect()
    
    # 发送连接状态
    if 'model_loaded' in response:
        emit('model_loaded', response['model_loaded'])
    if 'model_error' in response:
        emit('model_error', response['model_error'])
    if 'error' in response:
        emit('connect_error', {'error': response['error']})

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    socket_handle_disconnect()

@socketio.on('detect')
def handle_detect(data):
    """
    处理目标检测的WebSocket事件
    
    Args:
        data: 包含检测请求信息的字典
    """
    result = socket_handle_detect(data)
    
    if 'success' in result and result['success']:
        emit('detection_results', result)
    else:
        emit('detection_error', result)
