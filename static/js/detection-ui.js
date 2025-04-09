/**
 * detection-ui.js - 检测结果UI模块
 * 负责显示检测结果、状态消息和UI交互
 */

/**
 * 初始化检测UI
 */
function initDetectionUI() {
    // 监听模型加载事件
    document.addEventListener('model:loaded', function(e) {
        updateModelDisplay(e.detail.model);
    });
    
    // 监听检测结果事件
    document.addEventListener('detection:results', function(e) {
        // 重置检测按钮状态
        showLoading('#detectBtn', false);
        
        displayResults(e.detail.results, e.detail.result_image);
        updateStatusMessage(`检测完成，共找到 ${e.detail.results.length} 个目标`, 'success');
    });
    
    // 监听检测错误事件
    document.addEventListener('detection:error', function(e) {
        // 重置检测按钮状态
        showLoading('#detectBtn', false);
        
        updateStatusMessage(`检测失败: ${e.detail.error}`, 'danger');
    });
    
    // 绑定检测按钮事件
    const detectBtn = document.getElementById('detectBtn');
    if (detectBtn) {
        detectBtn.addEventListener('click', function() {
            if (window.DetectionCore && window.ImageProcessor) {
                const imagePath = window.ImageProcessor.getCurrentImagePath();
                
                if (!imagePath) {
                    showNotification('请先上传或捕获图像', 'warning');
                    return;
                }
                
                if (!window.DetectionCore.isModelLoaded()) {
                    showNotification('请先加载模型', 'warning');
                    return;
                }
                
                // 显示加载状态
                showLoading('#detectBtn', true);
                updateStatusMessage('正在执行检测...', 'info');
                
                // 执行检测
                window.DetectionCore.detect(imagePath);
            }
        });
    }
}

/**
 * 更新模型显示
 * @param {Object} model - 模型信息 
 */
function updateModelDisplay(model) {
    const currentModelInfo = document.getElementById('currentModelInfo');
    if (currentModelInfo && model) {
        currentModelInfo.innerHTML = `<strong>${model.name}</strong> (${model.type}) - ${model.description || ''}`;
        currentModelInfo.classList.remove('text-danger');
        currentModelInfo.classList.add('text-success');
        
        // 启用检测按钮
        const detectBtn = document.getElementById('detectBtn');
        if (detectBtn) {
            detectBtn.removeAttribute('disabled');
        }
    }
}

/**
 * 更新状态消息
 * @param {string} message - 状态消息
 * @param {string} type - 消息类型 (info, success, warning, danger)
 */
function updateStatusMessage(message, type = 'info') {
    const statusMessages = document.getElementById('statusMessages');
    if (statusMessages) {
        statusMessages.textContent = message;
        statusMessages.className = `alert alert-${type}`;
    }
}

/**
 * 显示检测结果
 * @param {Array} results - 检测结果数组
 * @param {string} resultImageUrl - 结果图像URL
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
        
        if (!results || results.length === 0) {
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

// 导出模块API
window.DetectionUI = {
    init: initDetectionUI,
    updateStatus: updateStatusMessage,
    displayResults: displayResults,
    clearResults: clearDetectionResults
};
