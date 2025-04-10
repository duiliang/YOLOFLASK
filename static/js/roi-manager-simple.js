/**
 * ROI区域管理器 - 简化版
 * 一个文件实现所有功能，避免模块间通信问题
 */

// 初始化变量
let canvas, ctx;
let currentTool = 'rectangle'; // 当前活动工具：rectangle或select
let isDrawing = false; // 是否正在绘制
let currentShape = null; // 当前绘制的形状
let startX, startY; // 绘制起点
let roiConfigs = {}; // 所有ROI配置
let currentConfig = null; // 当前选中的配置
let rois = []; // 当前配置的ROI列表
let selectedRoiIndex = -1; // 当前选中的ROI索引
let configChanged = false; // 配置是否已更改
let dragStartPoint = null; // 拖动起点

// DOM元素
const backgroundImage = document.getElementById('backgroundImage');
const backgroundImageInput = document.getElementById('backgroundImageInput');
const backgroundUploadArea = document.getElementById('backgroundUploadArea');

/**
 * 初始化ROI管理器
 */
function initRoiManager() {
    console.log('ROI管理器初始化...');
    
    // 初始化Canvas
    canvas = document.getElementById('roiCanvas');
    ctx = canvas.getContext('2d');
    
    // 设置工具
    setActiveTool('rectangle');
    
    // 加载ROI配置
    loadRoiConfigs();
    
    // 设置事件监听器
    setupEventListeners();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 工具按钮
    document.getElementById('tool-rectangle').addEventListener('click', () => setActiveTool('rectangle'));
    document.getElementById('tool-select').addEventListener('click', () => setActiveTool('select'));
    
    // 清除按钮
    document.getElementById('clearCurrentRoi').addEventListener('click', clearCanvas);
    
    // 删除选中ROI
    document.getElementById('deleteSelectedRoi').addEventListener('click', deleteSelectedRoi);
    
    // 创建配置
    document.getElementById('createConfigBtn').addEventListener('click', createNewConfig);
    
    // 删除配置
    document.getElementById('deleteConfigBtn').addEventListener('click', deleteCurrentConfig);
    
    // 保存配置
    document.getElementById('saveConfigBtn').addEventListener('click', saveAllConfigs);
    
    // 配置选择
    document.getElementById('configSelect').addEventListener('change', onConfigChange);
    
    // 背景图片上传
    backgroundImageInput.addEventListener('change', handleBackgroundUpload);
    backgroundUploadArea.addEventListener('click', () => backgroundImageInput.click());
    
    // 背景图片加载完成事件
    backgroundImage.onload = function() {
        console.log('背景图片加载完成');
        backgroundImage.style.display = 'block';
        drawCanvas();
    };
    
    // 画布事件
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
}

/**
 * 设置当前活动工具
 * @param {string} tool - 工具名称：rectangle或select
 */
function setActiveTool(tool) {
    currentTool = tool;
    console.log('设置工具:', tool);
    
    // 更新按钮样式
    document.getElementById('tool-rectangle').classList.remove('tool-selected');
    document.getElementById('tool-select').classList.remove('tool-selected');
    
    if (tool === 'rectangle') {
        document.getElementById('tool-rectangle').classList.add('tool-selected');
        canvas.style.cursor = 'crosshair';
    } else if (tool === 'select') {
        document.getElementById('tool-select').classList.add('tool-selected');
        canvas.style.cursor = 'default';
    }
}

/**
 * 加载ROI配置
 */
function loadRoiConfigs() {
    fetch('/api/roi-configs')
        .then(response => response.json())
        .then(data => {
            roiConfigs = data;
            updateConfigSelect();
        })
        .catch(error => {
            console.error('加载ROI配置失败:', error);
            roiConfigs = {};
        });
}

/**
 * 更新配置选择下拉框
 */
function updateConfigSelect() {
    const configSelect = document.getElementById('configSelect');
    
    // 清空当前选项
    configSelect.innerHTML = '<option value="" disabled selected>请选择配置</option>';
    
    // 添加每个配置
    Object.keys(roiConfigs).forEach(configName => {
        const option = document.createElement('option');
        option.value = configName;
        option.textContent = configName;
        configSelect.appendChild(option);
    });
}

/**
 * 配置选择变化事件处理函数
 */
