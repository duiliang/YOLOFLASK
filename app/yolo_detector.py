"""
YOLO检测器模块 - 代理类
这个文件是一个代理，用于保持向后兼容性，实际实现已迁移到yolomodel包中
"""
from app.yolomodel.detector import YOLODetector

# 保持相同的导入名称，使现有代码不需要修改
__all__ = ['YOLODetector']
