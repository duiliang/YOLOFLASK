"""
类别管理模块
负责从模型中提取类别名称，或提供默认类别
"""
import os
import json

class ClassManager:
    """类别管理器类"""
    
    def __init__(self, model_path, session=None):
        """
        初始化类别管理器
        
        Args:
            model_path: 模型文件路径
            session: ONNX会话对象
        """
        self.model_path = model_path
        self.session = session
    
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
    
    def extract_classes_from_model(self):
        """
        尝试从ONNX模型中提取类别名称
        
        Returns:
            如果成功，返回类别名称列表；如果失败，返回None
        """
        try:
            print("正在尝试从模型中提取类别名称...")
            
            # 确保session已设置
            if not self.session:
                print("无法提取类别：会话对象未设置")
                return None
            
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
                                print(f"尝试解析类别数据：{json.loads(class_data)}")
                                class_names = json.loads(class_data)
                                print(f"成功解析JSON数据：{type(class_names)}")
                                
                                # 根据数据类型进行处理
                                if isinstance(class_names, dict):
                                    print(f"处理字典类型的类别数据：{class_names}")
                                    try:
                                        # 将字典转换为列表，确保索引匹配
                                        keys = [int(idx) if isinstance(idx, str) else idx for idx in class_names.keys()]
                                        if not keys:
                                            print("警告：类别字典为空")
                                            return ['unknown']
                                            
                                        # 特殊处理：如果只有一个类别，直接返回单元素列表
                                        if len(keys) == 1:
                                            class_name = list(class_names.values())[0]
                                            print(f"检测到单类别模型，类别名: {class_name}")
                                            return [class_name]
                                            
                                        max_idx = max(keys)
                                        classes = [''] * (max_idx + 1)
                                        for idx, name in class_names.items():
                                            idx_int = int(idx) if isinstance(idx, str) else idx
                                            classes[idx_int] = name
                                        print(f"从模型中提取到 {len(classes)} 个类别名称（字典格式）")
                                        return classes
                                    except Exception as dict_e:
                                        print(f"处理字典格式类别数据时出错: {str(dict_e)}")
                                        # 尝试直接将字典值作为类别列表
                                        if class_names:
                                            classes = list(class_names.values())
                                            print(f"退化处理：直接使用字典值作为类别名: {classes}")
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
                                    classes = [c.strip() for c in class_data.split('\n') if c.strip()]
                                    print(f"从模型中提取到 {len(classes)} 个类别名称（换行符分隔格式）")
                                    return classes
                                else:
                                    # 如果没有分隔符，尝试直接解析
                                    classes = [c.strip() for c in class_data.split(',') if c.strip()]
                                    print(f"从模型中提取到 {len(classes)} 个类别名称（逗号分隔格式）")
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
                os.path.join(model_dir, 'classes.txt'),
                os.path.join(model_dir, 'labels.txt'),
                os.path.join(model_dir, f"{model_name}_classes.txt"),
                os.path.join(model_dir, f"{model_name}.names"),
                os.path.join(model_dir, f"{model_name}_names.txt"),
                os.path.join(model_dir, 'coco.names'),
                os.path.join(model_dir, 'coco_names.txt')
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
            if 'qr' in model_basename or 'qrcode' in model_basename:
                print(f"根据模型文件名推断此为二维码检测模型: {model_basename}")
                return ['qrcode']
            elif 'face' in model_basename:
                print(f"根据模型文件名推断此为人脸检测模型: {model_basename}")
                return ['face']
            
            # 如果检测到只有一个输出类别（如模型输出形状中的类别维度为1），则推断为单类别检测
            if hasattr(self, 'output_shape') and self.output_shape:
                if self.output_shape[1] == 5:  # 对于形状为(1, 5, 8400)的模型，通常是单类别检测
                    print("根据模型输出形状推断为单类别检测")
                    # 尝试从模型路径中推断类别名
                    path_parts = self.model_path.lower().split(os.sep)
                    for part in path_parts:
                        if part.endswith('.onnx'):
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
