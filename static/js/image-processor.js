/**
 * image-processor.js - 图像处理模块
 * 负责图像上传、摄像头捕获等图像相关功能
 */

// 图像处理状态
const imageState = {
    uploadedImagePath: null,
    capturedImage: null,
    webcamActive: false,
    webcamStream: null
};

/**
 * 初始化图像处理模块
 */
function initImageProcessor() {
    // 绑定图像来源切换事件
    const uploadImage = document.getElementById('uploadImage');
    const webcamImage = document.getElementById('webcamImage');
    
    if (uploadImage && webcamImage) {
        uploadImage.addEventListener('change', toggleImageSource);
        webcamImage.addEventListener('change', toggleImageSource);
    }
    
    // 绑定图像上传事件
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', handleImageUpload);
    }
    
    // 绑定摄像头捕获事件
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.addEventListener('click', captureWebcamImage);
    }
    
    // 绑定摄像头切换事件
    const startStopBtn = document.getElementById('startStopBtn');
    if (startStopBtn) {
        startStopBtn.addEventListener('click', toggleWebcam);
    }
    
    // 初始切换图像来源
    toggleImageSource();
}

/**
 * 切换图像来源
 */
function toggleImageSource() {
    const imageSource = document.querySelector('input[name="imageSource"]:checked');
    if (!imageSource) return;
    
    const source = imageSource.value;
    const uploadImageSection = document.getElementById('uploadImageSection');
    const webcamSection = document.getElementById('webcamSection');
    
    if (source === 'upload') {
        if (uploadImageSection) uploadImageSection.style.display = 'block';
        if (webcamSection) webcamSection.style.display = 'none';
        
        // 停止摄像头
        stopWebcam();
    } else if (source === 'webcam') {
        if (uploadImageSection) uploadImageSection.style.display = 'none';
        if (webcamSection) webcamSection.style.display = 'block';
        
        // 启动摄像头
        startWebcam();
    }
}

/**
 * 处理图像上传
 * @param {Event} event - 上传事件
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
            imageState.uploadedImagePath = data.filepath;
            
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
            
            // 触发自定义事件
            document.dispatchEvent(new CustomEvent('image:uploaded', { 
                detail: { 
                    path: data.filepath,
                    filename: data.filename
                } 
            }));
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
    if (imageState.webcamActive) return;
    
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
            imageState.webcamStream = stream;
            imageState.webcamActive = true;
            
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
    if (!imageState.webcamActive) return;
    
    const webcamVideo = document.getElementById('webcam');
    
    // 停止所有视频轨道
    if (imageState.webcamStream) {
        const tracks = imageState.webcamStream.getTracks();
        tracks.forEach(track => track.stop());
        imageState.webcamStream = null;
    }
    
    // 清除视频源
    if (webcamVideo) {
        webcamVideo.srcObject = null;
    }
    
    imageState.webcamActive = false;
    
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
    if (imageState.webcamActive) {
        stopWebcam();
    } else {
        startWebcam();
    }
}

/**
 * 从摄像头捕获图像
 */
function captureWebcamImage() {
    if (!imageState.webcamActive) {
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
                imageState.capturedImage = data.filepath;
                
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
                
                // 触发自定义事件
                document.dispatchEvent(new CustomEvent('image:captured', { 
                    detail: { 
                        path: data.filepath,
                        filename: data.filename
                    } 
                }));
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
 * 获取当前图像路径
 * @returns {string|null} 当前图像路径
 */
function getCurrentImagePath() {
    const imageSource = document.querySelector('input[name="imageSource"]:checked');
    if (!imageSource) return null;
    
    if (imageSource.value === 'upload') {
        return imageState.uploadedImagePath;
    } else if (imageSource.value === 'webcam') {
        return imageState.capturedImage;
    }
    
    return null;
}

/**
 * 检查是否有可用图像
 * @returns {boolean} 是否有可用图像
 */
function hasValidImage() {
    const imageSource = document.querySelector('input[name="imageSource"]:checked');
    if (!imageSource) return false;
    
    if (imageSource.value === 'upload') {
        return imageState.uploadedImagePath !== null;
    } else if (imageSource.value === 'webcam') {
        return imageState.capturedImage !== null;
    }
    
    return false;
}

// 导出模块API
window.ImageProcessor = {
    init: initImageProcessor,
    getCurrentImagePath: getCurrentImagePath,
    hasValidImage: hasValidImage,
    startWebcam: startWebcam,
    stopWebcam: stopWebcam,
    captureImage: captureWebcamImage
};
