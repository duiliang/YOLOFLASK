import cv2
import numpy as np
import onnxruntime as ort
import time
import os
import json

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
        self.model_path = model_path
        self.model_type = model_type
        
        # 加载配置
        self.load_config()
        
        # 初始化ONNX运行时会话
        try:
            self.session = ort.InferenceSession(model_path)
        except Exception as e:
            raise Exception(f"加载ONNX模型失败: {str(e)}")
            
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
            
        # 尝试从ONNX模型中提取类别名称，如果失败则使用默认类别
        self.classes = self.extract_classes_from_model() or self.get_default_classes()
        
        # 设置置信度阈值和NMS阈值
        self.conf_threshold = self.config['model']['conf_threshold']
        self.iou_threshold = self.config['model']['iou_threshold']
        
        print(f"YOLO检测器初始化成功: {model_type}, 输入尺寸: {self.input_width}x{self.input_height}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}，使用默认配置")
            self.config = {
                "model": {
                    "conf_threshold": 0.25,
                    "iou_threshold": 0.45
                }
            }
    
    def extract_classes_from_model(self):
        """
        尝试从ONNX模型中提取类别名称
        
        Returns:
            如果成功，返回类别名称列表；如果失败，返回None
        """
        try:
            print("正在尝试从模型中提取类别名称...")
            
            # 尝试获取模型的元数据
            metadata = self.session.get_modelmeta()
            
            # 检查元数据中是否有类别名称
            if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
                print(f"模型元数据: {metadata.custom_metadata_map.keys()}")
                
                # 尝试从不同的元数据键中获取类别名称
                for possible_key in ['names', 'classes', 'labels', 'class_names']:
                    if possible_key in metadata.custom_metadata_map:
                        try:
                            # 尝试解析类别名称（可能是JSON字符串）
                            class_data = metadata.custom_metadata_map[possible_key]
                            print(f"找到类别数据，键: {possible_key}, 值: {class_data[:100]}...")
                            
                            # 尝试解析为JSON
                            try:
                                class_names = json.loads(class_data)
                                
                                # 根据数据类型进行处理
                                if isinstance(class_names, dict):
                                    # 如果是字典（{0: 'person', 1: 'bicycle', ...}），则转换为列表
                                    max_idx = max(map(int, class_names.keys()))
                                    classes = [''] * (max_idx + 1)
                                    for idx, name in class_names.items():
                                        classes[int(idx)] = name
                                    print(f"从模型中提取到 {len(classes)} 个类别名称（字典格式）")
                                    return classes
                                elif isinstance(class_names, list):
                                    # 如果已经是列表，则直接返回
                                    print(f"从模型中提取到 {len(class_names)} 个类别名称（列表格式）")
                                    return class_names
                            except json.JSONDecodeError:
                                # 如果不是JSON，尝试其他格式
                                if ',' in class_data:
                                    # 可能是逗号分隔的类别列表
                                    classes = [c.strip() for c in class_data.split(',')]
                                    print(f"从模型中提取到 {len(classes)} 个类别名称（逗号分隔格式）")
                                    return classes
                                elif '\n' in class_data:
                                    # 可能是换行符分隔的类别列表
                                    classes = [c.strip() for c in class_data.split('\n')]
                                    print(f"从模型中提取到 {len(classes)} 个类别名称（换行符分隔格式）")
                                    return classes
                        except Exception as inner_e:
                            print(f"解析类别名称失败: {str(inner_e)}")
            
            # 如果元数据中没有找到，则查找模型文件旁边的类别文件
            print("在模型元数据中未找到类别信息，尝试从模型目录读取类别文件...")
            
            model_dir = os.path.dirname(self.model_path)
            model_name = os.path.splitext(os.path.basename(self.model_path))[0]
            
            # 获取模型目录下的所有文件
            try:
                dir_files = os.listdir(model_dir)
                print(f"模型目录中的文件: {dir_files}")
            except Exception as e:
                print(f"无法列出模型目录中的文件: {str(e)}")
            
            # 尝试多种可能的类别文件名
            possible_files = [
                os.path.join(model_dir, f"{model_name}.names"),
                os.path.join(model_dir, f"{model_name}.txt"),
                os.path.join(model_dir, f"{model_name}.classes"),
                os.path.join(model_dir, f"{model_name}_names.txt"),
                os.path.join(model_dir, "coco.names"),
                os.path.join(model_dir, "classes.txt"),
                os.path.join(model_dir, "labels.txt"),
                os.path.join(model_dir, "class_names.txt")
            ]
            
            for file_path in possible_files:
                if os.path.exists(file_path):
                    print(f"找到类别文件: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            classes = [line.strip() for line in f.readlines() if line.strip()]
                            if classes:
                                print(f"从文件 {os.path.basename(file_path)} 中读取到 {len(classes)} 个类别名称")
                                return classes
                    except Exception as e:
                        print(f"读取类别文件失败: {str(e)}")
            
            # 从模型文件名中提取可能的类别
            model_basename = os.path.basename(self.model_path).lower()
            if 'qrcode' in model_basename or 'qr' in model_basename:
                print(f"根据模型文件名推断此为二维码检测模型: {model_basename}")
                return ['qrcode']
            elif 'face' in model_basename:
                print(f"根据模型文件名推断此为人脸检测模型: {model_basename}")
                return ['face']
            
            # 如果检测到只有一个输出类别（如模型输出形状中的类别维度为1），则推断为单类别检测
            if hasattr(self, 'output_shape') and len(self.output_shape) >= 2:
                if self.output_shape[1] == 5:  # 对于形状为(1, 5, 8400)的模型，通常是单类别检测
                    print("根据模型输出形状推断为单类别检测")
                    # 尝试从模型路径中推断类别名
                    path_parts = self.model_path.lower().split(os.sep)
                    for part in path_parts:
                        if part not in ['models', 'weights', 'onnx', 'pt', 'yolo', 'yolov8']:
                            part = part.replace('.onnx', '').replace('yolov8', '').replace('_', ' ').strip()
                            if part and not part.isdigit() and len(part) > 1:
                                print(f"从模型路径中推断类别名: {part}")
                                return [part]
                    
                    # 如果无法推断，则使用通用类别名
                    print("无法推断类别名，使用'object'作为通用类别名")
                    return ['object']
            
            # 如果没有找到类别信息，返回None
            print("未找到类别信息")
            return None
        except Exception as e:
            print(f"从模型提取类别名称失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_default_classes(self):
        """
        获取默认的COCO数据集类别名称
        
        Returns:
            COCO数据集的80个类别名称列表
        """
        print("使用默认COCO数据集类别名称")
        return ["person", "bicycle", "car", "motorcycle", "airplane", "bus", 
               "train", "truck", "boat", "traffic light", "fire hydrant", 
               "stop sign", "parking meter", "bench", "bird", "cat", "dog", 
               "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", 
               "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", 
               "skis", "snowboard", "sports ball", "kite", "baseball bat", 
               "baseball glove", "skateboard", "surfboard", "tennis racket", 
               "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", 
               "banana", "apple", "sandwich", "orange", "broccoli", "carrot", 
               "hot dog", "pizza", "donut", "cake", "chair", "couch", 
               "potted plant", "bed", "dining table", "toilet", "tv", "laptop", 
               "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", 
               "toaster", "sink", "refrigerator", "book", "clock", "vase", 
               "scissors", "teddy bear", "hair drier", "toothbrush"]
    
    def preprocess(self, image):
        """
        图像预处理
        
        Args:
            image: OpenCV格式的图像(BGR)
            
        Returns:
            预处理后的图像和缩放比例
        """
        # 保存原始图像尺寸
        self.img_height, self.img_width = image.shape[:2]
        
        # 计算缩放比例
        scale_w = self.input_width / self.img_width
        scale_h = self.input_height / self.img_height
        
        if scale_w < scale_h:
            # 按宽度缩放
            scaled_width = self.input_width
            scaled_height = int(self.img_height * scale_w)
        else:
            # 按高度缩放
            scaled_width = int(self.img_width * scale_h)
            scaled_height = self.input_height
            
        # 缩放图像
        image_resized = cv2.resize(image, (scaled_width, scaled_height))
        
        # 创建空白画布(输入尺寸)
        canvas = np.zeros((self.input_height, self.input_width, 3), dtype=np.uint8)
        
        # 将调整大小的图像粘贴到画布中央
        offset_x = (self.input_width - scaled_width) // 2
        offset_y = (self.input_height - scaled_height) // 2
        canvas[offset_y:offset_y+scaled_height, offset_x:offset_x+scaled_width] = image_resized
        
        # 存储偏移量和缩放系数，用于后处理
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = min(scale_w, scale_h)
        
        # 归一化处理 [0-255] -> [0-1]
        input_img = canvas.astype(np.float32) / 255.0
        
        # BGR -> RGB
        input_img = input_img[:, :, ::-1]
        
        # HWC -> NCHW (批次,通道,高,宽)
        input_img = np.transpose(input_img, (2, 0, 1))
        input_img = np.expand_dims(input_img, 0)
        
        return input_img
    
    def detect(self, image):
        """
        执行目标检测
        
        Args:
            image: 要检测的图像(BGR格式)
            
        Returns:
            检测到的边界框、置信度分数、类别ID和处理后的图像
        """
        # 预处理图像
        input_tensor = self.preprocess(image)
        
        # 执行推理
        start_time = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        inference_time = time.time() - start_time
        print(f"推理时间: {inference_time*1000:.2f} ms")
        
        # 后处理结果 (根据模型类型)
        if self.model_type == 'yolov8':
            boxes, scores, class_ids = self.postprocess_yolov8(outputs[0])
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        # 在图像上绘制检测结果
        result_image = self.draw_detections(image.copy(), boxes, scores, class_ids)
        
        return boxes, scores, class_ids, result_image
    
    def postprocess_yolov8(self, output):
        """
        YOLOv8模型的后处理
        
        Args:
            output: 模型的原始输出
            
        Returns:
            处理后的边界框、置信度分数和类别ID
        """
        try:
            # 检查输出形状，判断是哪种格式的YOLOv8输出
            output_shape = output.shape
            
            # 打印出输出形状，用于调试
            print(f"YOLOv8输出形状: {output_shape}")
            
            # 处理两种常见的YOLOv8 ONNX输出格式
            if len(output_shape) == 3 and output_shape[1] <= 5:  # 新版本格式 [batch, 5, 8400] - YOLOv8检测
                print("检测到YOLOv8-Detect格式输出")
                # 获取输出并转置 [batch, 5, 8400] -> [batch, 8400, 5]
                output = np.transpose(output, (0, 2, 1))
                
                # 获取第一个批次的预测结果
                predictions = output[0]  # [8400, 5]
                
                # 获取边界框坐标和置信度
                boxes = predictions[:, 0:4]  # [8400, 4] - 边界框坐标
                confidences = predictions[:, 4]  # [8400] - 置信度分数
                
                # 根据置信度阈值筛选检测结果
                mask = confidences > self.conf_threshold
                print(f"检测到 {np.sum(mask)} 个目标(置信度 > {self.conf_threshold})")
                
                # 应用mask筛选
                boxes = boxes[mask]  # 重要：这里要更新boxes变量，而不是创建新变量
                scores = confidences[mask].astype(float)  # 确保是浮点数
                
                # 在这种情况下，所有检测对象都是同一类别(0)
                class_ids = np.zeros(len(scores), dtype=np.int32)
                
                if len(scores) == 0:
                    print("没有检测到足够置信度的目标")
                    return [], [], []
                
            elif len(output_shape) == 3:  # 新版本格式 [batch, 85, 8400] - YOLOv8分类
                print("检测到YOLOv8-Classify/Segment格式输出")
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
                    print("没有检测到足够置信度的目标")
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
                    print("没有检测到足够类别置信度的目标")
                    return [], [], []
                
            else:  # 传统格式 [batch, num_detections, 4+1+num_classes]
                print("检测到传统YOLOv8格式输出")
                # 提取置信度分数(第5列)
                scores = output[:, 4]
                
                # 根据置信度阈值筛选检测结果
                mask = scores >= self.conf_threshold
                filtered_output = output[mask]
                filtered_scores = scores[mask]
                
                if len(filtered_scores) == 0:
                    print("没有检测到足够置信度的目标")
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
                    print("没有检测到足够类别置信度的目标")
                    return [], [], []
            
            # 转换坐标(中心点xy,宽高wh -> 左上角xyxy)
            boxes = self.xywh2xyxy(boxes)
            
            # 从模型输入尺寸缩放回原始图像尺寸
            boxes = self.rescale_boxes(boxes)
            
            # 确保数据类型正确
            boxes_list = boxes.tolist()
            scores_list = scores.tolist()  # 确保是一维列表
            
            print(f"执行NMS: boxes类型: {type(boxes_list)}, scores类型: {type(scores_list)}")
            print(f"boxes长度: {len(boxes_list)}, scores长度: {len(scores_list)}")
            
            if len(boxes_list) > 0 and len(scores_list) > 0:
                # 确保boxes和scores长度相同
                if len(boxes_list) != len(scores_list):
                    print(f"警告: boxes长度({len(boxes_list)})和scores长度({len(scores_list)})不一致，截断到较小长度")
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
                    
                    print(f"NMS后保留 {len(final_boxes)} 个目标")
                    return final_boxes, final_scores, final_class_ids
                else:
                    print("NMS后没有保留的目标")
            
            # 如果没有结果或NMS后没有留下的框
            return [], [], []
        
        except Exception as e:
            # 详细记录错误信息，便于调试
            print(f"YOLOv8后处理错误: {str(e)}")
            print(f"输出形状: {output.shape}")
            import traceback
            traceback.print_exc()
            return [], [], []
    
    def xywh2xyxy(self, boxes):
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
    
    def rescale_boxes(self, boxes):
        """
        将边界框从模型输入尺寸转换回原始图像尺寸
        
        Args:
            boxes: 模型输入尺寸的边界框坐标
            
        Returns:
            原始图像尺寸的边界框坐标
        """
        # 减去偏移量
        boxes[:, [0, 2]] -= self.offset_x
        boxes[:, [1, 3]] -= self.offset_y
        
        # 缩放到原始图像尺寸
        boxes[:, :4] /= self.scale
        
        # 确保边界框在图像范围内
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, self.img_width - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, self.img_height - 1)
        
        return boxes
    
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
        for i, box in enumerate(boxes):
            # 提取坐标和置信度
            x1, y1, x2, y2 = map(int, box)
            score = scores[i]
            class_id = class_ids[i]
            class_name = self.get_class_name(class_id)
            
            # 生成不同类别的颜色
            color = self.generate_color(class_id)
            
            # 绘制边界框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # 准备标签文本
            label = f"{class_name}: {score:.2f}"
            
            # 获取文本大小
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # 绘制标签背景
            cv2.rectangle(image, (x1, y1 - text_height - 5), (x1 + text_width, y1), color, -1)
            
            # 绘制标签文本
            cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        return image
    
    def get_class_name(self, class_id):
        """
        获取类别名称
        
        Args:
            class_id: 类别ID
            
        Returns:
            对应的类别名称
        """
        if 0 <= class_id < len(self.classes):
            return self.classes[class_id]
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
