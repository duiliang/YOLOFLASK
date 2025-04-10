from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import json
from datetime import datetime
from app import socketio
from app.yolo_detector import YOLODetector
from app.yolomodel.preprocessor import ImagePreprocessor

# 创建蓝图
bp = Blueprint('main', __name__)

# 创建全局检测器对象
detector = None

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


@bp.route('/config.json')
def get_config():
    """获取配置文件内容"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify(config)
    except Exception as e:
        return jsonify({'error': f'无法读取配置文件: {str(e)}'}), 500


@bp.route('/api/models', methods=['GET'])
def get_models():
    """获取所有模型列表"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify(config.get('models', []))
    except Exception as e:
        return jsonify({'error': f'无法读取模型配置: {str(e)}'}), 500


@bp.route('/api/models', methods=['POST'])
def add_model():
    """添加新模型到配置"""
    data = request.json
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    name = data.get('name')
    path = data.get('path')
    model_type = data.get('type')
    description = data.get('description', '')
    
    if not name or not path:
        return jsonify({'error': '模型名称和路径为必填项'}), 400
    
    # 检查模型文件是否存在
    model_file_path = path
    if not os.path.isabs(model_file_path):
        model_file_path = os.path.join(current_app.config['ROOT_DIR'], path)
    
    if not os.path.exists(model_file_path):
        return jsonify({'error': f'模型文件不存在: {model_file_path}'}), 400
    
    # 如果未指定模型类型，尝试自动检测
    if not model_type:
        try:
            # 根据模型名称或内容自动检测类型
            if 'yolov5' in os.path.basename(path).lower():
                model_type = 'yolov5'
            elif 'yolov8' in os.path.basename(path).lower():
                model_type = 'yolov8'
            elif 'qrcode' in os.path.basename(path).lower() or 'qr' in os.path.basename(path).lower():
                model_type = 'yolov8'  # QR码检测模型通常是YOLOv8架构
            else:
                # 尝试加载模型，从元数据判断
                try:
                    import onnxruntime as ort
                    session = ort.InferenceSession(model_file_path)
                    metadata = session.get_modelmeta()
                    
                    if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
                        # YOLOv8特有的metadata键
                        yolov8_keys = ['stride', 'task', 'batch', 'imgsz']
                        # YOLOv5特有的metadata键
                        yolov5_keys = ['model_type', 'size', 'stride']
                        
                        # 统计匹配度
                        v8_count = sum(1 for k in yolov8_keys if k in metadata.custom_metadata_map)
                        v5_count = sum(1 for k in yolov5_keys if k in metadata.custom_metadata_map)
                        
                        if v8_count > v5_count:
                            model_type = 'yolov8'
                        else:
                            model_type = 'yolov5'
                    else:
                        # 如果无法确定，默认使用YOLOv8
                        model_type = 'yolov8'
                except Exception as e:
                    print(f"自动检测模型类型失败: {str(e)}")
                    model_type = 'yolov8'  # 默认使用YOLOv8
        except Exception as e:
            print(f"自动检测模型类型失败: {str(e)}")
            model_type = 'yolov8'  # 默认使用YOLOv8
    
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查重复模型
        for model in config.get('models', []):
            if model['name'] == name:
                return jsonify({'error': '模型名称已存在'}), 400
        
        # 添加新模型
        new_model = {
            'name': name,
            'path': path,
            'type': model_type,
            'description': description
        }
        
        if 'models' not in config:
            config['models'] = []
        
        config['models'].append(new_model)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True, 'model': new_model})
    except Exception as e:
        return jsonify({'error': f'无法更新模型配置: {str(e)}'}), 500


