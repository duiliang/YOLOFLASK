/**
 * model-manager.js - 模型管理模块
 * 处理模型的列表、添加、删除和切换等功能
 */

// 模型管理器状态
const modelManagerState = {
    currentModel: null,
    modelList: []
};

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化模型管理器
    initModelManager();
});

/**
 * 初始化模型管理器
 */
function initModelManager() {
    // 获取DOM元素
    const modelTableBody = document.getElementById('modelTableBody');
    const addModelForm = document.getElementById('addModelForm');
    
    // 加载模型列表
    loadModelList();
    
    // 设置事件监听器
    if (addModelForm) {
        addModelForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addNewModel();
        });
    }
    
    // 如果在模型管理页面，则监听表格操作
    if (modelTableBody) {
        modelTableBody.addEventListener('click', function(e) {
            const target = e.target;
            if (target.tagName === 'BUTTON') {
                const action = target.getAttribute('data-action');
                const modelName = target.getAttribute('data-model');
                
                if (action === 'use') {
                    useModel(modelName);
                } else if (action === 'delete') {
                    if (confirm(`确定要删除模型 "${modelName}" 吗？`)) {
                        deleteModel(modelName);
                    }
                }
            }
        });
    }
}

/**
 * 加载模型列表
 */
function loadModelList() {
    fetch('/api/models')
        .then(response => response.json())
        .then(models => {
            modelManagerState.modelList = models;
            renderModelList(models);
        })
        .catch(error => {
            console.error('加载模型列表失败:', error);
            showNotification('加载模型列表失败', 'danger');
        });
    
    // 同时获取当前模型设置
    loadConfig()
        .then(config => {
            const currentModelName = config.model.current_model;
            if (currentModelName) {
                modelManagerState.currentModel = currentModelName;
                // 如果在主页，更新当前模型显示
                updateCurrentModelDisplay(currentModelName);
            }
        })
        .catch(error => {
            console.error('加载当前模型设置失败:', error);
        });
}

/**
 * 更新当前模型显示
 * @param {string} modelName - 模型名称
 */
function updateCurrentModelDisplay(modelName) {
    const currentModelInfo = document.getElementById('currentModelInfo');
    if (currentModelInfo) {
        // 在模型列表中查找此模型
        loadConfig()
            .then(config => {
                const models = config.models || [];
                const model = models.find(m => m.name === modelName);
                
                if (model) {
                    currentModelInfo.innerHTML = `<strong>${model.name}</strong> (${model.type}) - ${model.description || ''}`;
                    currentModelInfo.classList.remove('text-danger');
                    currentModelInfo.classList.add('text-success');
                } else {
                    currentModelInfo.textContent = '没有加载模型';
                    currentModelInfo.classList.remove('text-success');
                    currentModelInfo.classList.add('text-danger');
                }
            });
    }
}

/**
 * 渲染模型列表
 * @param {Array} models - 模型数组
 */
function renderModelList(models) {
    const modelTableBody = document.getElementById('modelTableBody');
    if (!modelTableBody) return;
    
    modelTableBody.innerHTML = '';
    
    if (models.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `<td colspan="6" class="text-center">暂无模型</td>`;
        modelTableBody.appendChild(emptyRow);
        return;
    }
    
    // 获取当前模型名称
    loadConfig()
        .then(config => {
            const currentModelName = config.model.current_model;
            
            models.forEach(model => {
                const row = document.createElement('tr');
                
                // 如果是当前使用的模型，添加标识
                if (model.name === currentModelName) {
                    row.classList.add('table-success');
                }
                
                // 获取模型类别信息展示
                let classesHtml = '';
                if (model.classes && model.classes.length > 0) {
                    // 最多显示5个类别，超过则显示...
                    const visibleClasses = model.classes.slice(0, 5);
                    const hiddenCount = Math.max(0, model.classes.length - 5);
                    classesHtml = `
                        <div>
                            <span class="badge bg-primary me-1">共${model.classes.length}个类别</span>
                            ${visibleClasses.map(c => `<span class="badge bg-info text-dark me-1">${c}</span>`).join('')}
                            ${hiddenCount > 0 ? `<span class="badge bg-secondary">+${hiddenCount}个</span>` : ''}
                        </div>
                    `;
                } else {
                    classesHtml = '<span class="text-muted">未提取类别信息</span>';
                }
                
                row.innerHTML = `
                    <td>${model.name}</td>
                    <td>${model.type}</td>
                    <td>${model.description || '-'}</td>
                    <td>${classesHtml}</td>
                    <td>
                        ${model.name === currentModelName ? 
                            '<span class="badge bg-success">当前使用中</span>' : 
                            '<button class="btn btn-sm btn-primary" data-action="use" data-model="' + model.name + '">使用</button>'}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-danger" data-action="delete" data-model="${model.name}">删除</button>
                    </td>
                `;
                modelTableBody.appendChild(row);
            });
        });
}

