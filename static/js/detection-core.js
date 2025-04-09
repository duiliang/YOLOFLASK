/**
 * detection-core.js - 检测核心功能
 * 负责与服务器通信，进行实际的目标检测
 */

// Socket.IO连接实例
let socket = null;

// 检测相关状态
const detectionState = {
    modelLoaded: false,
    currentModelInfo: null
};

/**
 * 初始化Socket.IO连接
 */
function initSocketConnection() {
    // 创建Socket.IO连接
    socket = io();
    
    // 连接成功事件
    socket.on('connect', () => {
        console.log('WebSocket连接已建立');
        showNotification('已连接到服务器', 'success');
        
        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('socket:connected'));
    });
    
    // 连接断开事件
    socket.on('disconnect', () => {
        console.log('WebSocket连接已断开');
        showNotification('与服务器的连接已断开，请刷新页面', 'warning');
        
        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('socket:disconnected'));
    });
    
    // 模型加载成功事件
    socket.on('model_loaded', (data) => {
        console.log('模型加载成功:', data);
        if (data.model) {
            detectionState.modelLoaded = true;
            detectionState.currentModelInfo = data.model;
            
            // 触发自定义事件
            document.dispatchEvent(new CustomEvent('model:loaded', { detail: data }));
            
            // 更新侧边栏模型状态
            if (window.updateSidebarModelStatus) {
                const config = { model: { current_model: data.model.name }, models: [data.model] };
                window.updateSidebarModelStatus(config);
            }
            
            showNotification(data.message || '模型加载成功！现在可以进行检测了', 'success');
        }
    });
    
    // 检测结果事件
    socket.on('detection_results', (data) => {
        console.log('检测结果:', data);
        
        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('detection:results', { detail: data }));
        
        if (data.success) {
            showNotification('检测完成！', 'success');
        } else {
            showNotification('检测失败，请重试', 'danger');
        }
    });
    
    // 检测错误事件
    socket.on('detection_error', (data) => {
        console.error('检测错误:', data.error);
        
        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('detection:error', { detail: data }));
        
        showNotification(`检测错误: ${data.error}`, 'danger');
    });
}

/**
 * 执行目标检测
 * @param {string} imagePath - 图像路径 
 */
function performDetection(imagePath) {
    if (!socket) {
        showNotification('WebSocket连接未建立，请刷新页面', 'warning');
        return false;
    }
    
    if (!detectionState.modelLoaded) {
        showNotification('请先加载模型', 'warning');
        return false;
    }
    
    if (!imagePath) {
        showNotification('未提供图像路径', 'warning');
        return false;
    }
    
    // 准备检测请求数据
    const detectData = {
        image_path: imagePath
    };
    
    // 发送检测请求
    socket.emit('detect', detectData);
    return true;
}

/**
 * 检查检测前置条件
 * @returns {boolean} 是否可以执行检测
 */
function canPerformDetection() {
    return socket !== null && detectionState.modelLoaded;
}

/**
 * 获取当前模型信息
 * @returns {Object|null} 当前模型信息
 */
function getCurrentModelInfo() {
    return detectionState.currentModelInfo;
}

/**
 * 是否已加载模型
 * @returns {boolean} 是否已加载模型
 */
function isModelLoaded() {
    return detectionState.modelLoaded;
}

// 导出模块API
window.DetectionCore = {
    init: initSocketConnection,
    detect: performDetection,
    canDetect: canPerformDetection,
    getCurrentModel: getCurrentModelInfo,
    isModelLoaded: isModelLoaded
};
