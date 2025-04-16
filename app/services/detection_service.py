"""
检测服务模块
处理目标检测的核心业务逻辑
"""
import os
import cv2
import numpy as np
from flask import current_app

from app.yolomodel.preprocessor import ImagePreprocessor
from app.services.model_service import get_detector
from app.services.roi_service import get_roi_config_detail, get_roi_configs
from app.services.logic_service import get_logic_rules

def detect_objects(image_path, selected_rule_name=None):
    """
    对图像进行目标检测
    
    Args:
        image_path: 图像文件路径
        selected_rule_name: 选中的逻辑规则名称（可选）
        
    Returns:
        (成功标志, 检测结果或错误信息, 处理后的图像路径)
    """ 
    detector = get_detector()
    
    if detector is None:
        return False, '检测器未初始化，请先加载模型', None
    
    if not os.path.exists(image_path):
        return False, f'图像文件不存在: {image_path}', None
    
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            return False, '无法读取图像', None
        
        # 获取ROI配置（如果指定了规则名称）
        roi_config = None
        if selected_rule_name:
            logic_rules = get_logic_rules()
            if selected_rule_name in logic_rules:
                rule = logic_rules[selected_rule_name]
                roi_config_name = rule.get('roi_config')
                if roi_config_name:
                    # 获取ROI配置详情
                    roi_configs = get_roi_configs()
                    if roi_config_name in roi_configs:
                        roi_config = roi_configs[roi_config_name]
        
        # 使用ImagePreprocessor实例的resize_with_padding方法处理图像
        preprocessor = get_detector().preprocessor 
        processed_image, preprocess_paramsUseless = preprocessor.resize_with_padding(image,640,640)
        #暂时不处理版本
        #processed_image = image
        
        # 执行检测
        boxes, scores, class_ids, processed_image = detector.detect(processed_image)
        
        # 如果有ROI配置，在处理后的图像上绘制ROI区域
        if roi_config:
            # 在检测后的图像上绘制ROI区域
            processed_image = draw_roi_on_image(processed_image, roi_config)
        
        # 准备结果
        results = []
        for i, box in enumerate(boxes):
            # 转换box为列表
            bbox = box.tolist() if hasattr(box, 'tolist') else box
            
            # 创建检测结果对象
            detection = {
                'bbox': bbox,
                'score': float(scores[i]),
                'class_id': int(class_ids[i]),
                'class_name': detector.get_class_name(class_ids[i])
            }
            
            # 确定该对象位于哪个ROI区域（如果有）
            detection['roi_id'] = None  # 默认不在任何ROI区域内
            
            # 添加到结果列表
            results.append(detection)
        
        # 如果有ROI配置，为检测结果分配ROI区域
        if roi_config:
            assign_roi_to_detections(results, image.shape, roi_config)
        
        # 保存处理后的图像
        result_filename = f"result_{os.path.basename(image_path)}"
        result_path = os.path.join(current_app.config['RESULT_FOLDER'], result_filename)
        cv2.imwrite(result_path, processed_image)
        
        # 结果URL
        result_url = f"/static/results/{result_filename}"
        
        # 返回结果
        return True, results, result_url
    except Exception as e:
        return False, f'检测过程中出错: {str(e)}', None

