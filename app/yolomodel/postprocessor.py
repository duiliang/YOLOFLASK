"""
后处理模块，负责处理模型输出、坐标转换、非极大值抑制等操作
"""
import cv2
import numpy as np
import time
from .logger import get_logger

class YOLOPostprocessor:
    """YOLO后处理器类，处理模型输出"""
    
    def __init__(self, conf_threshold=0.25, iou_threshold=0.45):
        """
        初始化后处理器
        
        Args:
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值
        """
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.logger = get_logger("YOLO", "info")
    
    def postprocess(self, model_output, preprocess_params, model_type='yolov8'):
        """
        后处理模型输出
        
        Args:
            model_output: 模型原始输出
            preprocess_params: 预处理参数，用于坐标转换
            model_type: 模型类型，目前支持'yolov8'
            
        Returns:
            处理后的边界框、置信度分数和类别ID
        """
        if model_type == 'yolov8':
            return self.postprocess_yolov8(model_output, preprocess_params)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def postprocess_yolov8(self, output, preprocess_params):
        """
        YOLOv8模型的后处理
        
        Args:
            output: 模型的原始输出
            preprocess_params: 预处理参数，用于坐标转换
            
        Returns:
            处理后的边界框、置信度分数和类别ID
        """
        try:
            # 记录处理开始时间
            start_time = time.time()
            
            # 提取预处理参数
            offset_x = preprocess_params['offset_x']
            offset_y = preprocess_params['offset_y']
            scale = preprocess_params['scale']
            original_width = preprocess_params['original_width']
            original_height = preprocess_params['original_height']
            
            # 检查输出形状，判断是哪种格式的YOLOv8输出
            output_shape = output.shape
            
            # 打印出输出形状，用于调试
            self.logger.info(f"YOLOv8输出形状: {output_shape}")
            
            # 处理不同格式的YOLOv8输出
            if len(output_shape) == 3 and output_shape[1] <= 5:  # 新版本格式 [batch, 5, 8400] - YOLOv8检测
                self.logger.info(f"检测到YOLOv8-Detect格式输出")
                # 获取输出并转置 [batch, 5, 8400] -> [batch, 8400, 5]
                output = np.transpose(output, (0, 2, 1))
                
                # 获取第一个批次的预测结果
                predictions = output[0]  # [8400, 5]
                
                # 获取边界框坐标和置信度
                boxes = predictions[:, 0:4]  # [8400, 4] - 边界框坐标
                confidences = predictions[:, 4]  # [8400] - 置信度分数
                
                # 根据置信度阈值筛选检测结果
                mask = confidences > self.conf_threshold
                self.logger.info(f"检测到 {np.sum(mask)} 个目标(置信度 > {self.conf_threshold})")
                
                # 应用mask筛选
                boxes = boxes[mask]  # 重要：这里要更新boxes变量，而不是创建新变量
                scores = confidences[mask].astype(float)  # 确保是浮点数
                
                # 在这种情况下，所有检测对象都是同一类别(0)
                class_ids = np.zeros(len(scores), dtype=np.int32)
                
                if len(scores) == 0:
                    self.logger.info(f"没有检测到足够置信度的目标")
                    return [], [], []
                
            elif len(output_shape) == 3:  # 新版本格式 [batch, 85, 8400] - YOLOv8分类
                self.logger.info(f"检测到YOLOv8-Classify/Segment格式输出")
                # 转置以获得传统格式 [batch, 8400, 85]
                output = np.transpose(output, (0, 2, 1))
                
                # 获取第一个批次
                predictions = output[0]  # [8400, 85]
                
                # 分离边界框和类别概率
                num_classes = output_shape[1] - 4  # 减去4个边界框坐标
                boxes = predictions[:, :4]  # 前4列是边界框坐标 (xywh)
                
                # 第5列是目标置信度，后续列是类别分数
                object_conf = predictions[:, 4]
                
                # 根据目标置信度筛选
                mask = object_conf > self.conf_threshold
                boxes = boxes[mask]
                filtered_conf = object_conf[mask]
                
                if len(filtered_conf) == 0:
                    self.logger.info(f"没有检测到足够置信度的目标")
                    return [], [], []
                
                # 提取类别分数(第6列及之后)，并与置信度相乘
                class_scores = predictions[mask, 5:]
                class_scores *= filtered_conf[:, np.newaxis]
                
                # 获取最高类别概率及其索引
                best_class_scores = np.max(class_scores, axis=1)
                best_class_ids = np.argmax(class_scores, axis=1)
                
                # 再次根据类别分数筛选
                mask2 = best_class_scores > self.conf_threshold
                boxes = boxes[mask2]
                scores = best_class_scores[mask2].astype(float)  # 确保是浮点数
                class_ids = best_class_ids[mask2]
                
                if len(scores) == 0:
                    self.logger.info(f"没有检测到足够类别置信度的目标")
                    return [], [], []
                
            else:  # 传统格式 [batch, num_detections, 4+1+num_classes]
                self.logger.info(f"检测到传统YOLOv8格式输出")
                # 提取置信度分数(第5列)
                scores = output[:, 4]
                
                # 根据置信度阈值筛选检测结果
                mask = scores >= self.conf_threshold
                filtered_output = output[mask]
                filtered_scores = scores[mask]
                
                if len(filtered_scores) == 0:
                    self.logger.info(f"没有检测到足够置信度的目标")
                    return [], [], []
                
                # 提取类别概率(第6列及之后)
                class_probs = filtered_output[:, 5:]
                
                # 获取最高类别概率及其索引
                class_ids = np.argmax(class_probs, axis=1)
                class_scores = np.max(class_probs, axis=1)
                
                # 计算最终分数(置信度 * 类别概率)
                scores = filtered_scores * class_scores
                
                # 再次根据综合分数筛选
                mask2 = scores >= self.conf_threshold
                boxes = filtered_output[mask2, :4]  # 更新boxes变量
                scores = scores[mask2].astype(float)  # 确保是浮点数
                class_ids = class_ids[mask2]
                
                if len(scores) == 0:
                    self.logger.info(f"没有检测到足够类别置信度的目标")
                    return [], [], []
            
            # 转换坐标(中心点xy,宽高wh -> 左上角xyxy)
            boxes = self._xywh2xyxy(boxes)
            
            # 从模型输入尺寸缩放回原始图像尺寸
            boxes = self._rescale_boxes(boxes, offset_x, offset_y, scale, original_width, original_height)
            
            # 确保数据类型正确
            boxes_list = boxes.tolist()
            scores_list = scores.tolist()  # 确保是一维列表
            
            self.logger.info(f"执行NMS: boxes类型: {type(boxes_list)}, scores类型: {type(scores_list)}")
            self.logger.info(f"boxes长度: {len(boxes_list)}, scores长度: {len(scores_list)}")
            
            if len(boxes_list) > 0 and len(scores_list) > 0:
                # 确保boxes和scores长度相同
                if len(boxes_list) != len(scores_list):
                    self.logger.warning(f"警告: boxes长度({len(boxes_list)})和scores长度({len(scores_list)})不一致，截断到较小长度")
                    min_len = min(len(boxes_list), len(scores_list))
                    boxes_list = boxes_list[:min_len]
                    scores_list = scores_list[:min_len]
                    boxes = boxes[:min_len]
                    scores = scores[:min_len]
                    class_ids = class_ids[:min_len]
                
                # 执行非极大值抑制(NMS)
                indices = cv2.dnn.NMSBoxes(boxes_list, scores_list, self.conf_threshold, self.iou_threshold)
                
                if len(indices) > 0:
                    # OpenCV 4.x返回的indices格式不同
                    if isinstance(indices, tuple):
                        final_boxes = boxes[indices]
                        final_scores = scores[indices]
                        final_class_ids = class_ids[indices]
                    else:
                        indices = indices.flatten()
                        final_boxes = boxes[indices]
                        final_scores = scores[indices]
                        final_class_ids = class_ids[indices]
                    
                    process_time = time.time() - start_time
                    self.logger.info(f"NMS后保留 {len(final_boxes)} 个目标 (处理耗时: {process_time*1000:.2f}ms)")
                    return final_boxes, final_scores, final_class_ids
                else:
                    self.logger.info(f"NMS后没有保留的目标")
            
            # 如果没有结果或NMS后没有留下的框
            return [], [], []
        
        except Exception as e:
            # 详细记录错误信息，便于调试
            self.logger.error(f"YOLOv8后处理错误: {str(e)}")
            self.logger.error(f"输出形状: {output.shape if hasattr(output, 'shape') else 'unknown'}")
            import traceback
            self.logger.error(traceback.format_exc())
            return [], [], []
    
    def _xywh2xyxy(self, boxes):
        """
        将中心点+宽高格式(xywh)转换为左上角+右下角格式(x1y1x2y2)
        
        Args:
            boxes: xywh格式的边界框
            
        Returns:
            xyxy格式的边界框
        """
        xyxy = np.zeros_like(boxes)
        xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1 = x - w/2
        xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1 = y - h/2
        xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2 = x + w/2
        xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2 = y + h/2
        return xyxy
    
    def _rescale_boxes(self, boxes, offset_x, offset_y, scale, original_width, original_height):
        """
        将边界框从模型输入尺寸转换回原始图像尺寸
        
        Args:
            boxes: 模型输入尺寸的边界框坐标
            offset_x: X方向偏移量
            offset_y: Y方向偏移量
            scale: 缩放系数
            original_width: 原始图像宽度
            original_height: 原始图像高度
            
        Returns:
            原始图像尺寸的边界框坐标
        """
        # 减去偏移量
        boxes[:, [0, 2]] -= offset_x
        boxes[:, [1, 3]] -= offset_y
        
        # 缩放到原始图像尺寸
        boxes[:, :4] /= scale
        
        # 确保边界框在图像范围内
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, original_width - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, original_height - 1)
        
        return boxes
