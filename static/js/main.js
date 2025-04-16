/**
 * main.js - 通用JavaScript功能
 * 提供全局功能和辅助方法
 */

// 全局变量
const appState = {
    socketConnected: false,
    config: null
};

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('应用已初始化');
    
    // 显示通知消息的辅助函数
    window.showNotification = function(message, type = 'info') {
        const statusMessages = document.getElementById('statusMessages');
        if (statusMessages) {
            statusMessages.textContent = message;
            statusMessages.className = `alert alert-${type}`;
        }
    };
    
    // 格式化时间的辅助函数
    window.formatDateTime = function() {
        const now = new Date();
        return now.toLocaleString('zh-CN');
    };
    
    // 显示加载指示器的辅助函数
    window.showLoading = function(selector, show = true) {
        const element = document.querySelector(selector);
        if (element) {
            if (show) {
                element.classList.add('disabled');
                const originalText = element.textContent;
                element.setAttribute('data-original-text', originalText);
                element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>加载中...';
            } else {
                element.classList.remove('disabled');
                const originalText = element.getAttribute('data-original-text');
                if (originalText) {
                    element.textContent = originalText;
                }
            }
        }
    };
    
    // 初始化各个功能模块
    try {
        // 加载配置文件
        loadConfig().then(config => {
            appState.config = config;
            console.log('配置加载完成', config);
            
            // 初始化配置界面
            initConfigUI();
            
            // 检查Socket.IO库是否已加载
            checkSocketIOLibrary();
        });
    } catch (error) {
        console.error('初始化失败:', error);
        window.showNotification('应用初始化失败，请刷新页面重试', 'danger');
    }
});

/**
 * 加载配置文件
 * @returns {Promise} 返回配置对象的Promise
 */
async function loadConfig() {
    try {
        const response = await fetch('/config.json?t=' + new Date().getTime());
        if (!response.ok) {
            throw new Error('无法加载配置文件');
        }
        return await response.json();
    } catch (error) {
        console.error('加载配置失败:', error);
        // 返回默认配置
        return {
            server: {
                host: window.location.hostname,
                port: window.location.port || (window.location.protocol === 'https:' ? 443 : 80)
            },
            model: {
                default_path: '',
                default_type: 'yolov8',
                conf_threshold: 0.25,
                iou_threshold: 0.45
            },
            upload: {
                max_size_mb: 16,
                allowed_extensions: ["jpg", "jpeg", "png"]
            }
        };
    }
}

/**
 * 初始化配置界面
 */
function initConfigUI() {
    // 添加配置按钮到导航栏
    const navbarNav = document.querySelector('#navbarNav .navbar-nav');
    if (navbarNav) {
        const configLi = document.createElement('li');
        configLi.className = 'nav-item';
        configLi.innerHTML = `
            <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#configModal">
                <i class="bi bi-gear"></i> 配置
            </a>
        `;
        navbarNav.appendChild(configLi);
    }
    
    // 创建配置模态框
    const modalDiv = document.createElement('div');
    modalDiv.className = 'modal fade';
    modalDiv.id = 'configModal';
    modalDiv.tabIndex = '-1';
    modalDiv.setAttribute('aria-labelledby', 'configModalLabel');
    modalDiv.setAttribute('aria-hidden', 'true');
    
    modalDiv.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="configModalLabel">系统配置</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="configForm">
                        <div class="mb-3">
                            <h6>服务器设置</h6>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label for="serverHost" class="form-label">主机地址</label>
                                    <input type="text" class="form-control" id="serverHost" value="${appState.config?.server?.host || '0.0.0.0'}">
                                </div>
                                <div class="col-md-6">
                                    <label for="serverPort" class="form-label">端口</label>
                                    <input type="number" class="form-control" id="serverPort" value="${appState.config?.server?.port || 5000}">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <h6>模型设置</h6>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label for="defaultModelPath" class="form-label">默认模型路径</label>
                                    <input type="text" class="form-control" id="defaultModelPath" value="${appState.config?.model?.default_path || ''}">
                                </div>
                                <div class="col-md-6">
                                    <label for="defaultModelType" class="form-label">默认模型类型</label>
                                    <select class="form-select" id="defaultModelType">
                                        <option value="yolov8" ${appState.config?.model?.default_type === 'yolov8' ? 'selected' : ''}>YOLOv8</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label for="confThreshold" class="form-label">置信度阈值</label>
                                    <input type="number" class="form-control" id="confThreshold" min="0" max="1" step="0.05" value="${appState.config?.model?.conf_threshold || 0.25}">
                                </div>
                                <div class="col-md-6">
                                    <label for="iouThreshold" class="form-label">IOU阈值</label>
                                    <input type="number" class="form-control" id="iouThreshold" min="0" max="1" step="0.05" value="${appState.config?.model?.iou_threshold || 0.45}">
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" id="saveConfigBtn">保存配置</button>
                </div>
            </div>
        </div>
    `;
    
    // 添加模态框到body
    document.body.appendChild(modalDiv);
    
    // 添加保存配置的事件监听器
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveConfig);
    }
}

/**
 * 保存配置
 */
function saveConfig() {
    // 读取表单值
    const config = {
        server: {
            host: document.getElementById('serverHost').value,
            port: parseInt(document.getElementById('serverPort').value),
            debug: appState.config?.server?.debug || true
        },
        model: {
            default_path: document.getElementById('defaultModelPath').value,
            default_type: document.getElementById('defaultModelType').value,
            conf_threshold: parseFloat(document.getElementById('confThreshold').value),
            iou_threshold: parseFloat(document.getElementById('iouThreshold').value)
        },
        upload: appState.config?.upload || {
            max_size_mb: 16,
            allowed_extensions: ["jpg", "jpeg", "png"]
        }
    };
    
    // 更新全局配置
    appState.config = config;
    
    // 向服务器发送配置更新请求（暂时不明用途）
    fetch('/update_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
            modal.hide();
            
            // 显示成功消息
            showNotification('配置已保存，某些更改可能需要重启应用才能生效', 'success');
        } else {
            throw new Error(data.error || '保存配置失败');
        }
    })
    .catch(error => {
        console.error('保存配置失败:', error);
        showNotification(`保存配置失败: ${error.message}`, 'danger');
    });
}

/**
 * 检查Socket.IO库是否已加载，如果未加载则尝试使用本地副本
 */
function checkSocketIOLibrary() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO客户端库未加载，尝试加载本地副本');
        
        // 创建script元素
        const script = document.createElement('script');
        script.src = '/static/js/socket.io.min.js';
        script.async = true;
        script.onload = function() {
            console.log('本地Socket.IO库加载成功');
            showNotification('使用本地Socket.IO库连接', 'info');
        };
        script.onerror = function() {
            console.error('无法加载Socket.IO库，WebSocket功能将不可用');
            showNotification('无法加载Socket.IO库，部分功能可能不可用', 'warning');
        };
        
        // 添加到文档
        document.head.appendChild(script);
    }
}