function onConfigChange() {
    const configSelect = document.getElementById('configSelect');
    
    // 如果当前配置已更改且不是第一次选择配置
    if (configChanged && currentConfig) {
        if (!confirm('当前配置未保存，是否切换？')) {
            // 恢复选择
            configSelect.value = currentConfig;
            return;
        }
    }
    
    // 获取新选择的配置
    const newConfig = configSelect.value;
    
    if (newConfig && roiConfigs[newConfig]) {
        // 保存新的当前配置
        currentConfig = newConfig;
        
        // 加载当前配置的ROI
        rois = roiConfigs[currentConfig].rois || [];
        
        // 加载背景图片
        if (roiConfigs[currentConfig].background) {
            loadBackgroundImage(roiConfigs[currentConfig].background);
        } else {
            clearBackgroundImage();
        }
        
        // 更新ROI列表
        updateRoiList();
        
        // 重新绘制画布
        drawCanvas();
        
        // 重置配置标志
        configChanged = false;
    }
}

/**
 * 更新ROI列表UI
 */
function updateRoiList() {
    const roiList = document.getElementById('roiList');
    
    // 清空列表
    roiList.innerHTML = '';
    
    // 如果没有当前配置，则返回
    if (!currentConfig || !roiConfigs[currentConfig]) return;
    
    // 添加每个ROI到列表
    rois.forEach((roi, index) => {
        const listItem = document.createElement('button');
        listItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        
        // 计算宽度和高度
        let width, height;
        
        if (roi.type === 'rectangle') {
            width = roi.x2 - roi.x1;
            height = roi.y2 - roi.y1;
            
            listItem.innerHTML = `
                <span>ROI ${index + 1}: ${width}x${height}</span>
                <span class="badge bg-primary rounded-pill">${roi.x1},${roi.y1}</span>
            `;
        } else {
            listItem.innerHTML = `<span>ROI ${index + 1}</span>`;
        }
        
        // 点击列表项选择对应的ROI
        listItem.addEventListener('click', () => {
            selectedRoiIndex = index;
            document.getElementById('deleteSelectedRoi').style.display = 'inline-block';
            drawCanvas();
        });
        
        roiList.appendChild(listItem);
    });
}

/**
 * 创建新配置
 */
function createNewConfig() {
    const configNameInput = document.getElementById('configNameInput');
    const configName = configNameInput.value.trim();
    
    if (!configName) {
        alert('请输入配置名称');
        return;
    }
    
    // 检查名称是否已存在
    if (roiConfigs[configName]) {
        alert('配置名称已存在');
        return;
    }
    
    // 创建新配置
    roiConfigs[configName] = {
        name: configName,
        background: null,
        rois: []
    };
    
    // 更新配置选择下拉框
    updateConfigSelect();
    
    // 选择新创建的配置
    document.getElementById('configSelect').value = configName;
    currentConfig = configName;
    rois = [];
    
    // 清空画布
    clearCanvas();
    
    // 清空配置名称输入框
    configNameInput.value = '';
    
    // 更新配置标志
    configChanged = true;
}

/**
 * 删除当前配置
 */
