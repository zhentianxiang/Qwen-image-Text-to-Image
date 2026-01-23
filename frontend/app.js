/**
 * Qwen Image Studio - 前端应用
 */

// 配置
const CONFIG = {
    apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
};

// DOM 元素
let editImageFile = null;
let batchImageFile = null;

// ==============================================
// 初始化
// ==============================================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSliders();
    initUploads();
    loadSettings();
    checkHealth();
});

// 初始化标签页切换
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.tab-panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.dataset.tab;
            
            navItems.forEach(n => n.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(`${tabId}-panel`).classList.add('active');
        });
    });
}

// 初始化滑块
function initSliders() {
    const sliders = document.querySelectorAll('input[type="range"]');
    
    sliders.forEach(slider => {
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        
        slider.addEventListener('input', () => {
            let value = slider.value;
            if (slider.step && slider.step !== '1') {
                value = parseFloat(value).toFixed(1);
            }
            valueDisplay.textContent = value;
        });
    });
}

// 初始化上传区域
function initUploads() {
    // 图像编辑上传
    initUploadArea('edit-upload-area', 'edit-image-input', 'edit-preview', 'edit-preview-img', (file) => {
        editImageFile = file;
    });
    
    // 批量编辑上传
    initUploadArea('batch-upload-area', 'batch-image-input', 'batch-preview', 'batch-preview-img', (file) => {
        batchImageFile = file;
    });
}

function initUploadArea(areaId, inputId, previewId, previewImgId, onFileSelected) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const previewImg = document.getElementById(previewImgId);
    const uploadContent = area.querySelector('.upload-content');
    
    // 点击上传
    area.addEventListener('click', (e) => {
        if (!e.target.closest('.remove-btn')) {
            input.click();
        }
    });
    
    // 文件选择
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });
    
    // 拖拽上传
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('dragover');
    });
    
    area.addEventListener('dragleave', () => {
        area.classList.remove('dragover');
    });
    
    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleFile(file);
        }
    });
    
    function handleFile(file) {
        // 验证文件大小
        if (file.size > 20 * 1024 * 1024) {
            showToast('文件大小不能超过 20MB', 'error');
            return;
        }
        
        // 验证文件类型
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showToast('仅支持 JPG、PNG、WebP 格式', 'error');
            return;
        }
        
        onFileSelected(file);
        
        // 显示预览
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            uploadContent.hidden = true;
            preview.hidden = false;
        };
        reader.readAsDataURL(file);
    }
}

// ==============================================
// 设置
// ==============================================
function loadSettings() {
    document.getElementById('api-url').value = CONFIG.apiUrl;
}

function saveSettings() {
    const apiUrl = document.getElementById('api-url').value.trim();
    if (apiUrl) {
        CONFIG.apiUrl = apiUrl.replace(/\/$/, ''); // 移除末尾斜杠
        localStorage.setItem('apiUrl', CONFIG.apiUrl);
        showToast('设置已保存', 'success');
        toggleSettings();
        checkHealth();
    } else {
        showToast('请输入有效的 API 地址', 'error');
    }
}

function toggleSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.toggle('active');
}

// ==============================================
// 健康检查
// ==============================================
async function checkHealth() {
    const indicator = document.getElementById('statusIndicator');
    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');
    
    try {
        const response = await fetch(`${CONFIG.apiUrl}/health`, {
            method: 'GET',
            timeout: 5000,
        });
        
        if (response.ok) {
            const data = await response.json();
            dot.className = 'status-dot online';
            text.textContent = data.gpu_available ? `GPU 可用 (${data.gpu_count})` : 'CPU 模式';
        } else {
            throw new Error('Health check failed');
        }
    } catch (error) {
        dot.className = 'status-dot offline';
        text.textContent = '服务离线';
    }
}

