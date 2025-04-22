# YOLO目标检测系统

一个基于Flask和YOLO模型的简易目标检测Web应用，支持本地部署，采用了模块化设计。

## 项目概述

本项目是一个简单而强大的YOLO检测应用，具有以下特点：

- 基于Flask框架的Web应用
- 使用Bootstrap进行前端美化
- 采用模块化设计，降低耦合度
- 使用WebSocket实现前后端实时通信
- 支持ONNX格式的YOLO模型进行推理
- 支持图片上传和摄像头采集两种输入方式
- 标准化日志系统，便于排查问题
- 可使用PyInstaller打包成独立可执行程序，便于部署

## 功能特性

### 输入
1. 模型选择：用户可以选择本地ONNX格式的YOLO模型文件位置
2. 图像输入：支持用户上传图片或使用本地摄像头采集图像
   - 后期可扩展支持海康摄像头SDK

### 输出
1. 检测结果：使用ONNXRuntime进行推理，返回识别结果的坐标信息
2. 可视化结果：在图片上标注检测结果并显示
3. 日志记录：记录检测过程中的关键信息，便于问题排查

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
   - 首先在"模型管理"页面添加或选择ONNX模型
   - 选择图像来源（上传图片或使用摄像头）
   - 点击"执行检测"按钮
   - 查看检测结果和标注后的图像

## 项目结构

```
FlaskYolo/
│
├── app/                      # 应用代码
│   ├── __init__.py           # 应用工厂和配置
│   ├── routes.py             # 路由和请求处理
│   ├── utils.py              # 通用工具函数
│   ├── yolo_detector.py      # YOLO检测器代理类
│   └── yolomodel/            # YOLO模型相关组件
│       ├── __init__.py       # 包初始化
│       ├── detector.py       # 主检测器类
│       ├── preprocessor.py   # 图像预处理模块
│       ├── postprocessor.py  # 结果后处理模块
│       ├── class_utils.py    # 类别管理工具
│       ├── visualizer.py     # 结果可视化模块
│       ├── config.py         # 配置加载模块
│       └── logger.py         # 日志管理模块
│
├── static/                   # 静态资源
│   ├── css/                  # CSS样式
│   ├── js/                   # JavaScript代码
│   ├── uploads/              # 上传的图片
│   └── results/              # 检测结果图片
│
├── templates/                # HTML模板
│   ├── base.html             # 基础模板
│   ├── index.html            # 主页模板
│   └── model-management.html # 模型管理页面
│
├── config.json               # 全局配置文件
├── app.py                    # 应用入口
├── README.md                 # 项目说明
└── requirements.txt          # 依赖列表
```

## 系统设计

本项目采用了模块化设计，将原本单一的YOLO检测器类拆分为多个专注于不同功能的模块：

1. **detector.py**: 主检测器类，协调各个组件工作
2. **preprocessor.py**: 负责图像预处理，如调整大小、归一化等
3. **postprocessor.py**: 处理模型输出，包括坐标转换、置信度筛选、NMS等
4. **class_utils.py**: 管理类别名称，从模型中提取或使用默认类别
5. **visualizer.py**: 在图像上绘制检测结果
6. **config.py**: 加载和管理配置信息
7. **logger.py**: 统一的日志记录系统

这种模块化设计带来的好处包括：
- 代码更加清晰和易于维护
- 各个组件可以独立测试和更新
- 便于扩展新功能和支持新的模型类型

## 打包说明

本项目提供了专门的打包脚本，可将应用打包成完全离线运行的独立可执行程序：

```bash
# 使用内置打包脚本（推荐）
python build_exe.py

# 或手动使用PyInstaller
pyinstaller --name="YOLO目标检测系统" ^
            --onefile ^
            --console ^
            --icon=static/img/favicon.ico ^
            --add-data "templates;templates" ^
            --add-data "static;static" ^
            --add-data "config.json;." ^
            --hidden-import=eventlet.hubs.epolls ^
            --hidden-import=eventlet.hubs.kqueue ^
            --hidden-import=eventlet.hubs.selects ^
            --hidden-import=engineio.async_drivers.threading ^
            --hidden-import=gevent ^
            --hidden-import=gevent.ssl ^
            --hidden-import=gevent.builtins ^
            --hidden-import=socketio ^
            --hidden-import=engineio ^
            launcher.py
```

### 离线打包特性

本系统支持完全离线部署和运行，主要特性包括：

1. **所有依赖本地化**：
   - Bootstrap、jQuery、Popper.js等前端库已本地化
   - Socket.IO客户端库已本地化
   - 无需互联网连接即可运行

2. **资源目录结构**：
   打包后的文件结构为：
   ```
   dist/
   ├── YOLO目标检测系统.exe       # 主程序
   ├── config.json               # 主配置文件(根目录)
   ├── README.txt                # 使用说明
   └── resources/                # 资源目录
       ├── config/               # 配置文件备份
       ├── models/               # 模型文件
       ├── logs/                 # 日志文件
       └── static/               # 静态资源
           ├── uploads/          # 上传图片
           └── results/          # 检测结果
   ```

3. **自动资源管理**：
   - 程序会自动创建必要的资源目录
   - 上传的图片和处理结果保存在外部资源目录
   - 配置文件支持外部修改，重启程序后生效

### 部署与使用说明

1. 将整个`dist`文件夹复制到目标计算机上
2. 双击`YOLO目标检测系统.exe`启动应用
3. 在浏览器中访问`http://localhost:5000`使用系统
4. 模型文件位于`resources/models`目录，可以直接更换
5. 系统日志保存在`resources/logs`目录，便于排查问题

### 打包常见问题

1. **WebSocket连接失败**：
   - 确保打包时包含了所有必要的隐藏导入
   - 检查防火墙设置是否阻止了WebSocket连接

2. **静态资源加载失败**：
   - 确保`static`目录下的资源已正确打包
   - 检查资源文件路径是否正确

3. **配置文件加载失败**：
   - 确保`config.json`文件位于主程序同级目录
   - 检查配置文件格式是否正确

## 配置文件说明

`config.json`文件包含应用的全局配置，结构如下：

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": false
    },
    "model": {
        "conf_threshold": 0.25,
        "iou_threshold": 0.45,
        "current_model": "模型名称"
    },
    "models": [
        {
            "name": "模型名称",
            "path": "模型路径",
            "type": "yolov8",
            "description": "模型描述"
        }
    ],
    "upload": {
        "allowed_extensions": ["jpg", "jpeg", "png", "bmp"],
        "max_size_mb": 10
    }
}
```

## 常见问题解决

1. **模型加载失败**：
   - 检查模型路径是否正确
   - 确认模型格式为ONNX
   - 尝试使用绝对路径

2. **运行缓慢**：
   - 考虑使用更小的模型
   - 检查图像分辨率，过大的图像会影响速度
   - 在GPU环境中运行可提升性能

3. **依赖安装问题**：
   - 确保使用的是兼容版本的Python
   - 尝试按照`requirements.txt`中的精确版本安装
   - 如果安装OpenCV有问题，可尝试`pip install opencv-python-headless`

## 注意事项

1. 模型文件需自行下载YOLO的ONNX格式模型（如YOLOv8n.onnx）
2. 默认支持80类COCO数据集的对象检测
3. 为获得更好的检测效果，建议使用清晰的图像
4. 打包发布时，确保配置文件中使用绝对路径或可自动解析的相对路径

## 未来计划

1. 添加更多YOLO模型版本支持
2. 增加海康摄像头SDK支持
3. 增加用户自定义类别标签功能
4. 优化检测性能和用户界面
5. 添加批量处理功能