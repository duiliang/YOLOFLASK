/**
 * 逻辑规则管理JavaScript
 * 提供逻辑规则的添加、编辑、删除和预览功能
 */

// 状态对象
const state = {
    currentRuleName: null,    // 当前选中的规则名称
    ruleConfigs: {},          // 所有规则配置
    
    currentRoiConfig: null,   // 当前选中的ROI配置名称
    roiConfigs: {},           // 所有ROI配置
    rois: [],                 // 当前ROI配置中的所有ROI区域
    
    currentModel: null,       // 当前选中的模型
    modelList: [],            // 所有可用的模型列表
    classNames: [],           // 当前模型支持的类别
    
    rules: [],                // 当前规则配置中的规则列表
    
    dirtyFlag: false          // 是否有未保存的更改
};

// Canvas绘图相关
let canvas, ctx;

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Canvas
    initCanvas();
    
    // 初始化页面
    initPage();
    
    // 设置事件处理器
    setupEventHandlers();
});

/**
 * 初始化Canvas
 */
function initCanvas() {
    canvas = document.getElementById('roiCanvas');
    if (!canvas) {
        console.error('找不到Canvas元素');
        return;
    }
    
    ctx = canvas.getContext('2d');
}

/**
 * 初始化页面
 */
function initPage() {
    // 加载所有规则配置
    loadLogicRules();
    
    // 加载所有ROI配置
    loadRoiConfigs();
    
    // 加载所有模型
    loadModels();
}

/**
 * 设置事件处理器
 */
function setupEventHandlers() {
    // 规则配置选择器变更事件
    document.getElementById('logicRuleSelector').addEventListener('change', function() {
        const ruleName = this.value;
        if (ruleName) {
            selectLogicRule(ruleName);
        } else {
            resetForm();
        }
    });
    
    // ROI配置选择器变更事件
    document.getElementById('roiConfigSelector').addEventListener('change', function() {
        const roiConfigName = this.value;
        if (roiConfigName) {
            selectRoiConfig(roiConfigName);
        } else {
            clearRoiPreview();
        }
    });
    
    // 模型选择器变更事件
    document.getElementById('modelSelector').addEventListener('change', function() {
        const modelName = this.value;
        if (modelName) {
            selectModel(modelName);
        } else {
            clearClassSelector();
        }
    });
    
    // ROI区域选择器变更事件
    document.getElementById('roiSelector').addEventListener('change', function() {
        highlightSelectedRoi(this.value);
    });
    
    // 添加规则按钮事件
    document.getElementById('addRuleBtn').addEventListener('click', addRule);
    
    // 保存规则按钮事件
    document.getElementById('saveRuleBtn').addEventListener('click', saveRuleConfig);
    
    // 删除规则按钮事件
    document.getElementById('deleteRuleBtn').addEventListener('click', deleteRuleConfig);
    
    // 规则名称输入框事件
    document.getElementById('ruleNameInput').addEventListener('input', function() {
        state.dirtyFlag = true;
    });
    
    // 页面离开提醒
    window.addEventListener('beforeunload', function(e) {
        if (state.dirtyFlag) {
            e.returnValue = '您有未保存的更改，确定要离开吗？';
            return e.returnValue;
        }
    });
}

/**
 * 加载所有逻辑规则配置
 */
function loadLogicRules() {
    fetch('/api/logic-rules')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                state.ruleConfigs = data.data || {};
                updateLogicRuleSelector();
            } else {
                showNotification(data.message || '加载规则配置失败', 'danger');
            }
        })
        .catch(error => {
            console.error('加载规则配置失败:', error);
            showNotification('加载规则配置失败，请检查网络连接', 'danger');
        });
}

/**
 * 更新逻辑规则选择器
 */
function updateLogicRuleSelector() {
    const selector = document.getElementById('logicRuleSelector');
    
    // 保留第一个选项
    selector.innerHTML = '<option value="">新建规则配置...</option>';
    
    // 添加所有规则配置
    const ruleNames = Object.keys(state.ruleConfigs).sort();
    ruleNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        selector.appendChild(option);
    });
}

/**
 * 选择逻辑规则配置
 * @param {string} ruleName - 规则配置名称
 */