// ==============================================
// 文生图
// ==============================================
async function generateImage() {
    const prompt = document.getElementById('t2i-prompt').value.trim();
    
    if (!prompt) {
        showToast('请输入描述文本', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('negative_prompt', document.getElementById('t2i-negative').value.trim());
    formData.append('aspect_ratio', document.getElementById('t2i-ratio').value);
    formData.append('num_inference_steps', document.getElementById('t2i-steps').value);
    formData.append('true_cfg_scale', document.getElementById('t2i-cfg').value);
    formData.append('seed', document.getElementById('t2i-seed').value);
    
    showLoading('正在生成图像...', '这可能需要 30-60 秒，请耐心等待');
    
    try {
        const response = await fetch(`${CONFIG.apiUrl}/text-to-image`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '生成失败');
        }
        
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        displayResult('t2i-result', imageUrl, '文生图结果');
        showToast('图像生成成功', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ==============================================
// 图像编辑
// ==============================================
async function editImage() {
    if (!editImageFile) {
        showToast('请先上传图像', 'error');
        return;
    }
    
    const prompt = document.getElementById('edit-prompt').value.trim();
    if (!prompt) {
        showToast('请输入编辑描述', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('images', editImageFile);
    formData.append('prompt', prompt);
    formData.append('negative_prompt', document.getElementById('edit-negative').value.trim());
    formData.append('num_inference_steps', document.getElementById('edit-steps').value);
    formData.append('seed', document.getElementById('edit-seed').value);
    
    showLoading('正在编辑图像...', '这可能需要 30-60 秒，请耐心等待');
    
    try {
        const response = await fetch(`${CONFIG.apiUrl}/image-edit`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '编辑失败');
        }
        
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        displayResult('edit-result', imageUrl, '图像编辑结果');
        showToast('图像编辑成功', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function removeEditImage() {
    editImageFile = null;
    document.getElementById('edit-image-input').value = '';
    document.getElementById('edit-preview').hidden = true;
    document.querySelector('#edit-upload-area .upload-content').hidden = false;
}

// ==============================================
// 批量编辑
// ==============================================
async function batchEdit() {
    if (!batchImageFile) {
        showToast('请先上传图像', 'error');
        return;
    }
    
    const promptInputs = document.querySelectorAll('#prompts-list input');
    const prompts = Array.from(promptInputs)
        .map(input => input.value.trim())
        .filter(p => p);
    
    if (prompts.length === 0) {
        showToast('请输入至少一个编辑提示', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', batchImageFile);
    formData.append('prompts', prompts.join('|'));
    formData.append('negative_prompt', document.getElementById('batch-negative').value.trim());
    formData.append('num_inference_steps', document.getElementById('batch-steps').value);
    formData.append('seed', document.getElementById('batch-seed').value);
    
    showLoading('正在批量编辑...', `共 ${prompts.length} 个编辑任务，请耐心等待`);
    
    try {
        const response = await fetch(`${CONFIG.apiUrl}/image-edit/batch`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '批量编辑失败');
        }
        
        // 下载 ZIP 文件
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'batch_results.zip';
        a.click();
        
        displayBatchResult('batch-result', prompts.length);
        showToast('批量编辑完成，已下载 ZIP 文件', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function removeBatchImage() {
    batchImageFile = null;
    document.getElementById('batch-image-input').value = '';
    document.getElementById('batch-preview').hidden = true;
    document.querySelector('#batch-upload-area .upload-content').hidden = false;
}

function addPrompt() {
    const list = document.getElementById('prompts-list');
    const count = list.children.length;
    
    if (count >= 10) {
        showToast('最多添加 10 个编辑提示', 'warning');
        return;
    }
    
    const item = document.createElement('div');
    item.className = 'prompt-item';
    item.innerHTML = `
        <input type="text" placeholder="编辑提示 ${count + 1}">
        <button class="remove-prompt-btn" onclick="removePrompt(this)">×</button>
    `;
    list.appendChild(item);
    
    updateRemoveButtons();
}

function removePrompt(btn) {
    btn.parentElement.remove();
    updateRemoveButtons();
}

function updateRemoveButtons() {
    const buttons = document.querySelectorAll('#prompts-list .remove-prompt-btn');
    buttons.forEach(btn => {
        btn.disabled = buttons.length <= 1;
    });
}

// ==============================================
// 结果显示
// ==============================================
function displayResult(containerId, imageUrl, title) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="result-image">
            <img src="${imageUrl}" alt="${title}">
            <div class="result-actions">
                <button onclick="downloadImage('${imageUrl}', '${title}.png')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    下载图像
                </button>
                <button onclick="openInNewTab('${imageUrl}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                    新窗口打开
                </button>
            </div>
        </div>
    `;
}

function displayBatchResult(containerId, count) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="result-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--success)">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <p>批量编辑完成</p>
            <small>已生成 ${count} 张图像，ZIP 文件已自动下载</small>
        </div>
    `;
}

function downloadImage(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}

function openInNewTab(url) {
    window.open(url, '_blank');
}

// ==============================================
// 工具函数
// ==============================================
function randomSeed(inputId) {
    const input = document.getElementById(inputId);
    input.value = Math.floor(Math.random() * 2147483647);
}

function showLoading(text, tip) {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-tip').textContent = tip;
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// 定期检查健康状态
setInterval(checkHealth, 30000);
