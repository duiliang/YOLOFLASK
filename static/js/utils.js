/**
 * utils.js - 通用工具函数
 * 可复用的工具函数集合，用于减少代码重复和提高可维护性
 */

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success, danger, warning等）
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

/**
 * 显示加载状态
 * @param {string} selector - CSS选择器，定位到需要显示加载状态的元素
 * @param {boolean} isLoading - 是否显示加载状态
 */
function showLoading(selector, isLoading) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    if (isLoading) {
        // 保存原始文本，以便于在加载完成后恢复
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', element.innerHTML);
        }
        element.setAttribute('disabled', 'disabled');
        element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
    } else {
        element.removeAttribute('disabled');
        element.innerHTML = element.getAttribute('data-original-text') || '确定';
    }
}

/**
 * 异步加载配置
 * @returns {Promise} - 返回Promise对象，在成功时解析为配置对象
 */
function loadConfig() {
    return fetch('/config.json?t=' + Date.now())
        .then(response => {
            if (!response.ok) {
                throw new Error('配置加载失败: ' + response.statusText);
            }
            return response.json();
        })
        .then(config => {
            // 更新侧边栏模型状态
            updateSidebarModelStatus(config);
            return config;
        })
        .catch(error => {
            console.error('配置加载错误:', error);
            showNotification('无法加载配置，请刷新页面重试', 'danger');
            throw error;
        });
}

/**
 * 更新侧边栏中的模型状态显示
 * @param {Object} config - 配置对象
 */
function updateSidebarModelStatus(config) {
    const sidebarModelStatus = document.getElementById('sidebarModelStatus');
    if (!sidebarModelStatus) return;
    
    const currentModelName = config.model?.current_model;
    if (!currentModelName) {
        sidebarModelStatus.textContent = '未加载';
        sidebarModelStatus.className = 'text-warning';
        return;
    }
    
    // 查找当前模型的详细信息
    const currentModel = (config.models || []).find(model => model.name === currentModelName);
    if (currentModel) {
        sidebarModelStatus.textContent = currentModel.name;
        sidebarModelStatus.className = 'text-success';
    } else {
        sidebarModelStatus.textContent = '配置错误';
        sidebarModelStatus.className = 'text-danger';
    }
}

// 导出工具函数
window.showNotification = showNotification;
window.showLoading = showLoading;
window.loadConfig = loadConfig;
window.updateSidebarModelStatus = updateSidebarModelStatus;
