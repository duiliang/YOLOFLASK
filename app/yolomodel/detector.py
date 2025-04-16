"""
YOLO检测器主模块，集成了预处理、推理、后处理和可视化功能
"""
import os
import time
import onnxruntime as ort

from .config import ConfigLoader
from .class_utils import ClassManager
from .preprocessor import ImagePreprocessor
from .postprocessor import YOLOPostprocessor
from .visualizer import DetectionVisualizer
from .logger import get_logger

class YOLODetector:
    """
    YOLO目标检测器类，使用ONNX模型进行推理
    """
    
    def __init__(self, model_path, model_type='yolov8'):
        """
        初始化YOLO检测器
        
        Args:
            model_path: ONNX模型文件的路径
            model_type: 模型类型，目前支持'yolov8'
        """
        # 初始化日志
        self.logger = get_logger("YOLO", "info")
        
        self.model_path = model_path
        self.model_type = model_type
        
        # 加载配置
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        
        # 初始化ONNX运行时会话
        try:
            self.session = ort.InferenceSession(model_path)
        except Exception as e:
            error_msg = f"加载ONNX模型失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        # 获取模型输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]
        
        # 设置输入形状(假设只有一个输入)
        self.input_shape = self.session.get_inputs()[0].shape
        if self.input_shape[0] == -1:  # 动态批次大小
            self.batch_size = 1
            self.input_width = self.input_shape[2]
            self.input_height = self.input_shape[3]
        else:  # 固定批次大小
            self.batch_size = self.input_shape[0]
            self.input_width = self.input_shape[2]
            self.input_height = self.input_shape[3]
        
        # 初始化类别管理器和类别列表
        self.class_manager = ClassManager(model_path, self.session)
        self.classes = self.class_manager.extract_classes_from_model() or self.class_manager.get_default_classes()
        
        # 设置置信度阈值和NMS阈值
        self.conf_threshold = self.config['model']['conf_threshold']
        self.iou_threshold = self.config['model']['iou_threshold']
        
        # 初始化预处理器、后处理器和可视化器
        self.preprocessor = ImagePreprocessor(self.input_width, self.input_height)
        self.postprocessor = YOLOPostprocessor(self.conf_threshold, self.iou_threshold)
        self.visualizer = DetectionVisualizer(self.classes)
        
        self.logger.info(f"YOLO检测器初始化成功: {model_type}, 输入尺寸: {self.input_width}x{self.input_height}")
    
    def load_config(self):
        """加载配置文件"""
        return self.config_loader.load_config()
    
    def get_default_classes(self):
        """
        获取默认的COCO数据集类别名称
        
        Returns:
            COCO数据集的80个类别名称列表
        """
        return self.class_manager.get_default_classes()
    
    def extract_classes_from_model(self):
        """
        尝试从ONNX模型中提取类别名称
        
        Returns:
            如果成功，返回类别名称列表；如果失败，返回None
        """
        return self.class_manager.extract_classes_from_model()
    
    def preprocess(self, image):
        """
        图像预处理
        
        Args:
            image: OpenCV格式的图像(BGR)
            
        Returns:
            预处理后的图像和参数
        """
        return self.preprocessor.preprocess(image)
    
    def detect(self, image):
        """
        执行目标检测
        
        Args:
            image: 要检测的图像(BGR格式)
            
        Returns:
            检测到的边界框、置信度分数、类别ID和处理后的图像
        """
        # 预处理图像
        input_tensor, preprocess_params = self.preprocessor.preprocess(image)
        
        # 执行推理
        start_time = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        inference_time = time.time() - start_time
        detection_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.logger.info(f"[{detection_timestamp}] 推理时间: {inference_time*1000:.2f} ms")
        
        # 后处理结果 (根据模型类型)
        if self.model_type == 'yolov8':
            boxes, scores, class_ids = self.postprocessor.postprocess_yolov8(outputs[0], preprocess_params)
        else:
            error_msg = f"不支持的模型类型: {self.model_type}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 在图像上绘制检测结果
        result_image = self.visualizer.draw_detections(image.copy(), boxes, scores, class_ids)
        
        print(f"检测完成,输出图片大小为{result_image.shape}")
        
        return boxes, scores, class_ids, result_image
    
    def get_class_name(self, class_id):
        """
        获取类别名称
        
        Args:
            class_id: 类别ID
            
        Returns:
            对应的类别名称
        """
        return self.visualizer.get_class_name(class_id)
    
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
        return self.visualizer.draw_detections(image, boxes, scores, class_ids)
