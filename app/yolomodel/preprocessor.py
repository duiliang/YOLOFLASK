"""
预处理模块，负责图像的归一化、调整大小等预处理操作
"""
import cv2
import numpy as np

class ImagePreprocessor:
    """图像预处理器类，处理输入图像使其符合模型要求"""
    
    def __init__(self, input_width, input_height):
        """
        初始化预处理器
        
        Args:
            input_width: 模型输入宽度
            input_height: 模型输入高度
        """
        self.input_width = input_width
        self.input_height = input_height
    
    def resize_with_padding(self, image, target_width, target_height):
        """
        调整图像大小并添加填充，保持原始宽高比
        
        Args:
            image: 原始图像
            target_width: 目标宽度
            target_height: 目标高度
            
        Returns:
            调整大小后的图像和预处理参数
        """
        # 保存原始图像尺寸
        img_height, img_width = image.shape[:2]
        
        # 计算缩放比例
        scale_w = target_width / img_width
        scale_h = target_height / img_height
        
        # 确定缩放因子（保持宽高比）
        scale = min(scale_w, scale_h)
        
        if scale_w < scale_h:
            # 按宽度缩放
            scaled_width = target_width
            scaled_height = int(img_height * scale_w)
        else:
            # 按高度缩放
            scaled_width = int(img_width * scale_h)
            scaled_height = target_height
            
        # 缩放图像
        image_resized = cv2.resize(image, (scaled_width, scaled_height))
        
        # 创建空白画布(输入尺寸)
        canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # 将调整大小的图像粘贴到画布中央
        offset_x = (target_width - scaled_width) // 2
        offset_y = (target_height - scaled_height) // 2
        canvas[offset_y:offset_y+scaled_height, offset_x:offset_x+scaled_width] = image_resized
        
        # 构建预处理参数
        preprocess_params = {
            'offset_x': offset_x,
            'offset_y': offset_y,
            'scale': scale,
            'original_width': img_width,
            'original_height': img_height
        }
        
        return canvas, preprocess_params
    
    def preprocess(self, image):
        """
        图像预处理
        
        Args:
            image: OpenCV格式的图像(BGR)
            
        Returns:
            预处理后的图像，以及预处理参数(用于后续坐标转换)
        """
        # 调整图像大小并添加填充
        canvas, preprocess_params = self.resize_with_padding(image, self.input_width, self.input_height)
        
        # 归一化处理 [0-255] -> [0-1]
        input_img = canvas.astype(np.float32) / 255.0
        
        # BGR -> RGB
        input_img = input_img[:, :, ::-1]
        
        # HWC -> NCHW (批次,通道,高,宽)
        input_img = np.transpose(input_img, (2, 0, 1))
        input_img = np.expand_dims(input_img, 0)
        
        return input_img, preprocess_params