def draw_roi_on_image(image, roi_config):
    """
    在图像上绘制ROI区域
    
    Args:
        image: 原始图像
        roi_config: ROI配置
        
    Returns:
        添加了ROI区域的图像
    """
    if not roi_config or 'rois' not in roi_config:
        return image
    
    # 创建图像副本，避免修改原图
    result_image = image.copy()
    
    # 遍历所有ROI区域
    for roi_id, roi in enumerate(roi_config['rois']):
        # 获取ROI类型和坐标
        roi_type = roi.get('type')
        
        # 获取颜色，默认为蓝色
        color_hex = roi.get('color', '#007bff')
        # 将16进制颜色转换为BGR
        color = hex_to_bgr(color_hex)
        
        # ROI编号从1开始
        roi_display_id = roi_id + 1
        
        # 绘制ROI区域
        if roi_type == 'rectangle':
            x1, y1 = int(roi.get('x1', 0)), int(roi.get('y1', 0))
            x2, y2 = int(roi.get('x2', 0)), int(roi.get('y2', 0))
            
            # 绘制矩形
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 添加ROI ID标签
            cv2.putText(result_image, f"ROI {roi_display_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        elif roi_type == 'polygon':
            points = roi.get('points', [])
            if points:
                # 转换点数组
                poly_points = np.array([[p['x'], p['y']] for p in points], np.int32)
                poly_points = poly_points.reshape((-1, 1, 2))
                
                # 绘制多边形
                cv2.polylines(result_image, [poly_points], True, color, 2)
                
                # 添加ROI ID标签（使用第一个点作为标签位置）
                if len(points) > 0:
                    label_x, label_y = points[0]['x'], points[0]['y']
                    cv2.putText(result_image, f"ROI {roi_display_id}", (label_x, label_y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return result_image

def hex_to_bgr(hex_color):
    """
    将16进制颜色转换为BGR
    
    Args:
        hex_color: 16进制颜色代码（例如#FF0000）
        
    Returns:
        BGR颜色元组
    """
    # 去除#号
    hex_color = hex_color.lstrip('#')
    
    # 转换为RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # 返回BGR（OpenCV使用BGR）
    return (b, g, r)

def assign_roi_to_detections(detections, image_shape, specific_roi_config=None):
    """
    为每个检测结果分配ROI区域ID
    
    Args:
        detections: 检测结果列表
        image_shape: 图像尺寸 (height, width, channels)
        specific_roi_config: 特定的ROI配置（如果有）
    """
    # 如果提供了特定的ROI配置，就只检查这个配置
    if specific_roi_config and 'rois' in specific_roi_config:
        rois = specific_roi_config['rois']
        config_name = specific_roi_config.get('name', '')
        
        # 查找每个检测框是否在任何ROI区域内
        for detection in detections:
            bbox = detection['bbox']
            
            # 计算检测框中心点
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # 检查点是否在任何ROI区域内
            for roi_id, roi in enumerate(rois):
                if is_point_in_roi(center_x, center_y, roi, image_shape):
                    detection['roi_id'] = roi_id
                    detection['roi_config'] = config_name
                    break
        return
    
    # 否则，检查所有ROI配置
    # 获取所有ROI配置
    roi_configs = get_roi_configs()
    
    # 获取所有逻辑规则
    logic_rules = get_logic_rules()
    
    # 如果没有规则或配置，直接返回
    if not logic_rules or not roi_configs:
        return
    
    # 查找每个检测框是否在任何ROI区域内
    for detection in detections:
        bbox = detection['bbox']
        
        # 计算检测框中心点
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        # 遍历所有逻辑规则中可能用到的ROI配置
        for rule_name, rule in logic_rules.items():
            roi_config_name = rule.get('roi_config')
            if not roi_config_name or roi_config_name not in roi_configs:
                continue
                
            roi_config = roi_configs[roi_config_name]
            rois = roi_config.get('rois', [])
            
            # 检查点是否在任何ROI区域内
            for roi_id, roi in enumerate(rois):
                if is_point_in_roi(center_x, center_y, roi, image_shape):
                    detection['roi_id'] = roi_id
                    detection['roi_config'] = roi_config_name
                    break
            
            # 如果已经找到了ROI区域，就不需要继续检查其他配置
            if detection['roi_id'] is not None:
                break

def is_point_in_roi(x, y, roi, image_shape):
    """
    检查点是否在ROI区域内
    
    Args:
        x, y: 点的坐标
        roi: ROI区域定义
        image_shape: 图像尺寸
    
    Returns:
        bool: 点是否在ROI区域内
    """
    roi_type = roi.get('type')
    
    # 对于矩形ROI
    if roi_type == 'rectangle':
        x1, y1 = roi.get('x1', 0), roi.get('y1', 0)
        x2, y2 = roi.get('x2', 0), roi.get('y2', 0)
        return x1 <= x <= x2 and y1 <= y <= y2
    
    # 对于多边形ROI
    elif roi_type == 'polygon':
        points = roi.get('points', [])
        if not points:
            return False
            
        # 创建点数组
        poly_points = np.array([[p['x'], p['y']] for p in points], np.int32)
        
        # 使用OpenCV的pointPolygonTest函数
        dist = cv2.pointPolygonTest(poly_points, (float(x), float(y)), False)
        return dist >= 0
    
    # 未知类型默认不在区域内
    return False
