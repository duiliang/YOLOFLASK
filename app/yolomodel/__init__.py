"""
YOLO检测模型模块包

此包包含所有与YOLO模型检测相关的组件，包括：
- 预处理 (图像调整、归一化等)
- 模型加载与推理
- 后处理 (坐标变换、NMS等)
- 结果可视化
"""

from .detector import YOLODetector

__all__ = ['YOLODetector']
