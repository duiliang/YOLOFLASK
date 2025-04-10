"""
ROI控制器模块
处理与ROI相关的路由请求
"""
from flask import request, jsonify
from werkzeug.utils import secure_filename
from app.utils.file_utils import allowed_file
from app.services.roi_service import (
    get_roi_configs, save_roi_configs, 
    delete_roi_config as service_delete_roi_config,
    process_roi_background
)

def handle_get_roi_configs():
    """处理获取所有ROI配置请求"""
    try:
        roi_configs = get_roi_configs()
        return jsonify(roi_configs)
    except Exception as e:
        return jsonify({'error': f'无法读取ROI配置: {str(e)}'}), 500

def handle_save_roi_configs():
    """处理保存ROI配置请求"""
    try:
        roi_configs = request.json
        if not roi_configs:
            return jsonify({'error': '无效的ROI配置数据'}), 400
        
        # 保存配置
        if save_roi_configs(roi_configs):
            return jsonify({'success': True, 'message': 'ROI配置保存成功'})
        else:
            return jsonify({'error': '无法保存ROI配置'}), 500
    except Exception as e:
        return jsonify({'error': f'保存ROI配置失败: {str(e)}'}), 500

def handle_delete_roi_config(config_name):
    """处理删除指定ROI配置请求"""
    success, message = service_delete_roi_config(config_name)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 404

def handle_upload_roi_background():
    """处理ROI背景图片上传请求"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 检查文件类型是否允许
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    # 处理背景图片
    success, result = process_roi_background(file)
    
    if success:
        return jsonify({
            'success': True,
            'message': '背景图片上传成功',
            'image_url': result
        })
    else:
        return jsonify({'error': result}), 500
