# YOLO目标检测系统

一个基于Flask和YOLO模型的简易目标检测Web应用，支持本地部署。

## 项目概述

本项目是一个简单的YOLO检测应用，具有以下特点：

- 基于Flask框架的Web应用
- 使用Bootstrap进行前端美化
- 采用模块化设计，降低耦合度
- 使用WebSocket实现前后端实时通信
- 支持ONNX格式的YOLO模型进行推理
- 支持图片上传和摄像头采集两种输入方式
- 可使用PyInstaller打包成独立可执行程序，便于部署

## 功能特性

### 输入
1. 模型选择：用户可以选择本地ONNX格式的YOLO模型文件位置
2. 图像输入：支持用户上传图片或使用本地摄像头采集图像
   - 后期可扩展支持海康摄像头SDK

### 输出
1. 检测结果：使用ONNXRuntime进行推理，返回识别结果的坐标信息
2. 可视化结果：在图片上标注检测结果并显示

## 安装说明

### 环境要求
- Python 3.8+ (推荐3.10)
- Windows/Linux/macOS操作系统

### 安装步骤

1. 克隆或下载本项目到本地

2. 创建并激活虚拟环境（Windows系统）：
```
python -m venv venv
.\venv\Scripts\activate
```

3. 安装依赖包：
```
pip install -r requirements.txt
```

## 使用方法

1. 启动应用：
```
python app.py
```

2. 打开浏览器，访问：
```
http://localhost:5000
```

3. 使用流程：
   - 首先加载ONNX模型（输入模型的绝对路径）
   - 选择图像来源（上传图片或使用摄像头）
   - 点击"执行检测"按钮
   - 查看检测结果和标注后的图像

## 项目结构

```
FlaskYolo/
│
├── app/                    # 应用代码
│   ├── __init__.py         # 应用工厂和配置
│   ├── routes.py           # 路由和请求处理
│   └── yolo_detector.py    # YOLO检测器实现
│
├── static/                 # 静态资源
│   ├── css/                # CSS样式
│   ├── js/                 # JavaScript代码
│   ├── uploads/            # 上传的图片
│   └── results/            # 检测结果图片
│
├── templates/              # HTML模板
│   ├── base.html           # 基础模板
│   └── index.html          # 主页模板
│
├── models/                 # 存放ONNX模型文件
│
├── app.py                  # 应用入口
├── README.md               # 项目说明
└── requirements.txt        # 依赖列表
```

## 打包说明

使用PyInstaller打包成独立可执行程序：

```
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
```

## 注意事项

1. 模型文件需自行下载YOLO的ONNX格式模型（如YOLOv8n.onnx）
2. 默认支持80类COCO数据集的对象检测
3. 为获得更好的检测效果，建议使用清晰的图像

## 未来计划

1. 添加更多YOLO模型版本支持
2. 增加海康摄像头SDK支持
3. 增加用户自定义类别标签功能
4. 优化检测性能和用户界面