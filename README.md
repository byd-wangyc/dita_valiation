# DITA文件验证平台

这是一个用于验证DITA文件是否有错误的Web平台。用户可以上传DITA文件夹（ZIP格式），系统会自动验证文件结构并生成两个Excel验证报告。

## 功能特点

- 📁 支持上传ZIP格式的DITA文件夹
- ✅ 自动验证文件夹结构（检查infotree.xml和.dita文件）
- 🔄 自动执行DITA文件解析和验证流程
- 📊 生成两个Excel验证报告文件
- 🎨 现代化的Web界面，支持拖拽上传

## 系统要求

- Python 3.8+
- 现代浏览器（Chrome、Firefox、Edge等）

## 安装步骤

1. 克隆或下载项目到本地

2. 安装Python依赖：
```bash
pip install -r requirements.txt
```

3. 确保你的两个Python脚本已就绪：
   - `dita2json.py` - 将DITA文件转换为JSON并生成第一个Excel
   - `e_extract.py` - 从JSON提取数据并生成第二个Excel

## 使用方法

1. 启动服务器：
```bash
python main.py
```

或者使用uvicorn：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. 打开浏览器访问：
```
http://localhost:8000
```

3. 上传DITA文件夹：
   - 将DITA文件夹压缩为ZIP格式
   - 点击"选择文件"按钮或直接拖拽ZIP文件到上传区域
   - 系统会自动验证文件夹结构

4. 开始验证：
   - 点击"开始验证"按钮
   - 系统会依次执行dita2json.py和e_extract.py
   - 验证完成后可以下载两个Excel文件

## 项目结构

```
dita_valiation/
├── main.py              # FastAPI后端主文件
├── dita2json.py         # DITA转JSON脚本（需要你实现）
├── e_extract.py         # JSON提取脚本（需要你实现）
├── requirements.txt     # Python依赖列表
├── README.md           # 项目说明文档
├── static/             # 前端静态文件
│   ├── index.html      # 前端页面
│   ├── style.css       # 样式文件
│   └── script.js       # JavaScript文件
├── temp/               # 临时文件目录（自动创建）
└── output/             # 输出文件目录（自动创建）
```

## DITA文件夹结构要求

上传的DITA文件夹必须包含：
- `infotree.xml` 文件（必需）
- 至少一个 `.dita` 文件（必需）

如果文件夹结构不符合要求，前端会显示错误提示。

## API接口说明

### POST /api/upload
上传DITA文件夹（ZIP格式）

**请求：**
- Content-Type: multipart/form-data
- 参数：file (ZIP文件)

**响应：**
```json
{
  "success": true,
  "message": "验证通过，找到X个DITA文件",
  "temp_id": "临时ID",
  "dita_folder": "DITA文件夹路径"
}
```

### POST /api/validate
执行DITA文件验证

**请求：**
```json
{
  "temp_id": "临时ID"
}
```

**响应：**
```json
{
  "success": true,
  "message": "验证完成",
  "excel1": "/api/download/{temp_id}/excel1.xlsx",
  "excel2": "/api/download/{temp_id}/excel2.xlsx"
}
```

### GET /api/download/{temp_id}/{filename}
下载生成的Excel文件

## 开发说明

### 实现dita2json.py

你需要实现`dita2json.py`脚本，该脚本应该：
1. 接收三个参数：DITA文件夹路径、JSON输出文件夹路径、Excel输出文件路径
2. 读取DITA文件夹中的所有.dita文件
3. 解析DITA文件并转换为JSON格式
4. 将JSON文件保存到指定的输出文件夹
5. 生成第一个Excel验证报告

### 实现e_extract.py

你需要实现`e_extract.py`脚本，该脚本应该：
1. 接收两个参数：JSON文件夹路径、Excel输出文件路径
2. 读取JSON文件夹中的所有JSON文件
3. 提取所需的数据
4. 生成第二个Excel验证报告

## 注意事项

- 临时文件和输出文件会保存在`temp/`和`output/`目录中
- 建议定期清理这些目录以释放磁盘空间
- 确保有足够的磁盘空间存储上传的文件和生成的报告

## 故障排除

1. **上传失败**：检查文件是否为ZIP格式，文件夹结构是否符合要求
2. **验证失败**：检查dita2json.py和e_extract.py是否正确实现
3. **端口被占用**：修改main.py中的端口号或使用其他端口启动

## 许可证

本项目仅供学习和研究使用。

