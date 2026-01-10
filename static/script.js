// 全局变量
let uploadedFile = null;
let tempId = null;

// DOM元素
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadBox = document.getElementById('uploadBox');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeBtn = document.getElementById('removeBtn');
const validationSection = document.getElementById('validationSection');
const validateBtn = document.getElementById('validateBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const resultMessage = document.getElementById('resultMessage');
const downloadButtons = document.getElementById('downloadButtons');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

// 上传按钮点击事件
uploadBtn.addEventListener('click', () => {
    fileInput.click();
});

// 文件选择事件
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// 拖拽上传
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('dragover');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('dragover');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.endsWith('.zip')) {
            handleFileSelect(file);
        } else {
            showError('请上传ZIP格式的文件');
        }
    }
});

// 处理文件选择
function handleFileSelect(file) {
    if (!file.name.endsWith('.zip')) {
        showError('请上传ZIP格式的文件');
        return;
    }
    
    uploadedFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    uploadBtn.style.display = 'none';
    
    // 上传文件
    uploadFile(file);
}

// 移除文件
removeBtn.addEventListener('click', () => {
    uploadedFile = null;
    tempId = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    uploadBtn.style.display = 'inline-block';
    validationSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
});

// 上传文件到服务器
async function uploadFile(file) {
    try {
        showProgress(10, '正在上传文件...');
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            tempId = data.temp_id;
            showProgress(50, '文件上传成功，准备验证...');
            validationSection.style.display = 'block';
            hideError();
        } else {
            showError(data.error || '上传失败');
            resetUpload();
        }
    } catch (error) {
        showError('上传失败: ' + error.message);
        resetUpload();
    }
}

// 开始验证
validateBtn.addEventListener('click', async () => {
    if (!tempId) {
        showError('请先上传文件');
        return;
    }
    
    try {
        validateBtn.disabled = true;
        progressContainer.style.display = 'block';
        showProgress(30, '正在运行dita2json.py...');
        
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ temp_id: tempId })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showProgress(80, '正在运行e_extract.py...');
            await new Promise(resolve => setTimeout(resolve, 500));
            showProgress(100, '验证完成！');
            
            setTimeout(() => {
                showResult(data);
            }, 500);
        } else {
            showError(data.error || '验证失败');
            validateBtn.disabled = false;
        }
    } catch (error) {
        showError('验证过程出错: ' + error.message);
        validateBtn.disabled = false;
    }
});

// 显示进度
function showProgress(percent, text) {
    progressFill.style.width = percent + '%';
    progressText.textContent = text;
}

// 显示结果
function showResult(data) {
    progressContainer.style.display = 'none';
    resultSection.style.display = 'block';
    resultMessage.textContent = data.message || '验证完成！';
    
    downloadButtons.innerHTML = '';
    
    if (data.excel1) {
        const btn1 = document.createElement('a');
        btn1.href = data.excel1;
        btn1.className = 'download-btn';
        btn1.textContent = '下载Excel文件1';
        btn1.download = 'excel1.xlsx';
        downloadButtons.appendChild(btn1);
    }
    
    if (data.excel2) {
        const btn2 = document.createElement('a');
        btn2.href = data.excel2;
        btn2.className = 'download-btn';
        btn2.textContent = '下载Excel文件2';
        btn2.download = 'excel2.xlsx';
        downloadButtons.appendChild(btn2);
    }
    
    validateBtn.disabled = false;
}

// 显示错误
function showError(message) {
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    resultSection.style.display = 'none';
}

// 隐藏错误
function hideError() {
    errorSection.style.display = 'none';
}

// 重置上传状态
function resetUpload() {
    uploadedFile = null;
    tempId = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    uploadBtn.style.display = 'inline-block';
    validationSection.style.display = 'none';
    progressContainer.style.display = 'none';
}

