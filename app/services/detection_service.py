"""
检测服务模块
处理目标检测的核心业务逻辑
"""
import os
import cv2
from flask import current_app
from app.services.model_service import get_detector

def detect_objects(image_path):
    """
    对图像进行目标检测
    
    Args:
        image_path: 图像文件路径
        
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
        result_url = f"/static/results/{result_filename}"
        return True, results, result_url
    except Exception as e:
        return False, f'检测过程中出错: {str(e)}', None