function selectLogicRule(ruleName) {
    const config = state.ruleConfigs[ruleName];
    if (!config) {
        showNotification(`未找到规则配置 "${ruleName}"`, 'danger');
        return;
    }
    
    // 更新状态
    state.currentRuleName = ruleName;
    state.currentRoiConfig = config.roi_config;
    state.currentModel = config.model;
    state.rules = config.rules || [];
    
    // 更新表单
    document.getElementById('ruleNameInput').value = ruleName;
    document.getElementById('roiConfigSelector').value = config.roi_config;
    document.getElementById('modelSelector').value = config.model;
    
    // 显示删除按钮
    document.getElementById('deleteRuleBtn').style.display = 'inline-block';
    
    // 选择ROI配置
    if (config.roi_config) {
        selectRoiConfig(config.roi_config);
    }
    
    // 选择模型
    if (config.model) {
        selectModel(config.model);
    }
    
    // 渲染规则列表
    renderRuleList();
    
    // 清除脏标记
    state.dirtyFlag = false;
}

/**
 * 重置表单
 */
function resetForm() {
    // 清空表单
    document.getElementById('ruleNameInput').value = '';
    document.getElementById('roiConfigSelector').value = '';
    document.getElementById('modelSelector').value = '';
    document.getElementById('roiSelector').innerHTML = '<option value="">选择区域...</option>';
    document.getElementById('classSelector').innerHTML = '<option value="">选择类别...</option>';
    
    // 清空规则列表
    document.getElementById('ruleListContainer').innerHTML = 
        '<div class="alert alert-info">请先选择ROI配置和模型，然后添加规则。</div>';
    
    // 隐藏删除按钮
    document.getElementById('deleteRuleBtn').style.display = 'none';
    
    // 重置状态
    state.currentRuleName = null;
    state.currentRoiConfig = null;
    state.currentModel = null;
    state.rules = [];
    state.dirtyFlag = false;
    
    // 清空预览
    clearRoiPreview();
}

/**
 * 加载所有ROI配置
 */
function loadRoiConfigs() {
    fetch('/api/roi-configs')
        .then(response => response.json())
        .then(data => {
            state.roiConfigs = data || {};
            updateRoiConfigSelector();
        })
        .catch(error => {
            console.error('加载ROI配置失败:', error);
            showNotification('加载ROI配置失败，请检查网络连接', 'danger');
        });
}

/**
 * 更新ROI配置选择器
 */
function updateRoiConfigSelector() {
    const selector = document.getElementById('roiConfigSelector');
    
    // 保留第一个选项
    selector.innerHTML = '<option value="">选择ROI配置...</option>';
    
    // 添加所有ROI配置
    const configNames = Object.keys(state.roiConfigs).sort();
    configNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        selector.appendChild(option);
    });
}

/**
 * 选择ROI配置
 * @param {string} roiConfigName - ROI配置名称
 */