@bp.route('/api/models/<model_name>', methods=['DELETE'])
def delete_model(model_name):
    """删除指定模型"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'models' not in config:
            return jsonify({'error': '没有找到模型配置'}), 404
        
        # 寻找并删除模型
        found = False
        for i, model in enumerate(config['models']):
            if model['name'] == model_name:
                del config['models'][i]
                found = True
                break
        
        if not found:
            return jsonify({'error': f'没有找到名为 {model_name} 的模型'}), 404
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'无法删除模型: {str(e)}'}), 500


@bp.route('/api/models/current', methods=['POST'])
def set_current_model():
    """设置当前使用的模型"""
    data = request.json
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    model_name = data.get('name')
    if not model_name:
        return jsonify({'error': '模型名称为必填项'}), 400
    
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 查找模型
        found_model = None
        for model in config.get('models', []):
            if model['name'] == model_name:
                found_model = model
                break
        
        if not found_model:
            return jsonify({'error': f'没有找到名为 {model_name} 的模型'}), 404
        
        # 更新当前模型
        config['model']['current_model'] = model_name
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        # 加载模型
        global detector
        try:
            model_path = found_model['path']
            # 检查路径是否存在，如果是相对路径则转为绝对路径
            if not os.path.isabs(model_path):
                model_path = os.path.join(current_app.config['ROOT_DIR'], model_path)
                
            print(f"正在加载模型，路径: {model_path}")
            if not os.path.exists(model_path):
                return jsonify({'error': f'模型文件不存在: {model_path}'}), 404
                
            detector = YOLODetector(model_path, found_model['type'])
            print(f"已加载模型: {model_name}, 路径: {model_path}")
            
            # 使用socketio广播，通知所有客户端模型已更新
            socketio.emit('model_loaded', {
                'success': True, 
                'model': found_model,
                'message': f'成功加载模型: {model_name}'
            })
            
            return jsonify({
                'success': True, 
                'model': found_model,
                'message': f'成功加载模型: {model_name}'
            })
        except Exception as e:
            return jsonify({'error': f'模型加载失败: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'无法设置当前模型: {str(e)}'}), 500


@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    处理文件上传请求
    
    Returns:
        包含上传文件信息的JSON响应
    """
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'filepath': filepath
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400


@bp.route('/api/roi-configs', methods=['GET'])
def get_roi_configs():
    """获取所有ROI配置"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify(config.get('roi_configs', {}))
    except Exception as e:
        return jsonify({'error': f'无法读取ROI配置: {str(e)}'}), 500


@bp.route('/api/roi-configs', methods=['POST'])
def save_roi_configs():
    """保存ROI配置"""
    data = request.json
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        # 读取当前配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新ROI配置
        config['roi_configs'] = data
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'保存ROI配置失败: {str(e)}'}), 500


@bp.route('/api/roi-config/<config_name>', methods=['DELETE'])
def delete_roi_config(config_name):
    """删除指定的ROI配置"""
    config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
    try:
        # 读取当前配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查ROI配置是否存在
        if 'roi_configs' not in config or config_name not in config['roi_configs']:
            return jsonify({'error': f'找不到ROI配置: {config_name}'}), 404
        
        # 删除配置
        del config['roi_configs'][config_name]
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'删除ROI配置失败: {str(e)}'}), 500


@bp.route('/api/upload-roi-background', methods=['POST'])
def upload_roi_background():
    """处理ROI背景图片上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 使用统一的uploads目录，不再创建子文件夹
        uploads_dir = current_app.config['UPLOAD_FOLDER']
        
        # 保存原始文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"roi_bg_{timestamp}_{filename}"
        filepath = os.path.join(uploads_dir, new_filename)
        file.save(filepath)
        
        try:
            # 读取原始图像
            image = cv2.imread(filepath)
            if image is None:
                return jsonify({'error': '无法读取图像'}), 400
            
            # 使用ImagePreprocessor进行预处理，这里我们只需要处理后的显示图像
            preprocessor = ImagePreprocessor(640, 640)
            input_tensor, _ = preprocessor.preprocess(image)  # 忽略预处理参数
            
            # 从预处理结果中获取图像数据并转回OpenCV格式用于显示
            display_img = input_tensor[0]  # 移除批次维度
            display_img = np.transpose(display_img, (1, 2, 0))  # CHW -> HWC
            display_img = display_img[:, :, ::-1]  # RGB -> BGR (OpenCV格式)
            display_img = (display_img * 255).astype(np.uint8)  # [0-1] -> [0-255]
            
            # 生成处理后的文件名
            processed_filename = f"roi_bg_resized_{timestamp}_{filename}"
            processed_filepath = os.path.join(uploads_dir, processed_filename)
            
            # 保存处理后的图像
            cv2.imwrite(processed_filepath, display_img)
            
            # 返回处理后的图像URL (相对路径)
            return jsonify({
                'success': True,
                'url': f"/static/uploads/{processed_filename}"
                # 不再返回预处理参数，因为ROI阶段不需要
            })
        except Exception as e:
            return jsonify({'error': f'处理图像出错: {str(e)}'}), 500
    
    return jsonify({'error': '不支持的文件类型'}), 400


