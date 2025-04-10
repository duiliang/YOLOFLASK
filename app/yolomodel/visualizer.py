"""
可视化模块，负责在图像上绘制检测结果
"""
import cv2
import numpy as np

class DetectionVisualizer:
    """检测结果可视化器类"""
    
    def __init__(self, class_names=None):
        """
        初始化可视化器
        
        Args:
            class_names: 类别名称列表
        """
        self.class_names = class_names or []
    
    def draw_detections(self, image, boxes, scores, class_ids):
        """
        在图像上绘制检测结果
        
        Args:
            image: 原始图像
            boxes: 检测到的边界框
            scores: 置信度分数
            class_ids: 类别ID
            
        Returns:
            标注了检测结果的图像
        """
        result = image.copy()
        
        for i, box in enumerate(boxes):
            # 提取坐标和置信度
            x1, y1, x2, y2 = map(int, box)
            score = scores[i]
            class_id = class_ids[i]
            class_name = self.get_class_name(class_id)
            
            # 生成不同类别的颜色
            color = self.generate_color(class_id)
            
            # 绘制边界框
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            
            # 准备标签文本
            label = f"{class_name}: {score:.2f}"
            
            # 获取文本大小
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # 绘制标签背景
            cv2.rectangle(result, (x1, y1 - text_height - 5), (x1 + text_width, y1), color, -1)
            
            # 绘制标签文本
            cv2.putText(result, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        return result
    
    def get_class_name(self, class_id):
        """
        获取类别名称
        
        Args:
            class_id: 类别ID
            
        Returns:
            对应的类别名称
        """
        if 0 <= class_id < len(self.class_names):
            return self.class_names[class_id]
        return f"Unknown-{class_id}"
    
    def generate_color(self, class_id):
        """
        为类别生成唯一的颜色
        
        Args:
            class_id: 类别ID
            
        Returns:
            BGR格式的颜色元组
        """
        # 生成伪随机但确定的颜色
        np.random.seed(class_id)
        color = tuple(map(int, np.random.randint(0, 255, size=3)))
        np.random.seed(None)  # 重置随机数生成器
        return color
