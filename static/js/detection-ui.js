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
        
        // 显示检测结果，包括规则名称
        displayResults(e.detail.results, e.detail.result_image, e.detail.rule_name);
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
                
                // 获取选择的规则名称（如果有）
                const selectedRuleName = document.getElementById('logicRuleSelect')?.value;
                
                // 执行检测，传递规则名称
                window.DetectionCore.detect(imagePath, selectedRuleName || null);
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
 * @param {string} ruleName - 使用的规则名称（可选）
 */
function displayResults(results, resultImageUrl, ruleName) {
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
                
                // 创建结果内容，添加ROI区域信息（如果有）
                let resultContent = `<span>${index + 1}. ${item.class_name}</span>`;
                if (item.roi_id !== null && item.roi_id !== undefined) {
                    // 使ROI编号从1开始显示
                    const roiDisplayId = item.roi_id + 1;
                    resultContent = `<span>${index + 1}. ${item.class_name} (ROI ${roiDisplayId})</span>`;
                }
                
                resultItem.innerHTML = `
                    ${resultContent}
                    <span class="badge bg-primary rounded-pill">${confidencePercent}%</span>
                `;
                
                resultsList.appendChild(resultItem);
            });
        }
        
        // 显示结果区域
        detectionResults.style.display = 'block';
        
        // 如果使用了规则，在结果列表头部添加规则信息
        if (ruleName) {
            const ruleInfoItem = document.createElement('li');
            ruleInfoItem.className = 'list-group-item list-group-item-info';
            ruleInfoItem.innerHTML = `<strong>使用规则:</strong> ${ruleName}`;
            resultsList.insertBefore(ruleInfoItem, resultsList.firstChild);
        }
    }
}

/**
 * 清除检测结果
 */
function clearDetectionResults() {
    const resultsList = document.getElementById('resultsList');
    const detectionResults = document.getElementById('detectionResults');
    const resultImage = document.getElementById('resultImage');
    const validationResult = document.getElementById('ruleValidationResult');
    
    if (resultsList) {
        resultsList.innerHTML = '';
    }
    
    if (detectionResults) {
        detectionResults.style.display = 'none';
    }
    
    if (resultImage) {
        resultImage.style.display = 'none';
    }
    
    if (validationResult) {
        validationResult.style.display = 'none';
    }
}

// 导出模块API
window.DetectionUI = {
    init: initDetectionUI,
    updateStatus: updateStatusMessage,
    displayResults: displayResults,
    clearResults: clearDetectionResults
};
