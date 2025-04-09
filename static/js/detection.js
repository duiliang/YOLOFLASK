/**
 * detection.js - 检测功能的JavaScript实现
 * 处理WebSocket连接、图像上传和模型推理
 */

// 初始化状态
const state = {
    socket: null,
    uploadedImagePath: null,
    capturedImage: null,
    modelLoaded: false,
    webcamActive: false,
    webcamStream: null,
    currentModelInfo: null
};

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    const detectBtn = document.getElementById('detectBtn');
    const uploadImage = document.getElementById('uploadImage');
    const webcamImage = document.getElementById('webcamImage');
    const imageUpload = document.getElementById('imageUpload');
    const uploadImageSection = document.getElementById('uploadImageSection');
    const webcamSection = document.getElementById('webcamSection');
    const captureBtn = document.getElementById('captureBtn');
    const startStopBtn = document.getElementById('startStopBtn');
    const webcamVideo = document.getElementById('webcam');
    const currentModelInfo = document.getElementById('currentModelInfo');
    
    // 初始化Socket.IO连接
    initializeSocket();
    
    // 添加事件监听器    
    if (detectBtn) {
        detectBtn.addEventListener('click', handleDetection);
    }
    
    if (uploadImage && webcamImage) {
        uploadImage.addEventListener('change', toggleImageSource);
        webcamImage.addEventListener('change', toggleImageSource);
    }
    
    if (imageUpload) {
        imageUpload.addEventListener('change', handleImageUpload);
    }
    
    if (captureBtn) {
        captureBtn.addEventListener('click', captureWebcamImage);
    }
    
    if (startStopBtn) {
        startStopBtn.addEventListener('click', toggleWebcam);
    }
    
    // 初始状态设置
    toggleImageSource();
    
    // 加载配置
    loadConfig();
});

/**
 * 加载应用配置
 */
function loadConfig() {
    fetch('/config.json?t=' + Date.now())
        .then(response => response.json())
        .then(config => {
            console.log('配置加载成功:', config);
            
            // 检查是否有当前模型
            if (config.model && config.model.current_model) {
                const currentModelName = config.model.current_model;
                console.log('当前模型名称:', currentModelName);
                
                // 在模型列表中查找当前模型
                if (config.models && config.models.length > 0) {
                    const currentModel = config.models.find(model => model.name === currentModelName);
                    if (currentModel) {
                        console.log('找到当前模型:', currentModel);
                        updateCurrentModelDisplay(currentModel);
                    }
                }
            }
        })
        .catch(error => {
            console.error('加载配置失败:', error);
        });
}

/**
 * 更新当前模型显示
 */
function updateCurrentModelDisplay(model) {
    const currentModelInfo = document.getElementById('currentModelInfo');
    if (currentModelInfo) {
        currentModelInfo.innerHTML = `<strong>${model.name}</strong> (${model.type}) - ${model.description || ''}`;
        state.currentModelInfo = model;
        state.modelLoaded = true;
        
        // 启用检测按钮
        const detectBtn = document.getElementById('detectBtn');
        if (detectBtn) {
            detectBtn.removeAttribute('disabled');
        }
    }
}

/**
 * 初始化Socket.IO连接
 */
function initializeSocket() {
    // 创建Socket.IO连接
    const socket = io();
    
    // 连接成功事件
    socket.on('connect', () => {
        console.log('WebSocket连接已建立');
        showNotification('已连接到服务器', 'success');
        state.socket = socket;
    });
    
    // 连接断开事件
    socket.on('disconnect', () => {
        console.log('WebSocket连接已断开');
        showNotification('与服务器的连接已断开，请刷新页面', 'warning');
        state.socket = null;
    });
    
    // 模型加载成功事件
    socket.on('model_loaded', (data) => {
        console.log('模型加载成功:', data);
        if (data.model) {
            updateCurrentModelDisplay(data.model);
            showNotification(data.message || '模型加载成功！现在可以进行检测了', 'success');
        }
    });
    
    // 检测结果事件
    socket.on('detection_results', (data) => {
        console.log('检测结果:', data);
        showLoading('#detectBtn', false);
        
        if (data.success) {
            displayResults(data.results, data.result_image);
            showNotification('检测完成！', 'success');
            
            // 更新状态消息
            const statusMessages = document.getElementById('statusMessages');
            if (statusMessages) {
                statusMessages.textContent = `检测完成，共找到 ${data.results.length} 个目标`;
                statusMessages.className = 'alert alert-success';
            }
        } else {
            showNotification('检测失败，请重试', 'danger');
        }
    });
    
    // 检测错误事件
    socket.on('detection_error', (data) => {
        console.error('检测错误:', data.error);
        showLoading('#detectBtn', false);
        showNotification(`检测错误: ${data.error}`, 'danger');
        
        // 更新状态消息
        const statusMessages = document.getElementById('statusMessages');
        if (statusMessages) {
            statusMessages.textContent = `检测失败: ${data.error}`;
            statusMessages.className = 'alert alert-danger';
        }
    });
}