function selectRoiConfig(roiConfigName) {
    // 更新状态
    state.currentRoiConfig = roiConfigName;
    
    // 通过API获取ROI配置详情
    fetch(`/api/roi-config/${encodeURIComponent(roiConfigName)}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const roiConfig = result.data;
                
                // 更新状态
                state.rois = roiConfig.rois || [];
                
                // 更新ROI区域选择器
                updateRoiSelector();
                
                // 加载背景图片和绘制ROI区域
                const backgroundImage = document.getElementById('backgroundImage');
                backgroundImage.src = roiConfig.background || '';
                
                // 等待图片加载完成后渲染ROI区域
                backgroundImage.onload = function() {
                    drawRoiAreas();
                };
            } else {
                console.error(`未找到ROI配置 "${roiConfigName}":`, result.error || '未知错误');
                showNotification(`加载ROI配置失败: ${result.error || '未知错误'}`, 'danger');
            }
        })
        .catch(error => {
            console.error('加载ROI配置失败:', error);
            showNotification('加载ROI配置失败，请检查网络连接', 'danger');
        });
}

/**
 * 更新ROI区域选择器
 */
function updateRoiSelector() {
    const selector = document.getElementById('roiSelector');
    
    // 清空选择器
    selector.innerHTML = '<option value="">选择区域...</option>';
    
    // 添加所有ROI区域
    if (Array.isArray(state.rois)) {
        state.rois.forEach((roi, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `ROI ${index + 1}`;
            selector.appendChild(option);
        });
    } else {
        console.error('state.rois不是数组:', state.rois);
    }
}

/**
 * 加载背景图片和绘制ROI区域
 * @param {string} roiConfigName - ROI配置名称
 */
function loadRoiPreview(roiConfigName) {
    // 从配置文件获取ROI背景图片URL
    fetch('/config.json')
        .then(response => response.json())
        .then(config => {
            const roiConfigs = config.roi_configs || {};
            const roiConfig = roiConfigs[roiConfigName];
            
            if (!roiConfig) {
                console.error(`未找到ROI配置 "${roiConfigName}"`);
                return;
            }
            
            // 设置背景图片
            const backgroundImage = document.getElementById('backgroundImage');
            backgroundImage.src = roiConfig.background_image || '';
            
            // 等待图片加载完成后渲染ROI区域
            backgroundImage.onload = function() {
                drawRoiAreas();
            };
        })
        .catch(error => {
            console.error('加载ROI预览失败:', error);
            showNotification('加载ROI预览失败', 'danger');
        });
}

/**
 * 绘制ROI区域
 */
function drawRoiAreas() {
    if (!ctx) {
        console.error('Canvas上下文未初始化');
        return;
    }
    
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 检查ROI列表
    if (!Array.isArray(state.rois) || state.rois.length === 0) {
        console.log('没有ROI区域需要绘制');
        return;
    }
    
    // 绘制每个ROI区域
    state.rois.forEach((roi, index) => {
        // 设置样式
        ctx.strokeStyle = roi.color || `hsl(${(index * 30) % 360}, 70%, 50%)`;
        ctx.fillStyle = roi.color ? `${roi.color}33` : `hsla(${(index * 30) % 360}, 70%, 50%, 0.2)`;
        ctx.lineWidth = 2;
        
        // 开始绘制路径
        ctx.beginPath();
        
        // 根据ROI类型绘制
        if (roi.type === 'rectangle' || (roi.x1 !== undefined && roi.y1 !== undefined)) {
            // 绘制矩形
            const x = parseInt(roi.x1);
            const y = parseInt(roi.y1);
            const width = parseInt(roi.x2 - roi.x1);
            const height = parseInt(roi.y2 - roi.y1);
            
            ctx.rect(x, y, width, height);
        } else if (roi.points && Array.isArray(roi.points) && roi.points.length > 0) {
            // 绘制多边形
            const points = roi.points;
            ctx.moveTo(points[0][0], points[0][1]);
            
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i][0], points[i][1]);
            }
            
            ctx.closePath();
        }
        
        // 填充和描边
        ctx.fill();
        ctx.stroke();
        
        // 绘制ROI编号标签
        drawRoiLabel(index + 1, roi);
    });
}

/**
 * 绘制ROI编号标签
 * @param {number} number - ROI编号
 * @param {object} roi - ROI对象
 */
function drawRoiLabel(number, roi) {
    let x, y;
    
    if (roi.type === 'rectangle' || (roi.x1 !== undefined && roi.y1 !== undefined)) {
        x = parseInt(roi.x1);
        y = parseInt(roi.y1);
    } else if (roi.points && Array.isArray(roi.points) && roi.points.length > 0) {
        x = roi.points[0][0];
        y = roi.points[0][1];
    } else {
        return;
    }
    
    // 设置标签样式
    ctx.fillStyle = roi.color || `hsl(${((number - 1) * 30) % 360}, 70%, 50%)`;
    ctx.font = 'bold 14px Arial';
    
    // 绘制标签背景
    const padding = 4;
    const textWidth = ctx.measureText(number).width;
    ctx.fillRect(x, y, textWidth + padding * 2, 20);
    
    // 绘制标签文字
    ctx.fillStyle = '#fff';
    ctx.fillText(number, x + padding, y + 14);
}

/**
 * 高亮显示选中的ROI区域
 * @param {string} roiIndex - ROI区域索引
 */
function highlightSelectedRoi(roiIndex) {
    // 重绘所有ROI区域
    drawRoiAreas();
    
    // 如果没有选中ROI，则直接返回
    if (roiIndex === '') {
        return;
    }
    
    // 获取选中的ROI
    const index = parseInt(roiIndex);
    const roi = state.rois[index];
    
    if (!roi) {
        return;
    }
    
    // 绘制高亮边框
    ctx.strokeStyle = '#FF5722';
    ctx.lineWidth = 4;
    ctx.beginPath();
    
    if (roi.type === 'rectangle' || (roi.x1 !== undefined && roi.y1 !== undefined)) {
        // 矩形
        const x = parseInt(roi.x1);
        const y = parseInt(roi.y1);
        const width = parseInt(roi.x2 - roi.x1);
        const height = parseInt(roi.y2 - roi.y1);
        
        ctx.rect(x, y, width, height);
    } else if (roi.points && Array.isArray(roi.points) && roi.points.length > 0) {
        // 多边形
        const points = roi.points;
        ctx.moveTo(points[0][0], points[0][1]);
        
        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i][0], points[i][1]);
        }
        
        ctx.closePath();
    }
    
    ctx.stroke();
}

/**
 * 清空ROI预览
 */
function clearRoiPreview() {
    document.getElementById('backgroundImage').src = '';
    if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    document.getElementById('roiSelector').innerHTML = '<option value="">选择区域...</option>';
}

/**
 * 加载所有模型
 */
function loadModels() {
    fetch('/api/models')
        .then(response => response.json())
        .then(models => {
            state.modelList = models || [];
            updateModelSelector();
        })
        .catch(error => {
            console.error('加载模型列表失败:', error);
            showNotification('加载模型列表失败，请检查网络连接', 'danger');
        });
}

/**
 * 更新模型选择器
 */
function updateModelSelector() {
    const selector = document.getElementById('modelSelector');
    
    // 保留第一个选项
    selector.innerHTML = '<option value="">选择模型...</option>';
    
    // 添加所有模型
    state.modelList.forEach(model => {
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = model.name;
        selector.appendChild(option);
    });
}

/**
 * 选择模型
 * @param {string} modelName - 模型名称
 */
function selectModel(modelName) {
    // 更新状态
    state.currentModel = modelName;
    
    // 获取选中的模型
    const model = state.modelList.find(m => m.name === modelName);
    if (!model) {
        console.error(`未找到模型 "${modelName}"`);
        return;
    }
    
    // 获取模型支持的类别
    state.classNames = model.classes || [];
    
    // 更新类别选择器
    updateClassSelector();
}

/**
 * 更新类别选择器
 */
function updateClassSelector() {
    const selector = document.getElementById('classSelector');
    
    // 清空选择器
    selector.innerHTML = '<option value="">选择类别...</option>';
    
    // 添加所有类别
    state.classNames.forEach(className => {
        const option = document.createElement('option');
        option.value = className;
        option.textContent = className;
        selector.appendChild(option);
    });
}

/**
 * 清空类别选择器
 */
function clearClassSelector() {
    document.getElementById('classSelector').innerHTML = '<option value="">选择类别...</option>';
    state.classNames = [];
}

/**
 * 添加规则
 */
function addRule() {
    // 获取输入值
    const roiIndex = document.getElementById('roiSelector').value;
    const className = document.getElementById('classSelector').value;
    const operator = document.getElementById('operatorSelector').value;
    const count = parseInt(document.getElementById('countInput').value, 10);
    
    // 验证输入
    if (!roiIndex) {
        showNotification('请选择ROI区域', 'warning');
        return;
    }
    
    if (!className) {
        showNotification('请选择目标类别', 'warning');
        return;
    }
    
    if (isNaN(count) || count < 0) {
        showNotification('请输入有效的数量', 'warning');
        return;
    }
    
    // 添加规则
    state.rules.push({
        roi_id: parseInt(roiIndex, 10),
        class: className,
        operator: operator,
        count: count
    });
    
    // 标记有未保存的更改
    state.dirtyFlag = true;
    
    // 渲染规则列表
    renderRuleList();
    
    // 显示提示
    showNotification('规则已添加，请记得保存配置', 'info');
}

/**
 * 删除规则
 * @param {number} index - 规则索引
 */
function deleteRule(index) {
    // 确认删除
    if (!confirm('确定要删除这条规则吗？')) {
        return;
    }
    
    // 删除规则
    state.rules.splice(index, 1);
    
    // 标记有未保存的更改
    state.dirtyFlag = true;
    
    // 渲染规则列表
    renderRuleList();
    
    // 显示提示
    showNotification('规则已删除', 'info');
}

/**
 * 渲染规则列表
 */
function renderRuleList() {
    const container = document.getElementById('ruleListContainer');
    
    // 如果没有规则，显示提示
    if (state.rules.length === 0) {
        container.innerHTML = '<div class="alert alert-info">还没有添加任何规则，请使用上方表单添加规则。</div>';
        return;
    }
    
    // 创建表格
    const table = document.createElement('table');
    table.className = 'table table-hover';
    
    // 创建表头
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>ROI区域</th>
            <th>目标类别</th>
            <th>判断条件</th>
            <th>数量</th>
            <th>操作</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // 创建表格主体
    const tbody = document.createElement('tbody');
    
    // 添加每条规则
    state.rules.forEach((rule, index) => {
        const tr = document.createElement('tr');
        
        // ROI区域
        const tdRoi = document.createElement('td');
        tdRoi.textContent = `ROI ${rule.roi_id + 1}`;
        tr.appendChild(tdRoi);
        
        // 目标类别
        const tdClass = document.createElement('td');
        tdClass.textContent = rule.class;
        tr.appendChild(tdClass);
        
        // 判断条件
        const tdOperator = document.createElement('td');
        tdOperator.textContent = rule.operator;
        tr.appendChild(tdOperator);
        
        // 数量
        const tdCount = document.createElement('td');
        tdCount.textContent = rule.count;
        tr.appendChild(tdCount);
        
        // 操作按钮
        const tdAction = document.createElement('td');
        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-sm btn-danger';
        deleteButton.innerHTML = '<i class="bi bi-trash"></i>';
        deleteButton.onclick = function() {
            deleteRule(index);
        };
        tdAction.appendChild(deleteButton);
        tr.appendChild(tdAction);
        
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    
    // 添加到容器
    container.innerHTML = '';
    container.appendChild(table);
}

/**
 * 保存规则配置
 */
function saveRuleConfig() {
    // 获取规则名称
    const ruleName = document.getElementById('ruleNameInput').value.trim();
    
    // 验证输入
    if (!ruleName) {
        showNotification('请输入规则配置名称', 'warning');
        return;
    }
    
    if (!state.currentRoiConfig) {
        showNotification('请选择ROI配置', 'warning');
        return;
    }
    
    if (!state.currentModel) {
        showNotification('请选择检测模型', 'warning');
        return;
    }
    
    if (state.rules.length === 0) {
        showNotification('请至少添加一条规则', 'warning');
        return;
    }
    
    // 准备保存的数据
    const saveData = {
        rule_name: ruleName,
        roi_config: state.currentRoiConfig,
        model: state.currentModel,
        rules: state.rules
    };
    
    // 发送保存请求
    fetch('/api/logic-rules', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(saveData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新状态
                state.currentRuleName = ruleName;
                state.ruleConfigs[ruleName] = {
                    roi_config: state.currentRoiConfig,
                    model: state.currentModel,
                    rules: state.rules
                };
                
                // 更新选择器
                updateLogicRuleSelector();
                
                // 设置当前选中的规则
                document.getElementById('logicRuleSelector').value = ruleName;
                
                // 显示删除按钮
                document.getElementById('deleteRuleBtn').style.display = 'inline-block';
                
                // 清除脏标记
                state.dirtyFlag = false;
                
                // 显示成功提示
                showNotification(data.message || '规则配置保存成功', 'success');
            } else {
                showNotification(data.message || '保存失败', 'danger');
            }
        })
        .catch(error => {
            console.error('保存规则配置失败:', error);
            showNotification('保存规则配置失败，请检查网络连接', 'danger');
        });
}

/**
 * 删除规则配置
 */
function deleteRuleConfig() {
    // 确认删除
    if (!state.currentRuleName) {
        showNotification('请先选择要删除的规则配置', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除规则配置 "${state.currentRuleName}" 吗？`)) {
        return;
    }
    
    // 发送删除请求
    fetch(`/api/logic-rules?rule_name=${encodeURIComponent(state.currentRuleName)}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 删除本地状态中的规则配置
                delete state.ruleConfigs[state.currentRuleName];
                
                // 更新选择器
                updateLogicRuleSelector();
                
                // 重置表单
                resetForm();
                
                // 显示成功提示
                showNotification(data.message || '规则配置已删除', 'success');
            } else {
                showNotification(data.message || '删除失败', 'danger');
            }
        })
        .catch(error => {
            console.error('删除规则配置失败:', error);
            showNotification('删除规则配置失败，请检查网络连接', 'danger');
        });
}

/**
 * 显示通知
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, info, warning, danger)
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '400px';
    notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    
    // 设置通知内容
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}
