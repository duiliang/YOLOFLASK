"""
文件控制器模块
处理文件上传和管理的路由请求
"""
from flask import request, jsonify, current_app
import os
from app.utils.file_utils import allowed_file, save_uploaded_file

def handle_upload_file():
    """
    处理文件上传请求
    
    Returns:
        包含上传文件信息的JSON响应
    """
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
    
    try:
        # 保存文件
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path, url_path = save_uploaded_file(file, upload_folder)
        
        # 返回成功结果
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'filename': os.path.basename(file_path),
            'filepath': file_path,
            'url': url_path
        })
    except Exception as e:
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500
