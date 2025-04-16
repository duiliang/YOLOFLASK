/**
 * detection.js - 检测功能主协调器
 * 负责初始化和协调各个功能模块
 */

// 全局变量
let logicRules = {}; // 存储所有逻辑规则
let selectedRuleName = ''; // 当前选中的规则名称

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
    
    // 加载逻辑规则
    loadLogicRules();
    
    // 初始化逻辑规则选择事件
    setupLogicRuleSelect();
    
    console.log('应用程序初始化完成');
}

/**
 * 加载逻辑规则
 */
function loadLogicRules() {
    fetch('/api/logic-rules')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                logicRules = data.data;
                populateLogicRuleSelect(logicRules);
            }
        })
        .catch(error => {
            console.error('加载逻辑规则失败:', error);
        });
}

/**
 * 填充逻辑规则选择下拉框
 */
function populateLogicRuleSelect(rules) {
    const select = document.getElementById('logicRuleSelect');
    
    // 保留第一个"不使用逻辑规则"选项
    select.innerHTML = '<option value="" selected>不使用逻辑规则</option>';
    
    // 添加所有规则
    for (const ruleName in rules) {
        const option = document.createElement('option');
        option.value = ruleName;
        option.textContent = ruleName;
        select.appendChild(option);
    }
}

/**
 * 设置逻辑规则选择事件
 */
function setupLogicRuleSelect() {
    const select = document.getElementById('logicRuleSelect');
    select.addEventListener('change', function() {
        selectedRuleName = this.value;
        
        if (selectedRuleName) {
            // 如果选择了逻辑规则，切换到对应的模型
            const rule = logicRules[selectedRuleName];
            if (rule && rule.model) {
                setCurrentModel(rule.model);
            }
        }
        
        // 清除之前的验证结果
        clearValidationResults();
    });
}

/**
 * 设置当前模型
 */
function setCurrentModel(modelName) {
    fetch('/api/models/current', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_name: modelName })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            window.DetectionUI.updateStatus(`切换模型失败: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('切换模型出错:', error);
        window.DetectionUI.updateStatus(`切换模型出错: ${error}`, 'danger');
    });
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
    
    // 监听检测结果事件
    document.addEventListener('detection:results', function(e) {
        if (selectedRuleName) {
            validateDetectionResults(e.detail.results, selectedRuleName);
        }
    });
}

/**
 * 验证检测结果是否符合选中的逻辑规则
 */
function validateDetectionResults(results, ruleName) {
    // 打印结果以便调试
    console.log('检测结果用于验证:', results);
    
    fetch(`/api/validate-detection?rule_name=${encodeURIComponent(ruleName)}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // 直接发送检测结果数组，而不是包装在detections属性中
        body: JSON.stringify(results)
    })
    .then(response => response.json())
    .then(data => {
        displayValidationResults(data);
    })
    .catch(error => {
        console.error('验证检测结果出错:', error);
        window.DetectionUI.updateStatus(`验证检测结果出错: ${error}`, 'danger');
    });
}

/**
 * 显示验证结果
 */
function displayValidationResults(data) {
    const resultDiv = document.getElementById('ruleValidationResult');
    const statusDiv = document.getElementById('validationStatus');
    const detailsDiv = document.getElementById('validationDetails');
    
    resultDiv.style.display = 'block';
    
    if (data.success) {
        statusDiv.className = 'alert alert-success';
        statusDiv.textContent = '验证通过';
    } else {
        statusDiv.className = 'alert alert-danger';
        statusDiv.textContent = '验证失败';
    }
    
    detailsDiv.textContent = data.message || '';
}

/**
 * 清除验证结果
 */
function clearValidationResults() {
    const resultDiv = document.getElementById('ruleValidationResult');
    resultDiv.style.display = 'none';
    
    const statusDiv = document.getElementById('validationStatus');
    statusDiv.className = 'alert';
    statusDiv.textContent = '';
    
    const detailsDiv = document.getElementById('validationDetails');
    detailsDiv.textContent = '';
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
