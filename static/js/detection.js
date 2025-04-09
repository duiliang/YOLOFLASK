/**
 * detection.js - 检测功能主协调器
 * 负责初始化和协调各个功能模块
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
    // 初始化各个模块
    initializeApp();
});

/**
 * 初始化应用程序
 */
function initializeApp() {
    // 检查必要的模块是否存在
    if (!window.DetectionCore) {
        console.error('检测核心模块未加载');
        showErrorMessage('应用程序初始化失败：检测核心模块未加载');
        return;
    }
    
    if (!window.ImageProcessor) {
        console.error('图像处理模块未加载');
        showErrorMessage('应用程序初始化失败：图像处理模块未加载');
        return;
    }
    
    if (!window.DetectionUI) {
        console.error('检测UI模块未加载');
        showErrorMessage('应用程序初始化失败：检测UI模块未加载');
        return;
    }
    
    // 初始化各个模块
    window.DetectionCore.init();
    window.ImageProcessor.init();
    window.DetectionUI.init();
    
    // 初始化图像处理事件
    setupImageEvents();
    
    console.log('应用程序初始化完成');
}

/**
 * 设置图像处理事件
 */
function setupImageEvents() {
    // 监听图像上传事件
    document.addEventListener('image:uploaded', function(e) {
        window.DetectionUI.clearResults();
        window.DetectionUI.updateStatus('图像已上传，准备进行检测', 'success');
    });
    
    // 监听图像捕获事件
    document.addEventListener('image:captured', function(e) {
        window.DetectionUI.clearResults();
        window.DetectionUI.updateStatus('图像已捕获，准备进行检测', 'success');
    });
}

/**
 * 显示错误消息
 * @param {string} message - 错误消息
 */
function showErrorMessage(message) {
    const container = document.querySelector('main') || document.body;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    
    container.prepend(alertDiv);
}