/**
 * 处理检测请求
 */
function handleDetection() {
    if (!state.socket) {
        showNotification('WebSocket连接未建立，请刷新页面', 'warning');
        return;
    }
    
    if (!state.modelLoaded) {
        showNotification('请先加载模型', 'warning');
        return;
    }
    
    const imageSource = document.querySelector('input[name="imageSource"]:checked').value;
    
    if (imageSource === 'upload' && !state.uploadedImagePath) {
        showNotification('请先上传图像', 'warning');
        return;
    }
    
    if (imageSource === 'webcam' && !state.capturedImage) {
        showNotification('请先捕获图像', 'warning');
        return;
    }
    
    // 设置加载状态
    showLoading('#detectBtn', true);
    
    // 更新状态消息
    const statusMessages = document.getElementById('statusMessages');
    if (statusMessages) {
        statusMessages.textContent = '正在执行检测...';
        statusMessages.className = 'alert alert-info';
    }
    
    // 准备检测请求数据
    const detectData = {
        image_path: imageSource === 'upload' ? state.uploadedImagePath : state.capturedImage
    };
    
    // 发送检测请求
    state.socket.emit('detect', detectData);
}

/**
 * 切换图像来源
 */
function toggleImageSource() {
    const imageSource = document.querySelector('input[name="imageSource"]:checked').value;
    const uploadImageSection = document.getElementById('uploadImageSection');
    const webcamSection = document.getElementById('webcamSection');
    
    if (imageSource === 'upload') {
        if (uploadImageSection) uploadImageSection.style.display = 'block';
        if (webcamSection) webcamSection.style.display = 'none';
        
        // 停止摄像头
        stopWebcam();
    } else if (imageSource === 'webcam') {
        if (uploadImageSection) uploadImageSection.style.display = 'none';
        if (webcamSection) webcamSection.style.display = 'block';
        
        // 启动摄像头
        startWebcam();
    }
}

/**
 * 处理图像上传
 */
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 检查文件类型
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        showNotification('请上传JPEG或PNG格式的图像', 'warning');
        return;
    }
    
    // 检查文件大小
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        showNotification('图像文件过大，请上传小于16MB的文件', 'warning');
        return;
    }
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    
    // 更新状态消息
    const statusMessages = document.getElementById('statusMessages');
    if (statusMessages) {
        statusMessages.textContent = '正在上传图像...';
        statusMessages.className = 'alert alert-info';
    }
    
    // 发送上传请求
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            state.uploadedImagePath = data.filepath;
            
            showNotification('图像上传成功！', 'success');
            
            // 更新状态消息
            if (statusMessages) {
                statusMessages.textContent = `图像已上传，准备进行检测`;
                statusMessages.className = 'alert alert-success';
            }
            
            // 预览上传的图像
            const resultImage = document.getElementById('resultImage');
            if (resultImage) {
                resultImage.src = `/static/uploads/${data.filename}`;
                resultImage.style.display = 'block';
            }
            
            // 清除检测结果
            clearDetectionResults();
        } else {
            showNotification(`图像上传失败: ${data.error}`, 'danger');
            
            if (statusMessages) {
                statusMessages.textContent = `图像上传失败: ${data.error}`;
                statusMessages.className = 'alert alert-danger';
            }
        }
    })
    .catch(error => {
        console.error('图像上传错误:', error);
        showNotification('图像上传过程中出现错误，请重试', 'danger');
        
        if (statusMessages) {
            statusMessages.textContent = '图像上传过程中出现错误，请重试';
            statusMessages.className = 'alert alert-danger';
        }
    });
}

/**
 * 启动摄像头
 */
function startWebcam() {
    if (state.webcamActive) return;
    
    const webcamVideo = document.getElementById('webcam');
    if (!webcamVideo) return;
    
    // 检查浏览器是否支持getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showNotification('您的浏览器不支持摄像头功能', 'danger');
        return;
    }
    
    // 获取摄像头视频流
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            state.webcamStream = stream;
            state.webcamActive = true;
            
            // 绑定视频流到video元素
            webcamVideo.srcObject = stream;
            
            // 更新切换按钮文本
            const startStopBtn = document.getElementById('startStopBtn');
            if (startStopBtn) {
                startStopBtn.textContent = '停止';
            }
        })
        .catch(error => {
            console.error('访问摄像头失败:', error);
            showNotification('无法访问摄像头，请检查权限设置', 'danger');
        });
}

/**
 * 停止摄像头
 */
function stopWebcam() {
    if (!state.webcamActive) return;
    
    const webcamVideo = document.getElementById('webcam');
    
    // 停止所有视频轨道
    if (state.webcamStream) {
        const tracks = state.webcamStream.getTracks();
        tracks.forEach(track => track.stop());
        state.webcamStream = null;
    }
    
    // 清除视频源
    if (webcamVideo) {
        webcamVideo.srcObject = null;
    }
    
    state.webcamActive = false;
    
    // 更新切换按钮文本
    const startStopBtn = document.getElementById('startStopBtn');
    if (startStopBtn) {
        startStopBtn.textContent = '启动';
    }
}

