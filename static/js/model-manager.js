/**
 * 模型管理模块
 * 用于处理模型加载、列表展示、添加和删除模型等功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const modelTableBody = document.getElementById('modelTableBody');
    const addModelForm = document.getElementById('addModelForm');
    const modelManagerModal = document.getElementById('modelManagerModal');
    
    // 模型管理器初始化
    const modelManager = {
        /**
         * 初始化模型管理器
         */
        init: function() {
            this.loadModels();
            this.setupEventListeners();
        },
        
        /**
         * 设置事件监听器
         */
        setupEventListeners: function() {
            // 表单提交事件
            if (addModelForm) {
                addModelForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    modelManager.addNewModel();
                });
            }
            
            // 模态框显示事件
            if (modelManagerModal) {
                modelManagerModal.addEventListener('shown.bs.modal', function() {
                    modelManager.loadModels();
                });
            }
        },
        
        /**
         * 加载模型列表
         */
        loadModels: function() {
            fetch('/api/models')
                .then(response => response.json())
                .then(models => {
                    this.renderModelList(models);
                })
                .catch(error => {
                    console.error('加载模型列表失败:', error);
                    showToast('加载模型列表失败', 'danger');
                });
            
            // 同时获取当前模型设置
            fetch('/config.json')
                .then(response => response.json())
                .then(config => {
                    currentModelName = config.model.current_model;
                })
                .catch(error => {
                    console.error('加载配置失败:', error);
                });
        },
        
        /**
         * 渲染模型列表
         * @param {Array} models - 模型数组
         */
        renderModelList: function(models) {
            if (!modelTableBody) return;
            
            modelTableBody.innerHTML = '';
            
            if (models.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = `<td colspan="5" class="text-center">暂无模型</td>`;
                modelTableBody.appendChild(emptyRow);
                return;
            }
            
            // 获取当前模型名称
            fetch('/config.json')
                .then(response => response.json())
                .then(config => {
                    const currentModelName = config.model.current_model;
                    
                    // 渲染每个模型行
                    models.forEach(model => {
                        const row = document.createElement('tr');
                        const isCurrentModel = (model.name === currentModelName);
                        
                        row.innerHTML = `
                            <td>${model.name}</td>
                            <td>${model.type}</td>
                            <td>${model.path}</td>
                            <td>${model.description || '-'}</td>
                            <td>
                                ${isCurrentModel ? 
                                    '<span class="badge bg-success">当前使用</span>' : 
                                    `<button class="btn btn-sm btn-primary me-1" data-action="use" data-model="${model.name}">使用</button>`
                                }
                                <button class="btn btn-sm btn-danger" data-action="delete" data-model="${model.name}">删除</button>
                            </td>
                        `;
                        
                        modelTableBody.appendChild(row);
                    });
                    
                    // 绑定按钮事件
                    this.bindModelActions();
                })
                .catch(error => {
                    console.error('获取当前模型设置失败:', error);
                });
        },
        
        /**
         * 绑定模型操作按钮事件
         */
        bindModelActions: function() {
            // 使用事件委托绑定事件
            if (modelTableBody) {
                modelTableBody.addEventListener('click', function(e) {
                    const target = e.target;
                    if (target.tagName === 'BUTTON') {
                        const action = target.getAttribute('data-action');
                        const modelName = target.getAttribute('data-model');
                        
                        if (action === 'use') {
                            modelManager.useModel(modelName);
                        } else if (action === 'delete') {
                            if (confirm(`确定要删除模型 "${modelName}" 吗？`)) {
                                modelManager.deleteModel(modelName);
                            }
                        }
                    }
                });
            }
        },
        
        /**
         * 添加新模型
         */
        addNewModel: function() {
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
            
            fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newModel)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showToast(data.error, 'danger');
                    return;
                }
                
                showToast('模型添加成功', 'success');
                this.loadModels();
                
                // 重置表单
                addModelForm.reset();
            })
            .catch(error => {
                console.error('添加模型失败:', error);
                showToast('添加模型失败，请检查网络连接', 'danger');
            });
        },
        
        /**
         * 删除模型
         * @param {string} modelName - 要删除的模型名称
         */
        deleteModel: function(modelName) {
            fetch(`/api/models/${modelName}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showToast(data.error, 'danger');
                    return;
                }
                
                showToast(`模型 "${modelName}" 已删除`, 'success');
                this.loadModels();
            })
            .catch(error => {
                console.error('删除模型失败:', error);
                showToast('删除模型失败，请检查网络连接', 'danger');
            });
        },
        
        /**
         * 使用指定模型
         * @param {string} modelName - 要使用的模型名称
         */
        useModel: function(modelName) {
            fetch('/api/models/current', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: modelName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showToast(data.error, 'danger');
                    return;
                }
                
                showToast(data.message || `已切换到模型 "${modelName}"`, 'success');
                
                // 更新UI
                this.loadModels();
                
                // 关闭模态框
                const modalElement = document.getElementById('modelManagerModal');
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) {
                    modalInstance.hide();
                }
            })
            .catch(error => {
                console.error('切换模型失败:', error);
                showToast('切换模型失败，请检查网络连接', 'danger');
            });
        }
    };
    
    // 初始化模型管理器
    modelManager.init();
});

/**
 * 显示提示消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success, danger, warning等）
 */
function showToast(message, type = 'info') {
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