@socketio.on('connect')
def handle_connect():
    """处理新的WebSocket连接"""
    print('客户端已连接')
    # 尝试在连接时自动加载当前模型
    try:
        config_path = os.path.join(current_app.config['ROOT_DIR'], 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        current_model_name = config.get('model', {}).get('current_model')
        if current_model_name:
            print(f"尝试自动加载模型: {current_model_name}")
            found_model = None
            for model in config.get('models', []):
                if model['name'] == current_model_name:
                    found_model = model
                    break
            
            if found_model:
                global detector
                try:
                    model_path = found_model['path']
                    # 检查路径是否存在，如果是相对路径则转为绝对路径
                    if not os.path.isabs(model_path):
                        model_path = os.path.join(current_app.config['ROOT_DIR'], model_path)
                    
                    print(f"正在加载模型，路径: {model_path}")
                    if not os.path.exists(model_path):
                        print(f"警告: 模型文件不存在: {model_path}")
                        emit('model_error', {'error': f'模型文件不存在: {model_path}'})
                        return
                        
                    detector = YOLODetector(model_path, found_model['type'])
                    print(f"自动加载模型成功: {current_model_name}, 路径: {model_path}")
                    emit('model_loaded', {
                        'success': True,
                        'model': found_model,
                        'message': f'已自动加载模型: {current_model_name}'
                    })
                except Exception as e:
                    print(f"自动加载模型失败: {str(e)}")
                    emit('model_error', {'error': f'模型加载失败: {str(e)}'})
            else:
                print(f"找不到名为 {current_model_name} 的模型配置")
    except Exception as e:
        print(f"检查当前模型配置失败: {str(e)}")


@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    print('客户端断开连接')


@socketio.on('detect')
def handle_detect(data):
    """
    处理目标检测的WebSocket事件
    
    Args:
        data: 包含检测请求信息的字典
    """
    global detector
    image_path = data.get('image_path', '')
    
    if detector is None:
        emit('detection_error', {'error': '检测器未初始化，请先加载模型'})
        return
    
    if not os.path.exists(image_path):
        emit('detection_error', {'error': f'图像文件不存在: {image_path}'})
        return
    
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            emit('detection_error', {'error': '无法读取图像'})
            return
        
        # 执行检测
        boxes, scores, class_ids, processed_image = detector.detect(image)
        
        # 保存处理后的图像
        result_filename = f"result_{os.path.basename(image_path)}"
        result_path = os.path.join(current_app.config['RESULT_FOLDER'], result_filename)
        cv2.imwrite(result_path, processed_image)
        
        # 准备结果
        results = []
        for i, box in enumerate(boxes):
            results.append({
                'bbox': box.tolist() if hasattr(box, 'tolist') else box,
                'score': float(scores[i]),
                'class_id': int(class_ids[i]),
                'class_name': detector.get_class_name(class_ids[i])
            })
        
        # 返回结果
        emit('detection_results', {
            'success': True,
            'results': results,
            'result_image': f"/static/results/{result_filename}"
        })
    except Exception as e:
        emit('detection_error', {'error': f'检测过程中出错: {str(e)}'})