/**
 * 切换摄像头状态
 */
function toggleWebcam() {
    if (state.webcamActive) {
        stopWebcam();
    } else {
        startWebcam();
    }
}

/**
 * 从摄像头捕获图像
 */
function captureWebcamImage() {
    if (!state.webcamActive) {
        showNotification('摄像头未启动', 'warning');
        return;
    }
    
    const webcamVideo = document.getElementById('webcam');
    if (!webcamVideo) return;
    
    // 创建canvas元素
    const canvas = document.createElement('canvas');
    canvas.width = webcamVideo.videoWidth;
    canvas.height = webcamVideo.videoHeight;
    
    // 在canvas上绘制当前视频帧
    const ctx = canvas.getContext('2d');
    ctx.drawImage(webcamVideo, 0, 0, canvas.width, canvas.height);
    
    // 更新状态消息
    const statusMessages = document.getElementById('statusMessages');
    if (statusMessages) {
        statusMessages.textContent = '正在处理捕获的图像...';
        statusMessages.className = 'alert alert-info';
    }
    
    // 将canvas内容转换为Blob
    canvas.toBlob(blob => {
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', blob, `webcam_${Date.now()}.jpg`);
        
        // 发送上传请求
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                state.capturedImage = data.filepath;
                
                showNotification('图像捕获成功！', 'success');
                
                // 更新状态消息
                if (statusMessages) {
                    statusMessages.textContent = `图像已捕获，准备进行检测`;
                    statusMessages.className = 'alert alert-success';
                }
                
                // 预览捕获的图像
                const resultImage = document.getElementById('resultImage');
                if (resultImage) {
                    resultImage.src = `/static/uploads/${data.filename}`;
                    resultImage.style.display = 'block';
                }
                
                // 清除检测结果
                clearDetectionResults();
            } else {
                showNotification(`图像处理失败: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('图像处理错误:', error);
            showNotification('图像处理过程中出现错误，请重试', 'danger');
        });
    }, 'image/jpeg', 0.9);
}

/**
 * 显示检测结果
 */
function displayResults(results, resultImageUrl) {
    // 显示结果图像
    const resultImage = document.getElementById('resultImage');
    if (resultImage) {
        resultImage.src = resultImageUrl;
        resultImage.style.display = 'block';
    }
    
    // 显示结果列表
    const resultsList = document.getElementById('resultsList');
    const detectionResults = document.getElementById('detectionResults');
    
    if (resultsList && detectionResults) {
        // 清空现有结果
        resultsList.innerHTML = '';
        
        if (results.length === 0) {
            // 没有检测到物体
            const noResultItem = document.createElement('li');
            noResultItem.className = 'list-group-item';
            noResultItem.textContent = '未检测到任何物体';
            resultsList.appendChild(noResultItem);
        } else {
            // 添加检测结果
            results.forEach((item, index) => {
                const resultItem = document.createElement('li');
                resultItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                
                const confidencePercent = (item.score * 100).toFixed(2);
                resultItem.innerHTML = `
                    <span>${index + 1}. ${item.class_name}</span>
                    <span class="badge bg-primary rounded-pill">${confidencePercent}%</span>
                `;
                
                resultsList.appendChild(resultItem);
            });
        }
        
        // 显示结果区域
        detectionResults.style.display = 'block';
    }
}

/**
 * 清除检测结果
 */
function clearDetectionResults() {
    const resultsList = document.getElementById('resultsList');
    const detectionResults = document.getElementById('detectionResults');
    
    if (resultsList) {
        resultsList.innerHTML = '';
    }
    
    if (detectionResults) {
        detectionResults.style.display = 'none';
    }
}

/**
 * 显示加载状态
 */
function showLoading(selector, isLoading) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    if (isLoading) {
        element.setAttribute('disabled', 'disabled');
        element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
    } else {
        element.removeAttribute('disabled');
        element.innerHTML = element.getAttribute('data-original-text') || (selector === '#detectBtn' ? '执行检测' : '加载模型');
    }
}

/**
 * 显示通知消息
 */
function showNotification(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // 创建toast容器（如果不存在）
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastEl = document.createElement('div');
    const toastId = `toast-${Date.now()}`;
    toastEl.className = `toast show bg-${type} text-white`;
    toastEl.setAttribute('id', toastId);
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">系统消息</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // 添加到容器
    toastContainer.appendChild(toastEl);
    
    // 3秒后自动消失
    setTimeout(() => {
        const bsToast = new bootstrap.Toast(document.getElementById(toastId));
        if (bsToast) {
            bsToast.hide();
        } else {
            // 如果bootstrap实例不可用，手动移除元素
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                toastElement.remove();
            }
        }
    }, 3000);
}
