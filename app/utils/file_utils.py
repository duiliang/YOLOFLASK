"""
文件工具模块
处理文件上传、验证和存储等功能
"""
from flask import current_app
import os
from datetime import datetime
from werkzeug.utils import secure_filename

def allowed_file(filename):
    """
    检查文件扩展名是否在允许的扩展名列表中
    
    Args:
        filename: 要检查的文件名
    
    Returns:
        是否允许该文件类型
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_unique_filename(filename, prefix=''):
    """
    生成唯一的文件名，避免文件名冲突
    
    Args:
        filename: 原始文件名
        prefix: 文件名前缀
        
    Returns:
        唯一的文件名
    """
    # 安全处理文件名
    secure_name = secure_filename(filename)
    # 生成时间戳部分
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:20]
    # 分离文件名和扩展名
    name, ext = os.path.splitext(secure_name)
    # 组合新文件名
    return f"{prefix}{name}_{timestamp}{ext}"

def save_uploaded_file(file, upload_folder, prefix=''):
    """
    保存上传的文件到指定目录
    
    Args:
        file: 上传的文件对象
        upload_folder: 保存目录
        prefix: 文件名前缀
        
    Returns:
        保存的文件路径和URL
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    filename = get_unique_filename(file.filename, prefix)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # 获取相对URL路径
    url_path = file_path.replace(current_app.root_path, '')
    url_path = '/static' + url_path.split('/static')[-1] if '/static' in url_path else url_path
    url_path = url_path.replace('\\', '/')  # 处理Windows路径分隔符
    
    return file_path, url_path