function deleteCurrentConfig() {
    if (!currentConfig) {
        alert('请先选择一个配置');
        return;
    }
    
    if (!confirm(`确定要删除配置 "${currentConfig}" 吗？`)) {
        return;
    }
    
    // 删除配置
    fetch(`/api/roi-config/${currentConfig}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 从本地删除
            delete roiConfigs[currentConfig];
            
            // 更新配置选择下拉框
            updateConfigSelect();
            
            // 清空画布
            clearCanvas();
            
            // 重置当前配置
            currentConfig = null;
            rois = [];
            
            // 更新UI
            updateRoiList();
            clearBackgroundImage();
            
            alert('配置删除成功');
        } else {
            alert('删除失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('删除配置出错:', error);
        alert('删除配置出错');
    });
}

/**
 * 保存所有配置
 */
function saveAllConfigs() {
    if (!currentConfig) {
        alert('请先创建或选择一个配置');
        return;
    }
    
    // 保存当前配置的ROIs
    if (currentConfig && roiConfigs[currentConfig]) {
        roiConfigs[currentConfig].rois = rois;
    }
    
    // 发送到服务器
    fetch('/api/roi-configs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(roiConfigs)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('配置保存成功');
            configChanged = false;
        } else {
            alert('保存失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('保存配置出错:', error);
        alert('保存配置出错');
    });
}

/**
 * 删除选中的ROI
 */
function deleteSelectedRoi() {
    if (selectedRoiIndex === -1) return;
    
    // 删除选中的ROI
    rois.splice(selectedRoiIndex, 1);
    
    // 重置选中索引
    selectedRoiIndex = -1;
    
    // 隐藏删除按钮
    document.getElementById('deleteSelectedRoi').style.display = 'none';
    
    // 更新ROI列表
    updateRoiList();
    
    // 重新绘制画布
    drawCanvas();
    
    // 标记配置已更改
    configChanged = true;
}

/**
 * 处理背景图片上传
 */
function handleBackgroundUpload(event) {
    const file = event.target.files[0];
    
    if (!file) return;
    
    // 检查是否为图像文件
    if (!file.type.match('image.*')) {
        alert('请选择图像文件');
        return;
    }
    
    // 更新上传区域提示
    backgroundUploadArea.innerHTML = '<p class="text-info"><i class="bi bi-hourglass-split"></i> 正在处理图片...</p>';
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    
    // 发送到服务器
    fetch('/api/upload-roi-background', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('背景图片上传成功:', data);
            
            // 更新上传区域提示
            backgroundUploadArea.innerHTML = '<p class="text-success"><i class="bi bi-check-circle"></i> 背景图片已加载</p>';
            
            // 加载背景图片
            loadBackgroundImage(data.url);
            
            // 保存背景图片URL到当前配置
            if (currentConfig && roiConfigs[currentConfig]) {
                roiConfigs[currentConfig].background = data.url;
                configChanged = true;
            }
        } else {
            // 显示错误
            backgroundUploadArea.innerHTML = `<p class="text-danger"><i class="bi bi-exclamation-triangle"></i> ${data.error}</p>`;
            alert('上传失败: ' + data.error);
        }
    })
    .catch(error => {
        // 显示错误
        backgroundUploadArea.innerHTML = '<p class="text-danger"><i class="bi bi-exclamation-triangle"></i> 上传失败</p>';
        console.error('上传背景图片出错:', error);
        alert('上传背景图片出错');
    });
}

/**
 * 加载背景图片
 * @param {string} url - 图片URL
 */
function loadBackgroundImage(url) {
    if (!url) return;
    
    console.log('加载背景图片:', url);
    
    // 添加时间戳防止缓存
    const cacheBustUrl = url.includes('?') ? 
        `${url}&t=${new Date().getTime()}` : 
        `${url}?t=${new Date().getTime()}`;
    
    // 设置图片源
    backgroundImage.src = cacheBustUrl;
}

/**
 * 清除背景图片
 */
function clearBackgroundImage() {
    backgroundImage.src = '';
    backgroundImage.style.display = 'none';
    backgroundUploadArea.innerHTML = '<i class="bi bi-upload fs-2"></i><p class="mb-0">点击上传背景图片 (将调整为640x640)</p>';
}

/**
 * 处理鼠标按下事件
 */
function handleMouseDown(event) {
    if (!currentConfig) {
        alert('请先创建或选择一个配置');
        return;
    }
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    console.log('鼠标按下:', x, y, '当前工具:', currentTool);
    
    if (currentTool === 'rectangle') {
        isDrawing = true;
        startX = x;
        startY = y;
        currentShape = { type: 'rectangle', x1: x, y1: y, x2: x, y2: y, color: getRandomColor() };
    } else if (currentTool === 'select') {
        // 查找是否点击了某个ROI
        let found = false;
        for (let i = 0; i < rois.length; i++) {
            if (isPointInRoi(x, y, rois[i])) {
                selectedRoiIndex = i;
                found = true;
                
                // 显示删除按钮
                document.getElementById('deleteSelectedRoi').style.display = 'inline-block';
                
                // 开始拖动
                dragStartPoint = { x, y };
                
                break;
            }
        }
        
        if (!found) {
            // 取消选择
            selectedRoiIndex = -1;
            document.getElementById('deleteSelectedRoi').style.display = 'none';
            dragStartPoint = null;
        }
    }
    
    drawCanvas();
}

/**
 * 处理鼠标移动事件
 */
function handleMouseMove(event) {
    if (!isDrawing && currentTool !== 'select') return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    if (isDrawing && currentTool === 'rectangle') {
        currentShape.x2 = x;
        currentShape.y2 = y;
        drawCanvas();
    }
}

/**
 * 处理鼠标松开事件
 */
function handleMouseUp(event) {
    if (!isDrawing && currentTool !== 'select') return;
    
    if (isDrawing && currentTool === 'rectangle') {
        isDrawing = false;
        
        if (currentShape) {
            // 标准化矩形坐标(确保x1 <= x2, y1 <= y2)
            const x1 = Math.min(currentShape.x1, currentShape.x2);
            const y1 = Math.min(currentShape.y1, currentShape.y2);
            const x2 = Math.max(currentShape.x1, currentShape.x2);
            const y2 = Math.max(currentShape.y1, currentShape.y2);
            
            // 如果矩形太小，则忽略
            if (x2 - x1 < 10 || y2 - y1 < 10) {
                currentShape = null;
                drawCanvas();
                return;
            }
            
            // 创建ROI对象
            const roi = {
                type: 'rectangle',
                x1: x1,
                y1: y1,
                x2: x2,
                y2: y2,
                color: currentShape.color
            };
            
            // 添加到ROI列表
            rois.push(roi);
            
            // 更新ROI列表
            updateRoiList();
            
            // 标记配置已更改
            configChanged = true;
            
            // 清除当前形状
            currentShape = null;
            
            // 切换到选择工具
            setActiveTool('select');
        }
    } else if (currentTool === 'select') {
        dragStartPoint = null;
    }
    
    drawCanvas();
}

/**
 * 清空画布
 */
function clearCanvas() {
    // 清空ROI列表
    rois = [];
    
    // 重置选中索引
    selectedRoiIndex = -1;
    
    // 清除当前绘制
    isDrawing = false;
    currentShape = null;
    
    // 隐藏删除按钮
    document.getElementById('deleteSelectedRoi').style.display = 'none';
    
    // 更新ROI列表
    updateRoiList();
    
    // 重新绘制画布
    drawCanvas();
    
    // 标记配置已更改
    configChanged = true;
}

/**
 * 绘制Canvas内容
 */
function drawCanvas() {
    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制所有保存的ROI
    for (let i = 0; i < rois.length; i++) {
        const roi = rois[i];
        
        // 设置样式
        ctx.strokeStyle = roi.color || '#007bff';
        ctx.fillStyle = roi.color ? `${roi.color}33` : 'rgba(0, 123, 255, 0.2)';
        ctx.lineWidth = i === selectedRoiIndex ? 3 : 2;
        
        // 绘制矩形
        ctx.beginPath();
        ctx.rect(roi.x1, roi.y1, roi.x2 - roi.x1, roi.y2 - roi.y1);
        ctx.fill();
        ctx.stroke();
        
        // 如果被选中，绘制控制点
        if (i === selectedRoiIndex) {
            drawControlPoints(roi);
        }
    }
    
    // 绘制当前正在创建的矩形
    if (isDrawing && currentShape && currentShape.type === 'rectangle') {
        // 设置样式
        ctx.strokeStyle = currentShape.color || '#007bff';
        ctx.fillStyle = currentShape.color ? `${currentShape.color}33` : 'rgba(0, 123, 255, 0.2)';
        ctx.lineWidth = 2;
        
        // 绘制矩形
        const width = currentShape.x2 - currentShape.x1;
        const height = currentShape.y2 - currentShape.y1;
        
        ctx.beginPath();
        ctx.rect(currentShape.x1, currentShape.y1, width, height);
        ctx.fill();
        ctx.stroke();
    }
}

/**
 * 绘制控制点
 */
function drawControlPoints(roi) {
    const controlPoints = [
        { x: roi.x1, y: roi.y1 },
        { x: roi.x2, y: roi.y1 },
        { x: roi.x1, y: roi.y2 },
        { x: roi.x2, y: roi.y2 },
        { x: (roi.x1 + roi.x2) / 2, y: roi.y1 },
        { x: (roi.x1 + roi.x2) / 2, y: roi.y2 },
        { x: roi.x1, y: (roi.y1 + roi.y2) / 2 },
        { x: roi.x2, y: (roi.y1 + roi.y2) / 2 }
    ];
    
    // 绘制控制点
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    
    controlPoints.forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
    });
}

/**
 * 检查点是否在ROI内
 */
function isPointInRoi(x, y, roi) {
    return x >= roi.x1 && x <= roi.x2 && y >= roi.y1 && y <= roi.y2;
}

/**
 * 生成随机颜色
 */
function getRandomColor() {
    const colors = [
        '#007bff', // 蓝色
        '#28a745', // 绿色
        '#dc3545', // 红色
        '#fd7e14', // 橙色
        '#6f42c1', // 紫色
        '#20c997', // 青绿色
        '#e83e8c', // 粉色
        '#6c757d'  // 灰色
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// 页面加载时初始化ROI管理器
document.addEventListener('DOMContentLoaded', initRoiManager);