/**
 * 添加新模型
 */
function addNewModel() {
    const modelName = document.getElementById('modelName').value;
    const modelType = document.getElementById('modelType').value;
    const modelPath = document.getElementById('modelPath').value;
    const modelDescription = document.getElementById('modelDescription').value;
    
    const newModel = {
        name: modelName,
        path: modelPath,
        type: modelType,
        description: modelDescription
    };
    
    // 显示加载状态
    const submitBtn = document.querySelector('#addModelForm button[type="submit"]');
    showLoading('#addModelForm button[type="submit"]', true);
    
    fetch('/api/models', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newModel)
    })
    .then(response => response.json())
    .then(data => {
        showLoading('#addModelForm button[type="submit"]', false);
        
        if (data.error) {
            showNotification(data.error, 'danger');
            return;
        }
        
        showNotification('模型添加成功', 'success');
        
        // 重置表单
        document.getElementById('addModelForm').reset();
        
        // 刷新模型列表
        loadModelList();
    })
    .catch(error => {
        showLoading('#addModelForm button[type="submit"]', false);
        console.error('添加模型失败:', error);
        showNotification('添加模型失败，请检查网络连接', 'danger');
    });
}

/**
 * 删除模型
 * @param {string} modelName - 要删除的模型名称
 */
function deleteModel(modelName) {
    showLoading(`button[data-action="delete"][data-model="${modelName}"]`, true);
    
    fetch(`/api/models/${encodeURIComponent(modelName)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        showLoading(`button[data-action="delete"][data-model="${modelName}"]`, false);
        
        if (data.error) {
            showNotification(data.error, 'danger');
            return;
        }
        
        showNotification(`模型 "${modelName}" 已删除`, 'success');
        
        // 刷新模型列表
        loadModelList();
    })
    .catch(error => {
        showLoading(`button[data-action="delete"][data-model="${modelName}"]`, false);
        console.error('删除模型失败:', error);
        showNotification('删除模型失败，请检查网络连接', 'danger');
    });
}

/**
 * 使用指定模型
 * @param {string} modelName - 要使用的模型名称
 */
function useModel(modelName) {
    const buttonSelector = `button[data-action="use"][data-model="${modelName}"]`;
    showLoading(buttonSelector, true);
    
    fetch('/api/models/current', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_name: modelName })
    })
    .then(response => response.json())
    .then(data => {
        showLoading(buttonSelector, false);
        
        if (data.error) {
            showNotification(data.error, 'danger');
            return;
        }
        
        showNotification(data.message || `已切换到模型 "${modelName}"`, 'success');
        
        // 更新状态
        modelManagerState.currentModel = modelName;
        
        // 重新加载模型列表以更新UI
        loadModelList();
        
        // 更新当前模型显示(如果在主页)
        updateCurrentModelDisplay(modelName);
    })
    .catch(error => {
        showLoading(buttonSelector, false);
        
        console.error('切换模型失败:', error);
        showNotification('切换模型失败，请检查网络连接', 'danger');
    });
}

/**
 * 加载配置文件
 */
function loadConfig() {
    return fetch('/config.json')
        .then(response => response.json())
        .catch(error => {
            console.error('加载配置文件失败:', error);
        });
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success, danger, warning等）
 */
function showNotification(message, type = 'info') {
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
        const bsToast = bootstrap.Toast.getOrCreateInstance(document.getElementById(toastId));
        bsToast.hide();
    }, 3000);
}
