"""
文件路径处理工具，用于在打包为EXE后的环境下正确处理文件路径
"""
import os
import sys
import logging
import json

# 设置日志
logger = logging.getLogger(__name__)

def get_base_path():
    """
    获取应用的基础路径
    - 如果是通过PyInstaller打包的EXE，则返回EXE所在目录
    - 如果是直接运行脚本，则返回脚本所在目录
    """
    if getattr(sys, 'frozen', False):
        # 如果是通过PyInstaller打包的EXE
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接运行脚本
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_resource_path(relative_path=None):
    """
    获取资源文件路径
    - 如果是EXE，则使用EXE旁边的resources目录
    - 如果是脚本，则使用项目根目录
    
    Args:
        relative_path: 相对于资源根目录的路径
    """
    base_path = get_base_path()
    
    if getattr(sys, 'frozen', False):
        # 在EXE模式下，使用EXE旁边的resources目录
        resource_base = os.path.join(base_path, 'resources')
    else:
        # 在开发模式下，使用项目根目录
        resource_base = base_path
    
    # 确保资源目录存在
    if not os.path.exists(resource_base):
        os.makedirs(resource_base, exist_ok=True)
        
    if relative_path:
        return os.path.join(resource_base, relative_path)
    return resource_base

def setup_resource_directories():
    """
    设置资源目录结构，确保所有必要的目录都存在
    在应用启动时调用此函数
    """
    # 创建主要资源目录
    resources_dir = get_resource_path()
    logger.info(f"资源目录设置在: {resources_dir}")
    
    # 创建各个子目录
    dirs_to_create = [
        ('static', '静态资源目录'),
        ('static/uploads', '上传图片目录'),
        ('static/results', '检测结果目录'),
        ('models', '模型目录'),
        ('logs', '日志目录'),
        ('config', '配置目录')
    ]
    
    for dir_path, description in dirs_to_create:
        full_path = get_resource_path(dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"创建{description}: {full_path}")
    
    # 确保config.json存在于资源目录下
    config_src = os.path.join(get_base_path(), 'config.json')
    config_dest = get_resource_path('config/config.json')
    
    # 如果配置文件不存在，而且源配置文件存在，则复制
    if not os.path.exists(config_dest) and os.path.exists(config_src):
        try:
            with open(config_src, 'r', encoding='utf-8') as src_file:
                config_data = json.load(src_file)
                
                # 更新模型路径为相对资源目录的路径
                if 'models' in config_data:
                    for model in config_data['models']:
                        if 'path' in model and os.path.exists(model['path']):
                            # 获取模型文件名
                            model_filename = os.path.basename(model['path'])
                            # 设置为相对路径
                            model['path'] = os.path.join('models', model_filename)
                
                # 写入新的配置文件
                with open(config_dest, 'w', encoding='utf-8') as dest_file:
                    json.dump(config_data, dest_file, ensure_ascii=False, indent=4)
                logger.info(f"已复制并更新配置文件到: {config_dest}")
        except Exception as e:
            logger.error(f"复制配置文件失败: {str(e)}")
    
    return resources_dir

def get_config_path():
    """获取配置文件路径"""
    # 优先使用外部配置
    external_config = get_resource_path('config/config.json')
    if os.path.exists(external_config):
        return external_config
        
    # 回退到内部配置
    internal_config = os.path.join(get_base_path(), 'config.json')
    
    # 打印路径便于调试
    print(f"尝试加载配置文件的路径: \n1. 外部: {external_config}\n2. 内部: {internal_config}")
    
    if os.path.exists(internal_config):
        return internal_config
        
    raise FileNotFoundError(f"找不到配置文件，请确保config.json存在于以下路径之一:\n{external_config}\n{internal_config}")

def get_upload_dir():
    """获取上传目录路径"""
    external_upload_dir = os.path.join(get_resource_path(), 'static', 'uploads')
    
    # 如果是打包环境，优先使用外部上传目录
    if getattr(sys, 'frozen', False) and os.path.exists(external_upload_dir):
        print(f"使用外部上传目录: {external_upload_dir}")
        return external_upload_dir
    
    upload_dir = os.path.join(get_resource_path(), 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def get_results_dir():
    """获取结果目录路径"""
    external_results_dir = os.path.join(get_resource_path(), 'static', 'results')
    
    # 如果是打包环境，优先使用外部结果目录
    if getattr(sys, 'frozen', False) and os.path.exists(external_results_dir):
        print(f"使用外部结果目录: {external_results_dir}")
        return external_results_dir
    
    results_dir = os.path.join(get_resource_path(), 'static', 'results')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def get_models_dir():
    """获取模型目录路径"""
    return get_resource_path('models')
    
def get_logs_dir():
    """获取日志目录路径"""
    return get_resource_path('logs')
