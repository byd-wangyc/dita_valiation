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
    progressContainer.style.display = 'none';
    validateBtn.disabled = false;
    validateBtn.style.display = 'inline-block';
});

// 上传文件到服务器
function uploadFile(file) {
    validationSection.style.display = 'block';
    validateBtn.style.display = 'none';
    progressContainer.style.display = 'block';
    showProgress(0, '正在上传文件...');

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
            const rawPercent = Math.round((event.loaded / event.total) * 100);
            const percent = Math.min(99, rawPercent);
            const text = rawPercent >= 100
                ? '上传完成，正在处理...'
                : `正在上传文件... ${percent}%`;
            showProgress(percent, text);
        } else {
            showProgress(5, '正在上传文件...');
        }
    };

    xhr.onload = () => {
        let data = null;
        try {
            data = JSON.parse(xhr.responseText || '{}');
        } catch (error) {
            showError('上传失败：服务器返回无效响应');
            resetUpload();
            return;
        }

        if (xhr.status >= 200 && xhr.status < 300 && data.success) {
            tempId = data.temp_id;
            showProgress(100, '文件上传成功，可以开始验证');
            hideError();
            validateBtn.style.display = 'inline-block';
        } else {
            showError(data.error || '上传失败');
            resetUpload();
        }
    };

    xhr.onerror = () => {
        showError('上传失败: 网络错误');
        resetUpload();
    };

    xhr.send(formData);
}

// 开始验证
validateBtn.addEventListener('click', async () => {
    if (!tempId) {
        showError('请先上传文件');
        return;
    }
    
    try {
        validateBtn.disabled = true;
        validateBtn.style.display = 'none';
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
            validateBtn.style.display = 'inline-block';
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        showError('验证过程出错: ' + error.message);
        validateBtn.disabled = false;
        validateBtn.style.display = 'inline-block';
        progressContainer.style.display = 'none';
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
    errorSection.style.display = 'none';
    resultMessage.textContent = data.message || '验证完成！';
    
    downloadButtons.innerHTML = '';
    
    const excel1Url = data.excel1 || (tempId ? `/api/download/${tempId}/excel1.xlsx` : '');
    if (excel1Url) {
        const btn1 = document.createElement('a');
        btn1.href = excel1Url;
        btn1.className = 'download-btn';
        btn1.textContent = '下载Excel文件1';
        btn1.download = 'excel1.xlsx';
        downloadButtons.appendChild(btn1);
    }
    
    const excel2Url = data.excel2 || (tempId ? `/api/download/${tempId}/excel2.xlsx` : '');
    if (excel2Url) {
        const btn2 = document.createElement('a');
        btn2.href = excel2Url;
        btn2.className = 'download-btn';
        btn2.textContent = '下载Excel文件2';
        btn2.download = 'excel2.xlsx';
        downloadButtons.appendChild(btn2);
    }
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
    validateBtn.disabled = false;
    validateBtn.style.display = 'inline-block';
}
